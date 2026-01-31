import copy
from contextlib import contextmanager
from typing import Self, ClassVar
from pydantic import BaseModel, ConfigDict, model_validator, ValidationError
from pydantic_core import InitErrorDetails

from cidc_api.models.errors import ValueLocError
from functools import wraps


class Base(BaseModel):

    model_config = ConfigDict(
        validate_assignment=True,
        from_attributes=True,
        extra="allow",
    )
    forced_validators: ClassVar = []

    # Validates the new state and updates the object if valid
    def update(self, **kwargs):
        self.model_validate(self.__dict__ | kwargs)
        self.__dict__.update(kwargs)

    # CM that delays validation until all fields are applied.
    # If validation fails the original fields are restored and the ValidationError is raised.
    @contextmanager
    def delay_validation(self):
        original_dict = copy.deepcopy(self.__dict__)
        self.model_config["validate_assignment"] = False
        try:
            yield
        finally:
            self.model_config["validate_assignment"] = True
        try:
            self.model_validate(self.__dict__)
        except:
            self.__dict__.update(original_dict)
            raise

        # CM that delays validation until all fields are applied.

    @classmethod
    def split_list(cls, val):
        """Listify fields that are multi-valued in input data, e.g. 'lung|kidney'"""
        if type(val) == list:
            return val
        elif type(val) == str:
            if not val:
                return []
            return val.split("|")
        elif val == None:
            return []
        else:
            raise ValueError("Field value must be string or list")

    @model_validator(mode="wrap")
    @classmethod
    def check_all_forced_validators(cls, data, handler, info) -> Self:
        """This base validator ensures all registered forced_validator(s) get called along with
        normal model field validators no matter what the outcome of either is. Normal field_validator
        and model_validator decorators don't guarantee this. We want to collect as many errors as we can.

        Collects errors from both attempts and raises them in a combined ValidationError."""

        validation_errors = []
        # When assigning attributes to an already-hydrated model, data is an instance of the model
        # instead of a dict and handler is an AssignmentValidatorCallable instead of a ValidatorCallable(!!)
        extracted_data = data.model_dump() if not isinstance(data, dict) else data

        for validator in cls.forced_validators:
            try:
                func_name = validator.__name__
                func = getattr(cls, func_name)
                func(extracted_data, info)
            except (ValueError, ValueLocError) as e:
                validation_errors.append(
                    InitErrorDetails(
                        type="value_error",
                        loc=e.loc,
                        input=extracted_data,
                        ctx={"error": e},
                    )
                )
        try:
            # Instantiate the model to ensure all other normal field validations are called
            retval = handler(data)
        except ValidationError as e:
            validation_errors.extend(e.errors())
        if validation_errors:
            raise ValidationError.from_exception_data(title=cls.__name__, line_errors=validation_errors)
        return retval


def forced_validator(func):
    """A method marked with this decorator is added to the class list of forced_validators"""
    func._is_forced_validator = True  # Tag the function object with a custom attribute
    return func


def forced_validators(cls):
    """A class marked with this decorator accumulates its methods marked with force_validator into a list
    for later invocation."""

    cls.forced_validators = []
    for obj in cls.__dict__.values():
        if getattr(obj, "_is_forced_validator", False):
            cls.forced_validators.append(obj)
    return cls
