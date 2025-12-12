from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from io import BytesIO

from db.session import get_db
from models.contract import Contract
from api.schemas.contract import (
    ContractResponse,
    ContractListResponse,
    ContractUpdateRequest,
    ExtractedDataSchema,
    ValidationIssue
)
from core.constants import ContractStatus

router = APIRouter()


@router.get("/contracts", response_model=ContractListResponse)
def list_contracts(
    status: Optional[str] = None,
    requires_review: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    List all contracts with optional filtering.

    Query params:
    - status: Filter by contract status
    - requires_review: Filter by requires_human_review flag
    """
    query = db.query(Contract)

    if status:
        query = query.filter(Contract.status == status)

    if requires_review is not None:
        query = query.filter(Contract.requires_human_review == requires_review)

    # Order by most recent first
    contracts = query.order_by(Contract.created_at.desc()).all()

    contract_responses = []
    for c in contracts:
        # Parse extracted_data from JSON
        extracted_data = None
        if c.extracted_data:
            try:
                extracted_data = ExtractedDataSchema(**c.extracted_data)
            except Exception:
                extracted_data = ExtractedDataSchema(risk_score=50)

        # Parse validation_issues from JSON
        validation_issues = []
        if c.validation_issues:
            for issue in c.validation_issues:
                try:
                    validation_issues.append(ValidationIssue(**issue))
                except Exception:
                    pass

        contract_responses.append(ContractResponse(
            id=c.id,
            file_name=c.file_name,
            status=ContractStatus(c.status),
            created_at=c.created_at,
            processed_at=c.processed_at,
            extracted_data=extracted_data,
            validation_issues=validation_issues,
            requires_human_review=c.requires_human_review,
            review_reasons=c.review_reasons or [],
            confidence_score=c.confidence_score,
            human_approved=c.human_approved
        ))

    return ContractListResponse(
        contracts=contract_responses,
        total=len(contract_responses)
    )


@router.get("/contracts/{contract_id}", response_model=ContractResponse)
def get_contract(
    contract_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific contract by ID."""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Parse extracted_data from JSON
    extracted_data = None
    if contract.extracted_data:
        try:
            extracted_data = ExtractedDataSchema(**contract.extracted_data)
        except Exception:
            extracted_data = ExtractedDataSchema(risk_score=50)

    # Parse validation_issues from JSON
    validation_issues = []
    if contract.validation_issues:
        for issue in contract.validation_issues:
            try:
                validation_issues.append(ValidationIssue(**issue))
            except Exception:
                pass

    return ContractResponse(
        id=contract.id,
        file_name=contract.file_name,
        status=ContractStatus(contract.status),
        created_at=contract.created_at,
        processed_at=contract.processed_at,
        extracted_data=extracted_data,
        validation_issues=validation_issues,
        requires_human_review=contract.requires_human_review,
        review_reasons=contract.review_reasons or [],
        confidence_score=contract.confidence_score,
        human_approved=contract.human_approved
    )


@router.put("/contracts/{contract_id}", response_model=ContractResponse)
def update_contract(
    contract_id: str,
    update_request: ContractUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update contract extracted data (human correction).

    This endpoint allows human reviewers to correct AI extractions.
    """
    contract = db.query(Contract).filter(Contract.id == contract_id).first()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Update extracted data
    contract.extracted_data = update_request.extracted_data.model_dump()
    contract.human_approved = update_request.human_approved
    contract.reviewer_notes = update_request.reviewer_notes
    contract.reviewed_at = datetime.utcnow()

    # If human approved, update status
    if update_request.human_approved:
        contract.status = ContractStatus.APPROVED.value
        contract.requires_human_review = False

    db.commit()
    db.refresh(contract)

    # Parse for response
    extracted_data = ExtractedDataSchema(**contract.extracted_data)
    validation_issues = []
    if contract.validation_issues:
        for issue in contract.validation_issues:
            try:
                validation_issues.append(ValidationIssue(**issue))
            except Exception:
                pass

    return ContractResponse(
        id=contract.id,
        file_name=contract.file_name,
        status=ContractStatus(contract.status),
        created_at=contract.created_at,
        processed_at=contract.processed_at,
        extracted_data=extracted_data,
        validation_issues=validation_issues,
        requires_human_review=contract.requires_human_review,
        review_reasons=contract.review_reasons or [],
        confidence_score=contract.confidence_score,
        human_approved=contract.human_approved
    )


@router.get("/contracts/{contract_id}/text")
def get_contract_text(
    contract_id: str,
    db: Session = Depends(get_db)
):
    """Get the raw extracted text of a contract."""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    return {"text": contract.raw_text or ""}


@router.delete("/contracts/{contract_id}")
def delete_contract(
    contract_id: str,
    db: Session = Depends(get_db)
):
    """Delete a contract."""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    db.delete(contract)
    db.commit()

    return {"message": "Contract deleted successfully"}


@router.post("/contracts/load-sample")
async def load_sample_contracts(
    n: int = 3,
    db: Session = Depends(get_db)
):
    """
    Load sample contracts from the CUAD dataset (HuggingFace) and process them.

    This endpoint:
    1. Downloads contracts from https://huggingface.co/datasets/theatticusproject/cuad
    2. Runs each through the LLM extraction pipeline
    3. Validates against business rules
    4. Stores in the database

    Args:
        n: Number of sample contracts to load (default: 3, max: 10)

    Returns:
        List of processed contracts with their extraction results
    """
    import uuid
    import time
    from services.dataset_loader import get_dataset_loader
    from services.extraction_chain import ExtractionChain
    from services.validation_agent import ValidationAgent

    # Limit to prevent overloading
    n = min(n, 10)

    # Load dataset from HuggingFace
    loader = get_dataset_loader()
    samples = loader.get_sample_contracts(n=n)

    results = []

    for sample in samples:
        start_time = time.time()

        # Create contract record with PDF if available
        pdf_bytes = sample.get('pdf_bytes')
        contract = Contract(
            id=str(uuid.uuid4()),
            file_name=f"CUAD_{sample['title'][:50]}.pdf" if pdf_bytes else f"CUAD_{sample['title'][:50]}.txt",
            file_size=len(pdf_bytes) if pdf_bytes else len(sample['text']),
            pdf_content=pdf_bytes,
            file_mime_type="application/pdf" if pdf_bytes else "text/plain",
            raw_text=sample['text'],
            status=ContractStatus.PROCESSING.value
        )
        db.add(contract)
        db.commit()

        try:
            # Extract with LLM
            extraction_chain = ExtractionChain()
            extracted_data, confidence_score = await extraction_chain.extract(sample['text'])

            contract.extracted_data = extracted_data.model_dump()
            contract.confidence_score = confidence_score

            # Validate
            validation_agent = ValidationAgent()
            validation_result = await validation_agent.validate(extracted_data)

            contract.validation_issues = [
                issue.model_dump() for issue in validation_result.issues
            ]
            contract.requires_human_review = validation_result.requires_review
            contract.review_reasons = validation_result.review_reasons

            # Set status
            if validation_result.requires_review:
                contract.status = ContractStatus.REQUIRES_HUMAN_REVIEW.value
            else:
                contract.status = ContractStatus.APPROVED.value

            contract.processing_time_ms = int((time.time() - start_time) * 1000)

            db.commit()

            results.append({
                "id": contract.id,
                "title": sample['title'],
                "status": contract.status,
                "confidence_score": confidence_score,
                "requires_human_review": contract.requires_human_review,
                "processing_time_ms": contract.processing_time_ms
            })

        except Exception as e:
            contract.status = ContractStatus.REJECTED.value
            db.commit()
            results.append({
                "id": contract.id,
                "title": sample['title'],
                "status": "rejected",
                "error": str(e)
            })

    return {
        "loaded": len(results),
        "contracts": results
    }


# ============================================
# PDF Serving Endpoint
# ============================================

@router.get("/contracts/{contract_id}/pdf")
def get_contract_pdf(
    contract_id: str,
    db: Session = Depends(get_db)
):
    """
    Get the original PDF file of a contract.

    Returns the PDF as a streaming response for viewing in browser.
    """
    contract = db.query(Contract).filter(Contract.id == contract_id).first()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if not contract.pdf_content:
        raise HTTPException(status_code=404, detail="PDF not available for this contract")

    return StreamingResponse(
        BytesIO(contract.pdf_content),
        media_type=contract.file_mime_type or "application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=\"{contract.file_name}\"",
            "Content-Length": str(len(contract.pdf_content))
        }
    )
