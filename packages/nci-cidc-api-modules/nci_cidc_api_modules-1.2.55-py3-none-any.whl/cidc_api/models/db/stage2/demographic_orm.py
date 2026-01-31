from __future__ import annotations
from pydantic import NonNegativeFloat, PositiveFloat, PositiveInt
from typing import List

from sqlalchemy import ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from cidc_api.models.db.stage2.base_orm import BaseORM
from cidc_api.models.db.stage2.trial_orm import TrialORM
from cidc_api.models.types import (
    Sex,
    Race,
    Ethnicity,
    HeightUnits,
    WeightUnits,
    BodySurfaceAreaUnits,
    Occupation,
    Education,
    AgeAtEnrollmentUnits,
    YN,
)


class DemographicORM(BaseORM):
    __tablename__ = "demographic"
    __repr_attrs__ = ["demographic_id", "participant_id", "age_at_enrollment", "sex"]
    __data_category__ = "demographic"
    __table_args__ = (
        ForeignKeyConstraint(["trial_id", "version"], [TrialORM.trial_id, TrialORM.version], ondelete="CASCADE"),
    )

    trial_id: Mapped[str]
    version: Mapped[str]

    demographic_id: Mapped[int] = mapped_column(primary_key=True)
    participant_id: Mapped[int] = mapped_column(ForeignKey("stage2.participant.participant_id", ondelete="CASCADE"))
    age_at_enrollment: Mapped[PositiveInt | None]
    age_at_enrollment_units: Mapped[AgeAtEnrollmentUnits | None]
    age_90_or_over: Mapped[YN]
    sex: Mapped[Sex]
    race: Mapped[List[Race]] = mapped_column(JSON)
    ethnicity: Mapped[Ethnicity]
    height: Mapped[PositiveFloat]
    height_units: Mapped[HeightUnits]
    weight: Mapped[PositiveFloat]
    weight_units: Mapped[WeightUnits]
    body_mass_index: Mapped[PositiveFloat | None]
    body_surface_area: Mapped[PositiveFloat | None]
    body_surface_area_units: Mapped[BodySurfaceAreaUnits | None]
    occupation: Mapped[Occupation | None]
    income: Mapped[NonNegativeFloat | None]
    highest_level_of_education: Mapped[Education | None]

    participant: Mapped[ParticipantORM] = relationship(back_populates="demographic", cascade="all, delete")
