"""
db_utils.py — Database utility functions for managing clients.
"""

from fastapi import HTTPException

from common.constants import ROW_COLS
from common.models import ClientCreate, ClientOut, ClientUpdate, StatsOut


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


# Backward compatibility aliases
create_client = create_client_db
update_client = update_client_db
delete_client = delete_client_db
