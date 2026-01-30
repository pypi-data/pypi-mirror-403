from enum import Enum


class TaskStatus(str, Enum):
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    CREATED = "created"
    FAILED = "failed"
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"

    def __str__(self) -> str:
        return str(self.value)
