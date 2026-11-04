from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bird_api.core.database import Base


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    feeders: Mapped[list[Feeder]] = relationship(back_populates="client")


class Feeder(Base):
    __tablename__ = "feeders"

    id: Mapped[int] = mapped_column(primary_key=True)
    feeder_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    client: Mapped[Client] = relationship(back_populates="feeders")
    visits: Mapped[list[BirdVisit]] = relationship(back_populates="feeder")


class BirdVisit(Base):
    __tablename__ = "bird_visits"

    id: Mapped[int] = mapped_column(primary_key=True)
    feeder_id: Mapped[int] = mapped_column(ForeignKey("feeders.id"), index=True)
    species: Mapped[str] = mapped_column(String(255), index=True)
    confidence: Mapped[float] = mapped_column(Float)
    image_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    feeder: Mapped[Feeder] = relationship(back_populates="visits")
    