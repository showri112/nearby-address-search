import math
from uuid import UUID
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Union
import logging
import haversine as hs
from database import engine, get_db, Base
from models import Address
from schemas import (
    AddressCreate,
    AddressResponse,
    DistanceSearch,
    AddressResponseWithDistance,
)

try:
    import numpy as np
    have_numpy = True
except:
    have_numpy = False

# Configure logging
log_filename = "app.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(),
    ],
)
logging.getLogger("watchfiles").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)
logger.info("Database tables initialized")

app = FastAPI(
    title="Address Book API",
    description="Minimal API to manage addresses with distance search and validation",
)


@app.post("/addresses/", response_model=AddressResponse, tags=["Addresses"])
def create_address(address: AddressCreate, db: Session = Depends(get_db)):
    """
    Create a new address in the database.

    The address fields are validated to ensure:
    - Street, city, and country are non-empty strings
    - Latitude is between -90 and 90 degrees
    - Longitude is between -180 and 180 degrees

    Returns the newly created address with its ID.
    """
    try:
        db_address = Address(**address.model_dump())
        db.add(db_address)
        db.commit()
        db.refresh(db_address)
        logger.info(
            f"Address created successfully: ID={db_address.id}, City={db_address.city}"
        )
        return db_address
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating address: {str(e)}")
        raise HTTPException(
            status_code=400, detail=f"Failed to create address: {str(e)}"
        )


@app.get("/addresses/", response_model=List[AddressResponse], tags=["Addresses"])
def read_addresses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve all addresses from the database with pagination support.

    Args:
        skip: Number of records to skip (default: 0)
        limit: Maximum number of records to return (default: 100)

    Returns a list of all addresses stored in the database.
    """
    try:
        addresses = db.query(Address).offset(skip).limit(limit).all()
        logger.info(
            f"Retrieved {len(addresses)} addresses (skip={skip}, limit={limit})"
        )
        return addresses
    except Exception as e:
        logger.error(f"Error retrieving addresses: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve addresses")


@app.get("/addresses/{address_id}", response_model=AddressResponse, tags=["Addresses"])
def read_address(address_id: UUID, db: Session = Depends(get_db)):
    """
    Retrieve a specific address by its ID.

    Args:
        address_id: The unique identifier of the address to retrieve

    Returns the requested address if found, otherwise raises a 404 error.
    """
    try:
        db_address = db.query(Address).filter(Address.id == address_id).first()
        if db_address is None:
            logger.warning(f"Address not found: ID={address_id}")
            raise HTTPException(status_code=404, detail="Address not found")
        logger.info(f"Retrieved address: ID={address_id}")
        return db_address
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving address {address_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve address")


@app.put("/addresses/{address_id}", response_model=AddressResponse, tags=["Addresses"])
def update_address(
    address_id: UUID, address: AddressCreate, db: Session = Depends(get_db)
):
    """
    Update an existing address with new information.

    All fields (street, city, country, latitude, longitude) can be updated.
    The same validation rules apply as when creating an address.

    Args:
        address_id: The unique identifier of the address to update
        address: The new address data

    Returns the updated address or raises a 404 error if not found.
    """
    try:
        db_address = db.query(Address).filter(Address.id == address_id).first()
        if db_address is None:
            logger.warning(f"Address not found for update: ID={address_id}")
            raise HTTPException(status_code=404, detail="Address not found")

        for key, value in address.model_dump().items():
            setattr(db_address, key, value)

        db.commit()
        db.refresh(db_address)
        logger.info(f"Address updated successfully: ID={address_id}")
        return db_address
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating address {address_id}: {str(e)}")
        raise HTTPException(
            status_code=400, detail=f"Failed to update address: {str(e)}"
        )


@app.delete("/addresses/{address_id}", tags=["Addresses"])
def delete_address(address_id: UUID, db: Session = Depends(get_db)):
    """
    Delete an address from the database.

    Args:
        address_id: The unique identifier of the address to delete

    Returns a success message or raises a 404 error if the address is not found.
    """
    try:
        db_address = db.query(Address).filter(Address.id == address_id).first()
        if db_address is None:
            logger.warning(f"Address not found for deletion: ID={address_id}")
            raise HTTPException(status_code=404, detail="Address not found")

        db.delete(db_address)
        db.commit()
        logger.info(f"Address deleted successfully: ID={address_id}")
        return {"message": "Address deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting address {address_id}: {str(e)}")
        raise HTTPException(
            status_code=400, detail=f"Failed to delete address: {str(e)}"
        )


def calculate_distance(
    lat: float, lon: float, addresses: list
) -> Union[np.ndarray, list[float]]:
    if have_numpy:
        print("Using NumPy for distance calculations")
        search_point = np.array([[lat, lon]] * len(addresses))
        addr_points = np.array([[addr.latitude, addr.longitude] for addr in addresses])
        return hs.haversine_vector(search_point, addr_points, unit=hs.Unit.KILOMETERS)
    else:
        print("NumPy not available, using standard library")
        return [
            hs.haversine(
                (lat, lon), (addr.latitude, addr.longitude), unit=hs.Unit.KILOMETERS
            )
            for addr in addresses
        ]


@app.post(
    "/search/nearby", response_model=List[AddressResponseWithDistance], tags=["Search"]
)
def search_nearby(search_criteria: DistanceSearch, db: Session = Depends(get_db)):
    """
    Search for addresses within a specified distance of a given location.

    The endpoint first performs a bounding box query to limit the number of
    candidate addresses, then calculates the actual distance for each result
    and returns only those within the requested radius. Results are sorted
    by distance in ascending order.

    Args:
        search_criteria: The search parameters, including the reference
            latitude, longitude, and search radius in kilometers.
        db: Database session used to query address records.

    Returns:
        A list of addresses within the specified distance, with each address
        including its calculated distance from the search coordinates.
    """
    try:
        # Calculate the latitude and longitude offsets for the bounding box.
        lat_delta = search_criteria.distance_km / 111.0
        lon_delta = search_criteria.distance_km / (
            111.0 * abs(math.cos(math.radians(search_criteria.latitude)))
        )
        # Query addresses within the bounding box to reduce the number of distance calculations.
        all_addresses = (
            db.query(Address)
            .filter(
                Address.latitude.between(
                    search_criteria.latitude - lat_delta,
                    search_criteria.latitude + lat_delta,
                ),
                Address.longitude.between(
                    search_criteria.longitude - lon_delta,
                    search_criteria.longitude + lon_delta,
                ),
            )
            .all()
        )
        if not all_addresses:
            return []
        # Calculate distances and filter addresses within the specified distance
        distances = calculate_distance(
            search_criteria.latitude, search_criteria.longitude, all_addresses
        )
        # Pair addresses with their distances and filter by the specified distance
        nearby_addresses = [
            (addr, float(dist))
            for addr, dist in zip(all_addresses, distances)
            if dist <= search_criteria.distance_km
        ]
        # Sort the nearby addresses by distance
        nearby_addresses.sort(key=lambda x: x[1])

        # Return the addresses along with their distances in the response model
        return [
            {**addr.__dict__, "distance_km": dist} for addr, dist in nearby_addresses
        ]

    except Exception as e:
        logger.error(f"Error searching nearby addresses: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search nearby addresses")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)