from sqlalchemy_mixins import SerializeMixin, ReprMixin
from cidc_api.config.db import Stage2BaseModel, ModelMixin


class BaseORM(Stage2BaseModel, ModelMixin, ReprMixin, SerializeMixin):
    __abstract__ = True
    __repr__ = ReprMixin.__repr__
