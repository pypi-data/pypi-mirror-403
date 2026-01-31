from __future__ import annotations
from pydantic import NonNegativeInt

from sqlalchemy import ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cidc_api.models.db.stage2.base_orm import BaseORM
from cidc_api.models.db.stage2.trial_orm import TrialORM
from cidc_api.models.types import SurvivalStatus, CauseOfDeath, YNUNA, YN


class ResponseORM(BaseORM):
    __tablename__ = "response"
    __repr_attrs__ = ["response_id", "participant_id"]
    __data_category__ = "response"
    __table_args__ = (
        ForeignKeyConstraint(["trial_id", "version"], [TrialORM.trial_id, TrialORM.version], ondelete="CASCADE"),
    )

    trial_id: Mapped[str]
    version: Mapped[str]

    response_id: Mapped[int] = mapped_column(primary_key=True)
    participant_id: Mapped[int] = mapped_column(ForeignKey("stage2.participant.participant_id", ondelete="CASCADE"))
    survival_status: Mapped[SurvivalStatus]
    overall_survival: Mapped[NonNegativeInt]
    abscopal_response: Mapped[YNUNA | None]
    pathological_complete_response: Mapped[YNUNA | None]
    days_to_death: Mapped[NonNegativeInt | None]
    cause_of_death: Mapped[CauseOfDeath | None]
    evaluable_for_toxicity: Mapped[YN]
    evaluable_for_efficacy: Mapped[YN]
    days_to_last_vital_status: Mapped[NonNegativeInt | None]

    participant: Mapped[ParticipantORM] = relationship(back_populates="response", cascade="all, delete")
