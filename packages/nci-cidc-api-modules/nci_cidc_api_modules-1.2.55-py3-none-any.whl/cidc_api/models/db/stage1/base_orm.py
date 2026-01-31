from sqlalchemy_mixins import SerializeMixin, ReprMixin
from cidc_api.config.db import Stage1BaseModel, ModelMixin


class BaseORM(Stage1BaseModel, ModelMixin, ReprMixin, SerializeMixin):
    __abstract__ = True
    __repr__ = ReprMixin.__repr__
