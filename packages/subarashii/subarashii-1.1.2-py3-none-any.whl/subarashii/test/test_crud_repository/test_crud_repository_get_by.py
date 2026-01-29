from pytest import raises
from sqlalchemy.orm import Session

from subarashii.exception.attribute_not_found_exception import AttributeNotFoundException
from subarashii.model.subarashii_table import SubarashiiTable
from subarashii.repository import CRUDRepository


def test_crud_repository_get_by_throws_value_error(session: Session):
    repository = CRUDRepository(session, SubarashiiTable)

    with raises(ValueError) as e:
        repository.get_by()

    assert e.value.args[0] == "at least one field must be provided for filtering"


def test_crud_repository_get_by_throws_attribute_not_found(session: Session):
    repository = CRUDRepository(session, SubarashiiTable)

    with raises(AttributeNotFoundException) as e:
        repository.get_by(not_subarashii_field="not subarashii value")

    assert e.value.args[0] == "attribute not found"


def test_crud_repository_get_by(session: Session):
    repository = CRUDRepository(session, SubarashiiTable)

    repository.save(SubarashiiTable(subarashii_field="subarashii value"))

    repository.save(SubarashiiTable(subarashii_field="another subarashii value"))

    repository.save(SubarashiiTable(subarashii_field="another another subarashii value"))

    repository.save(SubarashiiTable(subarashii_field="another another another subarashii value"))

    result = repository.get_by(subarashii_field="subarashii value")

    assert len(result) == 1

    assert result[0].subarashii_field == "subarashii value"
