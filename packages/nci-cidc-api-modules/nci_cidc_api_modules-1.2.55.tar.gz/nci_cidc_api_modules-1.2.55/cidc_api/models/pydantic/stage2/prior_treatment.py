from typing import Self, Annotated, List

from pydantic import NonPositiveInt, NegativeInt, model_validator, BeforeValidator

from cidc_api.models.pydantic.base import Base
from cidc_api.models.types import ConditioningRegimenType, StemCellDonorType


class PriorTreatment(Base):
    __data_category__ = "prior_treatment"
    __cardinality__ = "many"

    # A unique internal identifier for the prior treatment record
    prior_treatment_id: int | None = None

    # A unique internal identifier for the associated participant record
    participant_id: str | None = None

    # Number of days from the enrollment date to the first recorded administration or occurrence of
    # the treatment modality.
    prior_treatment_days_to_start: NonPositiveInt | None = None

    # Number of days from the enrollment date to the last recorded administration or occurrence of
    # the treatment modality.
    prior_treatment_days_to_end: NonPositiveInt | None = None

    # Specifies the category or kind of prior treatment modality a participant received.

    # Description of the prior treatment such as its full generic name if it is a type of therapy agent,
    # radiotherapy procedure name and location, or surgical procedure name and location.
    prior_treatment_description: str

    # Best response from any response assessment system to the prior treatment if available or applicable.
    prior_treatment_best_response: str | None = None

    # If the prior treatment is "Conditioning therapy" received before a stem cell transplant, specifies what
    # type of conditioning regimen used.
    prior_treatment_conditioning_regimen_type: ConditioningRegimenType | None = None

    # If prior treatment is "Stem cell transplant", indicates what stem cell donor type used.
    prior_treatment_stem_cell_donor_type: StemCellDonorType | None = None

    # If prior treatment is "Stem cell transplant", indicates the number of days from enrollment
    # to the prior transplant. This must be a negative number.
    prior_treatment_days_from_transplant_to_treatment_initiation: NegativeInt | None = None
