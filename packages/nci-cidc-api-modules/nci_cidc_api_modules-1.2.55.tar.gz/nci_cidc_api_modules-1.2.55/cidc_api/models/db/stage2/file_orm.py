from __future__ import annotations
from datetime import datetime

from sqlalchemy import ForeignKeyConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cidc_api.models.db.stage2.base_orm import BaseORM
from cidc_api.models.db.stage2.trial_orm import TrialORM
from cidc_api.models.types import ChecksumType, FileFormat


class FileORM(BaseORM):
    __tablename__ = "file"
    __table_args__ = (
        ForeignKeyConstraint(["trial_id", "version"], [TrialORM.trial_id, TrialORM.version], ondelete="CASCADE"),
    )

    trial_id: Mapped[str]
    version: Mapped[str]

    file_id: Mapped[int] = mapped_column(primary_key=True)

    creator_id: Mapped[int | None] = mapped_column(ForeignKey("stage2.institution.institution_id", ondelete="CASCADE"))
    description: Mapped[str | None]
    uuid: Mapped[str]
    file_name: Mapped[str]
    object_url: Mapped[str]
    uploaded_timestamp: Mapped[datetime]
    file_size_bytes: Mapped[int]
    checksum_value: Mapped[str]
    checksum_type: Mapped[ChecksumType]
    file_format: Mapped[FileFormat]

    trial: Mapped[TrialORM] = relationship(back_populates="files", cascade="all, delete")
    creator: Mapped[InstitutionORM | None] = relationship(back_populates="files", cascade="all, delete")
