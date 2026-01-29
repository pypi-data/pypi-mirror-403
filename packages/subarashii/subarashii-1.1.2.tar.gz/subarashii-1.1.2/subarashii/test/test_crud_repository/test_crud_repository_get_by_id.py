from sqlalchemy.orm import Session

from subarashii.model.subarashii_table import SubarashiiTable
from subarashii.repository import CRUDRepository


def test_crud_repository_get_by_id_returning_none(session: Session):
    repository = CRUDRepository(session, SubarashiiTable)

    result = repository.get_by_id(1)

    assert result is None


def test_crud_repository_get_by_id(session: Session):
    repository = CRUDRepository(session, SubarashiiTable)

    result = repository.save(SubarashiiTable(subarashii_field="subarashii value"))

    result = repository.get_by_id(result.id)

    assert result is not None
