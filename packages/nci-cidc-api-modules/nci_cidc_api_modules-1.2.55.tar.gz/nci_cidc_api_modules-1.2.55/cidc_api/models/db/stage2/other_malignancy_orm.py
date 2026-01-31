from __future__ import annotations
from pydantic import NonPositiveInt
from sqlalchemy import ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cidc_api.models.db.stage2.base_orm import BaseORM
from cidc_api.models.db.stage2.trial_orm import TrialORM
from cidc_api.models.types import UberonAnatomicalTerm, ICDO3MorphologicalCode, ICDO3MorphologicalTerm, MalignancyStatus


class OtherMalignancyORM(BaseORM):
    __tablename__ = "other_malignancy"
    __repr_attrs__ = ["other_malignancy_id", "primary_disease_site"]
    __data_category__ = "other_malignancy"
    __table_args__ = (
        ForeignKeyConstraint(["trial_id", "version"], [TrialORM.trial_id, TrialORM.version], ondelete="CASCADE"),
    )

    trial_id: Mapped[str]
    version: Mapped[str]

    other_malignancy_id: Mapped[int] = mapped_column(primary_key=True)
    medical_history_id: Mapped[int] = mapped_column(
        ForeignKey("stage2.medical_history.medical_history_id", ondelete="CASCADE")
    )

    other_malignancy_primary_disease_site: Mapped[UberonAnatomicalTerm]
    other_malignancy_morphological_code: Mapped[ICDO3MorphologicalCode | None]
    other_malignancy_morphological_term: Mapped[ICDO3MorphologicalTerm | None]
    other_malignancy_description: Mapped[str | None]
    other_malignancy_days_since_diagnosis: Mapped[NonPositiveInt | None]
    other_malignancy_status: Mapped[MalignancyStatus | None]

    medical_history: Mapped[MedicalHistoryORM] = relationship(
        back_populates="other_malignancies", cascade="all, delete"
    )
