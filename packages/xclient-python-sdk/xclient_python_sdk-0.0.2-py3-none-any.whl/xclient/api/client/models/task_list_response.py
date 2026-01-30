from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.task import Task


T = TypeVar("T", bound="TaskListResponse")


@_attrs_define
class TaskListResponse:
    """
    Attributes:
        page (Union[Unset, int]):  Example: 1.
        page_size (Union[Unset, int]):  Example: 20.
        tasks (Union[Unset, list['Task']]): List of tasks
        total (Union[Unset, int]): Total number of tasks Example: 100.
    """

    page: Union[Unset, int] = UNSET
    page_size: Union[Unset, int] = UNSET
    tasks: Union[Unset, list["Task"]] = UNSET
    total: Union[Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        page = self.page

        page_size = self.page_size

        tasks: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.tasks, Unset):
            tasks = []
            for tasks_item_data in self.tasks:
                tasks_item = tasks_item_data.to_dict()
                tasks.append(tasks_item)

        total = self.total

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if page is not UNSET:
            field_dict["page"] = page
        if page_size is not UNSET:
            field_dict["page_size"] = page_size
        if tasks is not UNSET:
            field_dict["tasks"] = tasks
        if total is not UNSET:
            field_dict["total"] = total

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.task import Task

        d = dict(src_dict)
        page = d.pop("page", UNSET)

        page_size = d.pop("page_size", UNSET)

        tasks = []
        _tasks = d.pop("tasks", UNSET)
        for tasks_item_data in _tasks or []:
            tasks_item = Task.from_dict(tasks_item_data)

            tasks.append(tasks_item)

        total = d.pop("total", UNSET)

        task_list_response = cls(
            page=page,
            page_size=page_size,
            tasks=tasks,
            total=total,
        )

        task_list_response.additional_properties = d
        return task_list_response

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
