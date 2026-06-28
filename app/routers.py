"""API route definitions for the Address Book service."""

import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from . import crud
from .database import get_db
from .schemas import (
    AddressCreate,
    AddressResponse,
    AddressResponseWithDistance,
    AddressUpdate,
    DistanceSearch,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/addresses/", response_model=AddressResponse, tags=["Addresses"])
def create_address(address: AddressCreate, db: Session = Depends(get_db)):
    """Create a new address record."""
    try:
        new_address = crud.create_address(db, address)
        logger.info("Created address: %s, %s", new_address.id, new_address.city)
        return new_address
    except Exception:
        logger.exception("Failed to create address")
        raise HTTPException(status_code=400, detail="Failed to create address")


@router.get("/addresses/", response_model=List[AddressResponse], tags=["Addresses"])
def read_addresses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get paginated list of addresses."""
    try:
        addresses = crud.get_addresses(db, skip=skip, limit=limit)
        logger.info("Returned %d addresses (skip=%d, limit=%d)", len(addresses), skip, limit)
        return addresses
    except Exception:
        logger.exception("Failed to retrieve addresses")
        raise HTTPException(status_code=500, detail="Failed to retrieve addresses")


@router.get("/addresses/{address_id}", response_model=AddressResponse, tags=["Addresses"])
def read_address(address_id: UUID, db: Session = Depends(get_db)):
    """Get a single address by its UUID."""
    db_address = crud.get_address(db, address_id)
    if db_address is None:
        logger.warning("Address not found: %s", address_id)
        raise HTTPException(status_code=404, detail="Address not found")
    return db_address


@router.put("/addresses/{address_id}", response_model=AddressResponse, tags=["Addresses"])
def update_address(address_id: UUID, address: AddressUpdate, db: Session = Depends(get_db)):
    """Update an existing address with the provided fields."""
    if not address.model_dump(exclude_none=True):
        raise HTTPException(status_code=400, detail="No address fields provided for update")

    db_address = crud.update_address(db, address_id, address)
    if db_address is None:
        logger.warning("Address not found for update: %s", address_id)
        raise HTTPException(status_code=404, detail="Address not found")
    logger.info("Updated address: %s", address_id)
    return db_address


@router.delete("/addresses/{address_id}", tags=["Addresses"])
def delete_address(address_id: UUID, db: Session = Depends(get_db)):
    """Delete an address by its UUID."""
    success = crud.delete_address(db, address_id)
    if not success:
        logger.warning("Address not found for deletion: %s", address_id)
        raise HTTPException(status_code=404, detail="Address not found")
    logger.info("Deleted address: %s", address_id)
    return {"message": "Address deleted successfully"}


@router.post(
    "/search/nearby",
    response_model=List[AddressResponseWithDistance],
    tags=["Search"],
)
def search_nearby(search_criteria: DistanceSearch, db: Session = Depends(get_db)):
    """Search addresses within a specified radius."""
    try:
        results = crud.search_nearby(db, search_criteria)
        logger.info(
            "Nearby search returned %d results for centre (%s,%s) radius %s km",
            len(results),
            search_criteria.latitude,
            search_criteria.longitude,
            search_criteria.distance_km,
        )
        return results
    except Exception:
        logger.exception("Failed to search nearby addresses")
        raise HTTPException(status_code=500, detail="Failed to search nearby addresses")
