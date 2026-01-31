from enum import StrEnum
from typing import Any

from sqlalchemy import and_
from sqlalchemy.orm.session import Session

from cidc_api.models.pydantic.stage1 import all_models as stage1_all_models
from cidc_api.models.pydantic.stage2 import all_models as stage2_all_models
from cidc_api.models.db.stage1 import all_models as stage1_all_db_models
from cidc_api.models.db.stage2 import all_models as stage2_all_db_models
from cidc_api.models.db.stage1 import TrialORM as s1TrialORM
from cidc_api.models.db.stage2 import TrialORM as s2TrialORM


standard_data_categories = [
    model.__data_category__ for model in stage1_all_models if hasattr(model, "__data_category__")
]


# Maps data categories like "treatment" to their associated pydantic model
data_category_to_model = {
    "stage1": {model.__data_category__: model for model in stage1_all_models if hasattr(model, "__data_category__")},
    "stage2": {model.__data_category__: model for model in stage2_all_models if hasattr(model, "__data_category__")},
}


data_category_to_db_model = {
    "stage1": {model.__data_category__: model for model in stage1_all_db_models if hasattr(model, "__data_category__")},
    "stage2": {model.__data_category__: model for model in stage2_all_db_models if hasattr(model, "__data_category__")},
}


class Stages(StrEnum):
    STAGE1 = "stage1"
    STAGE2 = "stage2"
    STAGE3 = "stage3"

    @classmethod
    def members(cls):
        return list(v.value for v in cls.__members__.values())


def trial_exists(trial_id: str, version: str, stage: str, session: Session) -> bool:
    if stage not in Stages:
        raise ValueError(f"value for 'stage' must be in {Stages.members()}")

    if stage == Stages.STAGE1:
        TrialORM = s1TrialORM
    elif stage == Stages.STAGE2:
        TrialORM = s2TrialORM
    elif stage == Stages.STAGE3:
        pass  # stub

    trials = session.query(TrialORM).filter(and_(TrialORM.trial_id == trial_id, TrialORM.version == version)).all()
    return len(trials) == 1


# A class to hold the entire model representation of a trial's dataset
class Dataset(dict):
    def __init__(self, *args, **kwargs):
        for data_category in standard_data_categories:
            self[data_category] = []
        super().__init__(*args, **kwargs)

    def load(self, trial_id: str, version: str, stage: str, session: Session):
        if stage not in Stages:
            raise ValueError(f"value for 'stage' must be in {Stages.members()}")

        for data_category, _ in self.items():
            db_model_cls = data_category_to_db_model[stage][data_category]
            db_models = self.load_db_models(trial_id, version, db_model_cls, session)
            self[data_category] = db_models

    def load_db_models(self, trial_id: str, version: str, db_model_cls: Any, session: Session):
        db_models = (
            session.query(db_model_cls)
            .filter(and_(db_model_cls.trial_id == trial_id, db_model_cls.version == version))
            .all()
        )
        return db_models
