from pytest import raises
from sqlalchemy.orm import Session

from subarashii.exception.entity_not_found_exception import EntityNotFoundException
from subarashii.model.subarashii_table import SubarashiiTable
from subarashii.repository import CRUDRepository


def test_crud_repository_delete_throws_entity_not_found_exception(session: Session):
    repository = CRUDRepository(session, SubarashiiTable)

    with raises(EntityNotFoundException):
        repository.delete(1)


def test_crud_repository_delete(session: Session):
    repository = CRUDRepository(session, SubarashiiTable)

    expected_length = repository.get_all().total

    expected = repository.save(SubarashiiTable(subarashii_field="subarashii value"))

    repository.delete(expected.id)

    assert repository.get_all().total == expected_length
