from pydantic import NonPositiveInt
from cidc_api.models.pydantic.base import forced_validator, forced_validators

from cidc_api.models.errors import ValueLocError
from cidc_api.models.pydantic.base import Base
from cidc_api.models.types import UberonAnatomicalTerm, ICDO3MorphologicalCode, ICDO3MorphologicalTerm, MalignancyStatus


@forced_validators
class OtherMalignancy(Base):
    __data_category__ = "other_malignancy"
    __cardinality__ = "many"

    # The unique internal identifier for the OtherMalignancy record
    other_malignancy_id: int | None = None

    # The unique internal identifier for the associated MedicalHistory record
    medical_history_id: int | None = None

    # The location within the body from where the prior malignancy originated as captured in the Uberon anatomical term.
    other_malignancy_primary_disease_site: UberonAnatomicalTerm

    # The ICD-O-3 code which identifies the specific appearance of cells and tissues (normal and abnormal) used
    # to define the presence and nature of disease.
    other_malignancy_morphological_code: ICDO3MorphologicalCode | None = None

    # The ICD-O-3 textual label which identifies the specific appearance of cells and tissues (normal and abnormal) used
    # to define the presence and nature of disease.
    other_malignancy_morphological_term: ICDO3MorphologicalTerm | None = None

    # Description of the cancer type as recorded in the trial.
    other_malignancy_description: str | None = None

    # Number of days since original diagnosis from the enrollment date. This may be a negative number.
    other_malignancy_days_since_diagnosis: NonPositiveInt | None = None

    # Indicates the participant’s current clinical state regarding the cancer diagnosis.
    other_malignancy_status: MalignancyStatus | None = None

    @forced_validator
    @classmethod
    def validate_code_or_term_or_description_cr(cls, data, info) -> None:
        other_malignancy_morphological_term = data.get("other_malignancy_morphological_term", None)
        other_malignancy_description = data.get("other_malignancy_description", None)
        other_malignancy_morphological_code = data.get("other_malignancy_morphological_code", None)

        if (
            not other_malignancy_morphological_code
            and not other_malignancy_morphological_term
            and not other_malignancy_description
        ):
            raise ValueLocError(
                'Please provide at least one of "morphological_code", "morphological_term" or "malignancy_description".',
                loc="other_malignancy_morphological_code",
            )
