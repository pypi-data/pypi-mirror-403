from __future__ import annotations
from typing import List

from sqlalchemy import ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cidc_api.models.db.stage2.base_orm import BaseORM
from cidc_api.models.db.stage2.trial_orm import TrialORM


class InstitutionORM(BaseORM):
    __tablename__ = "institution"
    __repr_attrs__ = ["name"]
    __table_args__ = (
        ForeignKeyConstraint(["trial_id", "version"], [TrialORM.trial_id, TrialORM.version], ondelete="CASCADE"),
    )

    trial_id: Mapped[str]
    version: Mapped[str]

    institution_id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str]

    trial: Mapped[TrialORM] = relationship(back_populates="biobank", cascade="all, delete")
    administrative_people: Mapped[List[AdministrativePersonORM]] = relationship(
        back_populates="institution", cascade="all, delete", passive_deletes=True
    )
    shipments: Mapped[List[ShipmentORM]] = relationship(
        back_populates="institution", cascade="all, delete", passive_deletes=True
    )
    files: Mapped[List[FileORM]] = relationship(back_populates="creator", cascade="all, delete", passive_deletes=True)
    contacts: Mapped[List[ContactORM]] = relationship(back_populates="institution")
