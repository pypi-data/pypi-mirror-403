from typing import Optional

from sqlalchemy import MetaData, String
from sqlalchemy.orm import declarative_base, mapped_column, Mapped

SCHEMA = "code_systems"

metadata_obj = MetaData(schema=SCHEMA)
Base = declarative_base(metadata=metadata_obj)


class Ctcae60(Base):
    __tablename__ = "ctcae_60"

    code: Mapped[str] = mapped_column(String(8), primary_key=True)
    term: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"Ctcae60(code={self.code!r}, term={self.term!r})"


class Icdo3(Base):
    __tablename__ = "icdo_3"

    morphological_code: Mapped[str] = mapped_column(String(6), primary_key=True)
    morphological_term: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"Icdo3(morphological_code={self.morphological_code!r}, morphological_term={self.morphological_term!r})"
