from enum import StrEnum


class DataCollectionStatus(StrEnum):
    """
    Status of data collection for the AI agent in this chat.
    Only tracks field collection, not qualification status.

    - COLLECTING: Still collecting data from the user
    - MANDATORY_COMPLETED: All mandatory fields have been collected
    - ALL_COMPLETED: All fields (mandatory + optional) have been collected
    - CANCELLED: Data collection was cancelled
    """
    COLLECTING = "collecting"
    MANDATORY_COMPLETED = "mandatory_completed"
    ALL_COMPLETED = "all_completed"
    CANCELLED = "cancelled"


class PreQualifyStatus(StrEnum):
    """
    Status of pre-qualification for the AI agent in this chat.
    Separate from data collection - tracks qualification evaluation.

    - PENDING: Waiting for data collection to complete
    - EVALUATING: Data collected, evaluating acceptance criteria
    - QUALIFIED: User met acceptance criteria
    - UNQUALIFIED: User did NOT meet acceptance criteria
    """
    PENDING = "pending"
    EVALUATING = "evaluating"
    QUALIFIED = "qualified"
    UNQUALIFIED = "unqualified"
