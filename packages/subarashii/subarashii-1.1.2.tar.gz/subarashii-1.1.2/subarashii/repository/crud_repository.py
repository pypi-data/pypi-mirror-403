from typing import TypeVar, Type, Iterable, Optional, List

from sqlalchemy import exists
from sqlalchemy.orm import Session

from subarashii import Pageable, Page
from subarashii.exception.attribute_not_found_exception import AttributeNotFoundException
from subarashii.exception.entity_not_found_exception import EntityNotFoundException
from subarashii.repository.repository import Repository

ID = TypeVar("ID")

ENTITY = TypeVar("ENTITY")


class CRUDRepository(Repository[ENTITY, ID]):
    def __init__(self, session: Session, model: Type[ENTITY]) -> None:
        self.session = session

        self.model = model

    def save(self, entity: ENTITY) -> ENTITY:
        self.session.add(entity)

        self.session.commit()

        self.session.refresh(entity)

        return entity

    def save_all(self, iterable: Iterable[ENTITY]) -> Iterable[ENTITY]:
        self.session.add_all(iterable)

        self.session.commit()

        return iterable

    def get_all(self, pageable: Optional[Pageable] = None) -> Page[ENTITY]:
        query = self.session.query(self.model)

        total = query.count()

        if pageable:
            query = query.offset(pageable.page * pageable.size).limit(pageable.size)

            elements = query.all()

            return Page(elements, total, pageable.page, pageable.size)
        else:
            elements = query.all()

            return Page(elements, total, 0, total)

    def get_by_id(self, id: ID) -> Optional[ENTITY]:
        return self.session.get(self.model, id)

    def get_by(self, **kwargs) -> List[ENTITY]:
        if not kwargs:
            raise ValueError("at least one field must be provided for filtering")

        query = self.session.query(self.model)

        for key in kwargs:
            if not hasattr(self.model, key):
                raise AttributeNotFoundException()

        query = query.filter_by(**kwargs)

        return query.all()

    def update(self, id: ID, entity: ENTITY) -> ENTITY:
        existing = self.get_by_id(id)

        if not existing:
            raise EntityNotFoundException()

        for attr, value in vars(entity).items():
            if attr.startswith("_"):
                continue

            setattr(existing, attr, value)

        self.session.commit()

        self.session.refresh(existing)

        return existing

    def delete(self, id: ID) -> None:
        entity = self.get_by_id(id)

        if not entity:
            raise EntityNotFoundException()

        self.session.delete(entity)

        self.session.commit()

    def delete_all(self) -> None:
        self.session.query(self.model).delete()

        self.session.commit()

    def count(self) -> int:
        return self.session.query(self.model).count()

    def exists_by_id(self, id: ID) -> bool:
        return self.session.query(exists().where(self.model.id == id)).scalar()
