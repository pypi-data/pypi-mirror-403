from __future__ import annotations
from typing import List

from pydantic import NonNegativeInt
from sqlalchemy import ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cidc_api.models.db.stage2.base_orm import BaseORM
from cidc_api.models.db.stage2.trial_orm import TrialORM


class ConsentGroupORM(BaseORM):
    __tablename__ = "consent_group"
    __repr_attrs__ = ["consent_group_id", "consent_group_name"]
    __data_category__ = "consent_group"
    __table_args__ = (
        ForeignKeyConstraint(["trial_id", "version"], [TrialORM.trial_id, TrialORM.version], ondelete="CASCADE"),
    )

    trial_id: Mapped[str]
    version: Mapped[str]

    consent_group_id: Mapped[int] = mapped_column(primary_key=True)

    consent_group_short_name: Mapped[str]
    consent_group_name: Mapped[str]
    consent_group_number: Mapped[NonNegativeInt]

    trial: Mapped[TrialORM] = relationship(back_populates="consent_groups", cascade="all, delete")
    participants: Mapped[List[ParticipantORM]] = relationship(
        back_populates="consent_group", cascade="all, delete", passive_deletes=True
    )
