from __future__ import annotations
from sqlalchemy import ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cidc_api.models.db.stage2.base_orm import BaseORM
from cidc_api.models.db.stage2.trial_orm import TrialORM


class CohortORM(BaseORM):
    __tablename__ = "cohort"
    __repr_attrs__ = ["trial_id", "cohort_name"]
    __data_category__ = "cohort"
    __table_args__ = (
        ForeignKeyConstraint(["trial_id", "version"], [TrialORM.trial_id, TrialORM.version], ondelete="CASCADE"),
    )

    trial_id: Mapped[str]
    version: Mapped[str]

    cohort_id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str]

    trial: Mapped[TrialORM] = relationship(back_populates="cohorts", cascade="all, delete")
