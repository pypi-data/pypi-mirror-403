"""
High-level Task SDK interface for XClient.

This module provides a convenient interface for managing tasks through the XClient API.
"""

import json
from http import HTTPStatus
from typing import Optional
from ..api.client.api.tasks import (
    submit_task,
    get_task,
    list_tasks,
    cancel_task,
    delete_task,
)
from ..api.client.models.task import Task as TaskModel
from ..api.client.models.task_submit_request import TaskSubmitRequest
from ..api.client.models.task_submit_response import TaskSubmitResponse
from ..api.client.models.task_list_response import TaskListResponse
from ..api.client.models.task_status import TaskStatus
from ..api.client.models.error_response import ErrorResponse
from ..api.client.types import Response, UNSET, UNSET
from ..connection_config import ConnectionConfig
from ..exceptions import (
    NotFoundException,
    APIException,
)
from .client import TaskClient, handle_api_exception


class Task:
    """
    High-level interface for managing tasks.
    
    Example:
        ```python
        from xclient import Task, ConnectionConfig
        
        config = ConnectionConfig(api_key="your_api_key")
        task = Task(config=config)
        
        # Submit a task with script
        result = task.submit(
            name="my-task",
            cluster_id=1,
            script="#!/bin/bash\\necho 'Hello World'"
        )
        
        # Or submit with command
        result = task.submit(
            name="my-task",
            cluster_id=1,
            command="echo 'Hello World'"
        )
        
        # Get task details
        task_info = task.get(task_id=result.job_id, cluster_id=1)
        
        # List tasks
        tasks = task.list(status=TaskStatus.RUNNING)
        
        # Cancel a task
        task.cancel(task_id=result.job_id, cluster_id=1)
        ```
    """

    def __init__(
        self,
        config: Optional["ConnectionConfig"] = None,
        api_key: Optional[str] = None,
        access_token: Optional[str] = None,
        domain: Optional[str] = None,
        debug: Optional[bool] = None,
        request_timeout: Optional[float] = None,
    ):
        """
        Initialize the Task client.

        Args:
            config: ConnectionConfig instance. If not provided, a new one will be created.
            api_key: API key for authentication. Overrides config.api_key.
            access_token: Access token for authentication. Overrides config.access_token.
            domain: API domain. Overrides config.domain.
            debug: Enable debug mode. Overrides config.debug.
            request_timeout: Request timeout in seconds. Overrides config.request_timeout.
        """

        if config is None:
            config = ConnectionConfig()

        # Override config values if provided
        if api_key is not None:
            config.api_key = api_key
        if access_token is not None:
            config.access_token = access_token
        if domain is not None:
            config.domain = domain
        if debug is not None:
            config.debug = debug
        if request_timeout is not None:
            config.request_timeout = request_timeout

        self._config = config
        self._client = TaskClient(config=config)

    def submit(
        self,
        name: str,
        cluster_id: Optional[int] = None,
        script: Optional[str] = None,
        command: Optional[str] = None,
        resources: Optional[dict] = None,
        team_id: Optional[int] = None,
    ) -> TaskSubmitResponse:
        """
        Submit a new task.

        Args:
            name: Task name
            cluster_id: Cluster ID to submit the task to
            script: Task script content (optional, but at least one of script or command is required)
            command: Command to execute (optional, but at least one of script or command is required)
            resources: Resource requirements dict (optional)
            team_id: Team ID (optional)

        Returns:
            TaskSubmitResponse containing the submitted task information

        Raises:
            APIException: If the API returns an error
            AuthenticationException: If authentication fails
        """
        # Validate required fields
        if cluster_id is None:
            raise APIException("cluster_id is required")
        
        # At least one of script or command must be provided
        if not script and not command:
            raise APIException("At least one of 'script' or 'command' must be provided")
        
        # Map resources dict to individual fields
        # resources dict can contain: cpu, cpus_per_task, memory, nodes, gres, time, partition, etc.
        request_kwargs = {
            "name": name,
            "cluster_id": cluster_id,
        }
        
        # Handle script and command (at least one is required)
        # script is Union[Unset, str], so we need to set it or leave as UNSET
        if script:
            request_kwargs["script"] = script
        # command is Union[None, Unset, str], so we can set it or leave as UNSET
        if command:
            request_kwargs["command"] = command
        
        # team_id is Union[None, Unset, int]
        if team_id is not None:
            request_kwargs["team_id"] = team_id
        
        # Map resources dict to TaskSubmitRequest fields
        if resources:
            if "cpu" in resources or "cpus_per_task" in resources:
                request_kwargs["cpus_per_task"] = resources.get("cpus_per_task") or resources.get("cpu")
            if "memory" in resources:
                request_kwargs["memory"] = resources.get("memory")
            if "nodes" in resources:
                request_kwargs["nodes"] = resources.get("nodes")
            if "gres" in resources:
                request_kwargs["gres"] = resources.get("gres")
            if "time" in resources:
                request_kwargs["time"] = resources.get("time")
            if "partition" in resources:
                request_kwargs["partition"] = resources.get("partition")
            if "tres" in resources:
                request_kwargs["tres"] = resources.get("tres")
        
        request = TaskSubmitRequest(**request_kwargs)

        # Use sync_detailed to get full response information
        response_obj = submit_task.sync_detailed(client=self._client, body=request)
        response = response_obj.parsed

        if isinstance(response, ErrorResponse):
            # Check status code to determine exception type
            status_code = response.code if response.code != UNSET and response.code != 0 else response_obj.status_code.value
            
            # Extract error message from ErrorResponse
            error_msg = "Unknown error"
            if response.error and response.error != UNSET:
                error_msg = response.error
            elif response_obj.content:
                try:
                    error_data = json.loads(response_obj.content.decode())
                    error_msg = error_data.get("error", "Unknown error")
                except (json.JSONDecodeError, UnicodeDecodeError):
                    error_msg = response_obj.content.decode(errors="replace")
            
            # Raise appropriate exception based on status code
            if status_code == 404:
                raise NotFoundException(error_msg)
            
            # Use handle_api_exception which returns an exception object
            exception = handle_api_exception(
                Response(
                    status_code=HTTPStatus(status_code),
                    content=response_obj.content,
                    headers=response_obj.headers,
                    parsed=None,
                )
            )
            raise exception

        if response is None:
            # If response is None, try to extract error from raw response
            error_msg = "No response from server"
            if response_obj.content:
                try:
                    error_data = json.loads(response_obj.content.decode())
                    error_msg = error_data.get("error", f"HTTP {response_obj.status_code.value}: {response_obj.content.decode()}")
                except (json.JSONDecodeError, UnicodeDecodeError):
                    error_msg = f"HTTP {response_obj.status_code.value}: {response_obj.content.decode(errors='replace')}"
            raise APIException(f"Failed to submit task: {error_msg}")

        return response

    def get(
        self,
        task_id: int,
        cluster_id: int,
    ) -> TaskModel:
        """
        Get task details by task ID.

        Args:
            task_id: Task ID
            cluster_id: Cluster ID

        Returns:
            Task model with task details

        Raises:
            NotFoundException: If the task is not found
            APIException: If the API returns an error
        """
        # Use sync_detailed to get full response information
        response_obj = get_task.sync_detailed(
            id=task_id,
            client=self._client,
            cluster_id=cluster_id,
        )
        response = response_obj.parsed

        if isinstance(response, ErrorResponse):
            # Extract error message from ErrorResponse
            error_msg = f"Task {task_id} not found"
            if response.error and response.error != UNSET:
                error_msg = response.error
            elif response_obj.content:
                try:
                    error_data = json.loads(response_obj.content.decode())
                    error_msg = error_data.get("error", error_msg)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    error_msg = response_obj.content.decode(errors="replace")
            
            # Check status code to determine exception type
            status_code = response.code if response.code != UNSET and response.code != 0 else response_obj.status_code.value
            if status_code == 404:
                raise NotFoundException(error_msg)
            
            # Use handle_api_exception which returns an exception object
            exception = handle_api_exception(
                Response(
                    status_code=HTTPStatus(status_code),
                    content=response_obj.content,
                    headers=response_obj.headers,
                    parsed=None,
                )
            )
            raise exception

        if response is None:
            # If response is None, try to extract error from raw response
            error_msg = f"Task {task_id} not found"
            if response_obj.content:
                try:
                    error_data = json.loads(response_obj.content.decode())
                    error_msg = error_data.get("error", f"HTTP {response_obj.status_code.value}: {response_obj.content.decode()}")
                except (json.JSONDecodeError, UnicodeDecodeError):
                    error_msg = f"HTTP {response_obj.status_code.value}: {response_obj.content.decode(errors='replace')}"
            raise NotFoundException(error_msg)

        return response

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[TaskStatus] = None,
        user_id: Optional[int] = None,
        team_id: Optional[int] = None,
        cluster_id: Optional[int] = None,
    ) -> TaskListResponse:
        """
        List tasks with optional filtering.

        Args:
            page: Page number (default: 1)
            page_size: Number of items per page (default: 20)
            status: Filter by task status (optional)
            user_id: Filter by user ID (optional)
            team_id: Filter by team ID (optional)
            cluster_id: Filter by cluster ID (optional)

        Returns:
            TaskListResponse containing the list of tasks

        Raises:
            APIException: If the API returns an error
        """
        response = list_tasks.sync(
            client=self._client,
            page=page,
            page_size=page_size,
            status=status if status is not None else UNSET,
            user_id=user_id if user_id is not None else UNSET,
            team_id=team_id if team_id is not None else UNSET,
            cluster_id=cluster_id if cluster_id is not None else UNSET,
        )

        if isinstance(response, ErrorResponse):
            raise handle_api_exception(
                Response(
                    status_code=HTTPStatus(response.code if response.code != 0 else 400),
                    content=json.dumps({"error": response.error}).encode() if response.error else b"",
                    headers={},
                    parsed=None,
                )
            )

        if response is None:
            raise APIException("Failed to list tasks: No response from server")

        return response

    def cancel(
        self,
        task_id: int,
        cluster_id: int,
    ) -> bool:
        """
        Cancel a task.

        Args:
            task_id: Task ID to cancel
            cluster_id: Cluster ID where the task is running

        Returns:
            True if the task was cancelled successfully

        Raises:
            NotFoundException: If the task is not found
            APIException: If the API returns an error
        """
        # Use sync_detailed to get full response information
        response_obj = cancel_task.sync_detailed(
            id=task_id,
            client=self._client,
            cluster_id=cluster_id,
        )
        response = response_obj.parsed

        if isinstance(response, ErrorResponse):
            # Extract error message from ErrorResponse
            error_msg = f"Task {task_id} not found"
            if response.error and response.error != UNSET:
                error_msg = response.error
            elif response_obj.content:
                try:
                    error_data = json.loads(response_obj.content.decode())
                    error_msg = error_data.get("error", error_msg)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    error_msg = response_obj.content.decode(errors="replace")
            
            # Check status code to determine exception type
            status_code = response.code if response.code != UNSET and response.code != 0 else response_obj.status_code.value
            if status_code == 404:
                raise NotFoundException(error_msg)
            
            # Use handle_api_exception which returns an exception object
            exception = handle_api_exception(
                Response(
                    status_code=HTTPStatus(status_code),
                    content=response_obj.content,
                    headers=response_obj.headers,
                    parsed=None,
                )
            )
            raise exception

        return response is not None

    def delete(
        self,
        task_id: int,
        cluster_id: int,
    ) -> bool:
        """
        Delete a task.

        Args:
            task_id: Task ID to delete
            cluster_id: Cluster ID where the task is running

        Returns:
            True if the task was deleted successfully

        Raises:
            NotFoundException: If the task is not found
            APIException: If the API returns an error
        """
        # Use sync_detailed to get full response information
        response_obj = delete_task.sync_detailed(
            id=task_id,
            client=self._client,
            cluster_id=cluster_id,
        )
        response = response_obj.parsed

        if isinstance(response, ErrorResponse):
            # Extract error message from ErrorResponse
            error_msg = f"Task {task_id} not found"
            if response.error and response.error != UNSET:
                error_msg = response.error
            elif response_obj.content:
                try:
                    error_data = json.loads(response_obj.content.decode())
                    error_msg = error_data.get("error", error_msg)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    error_msg = response_obj.content.decode(errors="replace")
            
            # Check status code to determine exception type
            status_code = response.code if response.code != UNSET and response.code != 0 else response_obj.status_code.value
            if status_code == 404:
                raise NotFoundException(error_msg)
            
            # Use handle_api_exception which returns an exception object
            exception = handle_api_exception(
                Response(
                    status_code=HTTPStatus(response.code if response.code != 0 else 400),
                    content=json.dumps({"error": response.error}).encode() if response.error else b"",
                    headers={},
                    parsed=None,
                )
            )
            raise exception

        if response is None:
            raise APIException("Failed to delete task: No response from server")

        return response is not None