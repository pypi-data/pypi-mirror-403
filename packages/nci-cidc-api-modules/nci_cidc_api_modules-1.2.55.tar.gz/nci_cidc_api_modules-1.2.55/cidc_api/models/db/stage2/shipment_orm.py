from __future__ import annotations
from datetime import datetime
from typing import List

from sqlalchemy import ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cidc_api.models.db.stage2.base_orm import BaseORM
from cidc_api.models.db.stage2.trial_orm import TrialORM
from cidc_api.models.types import AssayPriority, AssayType, Courier, ShipmentCondition, ShipmentQuality


class ShipmentORM(BaseORM):
    __tablename__ = "shipment"
    __repr_attrs__ = ["shipment_id", "institution_id", "trial_id"]
    __table_args__ = (
        ForeignKeyConstraint(["trial_id", "version"], [TrialORM.trial_id, TrialORM.version], ondelete="CASCADE"),
    )

    trial_id: Mapped[str]
    version: Mapped[str]

    shipment_id: Mapped[int] = mapped_column(primary_key=True)
    institution_id: Mapped[int] = mapped_column(ForeignKey("stage2.institution.institution_id", ondelete="CASCADE"))

    manifest_id: Mapped[str]
    assay_priority: Mapped[AssayPriority | None]
    assay_type: Mapped[AssayType | None]
    courier: Mapped[Courier | None]
    tracking_number: Mapped[str | None]
    condition: Mapped[ShipmentCondition | None]
    condition_other: Mapped[str | None]
    date_shipped: Mapped[datetime | None]
    date_received: Mapped[datetime | None]
    quality: Mapped[ShipmentQuality | None]

    trial: Mapped[TrialORM] = relationship(back_populates="shipments", cascade="all, delete")
    institution: Mapped[InstitutionORM] = relationship(back_populates="shipments", cascade="all, delete")
    shipped_from: Mapped[ContactORM] = relationship(
        back_populates="shipment_from", cascade="all, delete", foreign_keys="[ContactORM.shipment_from_id]"
    )
    shipped_to: Mapped[ContactORM] = relationship(
        back_populates="shipment_to", cascade="all, delete", foreign_keys="[ContactORM.shipment_to_id]"
    )
    shipment_specimens: Mapped[List[ShipmentSpecimenORM]] = relationship(
        back_populates="shipment", cascade="all, delete", passive_deletes=True
    )
