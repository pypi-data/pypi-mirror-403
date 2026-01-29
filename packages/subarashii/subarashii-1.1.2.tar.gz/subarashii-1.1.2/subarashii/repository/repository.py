from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Iterable, Optional, List

from subarashii import Page, Pageable

ID = TypeVar("ID")

ENTITY = TypeVar("ENTITY")


class Repository(Generic[ENTITY, ID], ABC):
    @abstractmethod
    def save(self, entity: ENTITY) -> ENTITY:
        pass

    @abstractmethod
    def save_all(self, iterable: Iterable[ENTITY]) -> Iterable[ENTITY]:
        pass

    @abstractmethod
    def get_all(self, pageable: Optional[Pageable] = None) -> Page[ENTITY]:
        pass

    @abstractmethod
    def get_by_id(self, id: ID) -> Optional[ENTITY]:
        pass

    @abstractmethod
    def get_by(self, **kwargs) -> List[ENTITY]:
        pass

    @abstractmethod
    def update(self, id: ID, entity: ENTITY) -> ENTITY:
        pass

    @abstractmethod
    def delete(self, id: ID) -> None:
        pass

    @abstractmethod
    def delete_all(self) -> None:
        pass

    @abstractmethod
    def count(self) -> int:
        pass

    @abstractmethod
    def exists_by_id(self, id: ID) -> bool:
        pass
