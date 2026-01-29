from sqlalchemy.orm import Session

from subarashii.model.subarashii_table import SubarashiiTable
from subarashii.repository import CRUDRepository


def test_crud_repository_exists_by_id(session: Session):
    repository = CRUDRepository(session, SubarashiiTable)

    result = repository.save(SubarashiiTable(subarashii_field="subarashii value"))

    assert repository.exists_by_id(result.id) is not None

    assert repository.exists_by_id(result.id + 1) is not None
