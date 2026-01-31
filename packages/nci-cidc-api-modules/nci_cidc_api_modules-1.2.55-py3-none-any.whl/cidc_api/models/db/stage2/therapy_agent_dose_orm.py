from __future__ import annotations
from pydantic import NonNegativeInt, NonNegativeFloat, PositiveFloat

from sqlalchemy import ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cidc_api.models.db.stage2.base_orm import BaseORM
from cidc_api.models.db.stage2.trial_orm import TrialORM
from cidc_api.models.types import TherapyAgentDoseUnits, YNU


class TherapyAgentDoseORM(BaseORM):
    __tablename__ = "therapy_agent_dose"
    __repr_attrs__ = ["therapy_agent_dose_id", "therapy_agent_name"]
    __data_category__ = "therapy_agent_dose"
    __table_args__ = (
        ForeignKeyConstraint(["trial_id", "version"], [TrialORM.trial_id, TrialORM.version], ondelete="CASCADE"),
    )

    trial_id: Mapped[str]
    version: Mapped[str]

    therapy_agent_dose_id: Mapped[int] = mapped_column(primary_key=True)
    treatment_id: Mapped[int] = mapped_column(ForeignKey("stage2.treatment.treatment_id", ondelete="CASCADE"))

    course_number: Mapped[str | None]
    therapy_agent_name: Mapped[str]
    days_to_start: Mapped[NonNegativeInt]
    days_to_end: Mapped[NonNegativeInt]
    number_of_doses: Mapped[NonNegativeInt]
    received_dose: Mapped[NonNegativeFloat]
    received_dose_units: Mapped[TherapyAgentDoseUnits]
    planned_dose: Mapped[PositiveFloat | None]
    planned_dose_units: Mapped[TherapyAgentDoseUnits | None]
    dose_changes_delays: Mapped[YNU]
    changes_delays_description: Mapped[str | None]

    treatment: Mapped[TreatmentORM] = relationship(back_populates="therapy_agent_doses", cascade="all, delete")
