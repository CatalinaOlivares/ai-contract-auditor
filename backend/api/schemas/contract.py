from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime

from core.constants import ContractStatus


class PartySchema(BaseModel):
    """Represents a party in the contract."""

    name: str = Field(..., description="Name of the party")
    role: Optional[str] = Field(None, description="Role in contract (e.g., Seller, Buyer)")


class ExtractedDataSchema(BaseModel):
    """Structured data extracted from the contract by the LLM."""

    parties: List[PartySchema] = Field(default_factory=list, description="List of contract parties")
    effective_date: Optional[str] = Field(None, description="Contract start date (ISO format)")
    contract_duration_months: Optional[int] = Field(
        None,
        ge=0,
        description="Contract duration in months"
    )
    contract_duration_raw: Optional[str] = Field(
        None,
        description="Original duration text (e.g., 'two years and one day')"
    )
    jurisdiction: Optional[str] = Field(None, description="Governing law jurisdiction (city/country)")
    risk_score: int = Field(
        50,
        ge=1,
        le=100,
        description="Risk score based on aggressive language (1-100)"
    )


class ValidationIssue(BaseModel):
    """Represents a validation issue found during audit."""

    field: str = Field(..., description="Field with the issue")
    rule: str = Field(..., description="Rule that was violated")
    message: str = Field(..., description="Human-readable message")
    severity: str = Field("warning", description="Severity: warning, error, critical")
    reasoning: Optional[str] = Field(None, description="Agent's reasoning for the issue")


class ContractResponse(BaseModel):
    """Response schema for contract data."""

    id: str
    file_name: str
    status: ContractStatus
    created_at: datetime
    processed_at: Optional[datetime] = None
    extracted_data: Optional[ExtractedDataSchema] = None
    validation_issues: List[ValidationIssue] = Field(default_factory=list)
    requires_human_review: bool = False
    review_reasons: List[str] = Field(default_factory=list)
    confidence_score: Optional[float] = None
    human_approved: bool = False

    class Config:
        from_attributes = True


class ContractListResponse(BaseModel):
    """Response for list of contracts."""

    contracts: List[ContractResponse]
    total: int


class ContractUpdateRequest(BaseModel):
    """Request to update extracted data (human correction)."""

    extracted_data: ExtractedDataSchema
    human_approved: bool = False
    reviewer_notes: Optional[str] = None


class AuditResponse(BaseModel):
    """Response from the audit endpoint."""

    id: str
    status: ContractStatus
    extracted_data: ExtractedDataSchema
    validation_issues: List[ValidationIssue]
    requires_human_review: bool
    review_reasons: List[str]
    confidence_score: float
    processing_time_ms: int
