from __future__ import annotations
from pydantic import PositiveInt
from sqlalchemy import String, ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cidc_api.models.db.stage1.base_orm import BaseORM
from cidc_api.models.db.stage1.trial_orm import TrialORM
from cidc_api.models.types import ResponseSystem, ResponseSystemVersion, BestOverallResponse, YNUNA, YN


class ResponseBySystemORM(BaseORM):
    __tablename__ = "response_by_system"
    __repr_attrs__ = ["response_by_system_id", "participant_id"]
    __data_category__ = "response_by_system"
    __table_args__ = (
        ForeignKeyConstraint(["trial_id", "version"], [TrialORM.trial_id, TrialORM.version], ondelete="CASCADE"),
    )

    trial_id: Mapped[str]
    version: Mapped[str]

    response_by_system_id: Mapped[int] = mapped_column(primary_key=True)
    participant_id: Mapped[int] = mapped_column(ForeignKey("stage1.participant.participant_id", ondelete="CASCADE"))
    response_system: Mapped[ResponseSystem] = mapped_column(String)
    response_system_version: Mapped[ResponseSystemVersion] = mapped_column(String)
    best_overall_response: Mapped[BestOverallResponse] = mapped_column(String)
    response_duration: Mapped[PositiveInt | None]
    duration_of_stable_disease: Mapped[PositiveInt | None]
    durable_clinical_benefit: Mapped[YN | None]
    days_to_first_response: Mapped[PositiveInt | None]
    days_to_best_response: Mapped[PositiveInt | None]
    progression: Mapped[YNUNA]
    days_to_disease_progression: Mapped[PositiveInt | None]
    progression_free_survival_event: Mapped[YNUNA]
    progression_free_survival: Mapped[PositiveInt | None]

    participant: Mapped[ParticipantORM] = relationship(back_populates="response_by_systems", cascade="all, delete")
