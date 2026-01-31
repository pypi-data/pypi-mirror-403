from pydantic import NonNegativeInt
from cidc_api.models.pydantic.base import Base


class AdditionalTreatment(Base):
    __data_category__ = "additional_treatment"
    __cardinality__ = "many"

    # The unique internal identifier for the AdditionalTreatment record
    additional_treatment_id: int | None = None

    # The unique internal identifier for the associated Participant record
    participant_id: str | None = None

    # Number of days from the enrollment date to the first recorded administration or occurrence of the treatment modality.
    additional_treatment_days_to_start: NonNegativeInt | None = None

    # Number of days from the enrollment date to the last recorded administration or occurrence of the treatment modality.
    additional_treatment_days_to_end: NonNegativeInt | None = None

    # Description of the prior treatment such as its full generic name if it is a type of therapy agent, radiotherapy procedure
    # name and location, or surgical procedure name and location.
    additional_treatment_description: str
