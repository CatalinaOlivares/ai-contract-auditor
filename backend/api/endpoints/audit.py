from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import time
import uuid

from db.session import get_db
from models.contract import Contract
from services.pdf_extractor import PDFExtractor
from services.extraction_chain import ExtractionChain
from services.validation_agent import ValidationAgent
from api.schemas.contract import AuditResponse, ExtractedDataSchema, ValidationIssue
from core.constants import ContractStatus

router = APIRouter()


@router.post("/audit", response_model=AuditResponse)
async def audit_contract(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Audit a contract PDF.

    Pipeline:
    1. Validate PDF file
    2. Extract text from PDF
    3. Extract structured data with LLM
    4. Validate against business rules
    5. Persist results
    6. Return audit response
    """
    start_time = time.time()

    # 1. Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are accepted"
        )

    # Read file content
    content = await file.read()

    if len(content) == 0:
        raise HTTPException(
            status_code=400,
            detail="Empty file uploaded"
        )

    # 2. Create initial contract record with PDF content
    contract = Contract(
        id=str(uuid.uuid4()),
        file_name=file.filename,
        file_size=len(content),
        pdf_content=content,  # Store original PDF
        file_mime_type="application/pdf",
        status=ContractStatus.PROCESSING.value
    )
    db.add(contract)
    db.commit()

    try:
        # 3. Extract text from PDF
        pdf_extractor = PDFExtractor()
        raw_text = pdf_extractor.extract_text(content)
        contract.raw_text = raw_text

        if not raw_text.strip():
            raise ValueError("Could not extract any text from PDF")

        # 4. Extract structured data with LLM
        extraction_chain = ExtractionChain()
        extracted_data, confidence_score = await extraction_chain.extract(raw_text)

        contract.extracted_data = extracted_data.model_dump()
        contract.confidence_score = confidence_score

        # 5. Validate with business rules
        validation_agent = ValidationAgent()
        validation_result = await validation_agent.validate(extracted_data)

        contract.validation_issues = [
            issue.model_dump() for issue in validation_result.issues
        ]
        contract.requires_human_review = validation_result.requires_review
        contract.review_reasons = validation_result.review_reasons

        # 6. Determine final status
        if validation_result.requires_review:
            contract.status = ContractStatus.REQUIRES_HUMAN_REVIEW.value
        else:
            contract.status = ContractStatus.APPROVED.value

        contract.processed_at = datetime.utcnow()
        contract.processing_time_ms = int((time.time() - start_time) * 1000)

        db.commit()
        db.refresh(contract)

        return AuditResponse(
            id=contract.id,
            status=ContractStatus(contract.status),
            extracted_data=extracted_data,
            validation_issues=validation_result.issues,
            requires_human_review=validation_result.requires_review,
            review_reasons=validation_result.review_reasons,
            confidence_score=confidence_score,
            processing_time_ms=contract.processing_time_ms
        )

    except Exception as e:
        contract.status = ContractStatus.REJECTED.value
        contract.validation_issues = [{
            "field": "processing",
            "rule": "system_error",
            "message": str(e),
            "severity": "critical"
        }]
        db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing contract: {str(e)}"
        )
