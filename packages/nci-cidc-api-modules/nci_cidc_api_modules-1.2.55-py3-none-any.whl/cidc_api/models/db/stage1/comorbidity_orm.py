from __future__ import annotations
from sqlalchemy import ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cidc_api.models.db.stage1.base_orm import BaseORM
from cidc_api.models.db.stage1.trial_orm import TrialORM
from cidc_api.models.types import ICD10CMCode, ICD10CMTerm


class ComorbidityORM(BaseORM):
    __tablename__ = "comorbidity"
    __repr_attrs__ = ["comorbidity_id", "comorbidity_term"]
    __data_category__ = "comorbidity"
    __table_args__ = (
        ForeignKeyConstraint(["trial_id", "version"], [TrialORM.trial_id, TrialORM.version], ondelete="CASCADE"),
    )

    trial_id: Mapped[str]
    version: Mapped[str]

    comorbidity_id: Mapped[int] = mapped_column(primary_key=True)
    medical_history_id: Mapped[int] = mapped_column(
        ForeignKey("stage1.medical_history.medical_history_id", ondelete="CASCADE")
    )

    comorbidity_code: Mapped[ICD10CMCode | None]
    comorbidity_term: Mapped[ICD10CMTerm | None]
    comorbidity_other: Mapped[str | None]

    medical_history: Mapped[MedicalHistoryORM] = relationship(back_populates="comorbidities", cascade="all, delete")
