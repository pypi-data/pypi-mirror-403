from __future__ import annotations
from typing import List
from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from cidc_api.models.db.stage1.base_orm import BaseORM
from cidc_api.models.types import AssayType, TrialOrganization, TrialFundingAgency, AgeGroup, PrimaryPurposeType


class TrialORM(BaseORM):
    __tablename__ = "trial"
    __repr_attrs__ = ["trial_id", "version"]
    __data_category__ = "study"

    trial_id: Mapped[str] = mapped_column(primary_key=True)
    version: Mapped[str] = mapped_column(primary_key=True)

    primary_endpoint: Mapped[str | None]
    age_group: Mapped[List[AgeGroup]] = mapped_column(JSON, nullable=True)
    study_population: Mapped[str | None]
    trial_type: Mapped[str | None]
    dates_of_conduct_start: Mapped[datetime]
    dates_of_conduct_end: Mapped[datetime | None]
    primary_purpose_type: Mapped[PrimaryPurposeType]
    dbgap_study_accession: Mapped[str]

    participants: Mapped[List[ParticipantORM]] = relationship(
        back_populates="trial", cascade="all, delete", passive_deletes=True
    )
    consent_groups: Mapped[List[ConsentGroupORM]] = relationship(
        back_populates="trial", cascade="all, delete", passive_deletes=True
    )
