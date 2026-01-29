from sqlalchemy.orm import Session

from subarashii.model.subarashii_table import SubarashiiTable
from subarashii.repository import CRUDRepository


def test_crud_repository_save(session: Session):
    repository = CRUDRepository(session, SubarashiiTable)

    result = repository.get_all()

    assert result.elements == []

    assert result.total == 0

    result = repository.save(SubarashiiTable(subarashii_field="subarashii value"))

    assert result is not None

    result = repository.get_by_id(result.id)

    assert result is not None

    page = repository.get_all()

    assert page.elements

    assert page.total == 1
