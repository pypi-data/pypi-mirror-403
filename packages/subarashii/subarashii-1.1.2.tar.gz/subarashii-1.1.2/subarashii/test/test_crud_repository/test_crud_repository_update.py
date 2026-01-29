from pytest import raises
from sqlalchemy.orm import Session

from subarashii.exception.entity_not_found_exception import EntityNotFoundException
from subarashii.model.subarashii_table import SubarashiiTable
from subarashii.repository import CRUDRepository


def test_crud_repository_update_throws_entity_not_found_exception(session: Session):
    repository = CRUDRepository(session, SubarashiiTable)

    with raises(EntityNotFoundException):
        repository.update(1, SubarashiiTable(subarashii_field="subarashii value"))


def test_crud_repository_update(session: Session):
    repository = CRUDRepository(session, SubarashiiTable)

    expected = repository.save(SubarashiiTable(subarashii_field="subarashii value"))

    repository.update(expected.id, SubarashiiTable(subarashii_field="another subarashii value"))

    result = repository.get_by_id(expected.id)

    assert result is not None

    assert result.id == expected.id

    assert result.subarashii_field != "subarashii value"
