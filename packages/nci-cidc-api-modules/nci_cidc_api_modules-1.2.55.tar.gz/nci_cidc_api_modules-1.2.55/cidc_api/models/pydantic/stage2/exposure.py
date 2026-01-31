from cidc_api.models.pydantic.base import forced_validator, forced_validators

from cidc_api.models.errors import ValueLocError
from cidc_api.models.pydantic.base import Base
from cidc_api.models.types import YNU, ExposureType


@forced_validators
class Exposure(Base):
    __data_category__ = "exposure"
    __cardinality__ = "many"

    # A unique internal identifier for the exposure
    exposure_id: int | None = None

    # The unique identifier for the associated participant
    participant_id: str | None = None

    # An indication of whether the subject was exposed to any chemical, biological or physical agents
    # that increase the risk of neoplasms in humans or animals.
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=5205578%20and%20ver_nr=3
    carcinogen_exposure: YNU

    # The type of potentially harmful environmental agents to which an individual was exposed.
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=15753203%20and%20ver_nr=1
    exposure_type: ExposureType | None = None

    @forced_validator
    @classmethod
    def validate_exposure_type_cr(cls, data, info) -> None:
        carcinogen_exposure = data.get("carcinogen_exposure", None)
        exposure_type = data.get("exposure_type", None)

        if carcinogen_exposure in ["No", "Unknown"] and exposure_type:
            raise ValueLocError(
                "If carcinogen_exposure indicates non exposure, please leave exposure_type blank.",
                loc="exposure_type",
            )
