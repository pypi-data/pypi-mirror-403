from pydantic import NonPositiveInt, BeforeValidator
from cidc_api.models.pydantic.base import forced_validator, forced_validators

from typing import List, Self, Annotated, get_args, Any

from cidc_api.models.errors import ValueLocError
from cidc_api.models.pydantic.base import Base
from cidc_api.models.types import (
    TumorGrade,
    CancerStageSystem,
    CancerStageSystemVersion,
    CancerStageSystemVersionAJCC,
    CancerStageSystemVersionRISS,
    CancerStageSystemVersionFIGO,
    CancerStage,
    TCategory,
    NCategory,
    MCategory,
    UberonAnatomicalTerm,
    ICDO3MorphologicalCode,
    ICDO3MorphologicalTerm,
    YNU,
)


@forced_validators
class Disease(Base):
    __data_category__ = "disease"
    __cardinality__ = "many"

    # The unique internal identifier for this disease record
    disease_id: int | None = None

    # The unique internal identifier for the associated participant
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=12220014%20and%20ver_nr=1
    participant_id: str | None = None

    # The location within the body from where the disease of interest originated as captured in the Uberon identifier. e.g. "lung"
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=14883047%20and%20ver_nr=1
    primary_disease_site: UberonAnatomicalTerm

    # The ICD-O-3 morphology code that describes the tumor's histology, behavior, and grade-differentiation. e.g. "8480/6"
    # CDE: TBD
    morphological_code: ICDO3MorphologicalCode | None

    # The ICD-O-3 morphology term that describes the tumor's type. e.g. "Mucinous adenoma"
    # CDE: TBD
    morphological_term: ICDO3MorphologicalTerm | None

    # Words that broadly describe the cancer's characteristics and type. e.g. "Inflitrating Ductal Carcinoma"
    # CDE: TBD
    cancer_type_description: str | None = None

    # The number of days elapsed since the participant was first diagnosed with this condition.
    days_since_original_diagnosis: NonPositiveInt | None

    # Words that express the degree of abnormality of cancer cells as a measure of differentiation and aggressiveness. e.g. "G1 Low Grade"
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=11325685%20and%20ver_nr=2
    tumor_grade: TumorGrade | None = None

    # The name of the staging system used in the evaluation of the disease. e.g. "AJCC"
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=7429602%20and%20ver_nr=1
    cancer_stage_system: CancerStageSystem

    # Release version of the staging system used in the evaluation of the disease. e.g. "8" (for AJCC)
    cancer_stage_system_version: CancerStageSystemVersion | None = None

    # Stage of the cancer at enrollment date as determined by the specific staging system. e.g. "Stage 0" (for AJCC)
    # CDE(AJCC): https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=3440332%20and%20ver_nr=1
    # CDE(FIGO): TBD
    # CDE(RISS): TBD
    cancer_stage: CancerStage | None = None

    # Extent of the primary cancer based on evidence obtained from clinical assessment parameters determined prior to treatment. e.g. "T0"
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=3440328%20and%20ver_nr=1
    # TODO: Verify this CDE
    t_category: TCategory | None = None

    # Extent of the regional lymph node involvement for the cancer based on evidence obtained from clinical assessment parameters
    # determined prior to treatment. e.g. "N0"
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=3440330%20and%20ver_nr=1
    # TODO: Verify this CDE
    n_category: NCategory | None = None

    # Extent of the distant metastasis for the cancer based on evidence obtained from clinical assessment parameters determined
    # prior to treatment. e.g. "M0"
    # CDE: https://teams.microsoft.com/l/message/19:1c292b63-5df1-4f29-b177-86aed53f393d_f224ae83-209b-4cd9-a7ef-83d9d2120a27@unq.gbl.spaces/1758827414202?context=%7B%22contextType%22%3A%22chat%22%7D
    # TODO: Verify this CDE
    m_category: MCategory | None = None

    # The organ site where a tumor develops outside of the bone marrow as specified in the Uberon antatomical term.
    metastatic_organ: Annotated[List[UberonAnatomicalTerm] | None, BeforeValidator(Base.split_list)] = []

    # Indicates if participant has a hematological malignancy that is only extramedullary. e.g. "Yes"
    solely_extramedullary_disease: YNU

    extramedullary_organ: Annotated[List[UberonAnatomicalTerm] | None, BeforeValidator(Base.split_list)] = []

    @forced_validator
    @classmethod
    def validate_code_or_term_or_description_cr(cls, data, info) -> None:
        morphological_term = data.get("morphological_term", None)
        cancer_type_description = data.get("cancer_type_description", None)
        morphological_code = data.get("morphological_code", None)

        if not morphological_code and not morphological_term and not cancer_type_description:
            raise ValueLocError(
                'Please provide at least one of "morphological_code", "morphological_term" or "cancer_type_description".',
                loc="morphological_code",
            )

    @forced_validator
    @classmethod
    def validate_cancer_stage_system_version(cls, data, info) -> None:
        cancer_stage_system_version = data.get("cancer_stage_system_version", None)
        cancer_stage_system = data.get("cancer_stage_system", None)

        msg = f"{cancer_stage_system_version} is not applicable to {cancer_stage_system}"
        if cancer_stage_system == "AJCC" and cancer_stage_system_version not in get_args(CancerStageSystemVersionAJCC):
            raise ValueLocError(msg, loc="cancer_stage_system")
        elif cancer_stage_system == "RISS" and cancer_stage_system_version not in get_args(
            CancerStageSystemVersionRISS
        ):
            raise ValueLocError(msg, loc="cancer_stage_system")
        elif cancer_stage_system == "FIGO" and cancer_stage_system_version not in get_args(
            CancerStageSystemVersionFIGO
        ):
            raise ValueLocError(msg, loc="cancer_stage_system")

    @forced_validator
    @classmethod
    def validate_cancer_stage_system_version_cr(cls, data, info) -> None:
        cancer_stage_system = data.get("cancer_stage_system", None)
        cancer_stage_system_version = data.get("cancer_stage_system_version", None)

        if cancer_stage_system != "Not Applicable" and not cancer_stage_system_version:
            raise ValueLocError(
                f'Please provide cancer_stage_system_version when cancer_stage_system is "{cancer_stage_system}"',
                loc="cancer_stage_system_version",
            )

    @forced_validator
    @classmethod
    def validate_cancer_stage_cr(cls, data, info) -> None:
        cancer_stage_system = data.get("cancer_stage_system", None)
        cancer_stage = data.get("cancer_stage", None)

        if cancer_stage_system != "Not Applicable" and not cancer_stage:
            raise ValueLocError(
                f'Please provide cancer_stage when cancer_stage_system is "{cancer_stage_system}"',
                loc="cancer_stage",
            )

    @forced_validator
    @classmethod
    def validate_t_category_cr(cls, data, info) -> None:
        cancer_stage_system = data.get("cancer_stage_system", None)
        t_category = data.get("t_category", None)

        if cancer_stage_system == "AJCC" and not t_category:
            raise ValueLocError(
                f'Please provide t_category when cancer_stage_system is "{cancer_stage_system}"',
                loc="t_category",
            )

    @forced_validator
    @classmethod
    def validate_n_category_cr(cls, data, info) -> None:
        cancer_stage_system = data.get("cancer_stage_system", None)
        n_category = data.get("n_category", None)

        if cancer_stage_system == "AJCC" and not n_category:
            raise ValueLocError(
                f'Please provide n_category when cancer_stage_system is "{cancer_stage_system}"',
                loc="n_category",
            )

    @forced_validator
    @classmethod
    def validate_m_category_cr(cls, data, info) -> None:
        cancer_stage_system = data.get("cancer_stage_system", None)
        m_category = data.get("m_category", None)

        if cancer_stage_system == "AJCC" and not m_category:
            raise ValueLocError(
                f'Please provide m_category when cancer_stage_system is "{cancer_stage_system}"',
                loc="m_category",
            )

    @forced_validator
    @classmethod
    def validate_extramedullary_organ_cr(cls, data, info) -> None:
        solely_extramedullary_disease = data.get("solely_extramedullary_disease", None)
        extramedullary_organ = data.get("extramedullary_organ", None)

        if solely_extramedullary_disease in ["No", "Unknown"] and extramedullary_organ:
            raise ValueLocError(
                "If solely_extramedullary_disease indicates no disease, please leave extramedullary_organ blank.",
                loc="extramedullary_organ",
            )
