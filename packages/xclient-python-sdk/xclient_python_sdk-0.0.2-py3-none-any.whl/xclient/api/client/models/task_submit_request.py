from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.task_submit_request_environment_type_0 import TaskSubmitRequestEnvironmentType0


T = TypeVar("T", bound="TaskSubmitRequest")


@_attrs_define
class TaskSubmitRequest:
    """Task submission request

    Attributes:
        cluster_id (int): Slurm cluster ID to submit task to Example: 1.
        name (str): Task name Example: training-job.
        account (Union[None, Unset, str]): Account Example: research.
        command (Union[None, Unset, str]): Command to execute (alternative to script) Example: python train.py.
        comment (Union[None, Unset, str]): Job comment
        constraint (Union[None, Unset, str]): Node constraint Example: gpu.
        cpu_bind (Union[None, Unset, str]): CPU binding
        cpus_per_task (Union[None, Unset, int]): CPUs per task Example: 1.
        dependency (Union[None, Unset, str]): Job dependencies Example: afterok:12345.
        distribution (Union[None, Unset, str]): Task distribution Example: block.
        environment (Union['TaskSubmitRequestEnvironmentType0', None, Unset]): Environment variables as key-value pairs
            Example: {'CUDA_VISIBLE_DEVICES': '0,1', 'PYTHONPATH': '/opt/python/lib'}.
        error (Union[None, Unset, str]): Standard error file pattern Example: error_%j.log.
        exclude (Union[None, Unset, str]): Nodes to exclude
        export (Union[None, Unset, str]): Environment export Example: ALL.
        gres (Union[None, Unset, str]): Generic resources (e.g., "gpu:1", "gpu:tesla:2") Example: gpu:1.
        input_ (Union[None, Unset, str]): Standard input file
        mem_bind (Union[None, Unset, str]): Memory binding
        memory (Union[None, Unset, str]): Memory requirement (e.g., "8G", "4096M") Example: 8G.
        nice (Union[None, Unset, int]): Nice value
        nodelist (Union[None, Unset, str]): Specific nodes to use
        nodes (Union[None, Unset, int]): Number of nodes Example: 1.
        ntasks (Union[None, Unset, int]): Number of tasks Example: 4.
        output (Union[None, Unset, str]): Standard output file pattern Example: output_%j.log.
        partition (Union[None, Unset, str]): Partition name Example: gpu.
        qos (Union[None, Unset, str]): Quality of Service Example: normal.
        reservation (Union[None, Unset, str]): Reservation name
        script (Union[Unset, str]): Task script content (bash script with Example: #!/bin/bash
            #SBATCH --job-name=training
            python train.py.
        team_id (Union[None, Unset, int]): Team ID (auto-filled from current team) Example: 1.
        time (Union[None, Unset, str]): Time limit (format: DD-HH:MM:SS, HH:MM:SS, or MM:SS) Example: 01:00:00.
        tres (Union[None, Unset, str]): Trackable resources string Example: cpu=4,mem=8G.
    """

    cluster_id: int
    name: str
    account: Union[None, Unset, str] = UNSET
    command: Union[None, Unset, str] = UNSET
    comment: Union[None, Unset, str] = UNSET
    constraint: Union[None, Unset, str] = UNSET
    cpu_bind: Union[None, Unset, str] = UNSET
    cpus_per_task: Union[None, Unset, int] = UNSET
    dependency: Union[None, Unset, str] = UNSET
    distribution: Union[None, Unset, str] = UNSET
    environment: Union["TaskSubmitRequestEnvironmentType0", None, Unset] = UNSET
    error: Union[None, Unset, str] = UNSET
    exclude: Union[None, Unset, str] = UNSET
    export: Union[None, Unset, str] = UNSET
    gres: Union[None, Unset, str] = UNSET
    input_: Union[None, Unset, str] = UNSET
    mem_bind: Union[None, Unset, str] = UNSET
    memory: Union[None, Unset, str] = UNSET
    nice: Union[None, Unset, int] = UNSET
    nodelist: Union[None, Unset, str] = UNSET
    nodes: Union[None, Unset, int] = UNSET
    ntasks: Union[None, Unset, int] = UNSET
    output: Union[None, Unset, str] = UNSET
    partition: Union[None, Unset, str] = UNSET
    qos: Union[None, Unset, str] = UNSET
    reservation: Union[None, Unset, str] = UNSET
    script: Union[Unset, str] = UNSET
    team_id: Union[None, Unset, int] = UNSET
    time: Union[None, Unset, str] = UNSET
    tres: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.task_submit_request_environment_type_0 import TaskSubmitRequestEnvironmentType0

        cluster_id = self.cluster_id

        name = self.name

        account: Union[None, Unset, str]
        if isinstance(self.account, Unset):
            account = UNSET
        else:
            account = self.account

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

        constraint: Union[None, Unset, str]
        if isinstance(self.constraint, Unset):
            constraint = UNSET
        else:
            constraint = self.constraint

        cpu_bind: Union[None, Unset, str]
        if isinstance(self.cpu_bind, Unset):
            cpu_bind = UNSET
        else:
            cpu_bind = self.cpu_bind

        cpus_per_task: Union[None, Unset, int]
        if isinstance(self.cpus_per_task, Unset):
            cpus_per_task = UNSET
        else:
            cpus_per_task = self.cpus_per_task

        dependency: Union[None, Unset, str]
        if isinstance(self.dependency, Unset):
            dependency = UNSET
        else:
            dependency = self.dependency

        distribution: Union[None, Unset, str]
        if isinstance(self.distribution, Unset):
            distribution = UNSET
        else:
            distribution = self.distribution

        environment: Union[None, Unset, dict[str, Any]]
        if isinstance(self.environment, Unset):
            environment = UNSET
        elif isinstance(self.environment, TaskSubmitRequestEnvironmentType0):
            environment = self.environment.to_dict()
        else:
            environment = self.environment

        error: Union[None, Unset, str]
        if isinstance(self.error, Unset):
            error = UNSET
        else:
            error = self.error

        exclude: Union[None, Unset, str]
        if isinstance(self.exclude, Unset):
            exclude = UNSET
        else:
            exclude = self.exclude

        export: Union[None, Unset, str]
        if isinstance(self.export, Unset):
            export = UNSET
        else:
            export = self.export

        gres: Union[None, Unset, str]
        if isinstance(self.gres, Unset):
            gres = UNSET
        else:
            gres = self.gres

        input_: Union[None, Unset, str]
        if isinstance(self.input_, Unset):
            input_ = UNSET
        else:
            input_ = self.input_

        mem_bind: Union[None, Unset, str]
        if isinstance(self.mem_bind, Unset):
            mem_bind = UNSET
        else:
            mem_bind = self.mem_bind

        memory: Union[None, Unset, str]
        if isinstance(self.memory, Unset):
            memory = UNSET
        else:
            memory = self.memory

        nice: Union[None, Unset, int]
        if isinstance(self.nice, Unset):
            nice = UNSET
        else:
            nice = self.nice

        nodelist: Union[None, Unset, str]
        if isinstance(self.nodelist, Unset):
            nodelist = UNSET
        else:
            nodelist = self.nodelist

        nodes: Union[None, Unset, int]
        if isinstance(self.nodes, Unset):
            nodes = UNSET
        else:
            nodes = self.nodes

        ntasks: Union[None, Unset, int]
        if isinstance(self.ntasks, Unset):
            ntasks = UNSET
        else:
            ntasks = self.ntasks

        output: Union[None, Unset, str]
        if isinstance(self.output, Unset):
            output = UNSET
        else:
            output = self.output

        partition: Union[None, Unset, str]
        if isinstance(self.partition, Unset):
            partition = UNSET
        else:
            partition = self.partition

        qos: Union[None, Unset, str]
        if isinstance(self.qos, Unset):
            qos = UNSET
        else:
            qos = self.qos

        reservation: Union[None, Unset, str]
        if isinstance(self.reservation, Unset):
            reservation = UNSET
        else:
            reservation = self.reservation

        script = self.script

        team_id: Union[None, Unset, int]
        if isinstance(self.team_id, Unset):
            team_id = UNSET
        else:
            team_id = self.team_id

        time: Union[None, Unset, str]
        if isinstance(self.time, Unset):
            time = UNSET
        else:
            time = self.time

        tres: Union[None, Unset, str]
        if isinstance(self.tres, Unset):
            tres = UNSET
        else:
            tres = self.tres

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "cluster_id": cluster_id,
                "name": name,
            }
        )
        if account is not UNSET:
            field_dict["account"] = account
        if command is not UNSET:
            field_dict["command"] = command
        if comment is not UNSET:
            field_dict["comment"] = comment
        if constraint is not UNSET:
            field_dict["constraint"] = constraint
        if cpu_bind is not UNSET:
            field_dict["cpu_bind"] = cpu_bind
        if cpus_per_task is not UNSET:
            field_dict["cpus_per_task"] = cpus_per_task
        if dependency is not UNSET:
            field_dict["dependency"] = dependency
        if distribution is not UNSET:
            field_dict["distribution"] = distribution
        if environment is not UNSET:
            field_dict["environment"] = environment
        if error is not UNSET:
            field_dict["error"] = error
        if exclude is not UNSET:
            field_dict["exclude"] = exclude
        if export is not UNSET:
            field_dict["export"] = export
        if gres is not UNSET:
            field_dict["gres"] = gres
        if input_ is not UNSET:
            field_dict["input"] = input_
        if mem_bind is not UNSET:
            field_dict["mem_bind"] = mem_bind
        if memory is not UNSET:
            field_dict["memory"] = memory
        if nice is not UNSET:
            field_dict["nice"] = nice
        if nodelist is not UNSET:
            field_dict["nodelist"] = nodelist
        if nodes is not UNSET:
            field_dict["nodes"] = nodes
        if ntasks is not UNSET:
            field_dict["ntasks"] = ntasks
        if output is not UNSET:
            field_dict["output"] = output
        if partition is not UNSET:
            field_dict["partition"] = partition
        if qos is not UNSET:
            field_dict["qos"] = qos
        if reservation is not UNSET:
            field_dict["reservation"] = reservation
        if script is not UNSET:
            field_dict["script"] = script
        if team_id is not UNSET:
            field_dict["team_id"] = team_id
        if time is not UNSET:
            field_dict["time"] = time
        if tres is not UNSET:
            field_dict["tres"] = tres

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.task_submit_request_environment_type_0 import TaskSubmitRequestEnvironmentType0

        d = dict(src_dict)
        cluster_id = d.pop("cluster_id")

        name = d.pop("name")

        def _parse_account(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        account = _parse_account(d.pop("account", UNSET))

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

        def _parse_constraint(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        constraint = _parse_constraint(d.pop("constraint", UNSET))

        def _parse_cpu_bind(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        cpu_bind = _parse_cpu_bind(d.pop("cpu_bind", UNSET))

        def _parse_cpus_per_task(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        cpus_per_task = _parse_cpus_per_task(d.pop("cpus_per_task", UNSET))

        def _parse_dependency(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        dependency = _parse_dependency(d.pop("dependency", UNSET))

        def _parse_distribution(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        distribution = _parse_distribution(d.pop("distribution", UNSET))

        def _parse_environment(data: object) -> Union["TaskSubmitRequestEnvironmentType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                environment_type_0 = TaskSubmitRequestEnvironmentType0.from_dict(data)

                return environment_type_0
            except:  # noqa: E722
                pass
            return cast(Union["TaskSubmitRequestEnvironmentType0", None, Unset], data)

        environment = _parse_environment(d.pop("environment", UNSET))

        def _parse_error(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        error = _parse_error(d.pop("error", UNSET))

        def _parse_exclude(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        exclude = _parse_exclude(d.pop("exclude", UNSET))

        def _parse_export(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        export = _parse_export(d.pop("export", UNSET))

        def _parse_gres(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        gres = _parse_gres(d.pop("gres", UNSET))

        def _parse_input_(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        input_ = _parse_input_(d.pop("input", UNSET))

        def _parse_mem_bind(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        mem_bind = _parse_mem_bind(d.pop("mem_bind", UNSET))

        def _parse_memory(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        memory = _parse_memory(d.pop("memory", UNSET))

        def _parse_nice(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        nice = _parse_nice(d.pop("nice", UNSET))

        def _parse_nodelist(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        nodelist = _parse_nodelist(d.pop("nodelist", UNSET))

        def _parse_nodes(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        nodes = _parse_nodes(d.pop("nodes", UNSET))

        def _parse_ntasks(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        ntasks = _parse_ntasks(d.pop("ntasks", UNSET))

        def _parse_output(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        output = _parse_output(d.pop("output", UNSET))

        def _parse_partition(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        partition = _parse_partition(d.pop("partition", UNSET))

        def _parse_qos(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        qos = _parse_qos(d.pop("qos", UNSET))

        def _parse_reservation(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        reservation = _parse_reservation(d.pop("reservation", UNSET))

        script = d.pop("script", UNSET)

        def _parse_team_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        team_id = _parse_team_id(d.pop("team_id", UNSET))

        def _parse_time(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        time = _parse_time(d.pop("time", UNSET))

        def _parse_tres(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        tres = _parse_tres(d.pop("tres", UNSET))

        task_submit_request = cls(
            cluster_id=cluster_id,
            name=name,
            account=account,
            command=command,
            comment=comment,
            constraint=constraint,
            cpu_bind=cpu_bind,
            cpus_per_task=cpus_per_task,
            dependency=dependency,
            distribution=distribution,
            environment=environment,
            error=error,
            exclude=exclude,
            export=export,
            gres=gres,
            input_=input_,
            mem_bind=mem_bind,
            memory=memory,
            nice=nice,
            nodelist=nodelist,
            nodes=nodes,
            ntasks=ntasks,
            output=output,
            partition=partition,
            qos=qos,
            reservation=reservation,
            script=script,
            team_id=team_id,
            time=time,
            tres=tres,
        )

        task_submit_request.additional_properties = d
        return task_submit_request

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
