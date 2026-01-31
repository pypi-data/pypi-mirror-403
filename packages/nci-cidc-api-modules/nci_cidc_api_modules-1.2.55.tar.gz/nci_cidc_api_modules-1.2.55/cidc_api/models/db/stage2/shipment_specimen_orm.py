from __future__ import annotations

from sqlalchemy import ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cidc_api.models.db.stage2.base_orm import BaseORM
from cidc_api.models.db.stage2.trial_orm import TrialORM


class ShipmentSpecimenORM(BaseORM):
    __tablename__ = "shipment_specimen"
    __repr_attrs__ = ["specimen_id", "shipment_id"]
    __table_args__ = (
        ForeignKeyConstraint(["trial_id", "version"], [TrialORM.trial_id, TrialORM.version], ondelete="CASCADE"),
    )

    trial_id: Mapped[str]
    version: Mapped[str]

    specimen_id: Mapped[int] = mapped_column(
        ForeignKey("stage2.specimen.specimen_id", ondelete="CASCADE"), primary_key=True
    )
    shipment_id: Mapped[int] = mapped_column(
        ForeignKey("stage2.shipment.shipment_id", ondelete="CASCADE"), primary_key=True
    )
    box_number: Mapped[str]
    sample_location: Mapped[str]

    specimen: Mapped[SpecimenORM] = relationship(back_populates="shipment_specimen", cascade="all, delete")
    shipment: Mapped[ShipmentORM] = relationship(back_populates="shipment_specimens", cascade="all, delete")
