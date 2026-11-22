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
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common.db import db_instance

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/clients", tags=["clients"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ClientCreate(BaseModel):
    name: str
    address: str | None = None
    contact_number: str | None = None


class ClientUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    contact_number: str | None = None


class ClientOut(BaseModel):
    id: int
    owner_username: str
    name: str
    address: str | None
    contact_number: str | None
    created_at: datetime
    last_edited_at: datetime
    last_accessed_at: datetime | None


class StatsOut(BaseModel):
    total: int
    last_edited: ClientOut | None
    last_accessed: ClientOut | None


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

ROW_COLS = "id, owner_username, name, address, contact_number, created_at, last_edited_at, last_accessed_at"

def _row_to_client(row) -> ClientOut:
    return ClientOut(
        id=row[0],
        owner_username=row[1],
        name=row[2],
        address=row[3],
        contact_number=row[4],
        created_at=row[5],
        last_edited_at=row[6],
        last_accessed_at=row[7],
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/stats", response_model=StatsOut)
def get_stats(username: str, conn=Depends(db_instance.get_db)):
    with conn.cursor() as cur:
        # total
        cur.execute("SELECT COUNT(*) FROM clients WHERE owner_username = %s", (username,))
        total = cur.fetchone()[0]

        # last edited
        cur.execute(
            f"SELECT {ROW_COLS} FROM clients WHERE owner_username = %s ORDER BY last_edited_at DESC NULLS LAST LIMIT 1",
            (username,),
        )
        le_row = cur.fetchone()

        # last accessed
        cur.execute(
            f"SELECT {ROW_COLS} FROM clients WHERE owner_username = %s AND last_accessed_at IS NOT NULL ORDER BY last_accessed_at DESC NULLS LAST LIMIT 1",
            (username,),
        )
        la_row = cur.fetchone()

    return StatsOut(
        total=total,
        last_edited=_row_to_client(le_row) if le_row else None,
        last_accessed=_row_to_client(la_row) if la_row else None,
    )


@router.get("", response_model=list[ClientOut])
def list_clients(username: str, conn=Depends(db_instance.get_db)):
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT {ROW_COLS} FROM clients WHERE owner_username = %s ORDER BY last_edited_at DESC",
            (username,),
        )
        rows = cur.fetchall()
    return [_row_to_client(r) for r in rows]


@router.post("", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
def create_client(body: ClientCreate, username: str, conn=Depends(db_instance.get_db)):
    with conn.cursor() as cur:
        cur.execute(
            f"""
            INSERT INTO clients (owner_username, name, address, contact_number)
            VALUES (%s, %s, %s, %s)
            RETURNING {ROW_COLS}
            """,
            (username, body.name.strip(), body.address, body.contact_number),
        )
        row = cur.fetchone()
    conn.commit()
    return _row_to_client(row)


@router.get("/{client_id}", response_model=ClientOut)
def get_client(client_id: int, username: str, conn=Depends(db_instance.get_db)):
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT {ROW_COLS} FROM clients WHERE id = %s AND owner_username = %s",
            (client_id, username),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Client not found.")
        # update last_accessed_at
        cur.execute(
            "UPDATE clients SET last_accessed_at = NOW() WHERE id = %s",
            (client_id,),
        )
    conn.commit()
    return _row_to_client(row)


@router.put("/{client_id}", response_model=ClientOut)
def update_client(client_id: int, body: ClientUpdate, username: str, conn=Depends(db_instance.get_db)):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM clients WHERE id = %s AND owner_username = %s",
            (client_id, username),
        )
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Client not found.")

        fields = {k: v for k, v in body.model_dump().items() if v is not None}
        if not fields:
            raise HTTPException(status_code=400, detail="No fields to update.")

        set_clause = ", ".join(f"{k} = %s" for k in fields)
        values = list(fields.values()) + [client_id]
        cur.execute(
            f"UPDATE clients SET {set_clause}, last_edited_at = NOW() WHERE id = %s RETURNING {ROW_COLS}",
            values,
        )
        row = cur.fetchone()
    conn.commit()
    return _row_to_client(row)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(client_id: int, username: str, conn=Depends(db_instance.get_db)):
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM clients WHERE id = %s AND owner_username = %s",
            (client_id, username),
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Client not found.")
    conn.commit()
