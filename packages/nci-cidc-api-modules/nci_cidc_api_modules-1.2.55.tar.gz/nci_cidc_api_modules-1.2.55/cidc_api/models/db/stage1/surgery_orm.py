from __future__ import annotations
from pydantic import NonNegativeInt

from sqlalchemy import ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cidc_api.models.db.stage1.base_orm import BaseORM
from cidc_api.models.db.stage1.trial_orm import TrialORM
from cidc_api.models.types import SurgicalProcedure, UberonAnatomicalTerm, YNU


class SurgeryORM(BaseORM):
    __tablename__ = "surgery"
    __repr_attrs__ = ["surgery_id", "procedure"]
    __data_category__ = "surgery"
    __table_args__ = (
        ForeignKeyConstraint(["trial_id", "version"], [TrialORM.trial_id, TrialORM.version], ondelete="CASCADE"),
    )

    trial_id: Mapped[str]
    version: Mapped[str]

    surgery_id: Mapped[int] = mapped_column(primary_key=True)
    treatment_id: Mapped[int] = mapped_column(ForeignKey("stage1.treatment.treatment_id", ondelete="CASCADE"))

    procedure: Mapped[SurgicalProcedure]
    procedure_other: Mapped[str | None]
    days_to_procedure: Mapped[NonNegativeInt]
    anatomical_location: Mapped[UberonAnatomicalTerm]
    therapeutic: Mapped[YNU]
    findings: Mapped[str | None]
    extent_of_residual_disease: Mapped[str | None]

    treatment: Mapped[TreatmentORM] = relationship(back_populates="surgeries", cascade="all, delete")
