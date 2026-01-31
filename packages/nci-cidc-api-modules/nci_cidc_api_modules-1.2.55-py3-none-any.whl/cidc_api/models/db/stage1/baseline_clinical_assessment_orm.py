from __future__ import annotations
from sqlalchemy import ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cidc_api.models.db.stage1.base_orm import BaseORM
from cidc_api.models.db.stage1.trial_orm import TrialORM
from cidc_api.models.types import ECOGScore, KarnofskyScore


class BaselineClinicalAssessmentORM(BaseORM):
    __tablename__ = "baseline_clinical_assessment"
    __repr_attrs__ = ["baseline_clinical_assessment_id", "participant_id"]
    __data_category__ = "baseline_clinical_assessment"
    __table_args__ = (
        ForeignKeyConstraint(["trial_id", "version"], [TrialORM.trial_id, TrialORM.version], ondelete="CASCADE"),
    )

    trial_id: Mapped[str]
    version: Mapped[str]

    baseline_clinical_assessment_id: Mapped[int] = mapped_column(primary_key=True)
    participant_id: Mapped[int] = mapped_column(ForeignKey("stage1.participant.participant_id", ondelete="CASCADE"))

    ecog_score: Mapped[ECOGScore | None]
    karnofsky_score: Mapped[KarnofskyScore | None]

    participant: Mapped[ParticipantORM] = relationship(
        back_populates="baseline_clinical_assessment", cascade="all, delete"
    )
