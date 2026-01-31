from __future__ import annotations
from typing import List

from sqlalchemy import ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cidc_api.models.db.stage2.base_orm import BaseORM
from cidc_api.models.db.stage2.trial_orm import TrialORM


class AdministrativePersonORM(BaseORM):
    __tablename__ = "administrative_person"
    __repr_attrs__ = ["first_name", "last_name"]
    __table_args__ = (
        ForeignKeyConstraint(["trial_id", "version"], [TrialORM.trial_id, TrialORM.version], ondelete="CASCADE"),
    )

    trial_id: Mapped[str]
    version: Mapped[str]

    administrative_person_id: Mapped[int] = mapped_column(primary_key=True)
    institution_id: Mapped[int] = mapped_column(ForeignKey("stage2.institution.institution_id", ondelete="CASCADE"))
    first_name: Mapped[str]
    middle_name: Mapped[str | None]
    last_name: Mapped[str]
    email: Mapped[str | None]
    phone_number: Mapped[str | None]

    institution: Mapped[InstitutionORM] = relationship(back_populates="administrative_people", cascade="all, delete")
    administrative_role_assignments: Mapped[List[AdministrativeRoleAssignmentORM]] = relationship(
        back_populates="administrative_person", cascade="all, delete", passive_deletes=True
    )
