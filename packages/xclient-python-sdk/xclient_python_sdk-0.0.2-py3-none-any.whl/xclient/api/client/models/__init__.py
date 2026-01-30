"""Contains all the data models used in inputs/outputs"""

from .error_response import ErrorResponse
from .message_response import MessageResponse
from .task import Task
from .task_alloc_tres_type_0 import TaskAllocTresType0
from .task_gres_detail_type_0_item import TaskGresDetailType0Item
from .task_job_resources_type_0 import TaskJobResourcesType0
from .task_list_response import TaskListResponse
from .task_resources_type_0 import TaskResourcesType0
from .task_status import TaskStatus
from .task_submit_request import TaskSubmitRequest
from .task_submit_request_environment_type_0 import TaskSubmitRequestEnvironmentType0
from .task_submit_response import TaskSubmitResponse
from .task_tres_type_0 import TaskTresType0
from .task_tres_used_type_0 import TaskTresUsedType0

__all__ = (
    "ErrorResponse",
    "MessageResponse",
    "Task",
    "TaskAllocTresType0",
    "TaskGresDetailType0Item",
    "TaskJobResourcesType0",
    "TaskListResponse",
    "TaskResourcesType0",
    "TaskStatus",
    "TaskSubmitRequest",
    "TaskSubmitRequestEnvironmentType0",
    "TaskSubmitResponse",
    "TaskTresType0",
    "TaskTresUsedType0",
)
