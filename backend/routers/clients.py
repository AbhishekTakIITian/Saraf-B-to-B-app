"""
clients.py — Client CRUD router
---------------------------------
GET    /clients                        — list all clients for the logged-in user
POST   /clients                        — create a new client
GET    /clients/{client_id}            — get a single client (marks last_accessed_at)
PUT    /clients/{client_id}            — update a client
DELETE /clients/{client_id}            — delete a client
GET    /clients/stats                  — return total count, last_edited, last_accessed
POST   /clients/{client_id}/data       — create a data entry (auto sets date_created)
GET    /clients/{client_id}/data       — list all data entries for a client
PUT    /clients/{client_id}/data/{entry_id}/complete — complete an entry 
(sets final_value & date_completed)
"""

import logging
import os
import sys

from fastapi import APIRouter, Depends, status


from common.db import db_instance  # noqa: E402
from common.models import (  # noqa: E402
    ClientCreate,
    ClientOut,
    ClientUpdate,
    CompleteDataEntryPayload,
    CreateDataEntryPayload,
    GetClientDataEntryResponse,
    StatsOut,
    UpdateDataEntryPayload,
)
from utils.db_utils import (  # noqa: E402
    complete_client_data_entry_db,
    create_client_data_entry_db,
    create_client_db,
    delete_client_data_entry_db,
    delete_client_db,
    get_all_clients_stats,
    get_client_by_id,
    get_client_data_db,
    list_all_clients,
    update_client_data_entry_db,
    update_client_db,
)

# Ensure backend root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
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
def list_clients(
    username: str,
    search: str | None = None,
    contains: str | None = None,
    sort_by: str = "last_edited_at",
    sort_order: str = "desc",
    conn=Depends(db_instance.get_db),
):
    """List all clients owned by the specified username with optional search and sorting."""
    query_search = contains if contains is not None else search
    return list_all_clients(
        username, conn, search=query_search, sort_by=sort_by, sort_order=sort_order
    )


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
def get_client(
    client_id: int,
    username: str,
    sort_by: str = "id",
    sort_order: str = "asc",
    contains: str = None,
    conn=Depends(db_instance.get_db)
):
    """Get a single client by ID."""
    return get_client_by_id(
        client_id, username, conn, sort_by=sort_by, sort_order=sort_order, contains=contains
    )


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


@router.post("/{client_id}/data", status_code=status.HTTP_201_CREATED)
def create_client_data_entry(
    client_id: int,
    body: CreateDataEntryPayload,
    username: str,
    conn=Depends(db_instance.get_db),
):
    """Create a new data entry for a specific client. date_created is set automatically."""
    logger.info("Creating data entry for client %d by user '%s'.", client_id, username)
    return create_client_data_entry_db(client_id, body, username, conn)


@router.get("/{client_id}/data", response_model=list[GetClientDataEntryResponse])
def get_client_data(
    client_id: int,
    username: str,
    description_contains: str | None = None,
    search: str | None = None,
    sort_by: str = "number",
    sort_order: str = "desc",
    conn=Depends(db_instance.get_db),
):
    """Get all data entries for a specific client."""
    query_search = description_contains if description_contains is not None else search
    return get_client_data_db(
        client_id,
        username,
        conn,
        description_contains=query_search,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.put(
    "/{client_id}/data/{entry_id}",
    status_code=status.HTTP_200_OK,
)
def update_client_data_entry(
    client_id: int,
    entry_id: int,
    body: UpdateDataEntryPayload,
    username: str,
    conn=Depends(db_instance.get_db),
):
    """Update a data entry — updates fields and sets date_updated. If final_value is provided, sets date_completed."""
    logger.info(
        "Updating data entry %d for client %d by user '%s'.",
        entry_id, client_id, username,
    )
    return update_client_data_entry_db(client_id, entry_id, body, username, conn)


@router.put(
    "/{client_id}/data/{entry_id}/complete",
    status_code=status.HTTP_200_OK,
)
def complete_client_data_entry(
    client_id: int,
    entry_id: int,
    body: CompleteDataEntryPayload,
    username: str,
    conn=Depends(db_instance.get_db),
):
    """Mark a data entry as complete — sets final_value, date_completed, and date_updated."""
    logger.info(
        "Completing data entry %d for client %d by user '%s'.",
        entry_id, client_id, username,
    )
    return complete_client_data_entry_db(client_id, entry_id, body, username, conn)


@router.delete(
    "/{client_id}/data/{entry_id}",
    status_code=status.HTTP_200_OK,
)
def delete_client_data_entry(
    client_id: int,
    entry_id: int,
    username: str,
    conn=Depends(db_instance.get_db),
):
    """Delete a data entry by ID."""
    logger.info(
        "Deleting data entry %d for client %d by user '%s'.",
        entry_id, client_id, username,
    )
    return delete_client_data_entry_db(client_id, entry_id, username, conn)
