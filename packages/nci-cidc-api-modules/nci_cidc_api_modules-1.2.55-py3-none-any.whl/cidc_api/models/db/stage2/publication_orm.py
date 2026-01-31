from __future__ import annotations
from sqlalchemy import ForeignKeyConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cidc_api.models.db.stage2.base_orm import BaseORM
from cidc_api.models.db.stage2.trial_orm import TrialORM
from cidc_api.models.types import ConditioningRegimenType, StemCellDonorType


class PublicationORM(BaseORM):
    __tablename__ = "publication"
    __repr_attrs__ = ["publication_id", "publication_title"]
    __data_category__ = "publication"
    __table_args__ = (
        ForeignKeyConstraint(["trial_id", "version"], [TrialORM.trial_id, TrialORM.version], ondelete="CASCADE"),
    )

    trial_id: Mapped[str]
    version: Mapped[str]

    publication_id: Mapped[int] = mapped_column(primary_key=True)

    digital_object_id: Mapped[str]
    pubmed_id: Mapped[str | None]
    publication_title: Mapped[str | None]
    authorship: Mapped[str | None]
    year_of_publication: Mapped[str | None]
    journal_citation: Mapped[str | None]

    trial: Mapped[TrialORM] = relationship(back_populates="publications", cascade="all, delete")
