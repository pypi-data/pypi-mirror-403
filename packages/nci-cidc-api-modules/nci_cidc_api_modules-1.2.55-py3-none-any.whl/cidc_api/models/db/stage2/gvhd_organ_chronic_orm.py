from __future__ import annotations
from sqlalchemy import ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cidc_api.models.db.stage2.base_orm import BaseORM
from cidc_api.models.db.stage2.trial_orm import TrialORM
from cidc_api.models.types import GVHDOrgan, GVHDOrganChronicScore


class GVHDOrganChronicORM(BaseORM):
    __tablename__ = "gvhd_organ_chronic"
    __repr_attrs__ = ["gvhd_organ_chronic_id", "organ"]
    __data_category__ = "gvhd_organ_chronic"
    __table_args__ = (
        ForeignKeyConstraint(["trial_id", "version"], [TrialORM.trial_id, TrialORM.version], ondelete="CASCADE"),
    )

    trial_id: Mapped[str]
    version: Mapped[str]

    gvhd_organ_chronic_id: Mapped[int] = mapped_column(primary_key=True)
    gvhd_diagnosis_chronic_id: Mapped[int] = mapped_column(
        ForeignKey("stage2.gvhd_diagnosis_chronic.gvhd_diagnosis_chronic_id", ondelete="CASCADE")
    )
    organ: Mapped[GVHDOrgan]
    chronic_score: Mapped[GVHDOrganChronicScore]

    diagnosis: Mapped[GVHDDiagnosisChronicORM] = relationship(back_populates="organs", cascade="all, delete")
