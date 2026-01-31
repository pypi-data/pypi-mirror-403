from __future__ import annotations
from typing import List

from sqlalchemy import ForeignKey, ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cidc_api.models.db.stage1.base_orm import BaseORM
from cidc_api.models.db.stage1.trial_orm import TrialORM
from cidc_api.models.types import (
    GVHDDiagnosisChronicAssessmentSystem,
    GVHDDiagnosisChronicAssessmentSystemVersion,
    GVHDDiagnosisChronicGlobalSeverity,
    PreOrPostEnrollment,
)


class GVHDDiagnosisChronicORM(BaseORM):
    __tablename__ = "gvhd_diagnosis_chronic"
    __repr_attrs__ = ["gvhd_diagnosis_chronic_id", "pre_or_post_enrollment"]
    __data_category__ = "gvhd_diagnosis_chronic"
    __table_args__ = (
        UniqueConstraint(
            "participant_id", "pre_or_post_enrollment", name="unique_ix_gvhd_diagnosis_chronic_pre_or_post"
        ),
        ForeignKeyConstraint(["trial_id", "version"], [TrialORM.trial_id, TrialORM.version], ondelete="CASCADE"),
    )

    trial_id: Mapped[str]
    version: Mapped[str]

    gvhd_diagnosis_chronic_id: Mapped[int] = mapped_column(primary_key=True)
    participant_id: Mapped[int] = mapped_column(ForeignKey("stage1.participant.participant_id", ondelete="CASCADE"))
    chronic_assessment_system: Mapped[GVHDDiagnosisChronicAssessmentSystem]
    system_version: Mapped[GVHDDiagnosisChronicAssessmentSystemVersion]
    chronic_global_severity: Mapped[GVHDDiagnosisChronicGlobalSeverity]
    pre_or_post_enrollment: Mapped[PreOrPostEnrollment]

    participant: Mapped[ParticipantORM] = relationship(back_populates="gvhd_diagnosis_chronics", cascade="all, delete")
    organs: Mapped[List[GVHDOrganChronicORM]] = relationship(
        back_populates="diagnosis", cascade="all, delete", passive_deletes=True
    )
