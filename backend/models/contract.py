from sqlalchemy import Column, String, Text, JSON, DateTime, Boolean, Float, Integer, LargeBinary
from sqlalchemy.sql import func
import uuid

from db.base import Base
from core.constants import ContractStatus


class Contract(Base):
    """SQLAlchemy model for contracts."""

    __tablename__ = "contracts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # File metadata
    file_name = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    file_mime_type = Column(String(100), default="application/pdf")

    # PDF binary storage
    pdf_content = Column(LargeBinary, nullable=True)

    # Extracted content
    raw_text = Column(Text, nullable=True)

    # Processing status
    status = Column(
        String(50),
        default=ContractStatus.PENDING.value,
        index=True
    )

    # Extracted structured data (JSON)
    extracted_data = Column(JSON, default=dict)

    # Validation results
    validation_issues = Column(JSON, default=list)
    requires_human_review = Column(Boolean, default=False, index=True)
    review_reasons = Column(JSON, default=list)

    # Metrics
    confidence_score = Column(Float, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)

    # Human review
    human_approved = Column(Boolean, default=False)
    reviewer_notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    processed_at = Column(DateTime, nullable=True)
