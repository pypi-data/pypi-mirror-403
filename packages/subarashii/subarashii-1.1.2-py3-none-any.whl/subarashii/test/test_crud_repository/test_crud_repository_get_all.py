from sqlalchemy.orm import Session

from subarashii.model.subarashii_table import SubarashiiTable
from subarashii.repository import CRUDRepository


def test_crud_repository_get_all_returns_empty_list(session: Session):
    repository = CRUDRepository(session, SubarashiiTable)

    page = repository.get_all()

    assert page.elements == []

    assert page.total == 0


def test_crud_repository_get_all_returns_not_empty_list(session: Session):
    repository = CRUDRepository(session, SubarashiiTable)

    repository.save(SubarashiiTable(subarashii_field="subarashii value"))

    page = repository.get_all()

    assert page.elements != []

    assert page.total != 0
