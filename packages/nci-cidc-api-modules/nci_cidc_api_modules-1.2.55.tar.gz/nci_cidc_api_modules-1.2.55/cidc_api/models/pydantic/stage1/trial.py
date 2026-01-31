from datetime import datetime
from pydantic import BeforeValidator
from typing import List, Annotated

from cidc_api.models.pydantic.base import Base
from cidc_api.models.types import TrialOrganization, TrialFundingAgency, AssayType, AgeGroup, PrimaryPurposeType


class Trial(Base):
    __data_category__ = "study"
    __cardinality__ = None

    # The unique identifier for the clinical trial. e.g. "GU16-287","BACCI"
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=5054234%20and%20ver_nr=1
    trial_id: str | None = None

    # The version number of the trial dataset. e.g. "1.0"
    version: str | None = None

    # A broad textual description of the primary endpoint(s) of the trial.
    primary_endpoint: str | None = None

    # The identifiable class of the study participant based upon their age.
    age_group: Annotated[List[AgeGroup], BeforeValidator(Base.split_list)]

    # Clinical and/or molecular characteristics of the cancer(s) in the study population.
    study_population: str | None = None

    # The type of clinical trial conducted
    trial_type: str | None = None

    # The official day that study activity began
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=16333702%20and%20ver_nr=1
    dates_of_conduct_start: datetime

    # The official day that study activity ended
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=16333703%20and%20ver_nr=1
    dates_of_conduct_end: datetime | None = None

    # A classification of the study based upon the primary intent of the study's activities.
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=11160683%20and%20ver_nr=1
    primary_purpose_type: PrimaryPurposeType

    # The dbgap study accession number associated with the trial.
    dbgap_study_accession: str
