"""ORM models for the Address Book API."""

import uuid

from sqlalchemy import Column, Float, String, Uuid

from .database import Base


class Address(Base):
    """SQLAlchemy model representing an address record."""

    __tablename__ = "addresses"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    street = Column(String, nullable=False)
    city = Column(String, nullable=False)
    country = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
