from pydantic import NonNegativeInt
from cidc_api.models.pydantic.base import forced_validator, forced_validators

from cidc_api.models.errors import ValueLocError
from cidc_api.models.pydantic.base import Base
from cidc_api.models.types import SurvivalStatus, YNUNA, YN, CauseOfDeath


@forced_validators
class Response(Base):
    __data_category__ = "response"
    __cardinality__ = "one"

    # The unique internal identifier for the response record
    response_id: int | None = None

    # The unique internal identifier for the associated participant
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=12220014%20and%20ver_nr=1
    participant_id: str | None = None

    # The response to a question that describes a participant's survival status.
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=2847330%20and%20ver_nr=1
    survival_status: SurvivalStatus

    # Number of days from enrollment date to death date.
    overall_survival: NonNegativeInt

    # Indicator for whether there was an abscopal effect on disease after local therapy.
    abscopal_response: YNUNA | None = None

    # Indicates if pathological complete response (pCR) occurred.
    pathological_complete_response: YNUNA | None = None

    # Number of days between enrollment date and date of death, if applicable.
    days_to_death: NonNegativeInt | None = None

    # The circumstance or condition of greatest rank or importance that results in the death of the participant
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=4783274%20and%20ver_nr=1
    cause_of_death: CauseOfDeath | None = None

    # Indicates whether participant was evaluable for toxicity (adverse events, DLT, etc.) overall.
    evaluable_for_toxicity: YN

    # Indicates whether participant was evaluable for efficacy (for example, response, PFS, OS, etc.) overall.
    evaluable_for_efficacy: YN

    # Days from enrollment date to the last time the patient's vital status was verified.
    days_to_last_vital_status: NonNegativeInt | None = None

    @forced_validator
    @classmethod
    def validate_cause_of_death_cr(cls, data, info) -> None:
        survival_status = data.get("survival_status", None)
        cause_of_death = data.get("cause_of_death", None)

        if survival_status == "Dead" and not cause_of_death:
            raise ValueLocError(
                'If survival_status is "Dead" then cause_of_death is required.',
                loc="cause_of_death",
            )

    @forced_validator
    @classmethod
    def validate_cause_of_death_cr2(cls, data, info) -> None:
        survival_status = data.get("survival_status", None)
        cause_of_death = data.get("cause_of_death", None)

        if survival_status == "Alive" and cause_of_death:
            raise ValueLocError(
                'If survival_status is "Alive", please leave cause_of_death blank.',
                loc="cause_of_death",
            )

    @forced_validator
    @classmethod
    def validate_days_to_death_cr(cls, data, info) -> None:
        survival_status = data.get("survival_status", None)
        days_to_death = data.get("days_to_death", None)

        if survival_status in ["Alive", "Unknown"] and days_to_death:
            raise ValueLocError(
                "If survival_status does not indicate death, please leave days_to_death blank.",
                loc="days_to_death",
            )
