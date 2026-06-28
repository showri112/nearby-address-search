"""Utility helpers for geographic address search.

This module provides the bounding-box math and distance calculations used by
address search operations. It prefers NumPy vectorised calculations when NumPy
is installed, otherwise it falls back to the standard haversine function.
"""

import logging
import math
from typing import Iterable, Union

try:
    import numpy as np

    _have_numpy = True
except ImportError:
    _have_numpy = False

import haversine as hs

logger = logging.getLogger(__name__)


def build_bounding_box(
    latitude: float, longitude: float, distance_km: float
) -> tuple[float, float, float, float]:
    """Return bounding box coordinates for a circular search area.

    The bounding box is an approximation that helps reduce the number of
    addresses which need a full haversine distance check.

    Args:
        latitude: Search centre latitude in degrees.
        longitude: Search centre longitude in degrees.
        distance_km: Search radius in kilometres.

    Returns:
        A tuple of (min_lat, max_lat, min_lon, max_lon).
    """
    lat_delta = distance_km / 111.0
    cos_lat = abs(math.cos(math.radians(latitude)))
    cos_lat = max(cos_lat, 1e-6)
    lon_delta = distance_km / (111.0 * cos_lat)

    logger.debug(
        "Bounding box computed: lat +/- %s, lon +/- %s for centre (%s, %s)",
        lat_delta,
        lon_delta,
        latitude,
        longitude,
    )

    return (
        latitude - lat_delta,
        latitude + lat_delta,
        longitude - lon_delta,
        longitude + lon_delta,
    )


def calculate_distance(lat: float, lon: float, addresses: list) -> Union["np.ndarray", list[float]]:
    """Calculate distance from a point to a list of address coordinates.

    If NumPy is available, use the vectorised haversine path for better
    performance. Otherwise use the normal Python haversine function.

    Args:
        lat: Reference latitude.
        lon: Reference longitude.
        addresses: List of address objects with latitude and longitude attrs.

    Returns:
        Either a NumPy ndarray or a plain Python list of distances in kilometres.
    """
    if _have_numpy:
        logger.info("Using NumPy for distance calculations")
        search_point = np.array([[lat, lon]] * len(addresses))
        addr_points = np.array([[addr.latitude, addr.longitude] for addr in addresses])
        return hs.haversine_vector(search_point, addr_points, unit=hs.Unit.KILOMETERS)
    logger.info("NumPy not available, using standard haversine function")
    return [
        hs.haversine(
            (lat, lon), (addr.latitude, addr.longitude), unit=hs.Unit.KILOMETERS
        )
        for addr in addresses
    ]
