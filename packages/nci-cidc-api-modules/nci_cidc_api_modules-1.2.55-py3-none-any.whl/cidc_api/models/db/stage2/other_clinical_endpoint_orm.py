from __future__ import annotations
from sqlalchemy import String, ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cidc_api.models.db.stage2.base_orm import BaseORM
from cidc_api.models.db.stage2.trial_orm import TrialORM
from cidc_api.models.types import YNU, ResponseSystem, ResponseSystemVersion


class OtherClinicalEndpointORM(BaseORM):
    __tablename__ = "other_clinical_endpoint"
    __repr_attrs__ = ["other_clinical_endpoint_id", "name", "event"]
    __data_category__ = "other_clinical_endpoint"
    __table_args__ = (
        ForeignKeyConstraint(["trial_id", "version"], [TrialORM.trial_id, TrialORM.version], ondelete="CASCADE"),
    )

    trial_id: Mapped[str]
    version: Mapped[str]

    other_clinical_endpoint_id: Mapped[int] = mapped_column(primary_key=True)
    participant_id: Mapped[int] = mapped_column(ForeignKey("stage2.participant.participant_id", ondelete="CASCADE"))

    name: Mapped[str]
    event: Mapped[YNU]
    days: Mapped[int | None]
    description: Mapped[str | None]
    calculation: Mapped[str | None]
    response_system: Mapped[ResponseSystem | None] = mapped_column(String, nullable=True)
    response_system_version: Mapped[ResponseSystemVersion | None] = mapped_column(String, nullable=True)

    participant: Mapped[ParticipantORM] = relationship(back_populates="other_clinical_endpoints", cascade="all, delete")
