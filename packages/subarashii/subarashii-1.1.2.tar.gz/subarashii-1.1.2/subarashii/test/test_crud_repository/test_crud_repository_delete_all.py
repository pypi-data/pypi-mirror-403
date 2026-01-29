from sqlalchemy.orm import Session

from subarashii.model.subarashii_table import SubarashiiTable
from subarashii.repository import CRUDRepository


def test_crud_repository_delete_all(session: Session):
    repository = CRUDRepository(session, SubarashiiTable)

    repository.save(SubarashiiTable(subarashii_field="subarashii value"))

    repository.save(SubarashiiTable(subarashii_field="another subarashii value"))

    repository.save(SubarashiiTable(subarashii_field="another another subarashii value"))

    page = repository.get_all()

    start = page.total

    repository.delete_all()

    page = repository.get_all()

    end = page.total

    assert page.total == 0

    assert start != end
