from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Mapped

from subarashii.db import Base


class SubarashiiTable(Base):
    __tablename__ = "subarashii_table"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)

    subarashii_field: Mapped[str] = Column(String)
