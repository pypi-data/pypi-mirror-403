# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Any, List, Generic, TypeVar, Optional, cast
from typing_extensions import Protocol, override, runtime_checkable

from ._base_client import BasePage, PageInfo, BaseSyncPage, BaseAsyncPage

__all__ = ["SyncListTasks", "AsyncListTasks", "SyncListEnvs", "AsyncListEnvs"]

_T = TypeVar("_T")


@runtime_checkable
class ListTasksItem(Protocol):
    id: str


@runtime_checkable
class ListEnvsItem(Protocol):
    name: str


class SyncListTasks(BaseSyncPage[_T], BasePage[_T], Generic[_T]):
    result: List[_T]

    @override
    def _get_page_items(self) -> List[_T]:
        result = self.result
        if not result:
            return []
        return result

    @override
    def next_page_info(self) -> Optional[PageInfo]:
        is_forwards = not self._options.params.get("ending_before", False)

        result = self.result
        if not result:
            return None

        if is_forwards:
            item = cast(Any, result[-1])
            if not isinstance(item, ListTasksItem) or item.id is None:  # pyright: ignore[reportUnnecessaryComparison]
                # TODO emit warning log
                return None

            return PageInfo(params={"starting_after": item.id})
        else:
            item = cast(Any, self.result[0])
            if not isinstance(item, ListTasksItem) or item.id is None:  # pyright: ignore[reportUnnecessaryComparison]
                # TODO emit warning log
                return None

            return PageInfo(params={"ending_before": item.id})


class AsyncListTasks(BaseAsyncPage[_T], BasePage[_T], Generic[_T]):
    result: List[_T]

    @override
    def _get_page_items(self) -> List[_T]:
        result = self.result
        if not result:
            return []
        return result

    @override
    def next_page_info(self) -> Optional[PageInfo]:
        is_forwards = not self._options.params.get("ending_before", False)

        result = self.result
        if not result:
            return None

        if is_forwards:
            item = cast(Any, result[-1])
            if not isinstance(item, ListTasksItem) or item.id is None:  # pyright: ignore[reportUnnecessaryComparison]
                # TODO emit warning log
                return None

            return PageInfo(params={"starting_after": item.id})
        else:
            item = cast(Any, self.result[0])
            if not isinstance(item, ListTasksItem) or item.id is None:  # pyright: ignore[reportUnnecessaryComparison]
                # TODO emit warning log
                return None

            return PageInfo(params={"ending_before": item.id})


class SyncListEnvs(BaseSyncPage[_T], BasePage[_T], Generic[_T]):
    environments: List[_T]

    @override
    def _get_page_items(self) -> List[_T]:
        environments = self.environments
        if not environments:
            return []
        return environments

    @override
    def next_page_info(self) -> Optional[PageInfo]:
        is_forwards = not self._options.params.get("ending_before", False)

        environments = self.environments
        if not environments:
            return None

        if is_forwards:
            item = cast(Any, environments[-1])
            if not isinstance(item, ListEnvsItem) or item.name is None:  # pyright: ignore[reportUnnecessaryComparison]
                # TODO emit warning log
                return None

            return PageInfo(params={"starting_after": item.name})
        else:
            item = cast(Any, self.environments[0])
            if not isinstance(item, ListEnvsItem) or item.name is None:  # pyright: ignore[reportUnnecessaryComparison]
                # TODO emit warning log
                return None

            return PageInfo(params={"ending_before": item.name})


class AsyncListEnvs(BaseAsyncPage[_T], BasePage[_T], Generic[_T]):
    environments: List[_T]

    @override
    def _get_page_items(self) -> List[_T]:
        environments = self.environments
        if not environments:
            return []
        return environments

    @override
    def next_page_info(self) -> Optional[PageInfo]:
        is_forwards = not self._options.params.get("ending_before", False)

        environments = self.environments
        if not environments:
            return None

        if is_forwards:
            item = cast(Any, environments[-1])
            if not isinstance(item, ListEnvsItem) or item.name is None:  # pyright: ignore[reportUnnecessaryComparison]
                # TODO emit warning log
                return None

            return PageInfo(params={"starting_after": item.name})
        else:
            item = cast(Any, self.environments[0])
            if not isinstance(item, ListEnvsItem) or item.name is None:  # pyright: ignore[reportUnnecessaryComparison]
                # TODO emit warning log
                return None

            return PageInfo(params={"ending_before": item.name})
