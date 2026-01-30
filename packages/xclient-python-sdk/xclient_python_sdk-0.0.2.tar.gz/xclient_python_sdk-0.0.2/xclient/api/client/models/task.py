import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.task_status import TaskStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.task_alloc_tres_type_0 import TaskAllocTresType0
    from ..models.task_gres_detail_type_0_item import TaskGresDetailType0Item
    from ..models.task_job_resources_type_0 import TaskJobResourcesType0
    from ..models.task_resources_type_0 import TaskResourcesType0
    from ..models.task_tres_type_0 import TaskTresType0
    from ..models.task_tres_used_type_0 import TaskTresUsedType0


T = TypeVar("T", bound="Task")


@_attrs_define
class Task:
    """Task representation

    Attributes:
        account (Union[None, Unset, str]): Slurm account Example: research.
        alloc_tres (Union['TaskAllocTresType0', None, Unset]): Allocated Trackable Resources Example: {'cpu': 4, 'mem':
            8589934592}.
        array_job_id (Union[None, Unset, int]): Array job ID Example: 12345.
        array_task_id (Union[None, Unset, int]): Array task ID Example: 1.
        attempt_id (Union[Unset, str]): Attempt ID (UUID) - Task attempt identifier Example:
            660e8400-e29b-41d4-a716-446655440001.
        batch_features (Union[None, Unset, str]): Batch features
        batch_host (Union[None, Unset, str]): Batch host Example: node001.
        cluster (Union[None, Unset, str]): Cluster name Example: main-cluster.
        cluster_id (Union[None, Unset, int]):  Example: 1.
        command (Union[None, Unset, str]):  Example: python train.py.
        comment (Union[None, Unset, str]): Task comment Example: Machine learning training job.
        completed_at (Union[None, Unset, datetime.datetime]):  Example: 2024-01-01T00:00:00Z.
        cpus (Union[None, Unset, int]):  Example: 4.
        cpus_per_task (Union[None, Unset, int]): CPUs per task Example: 1.
        created_at (Union[Unset, datetime.datetime]):  Example: 2024-01-01T00:00:00Z.
        current_working_directory (Union[None, Unset, str]): Current working directory Example: /home/user/project.
        deadline (Union[None, Unset, datetime.datetime]): Deadline
        eligible_at (Union[None, Unset, datetime.datetime]): When the task becomes eligible for scheduling Example:
            2024-01-01T00:00:00Z.
        end_time (Union[None, Unset, datetime.datetime]): End time Example: 2024-01-01T01:00:00Z.
        exit_code (Union[None, Unset, int]):
        flags (Union[None, Unset, list[str]]): Job flags
        gres_detail (Union[None, Unset, list['TaskGresDetailType0Item']]): GRES detail
        group_id (Union[None, Unset, int]): Group ID Example: 1000.
        group_name (Union[None, Unset, str]): Group name Example: researchers.
        id (Union[Unset, int]): Database ID (slurm_jobs.id) Example: 1.
        job_id (Union[Unset, str]): Slurm Job ID Example: 12345.
        job_resources (Union['TaskJobResourcesType0', None, Unset]): Job resources (nodes, allocated CPUs, etc.)
            Example: {'allocated_cpus': 4, 'nodes': ['node001']}.
        last_sched_evaluation_at (Union[None, Unset, datetime.datetime]): Last time the scheduler evaluated this task
            Example: 2024-01-01T00:00:00Z.
        memory (Union[None, Unset, int]): Memory in bytes Example: 8589934592.
        minimum_cpus_per_node (Union[None, Unset, int]): Minimum CPUs per node Example: 1.
        minimum_tmp_disk_per_node (Union[None, Unset, int]): Minimum temporary disk per node
        name (Union[Unset, str]):  Example: training-job.
        node_count (Union[None, Unset, int]): Number of nodes Example: 1.
        nodes (Union[None, Unset, list[str]]):  Example: ['node1', 'node2'].
        partition (Union[None, Unset, str]):  Example: debug.
        pre_sus_time (Union[None, Unset, int]): Pre-suspension time in seconds
        priority (Union[None, Unset, int]):  Example: 4294901756.
        qos (Union[None, Unset, str]): Quality of Service Example: normal.
        requeue (Union[None, Unset, bool]): Whether requeue is enabled
        resize_time (Union[None, Unset, datetime.datetime]): Resize time
        resources (Union['TaskResourcesType0', None, Unset]): Resource requirements (JSON format) Example: {'cpu': 4,
            'gpu': 1, 'memory': '8GB'}.
        restart_count (Union[None, Unset, int]): Restart count
        script (Union[None, Unset, str]):  Example: #!/bin/bash
            python train.py.
        slurm_state (Union[None, Unset, str]): Slurm job state Example: RUNNING.
        standard_error (Union[None, Unset, str]): Standard error file path Example: /home/user/error.log.
        standard_input (Union[None, Unset, str]): Standard input file path
        standard_output (Union[None, Unset, str]): Standard output file path Example: /home/user/output.log.
        started_at (Union[None, Unset, datetime.datetime]):  Example: 2024-01-01T00:00:00Z.
        state_description (Union[None, Unset, str]): State description
        state_reason (Union[None, Unset, str]): State reason
        status (Union[Unset, TaskStatus]): Task status Example: pending.
        std_err (Union[None, Unset, str]): Standard error file Example: /home/user/error.log.
        std_in (Union[None, Unset, str]): Standard input file
        std_out (Union[None, Unset, str]): Standard output file Example: /home/user/output.log.
        submit_time (Union[None, Unset, datetime.datetime]): Submit time Example: 2024-01-01T00:00:00Z.
        submit_user_id (Union[None, Unset, int]): Submit user ID Example: 1.
        submit_user_name (Union[None, Unset, str]): Submit user name Example: john.
        suspend_time (Union[None, Unset, datetime.datetime]): Suspend time
        task_count (Union[None, Unset, int]): Number of tasks Example: 4.
        task_id (Union[Unset, str]): Task ID (UUID) - Business task identifier Example:
            550e8400-e29b-41d4-a716-446655440000.
        tasks (Union[None, Unset, int]): Number of tasks Example: 1.
        team_id (Union[None, Unset, int]):  Example: 1.
        time_limit (Union[None, Unset, int]): Time limit in seconds Example: 3600.
        time_used (Union[None, Unset, int]): Time used in seconds Example: 3600.
        tres (Union['TaskTresType0', None, Unset]): Trackable Resources Example: {'cpu': 4, 'mem': 8589934592}.
        tres_alloc_str (Union[None, Unset, str]): TRES allocation string Example: cpu=4,mem=8G.
        tres_req_str (Union[None, Unset, str]): TRES request string Example: cpu=4,mem=8G.
        tres_used (Union['TaskTresUsedType0', None, Unset]): Trackable Resources Used Example: {'cpu': 4, 'mem':
            4294967296}.
        updated_at (Union[Unset, datetime.datetime]):  Example: 2024-01-01T00:00:00Z.
        user_id (Union[Unset, int]):  Example: 1.
        user_name (Union[None, Unset, str]): User name Example: john.
        work_dir (Union[None, Unset, str]):  Example: /home/user.
    """

    account: Union[None, Unset, str] = UNSET
    alloc_tres: Union["TaskAllocTresType0", None, Unset] = UNSET
    array_job_id: Union[None, Unset, int] = UNSET
    array_task_id: Union[None, Unset, int] = UNSET
    attempt_id: Union[Unset, str] = UNSET
    batch_features: Union[None, Unset, str] = UNSET
    batch_host: Union[None, Unset, str] = UNSET
    cluster: Union[None, Unset, str] = UNSET
    cluster_id: Union[None, Unset, int] = UNSET
    command: Union[None, Unset, str] = UNSET
    comment: Union[None, Unset, str] = UNSET
    completed_at: Union[None, Unset, datetime.datetime] = UNSET
    cpus: Union[None, Unset, int] = UNSET
    cpus_per_task: Union[None, Unset, int] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    current_working_directory: Union[None, Unset, str] = UNSET
    deadline: Union[None, Unset, datetime.datetime] = UNSET
    eligible_at: Union[None, Unset, datetime.datetime] = UNSET
    end_time: Union[None, Unset, datetime.datetime] = UNSET
    exit_code: Union[None, Unset, int] = UNSET
    flags: Union[None, Unset, list[str]] = UNSET
    gres_detail: Union[None, Unset, list["TaskGresDetailType0Item"]] = UNSET
    group_id: Union[None, Unset, int] = UNSET
    group_name: Union[None, Unset, str] = UNSET
    id: Union[Unset, int] = UNSET
    job_id: Union[Unset, str] = UNSET
    job_resources: Union["TaskJobResourcesType0", None, Unset] = UNSET
    last_sched_evaluation_at: Union[None, Unset, datetime.datetime] = UNSET
    memory: Union[None, Unset, int] = UNSET
    minimum_cpus_per_node: Union[None, Unset, int] = UNSET
    minimum_tmp_disk_per_node: Union[None, Unset, int] = UNSET
    name: Union[Unset, str] = UNSET
    node_count: Union[None, Unset, int] = UNSET
    nodes: Union[None, Unset, list[str]] = UNSET
    partition: Union[None, Unset, str] = UNSET
    pre_sus_time: Union[None, Unset, int] = UNSET
    priority: Union[None, Unset, int] = UNSET
    qos: Union[None, Unset, str] = UNSET
    requeue: Union[None, Unset, bool] = UNSET
    resize_time: Union[None, Unset, datetime.datetime] = UNSET
    resources: Union["TaskResourcesType0", None, Unset] = UNSET
    restart_count: Union[None, Unset, int] = UNSET
    script: Union[None, Unset, str] = UNSET
    slurm_state: Union[None, Unset, str] = UNSET
    standard_error: Union[None, Unset, str] = UNSET
    standard_input: Union[None, Unset, str] = UNSET
    standard_output: Union[None, Unset, str] = UNSET
    started_at: Union[None, Unset, datetime.datetime] = UNSET
    state_description: Union[None, Unset, str] = UNSET
    state_reason: Union[None, Unset, str] = UNSET
    status: Union[Unset, TaskStatus] = UNSET
    std_err: Union[None, Unset, str] = UNSET
    std_in: Union[None, Unset, str] = UNSET
    std_out: Union[None, Unset, str] = UNSET
    submit_time: Union[None, Unset, datetime.datetime] = UNSET
    submit_user_id: Union[None, Unset, int] = UNSET
    submit_user_name: Union[None, Unset, str] = UNSET
    suspend_time: Union[None, Unset, datetime.datetime] = UNSET
    task_count: Union[None, Unset, int] = UNSET
    task_id: Union[Unset, str] = UNSET
    tasks: Union[None, Unset, int] = UNSET
    team_id: Union[None, Unset, int] = UNSET
    time_limit: Union[None, Unset, int] = UNSET
    time_used: Union[None, Unset, int] = UNSET
    tres: Union["TaskTresType0", None, Unset] = UNSET
    tres_alloc_str: Union[None, Unset, str] = UNSET
    tres_req_str: Union[None, Unset, str] = UNSET
    tres_used: Union["TaskTresUsedType0", None, Unset] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    user_id: Union[Unset, int] = UNSET
    user_name: Union[None, Unset, str] = UNSET
    work_dir: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.task_alloc_tres_type_0 import TaskAllocTresType0
        from ..models.task_job_resources_type_0 import TaskJobResourcesType0
        from ..models.task_resources_type_0 import TaskResourcesType0
        from ..models.task_tres_type_0 import TaskTresType0
        from ..models.task_tres_used_type_0 import TaskTresUsedType0

        account: Union[None, Unset, str]
        if isinstance(self.account, Unset):
            account = UNSET
        else:
            account = self.account

        alloc_tres: Union[None, Unset, dict[str, Any]]
        if isinstance(self.alloc_tres, Unset):
            alloc_tres = UNSET
        elif isinstance(self.alloc_tres, TaskAllocTresType0):
            alloc_tres = self.alloc_tres.to_dict()
        else:
            alloc_tres = self.alloc_tres

        array_job_id: Union[None, Unset, int]
        if isinstance(self.array_job_id, Unset):
            array_job_id = UNSET
        else:
            array_job_id = self.array_job_id

        array_task_id: Union[None, Unset, int]
        if isinstance(self.array_task_id, Unset):
            array_task_id = UNSET
        else:
            array_task_id = self.array_task_id

        attempt_id = self.attempt_id

        batch_features: Union[None, Unset, str]
        if isinstance(self.batch_features, Unset):
            batch_features = UNSET
        else:
            batch_features = self.batch_features

        batch_host: Union[None, Unset, str]
        if isinstance(self.batch_host, Unset):
            batch_host = UNSET
        else:
            batch_host = self.batch_host

        cluster: Union[None, Unset, str]
        if isinstance(self.cluster, Unset):
            cluster = UNSET
        else:
            cluster = self.cluster

        cluster_id: Union[None, Unset, int]
        if isinstance(self.cluster_id, Unset):
            cluster_id = UNSET
        else:
            cluster_id = self.cluster_id

        command: Union[None, Unset, str]
        if isinstance(self.command, Unset):
            command = UNSET
        else:
            command = self.command

        comment: Union[None, Unset, str]
        if isinstance(self.comment, Unset):
            comment = UNSET
        else:
            comment = self.comment

        completed_at: Union[None, Unset, str]
        if isinstance(self.completed_at, Unset):
            completed_at = UNSET
        elif isinstance(self.completed_at, datetime.datetime):
            completed_at = self.completed_at.isoformat()
        else:
            completed_at = self.completed_at

        cpus: Union[None, Unset, int]
        if isinstance(self.cpus, Unset):
            cpus = UNSET
        else:
            cpus = self.cpus

        cpus_per_task: Union[None, Unset, int]
        if isinstance(self.cpus_per_task, Unset):
            cpus_per_task = UNSET
        else:
            cpus_per_task = self.cpus_per_task

        created_at: Union[Unset, str] = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        current_working_directory: Union[None, Unset, str]
        if isinstance(self.current_working_directory, Unset):
            current_working_directory = UNSET
        else:
            current_working_directory = self.current_working_directory

        deadline: Union[None, Unset, str]
        if isinstance(self.deadline, Unset):
            deadline = UNSET
        elif isinstance(self.deadline, datetime.datetime):
            deadline = self.deadline.isoformat()
        else:
            deadline = self.deadline

        eligible_at: Union[None, Unset, str]
        if isinstance(self.eligible_at, Unset):
            eligible_at = UNSET
        elif isinstance(self.eligible_at, datetime.datetime):
            eligible_at = self.eligible_at.isoformat()
        else:
            eligible_at = self.eligible_at

        end_time: Union[None, Unset, str]
        if isinstance(self.end_time, Unset):
            end_time = UNSET
        elif isinstance(self.end_time, datetime.datetime):
            end_time = self.end_time.isoformat()
        else:
            end_time = self.end_time

        exit_code: Union[None, Unset, int]
        if isinstance(self.exit_code, Unset):
            exit_code = UNSET
        else:
            exit_code = self.exit_code

        flags: Union[None, Unset, list[str]]
        if isinstance(self.flags, Unset):
            flags = UNSET
        elif isinstance(self.flags, list):
            flags = self.flags

        else:
            flags = self.flags

        gres_detail: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.gres_detail, Unset):
            gres_detail = UNSET
        elif isinstance(self.gres_detail, list):
            gres_detail = []
            for gres_detail_type_0_item_data in self.gres_detail:
                gres_detail_type_0_item = gres_detail_type_0_item_data.to_dict()
                gres_detail.append(gres_detail_type_0_item)

        else:
            gres_detail = self.gres_detail

        group_id: Union[None, Unset, int]
        if isinstance(self.group_id, Unset):
            group_id = UNSET
        else:
            group_id = self.group_id

        group_name: Union[None, Unset, str]
        if isinstance(self.group_name, Unset):
            group_name = UNSET
        else:
            group_name = self.group_name

        id = self.id

        job_id = self.job_id

        job_resources: Union[None, Unset, dict[str, Any]]
        if isinstance(self.job_resources, Unset):
            job_resources = UNSET
        elif isinstance(self.job_resources, TaskJobResourcesType0):
            job_resources = self.job_resources.to_dict()
        else:
            job_resources = self.job_resources

        last_sched_evaluation_at: Union[None, Unset, str]
        if isinstance(self.last_sched_evaluation_at, Unset):
            last_sched_evaluation_at = UNSET
        elif isinstance(self.last_sched_evaluation_at, datetime.datetime):
            last_sched_evaluation_at = self.last_sched_evaluation_at.isoformat()
        else:
            last_sched_evaluation_at = self.last_sched_evaluation_at

        memory: Union[None, Unset, int]
        if isinstance(self.memory, Unset):
            memory = UNSET
        else:
            memory = self.memory

        minimum_cpus_per_node: Union[None, Unset, int]
        if isinstance(self.minimum_cpus_per_node, Unset):
            minimum_cpus_per_node = UNSET
        else:
            minimum_cpus_per_node = self.minimum_cpus_per_node

        minimum_tmp_disk_per_node: Union[None, Unset, int]
        if isinstance(self.minimum_tmp_disk_per_node, Unset):
            minimum_tmp_disk_per_node = UNSET
        else:
            minimum_tmp_disk_per_node = self.minimum_tmp_disk_per_node

        name = self.name

        node_count: Union[None, Unset, int]
        if isinstance(self.node_count, Unset):
            node_count = UNSET
        else:
            node_count = self.node_count

        nodes: Union[None, Unset, list[str]]
        if isinstance(self.nodes, Unset):
            nodes = UNSET
        elif isinstance(self.nodes, list):
            nodes = self.nodes

        else:
            nodes = self.nodes

        partition: Union[None, Unset, str]
        if isinstance(self.partition, Unset):
            partition = UNSET
        else:
            partition = self.partition

        pre_sus_time: Union[None, Unset, int]
        if isinstance(self.pre_sus_time, Unset):
            pre_sus_time = UNSET
        else:
            pre_sus_time = self.pre_sus_time

        priority: Union[None, Unset, int]
        if isinstance(self.priority, Unset):
            priority = UNSET
        else:
            priority = self.priority

        qos: Union[None, Unset, str]
        if isinstance(self.qos, Unset):
            qos = UNSET
        else:
            qos = self.qos

        requeue: Union[None, Unset, bool]
        if isinstance(self.requeue, Unset):
            requeue = UNSET
        else:
            requeue = self.requeue

        resize_time: Union[None, Unset, str]
        if isinstance(self.resize_time, Unset):
            resize_time = UNSET
        elif isinstance(self.resize_time, datetime.datetime):
            resize_time = self.resize_time.isoformat()
        else:
            resize_time = self.resize_time

        resources: Union[None, Unset, dict[str, Any]]
        if isinstance(self.resources, Unset):
            resources = UNSET
        elif isinstance(self.resources, TaskResourcesType0):
            resources = self.resources.to_dict()
        else:
            resources = self.resources

        restart_count: Union[None, Unset, int]
        if isinstance(self.restart_count, Unset):
            restart_count = UNSET
        else:
            restart_count = self.restart_count

        script: Union[None, Unset, str]
        if isinstance(self.script, Unset):
            script = UNSET
        else:
            script = self.script

        slurm_state: Union[None, Unset, str]
        if isinstance(self.slurm_state, Unset):
            slurm_state = UNSET
        else:
            slurm_state = self.slurm_state

        standard_error: Union[None, Unset, str]
        if isinstance(self.standard_error, Unset):
            standard_error = UNSET
        else:
            standard_error = self.standard_error

        standard_input: Union[None, Unset, str]
        if isinstance(self.standard_input, Unset):
            standard_input = UNSET
        else:
            standard_input = self.standard_input

        standard_output: Union[None, Unset, str]
        if isinstance(self.standard_output, Unset):
            standard_output = UNSET
        else:
            standard_output = self.standard_output

        started_at: Union[None, Unset, str]
        if isinstance(self.started_at, Unset):
            started_at = UNSET
        elif isinstance(self.started_at, datetime.datetime):
            started_at = self.started_at.isoformat()
        else:
            started_at = self.started_at

        state_description: Union[None, Unset, str]
        if isinstance(self.state_description, Unset):
            state_description = UNSET
        else:
            state_description = self.state_description

        state_reason: Union[None, Unset, str]
        if isinstance(self.state_reason, Unset):
            state_reason = UNSET
        else:
            state_reason = self.state_reason

        status: Union[Unset, str] = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        std_err: Union[None, Unset, str]
        if isinstance(self.std_err, Unset):
            std_err = UNSET
        else:
            std_err = self.std_err

        std_in: Union[None, Unset, str]
        if isinstance(self.std_in, Unset):
            std_in = UNSET
        else:
            std_in = self.std_in

        std_out: Union[None, Unset, str]
        if isinstance(self.std_out, Unset):
            std_out = UNSET
        else:
            std_out = self.std_out

        submit_time: Union[None, Unset, str]
        if isinstance(self.submit_time, Unset):
            submit_time = UNSET
        elif isinstance(self.submit_time, datetime.datetime):
            submit_time = self.submit_time.isoformat()
        else:
            submit_time = self.submit_time

        submit_user_id: Union[None, Unset, int]
        if isinstance(self.submit_user_id, Unset):
            submit_user_id = UNSET
        else:
            submit_user_id = self.submit_user_id

        submit_user_name: Union[None, Unset, str]
        if isinstance(self.submit_user_name, Unset):
            submit_user_name = UNSET
        else:
            submit_user_name = self.submit_user_name

        suspend_time: Union[None, Unset, str]
        if isinstance(self.suspend_time, Unset):
            suspend_time = UNSET
        elif isinstance(self.suspend_time, datetime.datetime):
            suspend_time = self.suspend_time.isoformat()
        else:
            suspend_time = self.suspend_time

        task_count: Union[None, Unset, int]
        if isinstance(self.task_count, Unset):
            task_count = UNSET
        else:
            task_count = self.task_count

        task_id = self.task_id

        tasks: Union[None, Unset, int]
        if isinstance(self.tasks, Unset):
            tasks = UNSET
        else:
            tasks = self.tasks

        team_id: Union[None, Unset, int]
        if isinstance(self.team_id, Unset):
            team_id = UNSET
        else:
            team_id = self.team_id

        time_limit: Union[None, Unset, int]
        if isinstance(self.time_limit, Unset):
            time_limit = UNSET
        else:
            time_limit = self.time_limit

        time_used: Union[None, Unset, int]
        if isinstance(self.time_used, Unset):
            time_used = UNSET
        else:
            time_used = self.time_used

        tres: Union[None, Unset, dict[str, Any]]
        if isinstance(self.tres, Unset):
            tres = UNSET
        elif isinstance(self.tres, TaskTresType0):
            tres = self.tres.to_dict()
        else:
            tres = self.tres

        tres_alloc_str: Union[None, Unset, str]
        if isinstance(self.tres_alloc_str, Unset):
            tres_alloc_str = UNSET
        else:
            tres_alloc_str = self.tres_alloc_str

        tres_req_str: Union[None, Unset, str]
        if isinstance(self.tres_req_str, Unset):
            tres_req_str = UNSET
        else:
            tres_req_str = self.tres_req_str

        tres_used: Union[None, Unset, dict[str, Any]]
        if isinstance(self.tres_used, Unset):
            tres_used = UNSET
        elif isinstance(self.tres_used, TaskTresUsedType0):
            tres_used = self.tres_used.to_dict()
        else:
            tres_used = self.tres_used

        updated_at: Union[Unset, str] = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        user_id = self.user_id

        user_name: Union[None, Unset, str]
        if isinstance(self.user_name, Unset):
            user_name = UNSET
        else:
            user_name = self.user_name

        work_dir: Union[None, Unset, str]
        if isinstance(self.work_dir, Unset):
            work_dir = UNSET
        else:
            work_dir = self.work_dir

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if account is not UNSET:
            field_dict["account"] = account
        if alloc_tres is not UNSET:
            field_dict["alloc_tres"] = alloc_tres
        if array_job_id is not UNSET:
            field_dict["array_job_id"] = array_job_id
        if array_task_id is not UNSET:
            field_dict["array_task_id"] = array_task_id
        if attempt_id is not UNSET:
            field_dict["attempt_id"] = attempt_id
        if batch_features is not UNSET:
            field_dict["batch_features"] = batch_features
        if batch_host is not UNSET:
            field_dict["batch_host"] = batch_host
        if cluster is not UNSET:
            field_dict["cluster"] = cluster
        if cluster_id is not UNSET:
            field_dict["cluster_id"] = cluster_id
        if command is not UNSET:
            field_dict["command"] = command
        if comment is not UNSET:
            field_dict["comment"] = comment
        if completed_at is not UNSET:
            field_dict["completed_at"] = completed_at
        if cpus is not UNSET:
            field_dict["cpus"] = cpus
        if cpus_per_task is not UNSET:
            field_dict["cpus_per_task"] = cpus_per_task
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if current_working_directory is not UNSET:
            field_dict["current_working_directory"] = current_working_directory
        if deadline is not UNSET:
            field_dict["deadline"] = deadline
        if eligible_at is not UNSET:
            field_dict["eligible_at"] = eligible_at
        if end_time is not UNSET:
            field_dict["end_time"] = end_time
        if exit_code is not UNSET:
            field_dict["exit_code"] = exit_code
        if flags is not UNSET:
            field_dict["flags"] = flags
        if gres_detail is not UNSET:
            field_dict["gres_detail"] = gres_detail
        if group_id is not UNSET:
            field_dict["group_id"] = group_id
        if group_name is not UNSET:
            field_dict["group_name"] = group_name
        if id is not UNSET:
            field_dict["id"] = id
        if job_id is not UNSET:
            field_dict["job_id"] = job_id
        if job_resources is not UNSET:
            field_dict["job_resources"] = job_resources
        if last_sched_evaluation_at is not UNSET:
            field_dict["last_sched_evaluation_at"] = last_sched_evaluation_at
        if memory is not UNSET:
            field_dict["memory"] = memory
        if minimum_cpus_per_node is not UNSET:
            field_dict["minimum_cpus_per_node"] = minimum_cpus_per_node
        if minimum_tmp_disk_per_node is not UNSET:
            field_dict["minimum_tmp_disk_per_node"] = minimum_tmp_disk_per_node
        if name is not UNSET:
            field_dict["name"] = name
        if node_count is not UNSET:
            field_dict["node_count"] = node_count
        if nodes is not UNSET:
            field_dict["nodes"] = nodes
        if partition is not UNSET:
            field_dict["partition"] = partition
        if pre_sus_time is not UNSET:
            field_dict["pre_sus_time"] = pre_sus_time
        if priority is not UNSET:
            field_dict["priority"] = priority
        if qos is not UNSET:
            field_dict["qos"] = qos
        if requeue is not UNSET:
            field_dict["requeue"] = requeue
        if resize_time is not UNSET:
            field_dict["resize_time"] = resize_time
        if resources is not UNSET:
            field_dict["resources"] = resources
        if restart_count is not UNSET:
            field_dict["restart_count"] = restart_count
        if script is not UNSET:
            field_dict["script"] = script
        if slurm_state is not UNSET:
            field_dict["slurm_state"] = slurm_state
        if standard_error is not UNSET:
            field_dict["standard_error"] = standard_error
        if standard_input is not UNSET:
            field_dict["standard_input"] = standard_input
        if standard_output is not UNSET:
            field_dict["standard_output"] = standard_output
        if started_at is not UNSET:
            field_dict["started_at"] = started_at
        if state_description is not UNSET:
            field_dict["state_description"] = state_description
        if state_reason is not UNSET:
            field_dict["state_reason"] = state_reason
        if status is not UNSET:
            field_dict["status"] = status
        if std_err is not UNSET:
            field_dict["std_err"] = std_err
        if std_in is not UNSET:
            field_dict["std_in"] = std_in
        if std_out is not UNSET:
            field_dict["std_out"] = std_out
        if submit_time is not UNSET:
            field_dict["submit_time"] = submit_time
        if submit_user_id is not UNSET:
            field_dict["submit_user_id"] = submit_user_id
        if submit_user_name is not UNSET:
            field_dict["submit_user_name"] = submit_user_name
        if suspend_time is not UNSET:
            field_dict["suspend_time"] = suspend_time
        if task_count is not UNSET:
            field_dict["task_count"] = task_count
        if task_id is not UNSET:
            field_dict["task_id"] = task_id
        if tasks is not UNSET:
            field_dict["tasks"] = tasks
        if team_id is not UNSET:
            field_dict["team_id"] = team_id
        if time_limit is not UNSET:
            field_dict["time_limit"] = time_limit
        if time_used is not UNSET:
            field_dict["time_used"] = time_used
        if tres is not UNSET:
            field_dict["tres"] = tres
        if tres_alloc_str is not UNSET:
            field_dict["tres_alloc_str"] = tres_alloc_str
        if tres_req_str is not UNSET:
            field_dict["tres_req_str"] = tres_req_str
        if tres_used is not UNSET:
            field_dict["tres_used"] = tres_used
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if user_id is not UNSET:
            field_dict["user_id"] = user_id
        if user_name is not UNSET:
            field_dict["user_name"] = user_name
        if work_dir is not UNSET:
            field_dict["work_dir"] = work_dir

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.task_alloc_tres_type_0 import TaskAllocTresType0
        from ..models.task_gres_detail_type_0_item import TaskGresDetailType0Item
        from ..models.task_job_resources_type_0 import TaskJobResourcesType0
        from ..models.task_resources_type_0 import TaskResourcesType0
        from ..models.task_tres_type_0 import TaskTresType0
        from ..models.task_tres_used_type_0 import TaskTresUsedType0

        d = dict(src_dict)

        def _parse_account(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        account = _parse_account(d.pop("account", UNSET))

        def _parse_alloc_tres(data: object) -> Union["TaskAllocTresType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                alloc_tres_type_0 = TaskAllocTresType0.from_dict(data)

                return alloc_tres_type_0
            except:  # noqa: E722
                pass
            return cast(Union["TaskAllocTresType0", None, Unset], data)

        alloc_tres = _parse_alloc_tres(d.pop("alloc_tres", UNSET))

        def _parse_array_job_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        array_job_id = _parse_array_job_id(d.pop("array_job_id", UNSET))

        def _parse_array_task_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        array_task_id = _parse_array_task_id(d.pop("array_task_id", UNSET))

        attempt_id = d.pop("attempt_id", UNSET)

        def _parse_batch_features(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        batch_features = _parse_batch_features(d.pop("batch_features", UNSET))

        def _parse_batch_host(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        batch_host = _parse_batch_host(d.pop("batch_host", UNSET))

        def _parse_cluster(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        cluster = _parse_cluster(d.pop("cluster", UNSET))

        def _parse_cluster_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        cluster_id = _parse_cluster_id(d.pop("cluster_id", UNSET))

        def _parse_command(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        command = _parse_command(d.pop("command", UNSET))

        def _parse_comment(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        comment = _parse_comment(d.pop("comment", UNSET))

        def _parse_completed_at(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                completed_at_type_0 = isoparse(data)

                return completed_at_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        completed_at = _parse_completed_at(d.pop("completed_at", UNSET))

        def _parse_cpus(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        cpus = _parse_cpus(d.pop("cpus", UNSET))

        def _parse_cpus_per_task(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        cpus_per_task = _parse_cpus_per_task(d.pop("cpus_per_task", UNSET))

        _created_at = d.pop("created_at", UNSET)
        created_at: Union[Unset, datetime.datetime]
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        def _parse_current_working_directory(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        current_working_directory = _parse_current_working_directory(d.pop("current_working_directory", UNSET))

        def _parse_deadline(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                deadline_type_0 = isoparse(data)

                return deadline_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        deadline = _parse_deadline(d.pop("deadline", UNSET))

        def _parse_eligible_at(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                eligible_at_type_0 = isoparse(data)

                return eligible_at_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        eligible_at = _parse_eligible_at(d.pop("eligible_at", UNSET))

        def _parse_end_time(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                end_time_type_0 = isoparse(data)

                return end_time_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        end_time = _parse_end_time(d.pop("end_time", UNSET))

        def _parse_exit_code(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        exit_code = _parse_exit_code(d.pop("exit_code", UNSET))

        def _parse_flags(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                flags_type_0 = cast(list[str], data)

                return flags_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        flags = _parse_flags(d.pop("flags", UNSET))

        def _parse_gres_detail(data: object) -> Union[None, Unset, list["TaskGresDetailType0Item"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                gres_detail_type_0 = []
                _gres_detail_type_0 = data
                for gres_detail_type_0_item_data in _gres_detail_type_0:
                    gres_detail_type_0_item = TaskGresDetailType0Item.from_dict(gres_detail_type_0_item_data)

                    gres_detail_type_0.append(gres_detail_type_0_item)

                return gres_detail_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list["TaskGresDetailType0Item"]], data)

        gres_detail = _parse_gres_detail(d.pop("gres_detail", UNSET))

        def _parse_group_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        group_id = _parse_group_id(d.pop("group_id", UNSET))

        def _parse_group_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        group_name = _parse_group_name(d.pop("group_name", UNSET))

        id = d.pop("id", UNSET)

        job_id = d.pop("job_id", UNSET)

        def _parse_job_resources(data: object) -> Union["TaskJobResourcesType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                job_resources_type_0 = TaskJobResourcesType0.from_dict(data)

                return job_resources_type_0
            except:  # noqa: E722
                pass
            return cast(Union["TaskJobResourcesType0", None, Unset], data)

        job_resources = _parse_job_resources(d.pop("job_resources", UNSET))

        def _parse_last_sched_evaluation_at(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_sched_evaluation_at_type_0 = isoparse(data)

                return last_sched_evaluation_at_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        last_sched_evaluation_at = _parse_last_sched_evaluation_at(d.pop("last_sched_evaluation_at", UNSET))

        def _parse_memory(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        memory = _parse_memory(d.pop("memory", UNSET))

        def _parse_minimum_cpus_per_node(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        minimum_cpus_per_node = _parse_minimum_cpus_per_node(d.pop("minimum_cpus_per_node", UNSET))

        def _parse_minimum_tmp_disk_per_node(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        minimum_tmp_disk_per_node = _parse_minimum_tmp_disk_per_node(d.pop("minimum_tmp_disk_per_node", UNSET))

        name = d.pop("name", UNSET)

        def _parse_node_count(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        node_count = _parse_node_count(d.pop("node_count", UNSET))

        def _parse_nodes(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                nodes_type_0 = cast(list[str], data)

                return nodes_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        nodes = _parse_nodes(d.pop("nodes", UNSET))

        def _parse_partition(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        partition = _parse_partition(d.pop("partition", UNSET))

        def _parse_pre_sus_time(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        pre_sus_time = _parse_pre_sus_time(d.pop("pre_sus_time", UNSET))

        def _parse_priority(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        priority = _parse_priority(d.pop("priority", UNSET))

        def _parse_qos(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        qos = _parse_qos(d.pop("qos", UNSET))

        def _parse_requeue(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        requeue = _parse_requeue(d.pop("requeue", UNSET))

        def _parse_resize_time(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                resize_time_type_0 = isoparse(data)

                return resize_time_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        resize_time = _parse_resize_time(d.pop("resize_time", UNSET))

        def _parse_resources(data: object) -> Union["TaskResourcesType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                resources_type_0 = TaskResourcesType0.from_dict(data)

                return resources_type_0
            except:  # noqa: E722
                pass
            return cast(Union["TaskResourcesType0", None, Unset], data)

        resources = _parse_resources(d.pop("resources", UNSET))

        def _parse_restart_count(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        restart_count = _parse_restart_count(d.pop("restart_count", UNSET))

        def _parse_script(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        script = _parse_script(d.pop("script", UNSET))

        def _parse_slurm_state(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        slurm_state = _parse_slurm_state(d.pop("slurm_state", UNSET))

        def _parse_standard_error(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        standard_error = _parse_standard_error(d.pop("standard_error", UNSET))

        def _parse_standard_input(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        standard_input = _parse_standard_input(d.pop("standard_input", UNSET))

        def _parse_standard_output(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        standard_output = _parse_standard_output(d.pop("standard_output", UNSET))

        def _parse_started_at(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                started_at_type_0 = isoparse(data)

                return started_at_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        started_at = _parse_started_at(d.pop("started_at", UNSET))

        def _parse_state_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        state_description = _parse_state_description(d.pop("state_description", UNSET))

        def _parse_state_reason(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        state_reason = _parse_state_reason(d.pop("state_reason", UNSET))

        _status = d.pop("status", UNSET)
        status: Union[Unset, TaskStatus]
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = TaskStatus(_status)

        def _parse_std_err(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        std_err = _parse_std_err(d.pop("std_err", UNSET))

        def _parse_std_in(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        std_in = _parse_std_in(d.pop("std_in", UNSET))

        def _parse_std_out(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        std_out = _parse_std_out(d.pop("std_out", UNSET))

        def _parse_submit_time(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                submit_time_type_0 = isoparse(data)

                return submit_time_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        submit_time = _parse_submit_time(d.pop("submit_time", UNSET))

        def _parse_submit_user_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        submit_user_id = _parse_submit_user_id(d.pop("submit_user_id", UNSET))

        def _parse_submit_user_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        submit_user_name = _parse_submit_user_name(d.pop("submit_user_name", UNSET))

        def _parse_suspend_time(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                suspend_time_type_0 = isoparse(data)

                return suspend_time_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        suspend_time = _parse_suspend_time(d.pop("suspend_time", UNSET))

        def _parse_task_count(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        task_count = _parse_task_count(d.pop("task_count", UNSET))

        task_id = d.pop("task_id", UNSET)

        def _parse_tasks(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        tasks = _parse_tasks(d.pop("tasks", UNSET))

        def _parse_team_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        team_id = _parse_team_id(d.pop("team_id", UNSET))

        def _parse_time_limit(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        time_limit = _parse_time_limit(d.pop("time_limit", UNSET))

        def _parse_time_used(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        time_used = _parse_time_used(d.pop("time_used", UNSET))

        def _parse_tres(data: object) -> Union["TaskTresType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                tres_type_0 = TaskTresType0.from_dict(data)

                return tres_type_0
            except:  # noqa: E722
                pass
            return cast(Union["TaskTresType0", None, Unset], data)

        tres = _parse_tres(d.pop("tres", UNSET))

        def _parse_tres_alloc_str(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        tres_alloc_str = _parse_tres_alloc_str(d.pop("tres_alloc_str", UNSET))

        def _parse_tres_req_str(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        tres_req_str = _parse_tres_req_str(d.pop("tres_req_str", UNSET))

        def _parse_tres_used(data: object) -> Union["TaskTresUsedType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                tres_used_type_0 = TaskTresUsedType0.from_dict(data)

                return tres_used_type_0
            except:  # noqa: E722
                pass
            return cast(Union["TaskTresUsedType0", None, Unset], data)

        tres_used = _parse_tres_used(d.pop("tres_used", UNSET))

        _updated_at = d.pop("updated_at", UNSET)
        updated_at: Union[Unset, datetime.datetime]
        if isinstance(_updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)

        user_id = d.pop("user_id", UNSET)

        def _parse_user_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        user_name = _parse_user_name(d.pop("user_name", UNSET))

        def _parse_work_dir(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        work_dir = _parse_work_dir(d.pop("work_dir", UNSET))

        task = cls(
            account=account,
            alloc_tres=alloc_tres,
            array_job_id=array_job_id,
            array_task_id=array_task_id,
            attempt_id=attempt_id,
            batch_features=batch_features,
            batch_host=batch_host,
            cluster=cluster,
            cluster_id=cluster_id,
            command=command,
            comment=comment,
            completed_at=completed_at,
            cpus=cpus,
            cpus_per_task=cpus_per_task,
            created_at=created_at,
            current_working_directory=current_working_directory,
            deadline=deadline,
            eligible_at=eligible_at,
            end_time=end_time,
            exit_code=exit_code,
            flags=flags,
            gres_detail=gres_detail,
            group_id=group_id,
            group_name=group_name,
            id=id,
            job_id=job_id,
            job_resources=job_resources,
            last_sched_evaluation_at=last_sched_evaluation_at,
            memory=memory,
            minimum_cpus_per_node=minimum_cpus_per_node,
            minimum_tmp_disk_per_node=minimum_tmp_disk_per_node,
            name=name,
            node_count=node_count,
            nodes=nodes,
            partition=partition,
            pre_sus_time=pre_sus_time,
            priority=priority,
            qos=qos,
            requeue=requeue,
            resize_time=resize_time,
            resources=resources,
            restart_count=restart_count,
            script=script,
            slurm_state=slurm_state,
            standard_error=standard_error,
            standard_input=standard_input,
            standard_output=standard_output,
            started_at=started_at,
            state_description=state_description,
            state_reason=state_reason,
            status=status,
            std_err=std_err,
            std_in=std_in,
            std_out=std_out,
            submit_time=submit_time,
            submit_user_id=submit_user_id,
            submit_user_name=submit_user_name,
            suspend_time=suspend_time,
            task_count=task_count,
            task_id=task_id,
            tasks=tasks,
            team_id=team_id,
            time_limit=time_limit,
            time_used=time_used,
            tres=tres,
            tres_alloc_str=tres_alloc_str,
            tres_req_str=tres_req_str,
            tres_used=tres_used,
            updated_at=updated_at,
            user_id=user_id,
            user_name=user_name,
            work_dir=work_dir,
        )

        task.additional_properties = d
        return task

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
