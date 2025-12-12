from enum import Enum


class ContractStatus(str, Enum):
    """Status of a contract in the audit pipeline."""

    PENDING = "pending"
    PROCESSING = "processing"
    APPROVED = "approved"
    REQUIRES_HUMAN_REVIEW = "requires_human_review"
    REJECTED = "rejected"
