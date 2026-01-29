from sqlalchemy.orm import Session

from subarashii.model.subarashii_table import SubarashiiTable
from subarashii.repository import CRUDRepository


def test_crud_repository_count(session: Session):
    repository = CRUDRepository(session, SubarashiiTable)

    count = repository.count()

    assert count == 0

    repository.save(SubarashiiTable(subarashii_field="subarashii value"))

    count = repository.count()

    assert count == 1

    repository.save(SubarashiiTable(subarashii_field="another subarashii value"))

    count = repository.count()

    assert count == 2
