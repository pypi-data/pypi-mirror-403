from __future__ import annotations
from typing import List

from sqlalchemy import ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cidc_api.models.db.stage2.base_orm import BaseORM
from cidc_api.models.db.stage2.trial_orm import TrialORM
from cidc_api.models.types import YNU, ExposureType


class ExposureORM(BaseORM):
    __tablename__ = "exposure"
    __repr_attrs__ = ["exposure_id", "exposure_type", "carcinogen_exposure"]
    __data_category__ = "exposure"
    __table_args__ = (
        ForeignKeyConstraint(["trial_id", "version"], [TrialORM.trial_id, TrialORM.version], ondelete="CASCADE"),
    )

    trial_id: Mapped[str]
    version: Mapped[str]

    exposure_id: Mapped[int] = mapped_column(primary_key=True)
    participant_id: Mapped[int] = mapped_column(ForeignKey("stage2.participant.participant_id", ondelete="CASCADE"))

    carcinogen_exposure: Mapped[YNU]
    exposure_type: Mapped[ExposureType | None]

    participant: Mapped[ParticipantORM] = relationship(back_populates="exposures", cascade="all, delete")
