from typing import Self

from pydantic import PositiveInt, NonNegativeInt, model_validator
from cidc_api.models.pydantic.base import forced_validator, forced_validators

from cidc_api.models.errors import ValueLocError
from cidc_api.models.pydantic.base import Base
from cidc_api.models.pydantic.stage1.response import Response
from cidc_api.models.types import ResponseSystem, ResponseSystemVersion, BestOverallResponse, YNUNA, YN


negative_response_values = [
    "Progressive Disease",
    "Stable Disease",
    "immune Unconfirmed Progressive Disease",
    "immune Confirmed Progressive Disease",
    "immune Stable Disease",
    "Not available",
    "Not assessed",
]


@forced_validators
class ResponseBySystem(Base):
    __data_category__ = "response_by_system"
    __cardinality__ = "many"

    # The unique internal identifier for this ResponseBySystem record
    response_by_system_id: int | None = None

    # The unique internal identifier for the associated participant
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=12220014%20and%20ver_nr=1
    participant_id: str | None = None

    # The linked parent response for the participant. Used for cross-model validation.
    response: Response | None = None

    # A standardized method used to evaluate and categorize the participant’s clinical response to treatment based on predefined criteria.
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=13381490%20and%20ver_nr=1
    response_system: ResponseSystem

    # The release version of the clinical assessment system used to evaluate a participant’s response to treatment.
    response_system_version: ResponseSystemVersion

    # Confirmed best overall response to study treatment by the corresponding response system.
    best_overall_response: BestOverallResponse

    # Days from first response to progression.
    response_duration: PositiveInt | None = None

    # The number of days from the start of the treatment to the first signs of disease progression.
    duration_of_stable_disease: NonNegativeInt | None = None

    # Indicates whether a patient achieved a durable clinical benefit.
    durable_clinical_benefit: YN | None = None

    # Number of days between enrollment date and the date of first response to trial treatment.
    days_to_first_response: PositiveInt | None = None

    # Number of days between enrollment date and the date of the best response to trial treatment.
    days_to_best_response: PositiveInt | None = None

    # Indicates whether a participant's disease progressed.
    progression: YNUNA

    # Number of days between enrollment date and date of disease progression.
    days_to_disease_progression: PositiveInt | None = None

    # Indicator to identify whether a patient had a Progression-Free Survival (PFS) event.
    progression_free_survival_event: YNUNA

    # The number of days from the date the patient was enrolled in the study to the date the patient was last verified to be free of progression.
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=5143957%20and%20ver_nr=1
    progression_free_survival: PositiveInt | None = None

    @forced_validator
    @classmethod
    def validate_response_duration_cr(cls, data, info) -> None:
        best_overall_response = data.get("best_overall_response", None)
        response_duration = data.get("response_duration", None)

        if best_overall_response in negative_response_values and response_duration:
            raise ValueLocError(
                "If best_overall_response does not indicate a positive response, "
                "please leave response_duration blank.",
                loc="response_duration",
            )

    @forced_validator
    @classmethod
    def validate_days_to_first_response_cr(cls, data, info) -> None:
        best_overall_response = data.get("best_overall_response", None)
        days_to_first_response = data.get("days_to_first_response", None)

        if best_overall_response in negative_response_values and days_to_first_response:
            raise ValueLocError(
                "If best_overall_response does not indicate a positive response, "
                "please leave days_to_first_response blank.",
                loc="days_to_first_response",
            )

    @forced_validator
    @classmethod
    def validate_days_to_best_response_cr(cls, data, info) -> None:
        best_overall_response = data.get("best_overall_response", None)
        days_to_best_response = data.get("days_to_best_response", None)

        if best_overall_response in negative_response_values and days_to_best_response:
            raise ValueLocError(
                "If best_overall_response does not indicate a positive response, "
                "please leave days_to_best_response blank.",
                loc="days_to_best_response",
            )

    @forced_validator
    @classmethod
    def validate_days_to_disease_progression_cr(cls, data, info) -> None:
        progression = data.get("progression", None)
        days_to_disease_progression = data.get("days_to_disease_progression", None)

        if progression in ["No", "Unknown", "Not Applicable"] and days_to_disease_progression:
            raise ValueLocError(
                "If progression does not indicate confirmed progression of the disease, "
                "please leave days_to_disease_progression blank.",
                loc="days_to_disease_progression",
            )

    @forced_validator
    @classmethod
    def validate_progression_free_survival_cr(cls, data, info) -> None:
        progression_free_survival_event = data.get("progression_free_survival_event", None)
        progression_free_survival = data.get("progression_free_survival", None)

        if progression_free_survival_event in ["Unknown", "Not Applicable"] and progression_free_survival:
            raise ValueLocError(
                "If progression_free_survival_event is not known, " "please leave progression_free_survival blank.",
                loc="progression_free_survival",
            )

    @forced_validator
    @classmethod
    def validate_days_to_best_response_chronology(cls, data, info) -> None:
        days_to_first_response = data.get("days_to_first_response", None)
        days_to_best_response = data.get("days_to_best_response", None)

        if days_to_best_response is not None and days_to_first_response is not None:
            if int(days_to_best_response) < int(days_to_first_response):
                raise ValueLocError(
                    'Violate "days_to_best_response" >= days_to_first_response"',
                    loc="days_to_best_response",
                )

    @forced_validator
    @classmethod
    def validate_days_to_disease_progression_chronology(cls, data, info) -> None:
        days_to_disease_progression = data.get("days_to_disease_progression", None)
        days_to_first_response = data.get("days_to_first_response", None)

        if days_to_first_response is not None and days_to_disease_progression is not None:
            if int(days_to_first_response) >= int(days_to_disease_progression):
                raise ValueLocError(
                    'Violate "days_to_first_response" < "days_to_disease_progression"',
                    loc="days_to_first_response",
                )

    @forced_validator
    @classmethod
    def validate_days_to_best_response_progression_chronology(cls, data, info) -> None:
        days_to_disease_progression = data.get("days_to_disease_progression", None)
        days_to_best_response = data.get("days_to_best_response", None)

        if days_to_best_response is not None and days_to_disease_progression is not None:
            if int(days_to_best_response) >= int(days_to_disease_progression):
                raise ValueLocError(
                    'Violate "days_to_best_response" < "days_to_disease_progression"',
                    loc="days_to_best_response",
                )

    @model_validator(mode="after")
    def validate_days_to_last_vital_status_chronology(self) -> Self:
        if not self.response:
            return self

        if not self.response.days_to_last_vital_status:
            return self

        max_value = max(
            self.response.days_to_last_vital_status or 0,
            self.days_to_first_response or 0,
            self.days_to_best_response or 0,
            self.days_to_disease_progression or 0,
        )
        if (self.response.days_to_last_vital_status or 0) != max_value:
            raise ValueLocError(
                '"days_to_last_vital_status" is not the max of all events. Rule: days_to_last_vital_status '
                ">= max(days_to_first_response,days_to_best_response,days_to_disease_progression)",
                loc="days_to_last_vital_status,days_to_first_response,days_to_best_response,days_to_disease_progression",
            )
        return self

    @model_validator(mode="after")
    def validate_days_to_death_chronology(self) -> Self:
        if not self.response:
            return self
        if not self.response.days_to_death:
            return self

        max_value = max(
            self.response.days_to_death or 0,
            self.days_to_first_response or 0,
            self.days_to_best_response or 0,
            self.days_to_disease_progression or 0,
        )
        if (self.response.days_to_death or 0) != max_value:
            raise ValueLocError(
                '"days_to_death" is not the max of all events. Rule: days_to_death'
                ">= max(days_to_first_response,days_to_best_response,days_to_disease_progression)",
                loc="days_to_death,days_to_first_response,days_to_best_response,days_to_disease_progression",
            )
        return self
