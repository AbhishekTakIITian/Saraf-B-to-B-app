"""
db_utils.py — Database utility functions for managing clients.
"""
import json

from fastapi import HTTPException

from common.constants import ROW_COLS
from common.models import (
    ClientCreate,
    ClientOut,
    ClientUpdate,
    CompleteDataEntryPayload,
    CreateDataEntryPayload,
    GetClientDataEntryResponse,
    StatsOut,
    UpdateDataEntryPayload,
)
from utils.utils import get_current_timestamp


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _row_to_client(row: tuple | list | None) -> ClientOut:
    """Map a database row tuple to a ClientOut Pydantic model."""
    if not row:
        raise ValueError("Cannot convert empty row to ClientOut.")
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


def get_all_clients_stats(username: str, conn) -> StatsOut:
    """Return total count, last edited client, and last accessed client for a given username."""
    with conn.cursor() as cur:
        # total
        cur.execute("SELECT COUNT(*) FROM clients WHERE owner_username = %s", (username,))
        total = cur.fetchone()[0]

        # last edited
        cur.execute(
            (
                f"SELECT {ROW_COLS} FROM clients WHERE owner_username = %s "
                "ORDER BY last_edited_at DESC NULLS LAST LIMIT 1"
            ),
            (username,),
        )
        le_row = cur.fetchone()

        # last accessed
        cur.execute(
            (
                f"SELECT {ROW_COLS} FROM clients WHERE owner_username = %s AND last_accessed_at "
                "IS NOT NULL ORDER BY last_accessed_at DESC NULLS LAST LIMIT 1"
            ),
            (username,),
        )
        la_row = cur.fetchone()

    return StatsOut(
        total=total,
        last_edited=_row_to_client(le_row) if le_row else None,
        last_accessed=_row_to_client(la_row) if la_row else None,
    )


def list_all_clients(username: str, conn) -> list[ClientOut]:
    """Return a list of all clients for a given username, ordered by last_edited_at descending."""
    with conn.cursor() as cur:
        cur.execute(
            (
                f"SELECT {ROW_COLS} FROM clients "
                "WHERE owner_username = %s ORDER BY last_edited_at DESC"
            ),
            (username,),
        )
        rows = cur.fetchall()
    return [_row_to_client(r) for r in rows]


def create_client_db(body: ClientCreate, username: str, conn) -> ClientOut:
    """Create a new client for a given username."""
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


def get_client_by_id(client_id: int, username: str, conn) -> ClientOut:
    """Retrieve a client by ID for a given username. Updates last_accessed_at."""
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


def update_client_db(client_id: int, body: ClientUpdate, username: str, conn) -> ClientOut:
    """Update a client by ID for a given username."""
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
            (
                f"UPDATE clients SET {set_clause}, last_edited_at = NOW() "
                f"WHERE id = %s RETURNING {ROW_COLS}"
            ),
            values,
        )
        row = cur.fetchone()
    conn.commit()
    return _row_to_client(row)


def delete_client_db(client_id: int, username: str, conn) -> dict[str, str]:
    """Delete a client by ID for a given username."""
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM clients WHERE id = %s AND owner_username = %s",
            (client_id, username),
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Client not found.")
    conn.commit()
    return {"message": "Client deleted successfully."}

def create_client_data_entry_db(
    client_id: int,
    body: CreateDataEntryPayload,
    username: str,
    conn,
) -> dict[str, str]:
    """Create a new data entry for a specific client. Sets date_created automatically."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM clients WHERE id = %s AND owner_username = %s",
            (client_id, username),
        )
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Client not found.")

        data = {
            "number": body.number,
            "jwellery_value": body.jwellery_value,
            "description": body.description,
            "date_created": get_current_timestamp(),
            "date_updated": None,
            "date_completed": None,
            "final_value": None,
        }
        cur.execute(
            """
            INSERT INTO client_data (client_id, data)
            VALUES (%s, %s)
            """,
            (client_id, json.dumps(data)),
        )
    conn.commit()
    return {"message": "Data entry created successfully."}


def update_client_data_entry_db(
    client_id: int,
    entry_id: int,
    body: UpdateDataEntryPayload,
    username: str,
    conn,
) -> dict[str, str]:
    """
    Update a data entry — 
    updates fields and sets date_updated. If final_value is provided, sets date_completed.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM clients WHERE id = %s AND owner_username = %s",
            (client_id, username),
        )
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Client not found.")

        cur.execute(
            "SELECT data FROM client_data WHERE id = %s AND client_id = %s",
            (entry_id, client_id),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Data entry not found.")

        existing: dict = row[0] if isinstance(row[0], dict) else json.loads(row[0])
        if body.number is not None:
            existing["number"] = body.number
        if body.jwellery_value is not None:
            existing["jwellery_value"] = body.jwellery_value
        if body.description is not None:
            existing["description"] = body.description
        if body.final_value is not None:
            existing["final_value"] = body.final_value
            if not existing.get("date_completed"):
                existing["date_completed"] = get_current_timestamp()

        existing["date_updated"] = get_current_timestamp()

        cur.execute(
            "UPDATE client_data SET data = %s WHERE id = %s",
            (json.dumps(existing), entry_id),
        )
    conn.commit()
    return {"message": "Data entry updated successfully."}


def complete_client_data_entry_db(
    client_id: int,
    entry_id: int,
    body: CompleteDataEntryPayload,
    username: str,
    conn,
) -> dict[str, str]:
    """Complete a data entry — sets date_completed and final_value, updates date_updated."""
    update_payload = UpdateDataEntryPayload(final_value=body.final_value)
    return update_client_data_entry_db(client_id, entry_id, update_payload, username, conn)


def delete_client_data_entry_db(
    client_id: int,
    entry_id: int,
    username: str,
    conn,
) -> dict[str, str]:
    """Delete a data entry for a specific client."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM clients WHERE id = %s AND owner_username = %s",
            (client_id, username),
        )
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Client not found.")

        cur.execute(
            "DELETE FROM client_data WHERE id = %s AND client_id = %s",
            (entry_id, client_id),
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Data entry not found.")
    conn.commit()
    return {"message": "Data entry deleted successfully."}

def get_client_data_db(
    client_id: int,
    username: str,
    conn,
) -> list[GetClientDataEntryResponse]:
    """Retrieve all data entries for a specific client."""
    with conn.cursor() as cur:
        # Check if the client exists and belongs to the user
        cur.execute(
            "SELECT id FROM clients WHERE id = %s AND owner_username = %s",
            (client_id, username),
        )
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Client not found.")

        # Explicit column selection avoids brittle index assumptions
        cur.execute(
            """
            SELECT id, client_id, data
            FROM client_data
            WHERE client_id = %s
            ORDER BY created_at DESC
            """,
            (client_id,),
        )
        rows = cur.fetchall()

    data_entries: list[GetClientDataEntryResponse] = []
    for row in rows:
        payload = row[2] if isinstance(row[2], dict) else json.loads(row[2])
        data_entries.append(
            GetClientDataEntryResponse(
                id=row[0],
                client_id=row[1],
                **payload,
            )
        )
    return data_entries
