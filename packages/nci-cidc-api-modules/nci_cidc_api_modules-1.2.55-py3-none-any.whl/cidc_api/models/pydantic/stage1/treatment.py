from cidc_api.models.pydantic.base import forced_validator, forced_validators

from cidc_api.models.errors import ValueLocError
from cidc_api.models.pydantic.base import Base
from cidc_api.models.types import YNU, OffTreatmentReason


@forced_validators
class Treatment(Base):
    __data_category__ = "treatment"
    __cardinality__ = "many"

    # The unique internal identifier for the Treatment record
    treatment_id: int | None = None

    # The unique internal identifier for the associated Participant record
    participant_id: str | None = None

    # The unique internal identifier for the associated Arm record
    arm: str | None = None

    # The unique internal identifier for the associated Cohort record
    cohort: str | None = None

    # A unique identifier used to describe a distinct, specific intervention or
    # treatment that a group or subgroup of participants in a clinical trial receives.
    treatment_description: str

    # Indicates if the participant has stopped receiving this particular treatment at
    # the time of data submission.
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=16391087%20and%20ver_nr=1
    off_treatment: YNU

    # An explanation describing why an individual is no longer receiving this particular treatment.
    off_treatment_reason: OffTreatmentReason | None = None

    # If "Other" is selected for "off_treatment_reason", provide a description of the reason.
    off_treatment_reason_other: str | None = None

    @forced_validator
    @classmethod
    def validate_off_treatment_reason_cr(cls, data, info) -> None:
        off_treatment = data.get("off_treatment", None)
        off_treatment_reason = data.get("off_treatment_reason", None)

        if off_treatment == "Yes" and not off_treatment_reason:
            raise ValueLocError(
                'If off_treatment is "Yes", please provide off_treatment_reason.',
                loc="off_treatment_reason",
            )
        return off_treatment_reason

    @forced_validator
    @classmethod
    def validate_off_treatment_reason_other_cr(cls, data, info) -> None:
        off_treatment_reason = data.get("off_treatment_reason", None)
        off_treatment_reason_other = data.get("off_treatment_reason_other", None)

        if off_treatment_reason == "Other" and not off_treatment_reason_other:
            raise ValueLocError(
                'If off_treatment_reason is "Other", please provide off_treatment_reason_other.',
                loc="off_treatment_reason_other",
            )
        return off_treatment_reason_other
