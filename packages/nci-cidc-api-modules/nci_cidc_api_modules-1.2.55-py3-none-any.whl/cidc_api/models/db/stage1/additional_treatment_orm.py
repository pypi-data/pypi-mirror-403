from __future__ import annotations
from pydantic import NonNegativeInt

from sqlalchemy import ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cidc_api.models.db.stage1.base_orm import BaseORM
from cidc_api.models.db.stage1.trial_orm import TrialORM


class AdditionalTreatmentORM(BaseORM):
    __tablename__ = "additional_treatment"
    __repr_attrs__ = ["additional_treatment_id", "participant_id"]
    __data_category__ = "additional_treatment"
    __table_args__ = (
        ForeignKeyConstraint(["trial_id", "version"], [TrialORM.trial_id, TrialORM.version], ondelete="CASCADE"),
    )

    trial_id: Mapped[str]
    version: Mapped[str]

    additional_treatment_id: Mapped[int] = mapped_column(primary_key=True)
    participant_id: Mapped[int] = mapped_column(ForeignKey("stage1.participant.participant_id", ondelete="CASCADE"))

    additional_treatment_days_to_start: Mapped[NonNegativeInt | None]
    additional_treatment_days_to_end: Mapped[NonNegativeInt | None]
    additional_treatment_description: Mapped[str]

    participant: Mapped["ParticipantORM"] = relationship(back_populates="additional_treatments", cascade="all, delete")
