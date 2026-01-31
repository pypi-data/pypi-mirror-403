from __future__ import annotations
from typing import List

from pydantic import NonPositiveInt, NegativeInt
from sqlalchemy import ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cidc_api.models.db.stage2.base_orm import BaseORM
from cidc_api.models.db.stage2.trial_orm import TrialORM
from cidc_api.models.types import ConditioningRegimenType, StemCellDonorType


class PriorTreatmentORM(BaseORM):
    __tablename__ = "prior_treatment"
    __repr_attrs__ = ["prior_treatment_id", "type"]
    __data_category__ = "prior_treatment"
    __table_args__ = (
        ForeignKeyConstraint(["trial_id", "version"], [TrialORM.trial_id, TrialORM.version], ondelete="CASCADE"),
    )

    trial_id: Mapped[str]
    version: Mapped[str]

    prior_treatment_id: Mapped[int] = mapped_column(primary_key=True)
    participant_id: Mapped[int] = mapped_column(ForeignKey("stage2.participant.participant_id", ondelete="CASCADE"))

    prior_treatment_days_to_start: Mapped[NonPositiveInt | None]
    prior_treatment_days_to_end: Mapped[NonPositiveInt | None]
    prior_treatment_description: Mapped[str]
    prior_treatment_best_response: Mapped[str | None]
    prior_treatment_conditioning_regimen_type: Mapped[ConditioningRegimenType | None]
    prior_treatment_stem_cell_donor_type: Mapped[StemCellDonorType | None]
    prior_treatment_days_from_transplant_to_treatment_initiation: Mapped[NegativeInt | None]

    participant: Mapped[ParticipantORM] = relationship(back_populates="prior_treatments", cascade="all, delete")
