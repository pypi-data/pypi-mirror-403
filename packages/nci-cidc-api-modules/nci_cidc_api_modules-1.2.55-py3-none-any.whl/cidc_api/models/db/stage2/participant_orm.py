from __future__ import annotations
from typing import List

from sqlalchemy import ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cidc_api.models.db.stage2.base_orm import BaseORM
from cidc_api.models.db.stage2.trial_orm import TrialORM
from cidc_api.models.types import OffStudyReason, YNU


class ParticipantORM(BaseORM):
    __tablename__ = "participant"
    __repr_attrs__ = ["participant_id", "native_participant_id", "cimac_participant_id"]
    __data_category__ = "participant"
    __table_args__ = (
        ForeignKeyConstraint(["trial_id", "version"], [TrialORM.trial_id, TrialORM.version], ondelete="CASCADE"),
    )

    trial_id: Mapped[str]
    version: Mapped[str]

    participant_id: Mapped[int] = mapped_column(primary_key=True)
    native_participant_id: Mapped[str | None]
    cimac_participant_id: Mapped[str | None]
    consent_group_id: Mapped[int | None] = mapped_column(
        ForeignKey("stage2.consent_group.consent_group_id", ondelete="CASCADE")
    )
    off_study: Mapped[YNU]
    off_study_reason: Mapped[OffStudyReason | None]
    off_study_reason_other: Mapped[str | None]

    trial: Mapped[TrialORM] = relationship(back_populates="participants", cascade="all, delete")
    demographic: Mapped[DemographicORM] = relationship(
        back_populates="participant", cascade="all, delete", passive_deletes=True
    )
    prior_treatments: Mapped[List[PriorTreatmentORM]] = relationship(
        back_populates="participant", cascade="all, delete", passive_deletes=True
    )
    treatments: Mapped[List[TreatmentORM]] = relationship(
        back_populates="participant", cascade="all, delete", passive_deletes=True
    )
    diseases: Mapped[List[DiseaseORM]] = relationship(
        back_populates="participant", cascade="all, delete", passive_deletes=True
    )
    response_by_systems: Mapped[List[ResponseBySystemORM]] = relationship(
        back_populates="participant", cascade="all, delete", passive_deletes=True
    )
    response: Mapped[ResponseORM | None] = relationship(
        back_populates="participant", cascade="all, delete", passive_deletes=True
    )
    adverse_events: Mapped[List[AdverseEventORM]] = relationship(
        back_populates="participant", cascade="all, delete", passive_deletes=True
    )
    baseline_clinical_assessment: Mapped[BaselineClinicalAssessmentORM | None] = relationship(
        back_populates="participant", cascade="all, delete", passive_deletes=True
    )
    medical_history: Mapped[MedicalHistoryORM | None] = relationship(
        back_populates="participant", cascade="all, delete", passive_deletes=True
    )
    exposures: Mapped[List[ExposureORM]] = relationship(
        back_populates="participant", cascade="all, delete", passive_deletes=True
    )
    gvhd_diagnosis_acutes: Mapped[List[GVHDDiagnosisAcuteORM]] = relationship(
        back_populates="participant", cascade="all, delete", passive_deletes=True
    )
    gvhd_diagnosis_chronics: Mapped[List[GVHDDiagnosisChronicORM]] = relationship(
        back_populates="participant", cascade="all, delete", passive_deletes=True
    )
    specimens: Mapped[List[SpecimenORM]] = relationship(
        back_populates="participant", cascade="all, delete", passive_deletes=True
    )
    other_clinical_endpoints: Mapped[List[OtherClinicalEndpointORM]] = relationship(
        back_populates="participant", cascade="all, delete", passive_deletes=True
    )
    additional_treatments: Mapped[List[AdditionalTreatmentORM]] = relationship(
        back_populates="participant", cascade="all, delete", passive_deletes=True
    )
    consent_group: Mapped[ConsentGroupORM] = relationship(back_populates="participants", cascade="all, delete")
