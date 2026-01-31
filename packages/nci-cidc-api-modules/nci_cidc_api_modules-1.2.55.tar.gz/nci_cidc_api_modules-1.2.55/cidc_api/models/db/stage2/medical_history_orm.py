from __future__ import annotations
from typing import List

from pydantic import NonNegativeInt, PositiveFloat
from sqlalchemy import ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cidc_api.models.db.stage2.base_orm import BaseORM
from cidc_api.models.db.stage2.trial_orm import TrialORM
from cidc_api.models.types import TobaccoSmokingStatus


class MedicalHistoryORM(BaseORM):
    __tablename__ = "medical_history"
    __repr_attrs__ = ["medical_history_id"]
    __data_category__ = "medical_history"
    __table_args__ = (
        ForeignKeyConstraint(["trial_id", "version"], [TrialORM.trial_id, TrialORM.version], ondelete="CASCADE"),
    )

    trial_id: Mapped[str]
    version: Mapped[str]

    medical_history_id: Mapped[int] = mapped_column(primary_key=True)
    participant_id: Mapped[int] = mapped_column(ForeignKey("stage2.participant.participant_id", ondelete="CASCADE"))

    tobacco_smoking_status: Mapped[TobaccoSmokingStatus | None]
    pack_years_smoked: Mapped[PositiveFloat | None]
    num_prior_systemic_therapies: Mapped[NonNegativeInt | None]

    participant: Mapped[ParticipantORM] = relationship(back_populates="medical_history", cascade="all, delete")
    other_malignancies: Mapped[List[OtherMalignancyORM]] = relationship(
        back_populates="medical_history", cascade="all, delete", passive_deletes=True
    )
    comorbidities: Mapped[List[ComorbidityORM]] = relationship(
        back_populates="medical_history", cascade="all, delete", passive_deletes=True
    )
