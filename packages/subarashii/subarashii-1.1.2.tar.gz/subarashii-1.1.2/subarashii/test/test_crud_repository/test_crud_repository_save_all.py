from sqlalchemy.orm import Session

from subarashii.model.subarashii_table import SubarashiiTable
from subarashii.repository import CRUDRepository


def test_crud_repository_save_all(session: Session):
    repository = CRUDRepository(session, SubarashiiTable)

    items = [
        SubarashiiTable(subarashii_field="subarashii value"),
        SubarashiiTable(subarashii_field="another subarashii value"),
        SubarashiiTable(subarashii_field="another another subarashii value"),
    ]

    repository.save_all(items)

    page = repository.get_all()

    assert page.total == len(items)

    for i in range(0, page.total):
        assert items[i].subarashii_field == page.elements[i].subarashii_field
