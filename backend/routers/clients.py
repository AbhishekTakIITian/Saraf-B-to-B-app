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
import sys
import os

from fastapi import APIRouter, Depends, status

from common.db import db_instance
from common.models import ClientCreate, ClientUpdate, ClientOut, StatsOut
from utils.db_utils import get_all_clients_stats, list_all_clients, create_client_db, get_client_by_id,\
    update_client, delete_client

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/clients", tags=["clients"])

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/stats", response_model=StatsOut)
def get_stats(username: str, conn=Depends(db_instance.get_db)):
    return get_all_clients_stats(username, conn)


@router.get("", response_model=list[ClientOut])
def list_clients(username: str, conn=Depends(db_instance.get_db)):
    return list_all_clients(username, conn)


@router.post("", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
def create_client(body: ClientCreate, username: str, conn=Depends(db_instance.get_db)):
    return create_client_db(body, username, conn)


@router.get("/{client_id}", response_model=ClientOut)
def get_client(client_id: int, username: str, conn=Depends(db_instance.get_db)):
    return get_client_by_id(client_id, username, conn)


@router.put("/{client_id}", response_model=ClientOut)
def update_client(client_id: int, body: ClientUpdate, username: str, conn=Depends(db_instance.get_db)):
    return update_client(client_id, body, username, conn)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(client_id: int, username: str, conn=Depends(db_instance.get_db)):
    return delete_client(client_id, username, conn)
