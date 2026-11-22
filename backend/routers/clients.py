"""
clients.py — Client CRUD router
---------------------------------
GET    /clients              — list all clients for the logged-in user
POST   /clients              — create a new client
GET    /clients/{client_id}  — get a single client (marks last_accessed_at)
PUT    /clients/{client_id}  — update a client
DELETE /clients/{client_id}  — delete a client
GET    /clients/stats        — return total count, last_edited, last_accessed
"""

import logging
import os
import sys

from fastapi import APIRouter, Depends, status

# Ensure backend root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from common.db import db_instance  # noqa: E402
from common.models import ClientCreate, ClientOut, ClientUpdate, StatsOut  # noqa: E402
from utils.db_utils import (  # noqa: E402
    create_client_db,
    delete_client_db,
    get_all_clients_stats,
    get_client_by_id,
    list_all_clients,
    update_client_db,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/clients", tags=["clients"])


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/stats", response_model=StatsOut)
def get_stats(username: str, conn=Depends(db_instance.get_db)):
    """Return total count, last edited client, and last accessed client."""
    return get_all_clients_stats(username, conn)


@router.get("", response_model=list[ClientOut])
def list_clients(username: str, conn=Depends(db_instance.get_db)):
    """List all clients owned by the specified username."""
    return list_all_clients(username, conn)


@router.post("", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
def create_client(
    body: ClientCreate,
    username: str,
    conn=Depends(db_instance.get_db),
):
    """Create a new client for the specified username."""
    logger.info("Creating client '%s' for user '%s'.", body.name, username)
    return create_client_db(body, username, conn)


@router.get("/{client_id}", response_model=ClientOut)
def get_client(client_id: int, username: str, conn=Depends(db_instance.get_db)):
    """Get a single client by ID."""
    return get_client_by_id(client_id, username, conn)


@router.put("/{client_id}", response_model=ClientOut)
def update_client(
    client_id: int,
    body: ClientUpdate,
    username: str,
    conn=Depends(db_instance.get_db),
):
    """Update an existing client by ID."""
    logger.info("Updating client %d for user '%s'.", client_id, username)
    return update_client_db(client_id, body, username, conn)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(client_id: int, username: str, conn=Depends(db_instance.get_db)):
    """Delete a client by ID."""
    logger.info("Deleting client %d for user '%s'.", client_id, username)
    return delete_client_db(client_id, username, conn)
