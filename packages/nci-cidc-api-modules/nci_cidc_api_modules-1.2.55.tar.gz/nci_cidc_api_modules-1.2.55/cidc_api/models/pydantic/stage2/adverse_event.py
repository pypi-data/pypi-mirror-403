from pydantic import NonNegativeInt

from cidc_api.models.pydantic.base import Base
from cidc_api.code_systems.ctcae import is_ctcae_other_term
from cidc_api.models.pydantic.base import forced_validator, forced_validators
from cidc_api.models.errors import ValueLocError
from cidc_api.models.types import (
    CTCAEEventTerm,
    CTCAEEventCode,
    SeverityGradeSystem,
    SeverityGradeSystemVersion,
    SeverityGrade,
    SystemOrganClass,
    AttributionCause,
    AttributionLikelihood,
    YN,
    YNU,
)


@forced_validators
class AdverseEvent(Base):
    __data_category__ = "adverse_event"
    __cardinality__ = "many"

    # The unique internal identifier of the adverse event
    adverse_event_id: int | None = None

    # The unique internal identifier of the associated participant
    participant_id: str | None = None

    # The unique internal identifier of the attributed treatment, if any
    treatment_id: int | None = None

    # Text that represents the Common Terminology Criteria for Adverse Events low level term name for an adverse event.
    event_term: CTCAEEventTerm | None = None

    # A MedDRA code mapped to a CTCAE low level name for an adverse event.
    event_code: CTCAEEventCode | None = None

    # System used to define and report adverse event severity grade.
    severity_grade_system: SeverityGradeSystem

    # The version of the adverse event grading system.
    severity_grade_system_version: SeverityGradeSystemVersion

    # Numerical grade indicating the severity of an adverse event.
    severity_grade: SeverityGrade

    # A brief description that sufficiently details the event.
    event_other_specify: str | None = None

    # The highest level of the MedDRA hierarchy, distinguished by anatomical or physiological system, etiology (disease origin) or purpose.
    system_organ_class: SystemOrganClass | None = None

    # Indicator to identify whether a participant exited the study prematurely due to the adverse event being described.
    discontinuation_due_to_event: YN

    # Days from enrollment date to date of onset of the adverse event.
    days_to_onset_of_event: NonNegativeInt

    # Days from enrollment date to date of resolution of the adverse event.
    days_to_resolution_of_event: NonNegativeInt | None = None

    # Indicates whether the adverse event was a serious adverse event (SAE).
    serious_adverse_event: YNU

    # Indicates whether the adverse event was a dose-limiting toxicity (DLT).
    dose_limiting_toxicity: YNU

    # Indicates if the adverse was attributable to the protocol as a whole or to an individual treatment.
    attribution_cause: AttributionCause

    # The code that indicates whether the adverse event is related to the treatment/intervention.
    attribution_likelihood: AttributionLikelihood

    # The individual therapy (therapy agent, radiotherapy, surgery, stem cell transplant) in the treatment that is attributed to the adverse event.
    individual_therapy: str | None = None

    @forced_validator
    @classmethod
    def validate_term_and_code_cr(cls, data, info) -> None:
        event_code = data.get("event_code", None)
        event_term = data.get("event_term", None)

        if not event_term and not event_code:
            raise ValueLocError(
                "Please provide event_term or event_code or both",
                loc="event_term,event_code",
            )

    @forced_validator
    @classmethod
    def validate_event_other_specify_cr(cls, data, info) -> None:
        event_other_specify = data.get("event_other_specify", None)
        severity_grade_system = data.get("severity_grade_system", None)
        event_term = data.get("event_term", None)

        if severity_grade_system == "CTCAE" and is_ctcae_other_term(event_term) and not event_other_specify:
            raise ValueLocError(
                'If severity_grade_system is "CTCAE" and the event_code or event_term are of type '
                '"Other, specify", please provide event_other_specify',
                loc="event_other_specify",
            )

    @forced_validator
    @classmethod
    def validate_system_organ_class_cr(cls, data, info) -> None:
        event_other_specify = data.get("event_other_specify", None)
        system_organ_class = data.get("system_organ_class", None)

        if event_other_specify and not system_organ_class:
            raise ValueLocError(
                "If event_other_specify is provided, please provide system_organ_class.", loc="system_organ_class"
            )

    @forced_validator
    @classmethod
    def validate_days_to_resolution_of_event_chronology(cls, data, info) -> None:
        days_to_onset_of_event = data.get("days_to_onset_of_event", None)
        days_to_resolution_of_event = data.get("days_to_resolution_of_event", None)

        if days_to_resolution_of_event is not None and days_to_onset_of_event is not None:
            if int(days_to_resolution_of_event) < int(days_to_onset_of_event):
                raise ValueLocError(
                    'Violate "days_to_onset_of_event" <= "days_to_resolution_of_event"',
                    loc="days_to_resolution_of_event",
                )
