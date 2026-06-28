"""Pydantic schemas for validating and serializing address data."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AddressBase(BaseModel):
    """Shared address fields for create and read operations."""

    street: str = Field(..., min_length=1, description="Street address")
    city: str = Field(..., min_length=1, description="City name")
    country: str = Field(..., min_length=1, description="Country name")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate (-90 to 90)")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate (-180 to 180)")


class AddressCreate(AddressBase):
    """Schema used when creating a new address."""
    pass


class AddressUpdate(BaseModel):
    """Schema used for partial address updates."""

    street: Optional[str] = Field(None, min_length=1, description="Street address")
    city: Optional[str] = Field(None, min_length=1, description="City name")
    country: Optional[str] = Field(None, min_length=1, description="Country name")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude coordinate (-90 to 90)")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude coordinate (-180 to 180)")


class AddressResponse(AddressBase):
    """Schema returned for address data from the API."""

    id: UUID = Field(..., description="Unique address identifier")

    model_config = {"from_attributes": True}


class AddressResponseWithDistance(AddressResponse):
    """Extended address response that includes distance from search centre."""

    distance_km: float = Field(..., ge=0, description="Distance from search coordinates in kilometers")


class DistanceSearch(BaseModel):
    """Schema for nearby search requests."""

    latitude: float = Field(..., ge=-90, le=90, description="Search center latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Search center longitude")
    distance_km: float = Field(..., gt=0, description="Maximum search radius in kilometers")
