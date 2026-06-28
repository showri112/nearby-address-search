"""FastAPI application entry point for the Address Book API.

This module configures logging, prepares the app instance, and provides a
simple startup helper to create database tables before running the server.
"""

import logging

from fastapi import FastAPI

from .database import Base, engine
from .routers import router

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

app = FastAPI(
    title="Address Book API",
    description="Minimal API to manage addresses with distance search and validation",
)
app.include_router(router)


def create_tables() -> None:
    """Create all database tables for the application.

    This is a convenient shortcut for local development. In production, an
    actual migration tool such as Alembic should be used instead.
    """
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")


if __name__ == "__main__":
    import uvicorn

    create_tables()
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
