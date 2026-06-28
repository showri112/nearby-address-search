from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

class AddressBase(BaseModel):
    """
    Base schema containing the core address fields with validation rules.
    
    All fields are required and validated according to geographic standards.
    """
    street: str = Field(..., min_length=1, description="Street address")
    city: str = Field(..., min_length=1, description="City name")
    country: str = Field(..., min_length=1, description="Country name")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate (-90 to 90)")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate (-180 to 180)")

class AddressCreate(AddressBase):
    """
    Schema for creating a new address. Uses all fields from AddressBase.
    This schema is used for POST requests to create addresses.
    """
    pass

class AddressResponse(AddressBase):
    """
    Schema for address responses from the API.
    Includes the database-generated ID along with all address fields.
    """
    id: UUID = Field(..., description="Unique address identifier")

    class Config:
        from_attributes = True  # Allows Pydantic to read data from ORM models directly

class AddressResponseWithDistance(AddressResponse):
    """
    Extended schema for distance search results.
    Includes the calculated distance from the search coordinates in kilometers.
    """
    distance_km: float = Field(..., ge=0, description="Distance from search coordinates in kilometers")

class DistanceSearch(BaseModel):
    """
    Schema for nearby address search requests.
    Contains the search center coordinates and maximum search distance.
    """
    latitude: float = Field(..., ge=-90, le=90, description="Search center latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Search center longitude")
    distance_km: float = Field(..., gt=0, description="Maximum search radius in kilometers")