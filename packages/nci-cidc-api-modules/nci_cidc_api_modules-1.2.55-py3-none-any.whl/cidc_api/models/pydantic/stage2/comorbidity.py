from typing import Any

from cidc_api.models.pydantic.base import forced_validator, forced_validators

from cidc_api.models.errors import ValueLocError
from cidc_api.models.pydantic.base import Base
from cidc_api.models.types import ICD10CMCode, ICD10CMTerm


@forced_validators
class Comorbidity(Base):
    __data_category__ = "comorbidity"
    __cardinality__ = "many"

    # The unique internal identifier for the comorbidity record
    comorbidity_id: int | None = None

    # The unique internal identifier for the associated MedicalHistory record
    medical_history_id: int | None = None

    # The diagnosis, in humans, as captured in the tenth version of the
    # International Classification of Disease (ICD-10-CM, the disease code subset of ICD-10).
    comorbidity_code: ICD10CMCode | None = None

    # The words from the tenth version of the International Classification of Disease (ICD-10-CM,
    # the disease subset of ICD-10) used to identify the diagnosis in humans.
    comorbidity_term: ICD10CMTerm | None = None

    # A descriptive string that names or briefly describes the comorbidity.
    comorbidity_other: str | None = None

    @forced_validator
    @classmethod
    def validate_code_or_term_or_other_cr(cls, data, info) -> None:
        comorbidity_term = data.get("comorbidity_term", None)
        comorbidity_other = data.get("comorbidity_other", None)
        comorbidity_code = data.get("comorbidity_code", None)

        if not comorbidity_code and not comorbidity_term and not comorbidity_other:
            raise ValueLocError(
                'Please provide at least one of "comorbidity_code", "comorbidity_term" or "comorbidity_other".',
                loc="comorbidity_code,comorbidity_term,comorbidity_other",
            )
