from pydantic import NonNegativeInt, PositiveFloat
from cidc_api.models.pydantic.base import forced_validator, forced_validators

from cidc_api.models.errors import ValueLocError
from cidc_api.models.pydantic.base import Base
from cidc_api.models.types import TobaccoSmokingStatus


@forced_validators
class MedicalHistory(Base):
    __data_category__ = "medical_history"
    __cardinality__ = "one"

    # A unique internal identifier for the medical history
    medical_history_id: int | None = None

    # The unique identifier for the associated participant
    participant_id: str | None = None

    # Text representation of a person's status relative to smoking tobacco in the form of cigarettes,
    # based on questions about current and former use of cigarettes.
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=16333929%20and%20ver_nr=1
    tobacco_smoking_status: TobaccoSmokingStatus | None = None

    # Average number of packs of cigarettes smoked per day multiplied by number of years the participant has smoked.
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=6841869%20and%20ver_nr=1
    pack_years_smoked: PositiveFloat | None = None

    # Number of prior systemic therapies.
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=16089302%20and%20ver_nr=1
    num_prior_systemic_therapies: NonNegativeInt | None = None

    @forced_validator
    @classmethod
    def validate_pack_years_smoked_cr(cls, data, info) -> None:
        tobacco_smoking_status = data.get("tobacco_smoking_status", None)
        pack_years_smoked = data.get("pack_years_smoked", None)

        if tobacco_smoking_status in ["Never Smoker", "Unknown", "Not reported"] and pack_years_smoked:
            raise ValueLocError(
                "If tobacco_smoking_status indicates non-smoker, please leave pack_years_smoked blank.",
                loc="pack_years_smoked",
            )
