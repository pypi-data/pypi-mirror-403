from __future__ import annotations

from sqlalchemy import ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cidc_api.models.db.stage2.base_orm import BaseORM
from cidc_api.models.db.stage2.trial_orm import TrialORM
from cidc_api.models.types import (
    UberonAnatomicalTerm,
)


class SpecimenORM(BaseORM):
    __tablename__ = "specimen"
    __repr_attrs__ = ["specimen_id", "participant_id", "cimac_id"]
    __data_category__ = "specimen"
    __table_args__ = (
        ForeignKeyConstraint(["trial_id", "version"], [TrialORM.trial_id, TrialORM.version], ondelete="CASCADE"),
    )

    trial_id: Mapped[str]
    version: Mapped[str]

    specimen_id: Mapped[int] = mapped_column(primary_key=True)
    participant_id: Mapped[int] = mapped_column(ForeignKey("stage2.participant.participant_id", ondelete="CASCADE"))

    cimac_id: Mapped[str]
    collection_event_name: Mapped[str]
    days_to_specimen_collection: Mapped[int]
    organ_site_of_collection: Mapped[UberonAnatomicalTerm]

    participant: Mapped[ParticipantORM] = relationship(back_populates="specimens", cascade="all, delete")
    shipment_specimen: Mapped[ShipmentSpecimenORM] = relationship(
        back_populates="specimen", cascade="all, delete", passive_deletes=True
    )
