from datetime import datetime

from cidc_api.models.pydantic.base import Base
from cidc_api.models.types import UberonAnatomicalTerm


class Specimen(Base):
    __data_category__ = "specimen"
    __cardinality__ = "many"

    # The unique internal identifier for the specimen record
    specimen_id: int | None = None

    # The unique internal identifier for the associated participant
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=12220014%20and%20ver_nr=1
    participant_id: str | None = None

    # The unique specimen identifier assigned by the CIMAC-CIDC Network.
    # Formatted as CTTTPPPSS.AA for trial code TTT, participant PPP, sample SS, and aliquot AA.
    cimac_id: str

    # Categorical description of timepoint at which the sample was taken.
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=5899851%20and%20ver_nr=1
    # Note: CIDC doesn't conform to this CDE's PVs
    collection_event_name: str

    # Days from enrollment date to date specimen was collected.
    days_to_specimen_collection: int

    # The location within the body from which a specimen was originally obtained as captured in the Uberon anatomical term.
    organ_site_of_collection: UberonAnatomicalTerm
