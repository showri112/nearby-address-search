"""CRUD operations and business logic for the Address Book API."""

import logging
from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from .models import Address
from .schemas import AddressCreate, AddressUpdate, DistanceSearch
from .utils import build_bounding_box, calculate_distance

logger = logging.getLogger(__name__)


def create_address(db: Session, address: AddressCreate) -> Address:
    """Insert a new address record into the database."""
    db_address = Address(**address.model_dump())
    db.add(db_address)
    db.commit()
    db.refresh(db_address)
    logger.debug("Saved address record: %s", db_address.id)
    return db_address


def get_addresses(db: Session, skip: int = 0, limit: int = 100) -> List[Address]:
    """Fetch a page of addresses from the database."""
    return db.query(Address).offset(skip).limit(limit).all()


def get_address(db: Session, address_id: UUID) -> Address | None:
    """Fetch a single address by its UUID."""
    return db.query(Address).filter(Address.id == address_id).first()


def update_address(db: Session, address_id: UUID, address_update: AddressUpdate) -> Address | None:
    """Apply partial updates to an existing address record."""
    db_address = get_address(db, address_id)
    if db_address is None:
        logger.debug("No address found for update: %s", address_id)
        return None

    update_data = address_update.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(db_address, key, value)

    db.commit()
    db.refresh(db_address)
    logger.debug("Updated address record: %s", address_id)
    return db_address


def delete_address(db: Session, address_id: UUID) -> bool:
    """Remove an address from the database."""
    db_address = get_address(db, address_id)
    if db_address is None:
        logger.debug("No address found for delete: %s", address_id)
        return False

    db.delete(db_address)
    db.commit()
    logger.debug("Deleted address record: %s", address_id)
    return True


def search_nearby(db: Session, search_criteria: DistanceSearch) -> List[dict]:
    """Find nearby addresses within the requested search radius."""
    min_lat, max_lat, min_lon, max_lon = build_bounding_box(
        search_criteria.latitude,
        search_criteria.longitude,
        search_criteria.distance_km,
    )

    # Use a bounding box first to reduce the number of expensive distance checks.
    candidates = (
        db.query(Address)
        .filter(
            Address.latitude.between(min_lat, max_lat),
            Address.longitude.between(min_lon, max_lon),
        )
        .all()
    )

    if not candidates:
        logger.debug("No candidate addresses found inside bounding box")
        return []

    distances = calculate_distance(
        search_criteria.latitude,
        search_criteria.longitude,
        candidates,
    )

    nearby = []
    for address, distance in zip(candidates, distances):
        if distance <= search_criteria.distance_km:
            payload = {
                **{k: v for k, v in address.__dict__.items() if k != "_sa_instance_state"},
                "distance_km": float(distance),
            }
            nearby.append(payload)

    nearby.sort(key=lambda item: item["distance_km"])
    logger.debug("Nearby search returned %d results", len(nearby))
    return nearby
