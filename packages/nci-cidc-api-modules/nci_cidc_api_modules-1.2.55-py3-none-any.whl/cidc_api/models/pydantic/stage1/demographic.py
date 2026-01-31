from typing import Annotated, List

from pydantic import PositiveInt, NonNegativeFloat, PositiveFloat, BeforeValidator
from cidc_api.models.pydantic.base import forced_validator, forced_validators

from cidc_api.models.errors import ValueLocError
from cidc_api.models.pydantic.base import Base
from cidc_api.models.types import (
    Sex,
    Race,
    Ethnicity,
    HeightUnits,
    WeightUnits,
    BodySurfaceAreaUnits,
    Occupation,
    Education,
    AgeAtEnrollmentUnits,
    YN,
)


@forced_validators
class Demographic(Base):
    __data_category__ = "demographic"
    __cardinality__ = "one"

    # The unique internal identifier for this demographic record
    demographic_id: int | None = None

    # The unique internal identifier for the associated participant
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=12220014%20and%20ver_nr=1
    participant_id: str | None = None

    # The age of the subject when the subject enrolled in the study.
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=15742605%20and%20ver_nr=1
    age_at_enrollment: PositiveInt | None = None

    # Unit of measurement for the age of the participant. e.g. "Years"
    age_at_enrollment_units: AgeAtEnrollmentUnits | None = None

    # Indicates whether the participant is 90 years old or over. (for PHI purposes)
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=15354920%20and%20ver_nr=1
    age_90_or_over: YN

    # A textual description of a person's sex at birth. e.g. "Male"
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=7572817%20and%20ver_nr=3
    sex: Sex

    # The race of the participant. e.g. "White"
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=2192199%20and%20ver_nr=1
    race: Annotated[List[Race], BeforeValidator(Base.split_list)]

    # The ethnicity of the participant. e.g. "Hispanic or Latino"
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=2192217%20and%20ver_nr=2
    ethnicity: Ethnicity

    # The number that describes the vertical distance of the participant at enrollment date.
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=2179643%20and%20ver_nr=4
    height: PositiveFloat

    # Unit of measurement for the height of the participant at the enrollment date. e.g. "in"
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=2538920%20and%20ver_nr=1
    height_units: HeightUnits

    # The mass of the participant's entire body at the enrollment date.
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=2179689%20and%20ver_nr=4
    weight: PositiveFloat

    # Unit of measurement for the weight of the participant at the enrollment date. e.g. "kg"
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=2630200%20and%20ver_nr=1
    weight_units: WeightUnits

    # The body mass index of the participant at the enrollment date.
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=2006410%20and%20ver_nr=3
    body_mass_index: PositiveFloat | None = None

    # A decimal number that represents the measure of the 2-dimensional extent of the body surface (i.e., the skin) of the participant at the enrollment date.
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=6606197%20and%20ver_nr=1
    body_surface_area: PositiveFloat | None = None

    # Unit of measurement for body surface area of the participant at the enrollment date. e.g. "m2"
    # https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=15114329%20and%20ver_nr=1
    body_surface_area_units: BodySurfaceAreaUnits | None = None

    # The occupation/job category of the participant. e.g. "Manager"
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=6617540%20and%20ver_nr=1
    occupation: Occupation | None = None

    # The amount of earnings in USD made by the participant's family in a year.
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=14834966%20and%20ver_nr=1
    income: NonNegativeFloat | None = None

    # The highest level of education attained by the participant. e.g. "Bachelor's Degree"
    # CDE: https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=CDEDD.ITEM_ID=2681552%20and%20ver_nr=1
    highest_level_of_education: Education | None = None

    @forced_validator
    @classmethod
    def validate_age_at_enrollment_cr(cls, data, info) -> None:
        age_at_enrollment_units = data.get("age_at_enrollment_units", None)
        age_90_or_over = data.get("age_90_or_over", None)
        age_at_enrollment = int(data.get("age_at_enrollment", None) or 0)

        if age_90_or_over == "Yes":
            if age_at_enrollment or age_at_enrollment_units:
                raise ValueLocError(
                    'If "age_90_or_over" is "Yes" then "age_at_enrollment" and "age_at_enrollment_units" must be blank.',
                    loc="age_at_enrollment",
                )
        elif age_90_or_over == "No":
            if not age_at_enrollment or not age_at_enrollment_units:
                raise ValueLocError(
                    'If "age_90_or_over" is "No" then "age_at_enrollment" and "age_at_enrollment_units" are required.',
                    loc="age_at_enrollment",
                )

    @forced_validator
    @classmethod
    def validate_age_at_enrollment_value(cls, data, info) -> None:
        age_at_enrollment_units = data.get("age_at_enrollment_units", None)
        age_90_or_over = data.get("age_90_or_over", None)
        age_at_enrollment = int(data.get("age_at_enrollment", None) or 0)

        if age_90_or_over == "No":
            age_in_years = age_at_enrollment if age_at_enrollment_units == "Years" else age_at_enrollment / 365.25
            if age_in_years >= 90:
                raise ValueLocError(
                    '"age_at_enrollment" cannot represent a value greater than 90 years of age.',
                    loc="age_at_enrollment",
                )

    @forced_validator
    @classmethod
    def validate_body_surface_area_units_cr(cls, data, info) -> None:
        body_surface_area = data.get("body_surface_area", None)
        body_surface_area_units = data.get("body_surface_area_units", None)

        if body_surface_area and not body_surface_area_units:
            raise ValueLocError(
                'If "body_surface_area" is provided then "body_surface_area_units" must also be provided.'
            )
