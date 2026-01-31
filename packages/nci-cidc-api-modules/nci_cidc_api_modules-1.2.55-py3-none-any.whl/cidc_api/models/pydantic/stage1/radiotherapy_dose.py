from pydantic import NonNegativeInt, NonNegativeFloat
from cidc_api.models.pydantic.base import forced_validator, forced_validators

from cidc_api.models.errors import ValueLocError
from cidc_api.models.pydantic.base import Base
from cidc_api.models.types import (
    YN,
    YNU,
    RadiotherapyProcedure,
    UberonAnatomicalTerm,
    RadiotherapyDoseUnits,
    RadiationExtent,
)


@forced_validators
class RadiotherapyDose(Base):
    __data_category__ = "radiotherapy_dose"
    __cardinality__ = "many"

    # The unique internal identifier for the radiotherapy dose record
    radiotherapy_dose_id: int | None = None

    # The unique internal identifier for the associated treatment record
    treatment_id: int | None = None

    # Number of days from enrollment date to the start of the radiotherapy dose.
    days_to_start: NonNegativeInt

    # Number of days from enrollment date to the end of the radiotherapy dose.
    days_to_end: NonNegativeInt

    # The term that describes the kind of radiotherapy procedure administered.
    procedure: RadiotherapyProcedure

    # The Uberon anatomical term for the site of surgery.
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=14461856%20and%20ver_nr=1
    anatomical_location: UberonAnatomicalTerm | None = None

    # Indicates whether the record represents the total dose for a radiotherapy treatment course (which may be either
    # a multi-fractionated or a single-fraction dose).
    is_total_dose: YN

    # The number of fractions a participant received to deliver the radiation dose.
    number_of_fractions: NonNegativeInt | None = None

    # The dose amount received by the participant.
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=13433490%20and%20ver_nr=1
    received_dose: NonNegativeFloat

    # Unit of measure for the dose of the radiotherapy to be received by the participant.
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=13383458%20and%20ver_nr=1
    received_dose_units: RadiotherapyDoseUnits

    # The planned dose amount for the participant.
    planned_dose: NonNegativeFloat | None = None

    # Unit of measure for the planned total dose of the radiotherapy to be received by the participant.
    planned_dose_units: RadiotherapyDoseUnits | None = None

    # Indicates if the radiotherapy dose was changed, missed, or delayed.
    dose_changes_delays: YNU

    # Description of the radiotherapy dose changes, misses, or delays.
    changes_delays_description: str | None = None

    # The extent of radiation exposure administered to the patient's body during radiation therapy.
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=7063755%20and%20ver_nr=1
    radiation_extent: RadiationExtent

    @forced_validator
    @classmethod
    def validate_changes_delays_description_cr(cls, data, info) -> None:
        dose_changes_delays = data.get("dose_changes_delays", None)
        changes_delays_description = data.get("changes_delays_description", None)

        if dose_changes_delays == "Yes" and not changes_delays_description:
            raise ValueLocError(
                'If dose_changes_delays is "Yes", please provide changes_delays_description.',
                loc="changes_delays_description",
            )

    @forced_validator
    @classmethod
    def validate_planned_dose_units_cr(cls, data, info) -> None:
        planned_dose = data.get("planned_dose", None)
        planned_dose_units = data.get("planned_dose_units", None)

        if planned_dose and not planned_dose_units:
            raise ValueLocError(
                "If planned_dose is provided, please provide planned_dose_units.",
                loc="planned_dose_units",
            )
