from sqlalchemy import Column, String, Float, Uuid
from database import Base
import uuid

class Address(Base):
    """
    SQLAlchemy ORM model representing an address in the database.
    
    An address contains location information including street details, city, country,
    and geographic coordinates (latitude and longitude) which can be used for
    distance calculations and geographic queries.
    
    Attributes:
        id: Unique identifier for the address (auto-generated)
        street: Street address (required, non-empty)
        city: City name (required, non-empty)
        country: Country name (required, non-empty)
        latitude: Geographic latitude coordinate between -90 and 90 degrees (required)
        longitude: Geographic longitude coordinate between -180 and 180 degrees (required)
    """
    __tablename__ = "addresses"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    street = Column(String, nullable=False)
    city = Column(String, nullable=False)
    country = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)