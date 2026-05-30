"""
SQLAlchemy ORM models for the PACE Intelligence platform.

Central entity: Parcel (identified by APN — Assessor's Parcel Number).
A parcel can have multiple PACE assessments, recorder documents, tax records,
and assessor snapshots over time.
"""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


# ---------------------------------------------------------------------------
# Core property entity

class Parcel(Base):
    """One row per unique APN (Assessor's Parcel Number) in Riverside County."""

    __tablename__ = "parcels"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    apn: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    apn_formatted: Mapped[str] = mapped_column(String(30), nullable=False)  # e.g. 123-456-789

    # Address
    situs_address: Mapped[Optional[str]] = mapped_column(String(200))
    situs_city: Mapped[str] = mapped_column(String(100), default="Riverside")
    situs_state: Mapped[str] = mapped_column(String(2), default="CA")
    situs_zip: Mapped[Optional[str]] = mapped_column(String(10))

    # Census / geographic identifiers
    census_tract: Mapped[Optional[str]] = mapped_column(String(20))
    census_block: Mapped[Optional[str]] = mapped_column(String(20))
    zip_code: Mapped[Optional[str]] = mapped_column(String(10))
    council_district: Mapped[Optional[str]] = mapped_column(String(10))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    assessor_snapshots: Mapped[list["AssessorSnapshot"]] = relationship(back_populates="parcel")
    pace_assessments: Mapped[list["PaceAssessment"]] = relationship(back_populates="parcel")
    recorder_documents: Mapped[list["RecorderDocument"]] = relationship(back_populates="parcel")
    tax_records: Mapped[list["TaxRecord"]] = relationship(back_populates="parcel")

    __table_args__ = (Index("ix_parcels_situs_zip", "situs_zip"),)


# ---------------------------------------------------------------------------
# Assessor data

class AssessorSnapshot(Base):
    """Point-in-time snapshot of assessor property characteristics."""

    __tablename__ = "assessor_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    parcel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("parcels.id"), index=True)
    snapshot_year: Mapped[int] = mapped_column(Integer, nullable=False)

    # Ownership
    owner_name: Mapped[Optional[str]] = mapped_column(String(200))

    # Property characteristics
    property_use_code: Mapped[Optional[str]] = mapped_column(String(10))
    property_use_description: Mapped[Optional[str]] = mapped_column(String(100))
    year_built: Mapped[Optional[int]] = mapped_column(Integer)
    effective_year_built: Mapped[Optional[int]] = mapped_column(Integer)
    building_sqft: Mapped[Optional[int]] = mapped_column(Integer)
    lot_sqft: Mapped[Optional[int]] = mapped_column(Integer)
    bedrooms: Mapped[Optional[int]] = mapped_column(Integer)
    bathrooms: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1))
    stories: Mapped[Optional[int]] = mapped_column(Integer)
    garage_spaces: Mapped[Optional[int]] = mapped_column(Integer)
    pool: Mapped[Optional[bool]] = mapped_column(Boolean)

    # Assessed values
    assessed_land_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    assessed_improvement_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    assessed_total_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    net_taxable_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    homeowners_exemption: Mapped[bool] = mapped_column(Boolean, default=False)

    raw_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    parcel: Mapped["Parcel"] = relationship(back_populates="assessor_snapshots")

    __table_args__ = (
        UniqueConstraint("parcel_id", "snapshot_year", name="uq_assessor_parcel_year"),
        Index("ix_assessor_snapshot_year", "snapshot_year"),
    )


# ---------------------------------------------------------------------------
# PACE assessments

class PaceAdministrator(Base):
    """A licensed PACE program administrator (e.g., Ygrene, CalFirst)."""

    __tablename__ = "pace_administrators"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    program_name: Mapped[Optional[str]] = mapped_column(String(200))
    dfpi_license_number: Mapped[Optional[str]] = mapped_column(String(50))
    caeatfa_program_id: Mapped[Optional[str]] = mapped_column(String(50))
    website: Mapped[Optional[str]] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(50), default="active")  # active, suspended, terminated
    licensed_since: Mapped[Optional[date]] = mapped_column(Date)
    raw_data: Mapped[Optional[dict]] = mapped_column(JSONB)

    assessments: Mapped[list["PaceAssessment"]] = relationship(back_populates="administrator")


class PaceAssessment(Base):
    """
    A single PACE lien/assessment on a parcel.

    PACE assessments are recorded as liens against the property and collected
    through the property tax bill. Source: county recorder (Notice of Assessment)
    and CAEATFA administrator reports.
    """

    __tablename__ = "pace_assessments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    parcel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("parcels.id"), index=True)
    administrator_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("pace_administrators.id"))

    # Document reference
    recorder_document_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("recorder_documents.id"))
    document_number: Mapped[Optional[str]] = mapped_column(String(50), index=True)

    # Assessment details
    assessment_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    recording_date: Mapped[Optional[date]] = mapped_column(Date, index=True)
    term_years: Mapped[Optional[int]] = mapped_column(Integer)
    interest_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 4))
    annual_installment: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))

    # Improvements funded
    improvement_types: Mapped[Optional[list]] = mapped_column(JSONB)  # e.g. ["solar", "hvac", "roofing"]
    improvement_description: Mapped[Optional[str]] = mapped_column(Text)

    # Contractor
    contractor_name: Mapped[Optional[str]] = mapped_column(String(200))
    contractor_license: Mapped[Optional[str]] = mapped_column(String(50))

    # Status
    status: Mapped[str] = mapped_column(String(30), default="active")  # active, paid_off, in_default, foreclosed
    payoff_date: Mapped[Optional[date]] = mapped_column(Date)

    raw_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    source: Mapped[str] = mapped_column(String(50))  # recorder, caeatfa, tax_roll

    parcel: Mapped["Parcel"] = relationship(back_populates="pace_assessments")
    administrator: Mapped[Optional["PaceAdministrator"]] = relationship(back_populates="assessments")
    recorder_document: Mapped[Optional["RecorderDocument"]] = relationship()

    __table_args__ = (
        Index("ix_pace_recording_date", "recording_date"),
        Index("ix_pace_status", "status"),
    )


# ---------------------------------------------------------------------------
# County Recorder documents

class RecorderDocument(Base):
    """
    A document recorded with the Riverside County Recorder-Clerk.
    PACE-relevant document types include Notice of Assessment, Lien, Release of Lien.
    """

    __tablename__ = "recorder_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    parcel_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("parcels.id"), index=True)

    document_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    recording_date: Mapped[Optional[date]] = mapped_column(Date, index=True)
    document_type: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    document_type_code: Mapped[Optional[str]] = mapped_column(String(20))

    grantor: Mapped[Optional[str]] = mapped_column(String(300))
    grantee: Mapped[Optional[str]] = mapped_column(String(300))

    # Book / page (older format)
    book: Mapped[Optional[str]] = mapped_column(String(20))
    page: Mapped[Optional[str]] = mapped_column(String(20))

    # Consideration amount (e.g., sale price for deeds)
    consideration_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))

    is_pace_related: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    raw_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    parcel: Mapped[Optional["Parcel"]] = relationship(back_populates="recorder_documents")

    __table_args__ = (
        Index("ix_recorder_doc_type_date", "document_type", "recording_date"),
        Index("ix_recorder_pace_related", "is_pace_related", "recording_date"),
    )

