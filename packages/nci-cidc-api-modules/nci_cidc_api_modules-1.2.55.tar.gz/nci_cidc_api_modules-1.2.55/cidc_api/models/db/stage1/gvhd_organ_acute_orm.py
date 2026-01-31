from __future__ import annotations
from sqlalchemy import ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cidc_api.models.db.stage1.base_orm import BaseORM
from cidc_api.models.db.stage1.trial_orm import TrialORM
from cidc_api.models.types import GVHDOrgan, GVHDOrganAcuteStage


class GVHDOrganAcuteORM(BaseORM):
    __tablename__ = "gvhd_organ_acute"
    __repr_attrs__ = ["gvhd_organ_acute_id", "organ"]
    __data_category__ = "gvhd_organ_acute"
    __table_args__ = (
        ForeignKeyConstraint(["trial_id", "version"], [TrialORM.trial_id, TrialORM.version], ondelete="CASCADE"),
    )

    trial_id: Mapped[str]
    version: Mapped[str]

    gvhd_organ_acute_id: Mapped[int] = mapped_column(primary_key=True)
    gvhd_diagnosis_acute_id: Mapped[int] = mapped_column(
        ForeignKey("stage1.gvhd_diagnosis_acute.gvhd_diagnosis_acute_id", ondelete="CASCADE")
    )
    organ: Mapped[GVHDOrgan]
    acute_stage: Mapped[GVHDOrganAcuteStage]

    diagnosis: Mapped[GVHDDiagnosisAcuteORM] = relationship(back_populates="organs", cascade="all, delete")
