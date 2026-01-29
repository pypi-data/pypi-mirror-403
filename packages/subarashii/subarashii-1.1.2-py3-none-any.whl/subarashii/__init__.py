from typing import Generic, List, TypeVar

from subarashii.db import SessionLocal
from subarashii.exception.attribute_not_found_exception import AttributeNotFoundException
from subarashii.exception.entity_not_found_exception import EntityNotFoundException

ID = TypeVar("ID")

ENTITY = TypeVar("ENTITY")


class Pageable:
    def __init__(self, page: int = 0, size: int = 10):
        self.page = max(page, 0)

        self.size = max(size, 1)

    def __str__(self):
        return f"Pageable(page={self.page}, size={self.size})"


class Page(Generic[ENTITY]):
    def __init__(self, elements: List[ENTITY], total: int, page: int, size: int):
        self.elements = elements

        self.total = total

        self.page = page

        self.size = size

    def __str__(self):
        return f"Page(page={self.page}, size={self.size}, total={self.total}, elements={self.elements})"
