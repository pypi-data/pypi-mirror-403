from __future__ import annotations
from pydantic import NonNegativeInt, NonNegativeFloat, PositiveFloat

from sqlalchemy import ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cidc_api.models.db.stage1.base_orm import BaseORM
from cidc_api.models.db.stage1.trial_orm import TrialORM
from cidc_api.models.types import (
    RadiotherapyProcedure,
    UberonAnatomicalTerm,
    RadiotherapyDoseUnits,
    RadiationExtent,
    YN,
    YNU,
)


class RadiotherapyDoseORM(BaseORM):
    __tablename__ = "radiotherapy_dose"
    __repr_attrs__ = ["radiotherapy_dose_id", "procedure"]
    __data_category__ = "radiotherapy_dose"
    __table_args__ = (
        ForeignKeyConstraint(["trial_id", "version"], [TrialORM.trial_id, TrialORM.version], ondelete="CASCADE"),
    )

    trial_id: Mapped[str]
    version: Mapped[str]

    radiotherapy_dose_id: Mapped[int] = mapped_column(primary_key=True)
    treatment_id: Mapped[int] = mapped_column(ForeignKey("stage1.treatment.treatment_id", ondelete="CASCADE"))

    days_to_start: Mapped[NonNegativeInt]
    days_to_end: Mapped[NonNegativeInt]
    procedure: Mapped[RadiotherapyProcedure]
    anatomical_location: Mapped[UberonAnatomicalTerm | None]
    is_total_dose: Mapped[YN]
    number_of_fractions: Mapped[NonNegativeInt | None]
    received_dose: Mapped[NonNegativeFloat]
    received_dose_units: Mapped[RadiotherapyDoseUnits]
    planned_dose: Mapped[PositiveFloat | None]
    planned_dose_units: Mapped[RadiotherapyDoseUnits | None]
    dose_changes_delays: Mapped[YNU]
    changes_delays_description: Mapped[str | None]
    radiation_extent: Mapped[RadiationExtent]

    treatment: Mapped[TreatmentORM] = relationship(back_populates="radiotherapy_doses", cascade="all, delete")
