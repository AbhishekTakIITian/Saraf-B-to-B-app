"""
login.py — Authentication router
----------------------------------
POST /login    — verify credentials against the DB
POST /users    — add a new user (admin only)
"""

import logging
import os
import sys

from fastapi import APIRouter, Depends, HTTPException, status

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import the shared Database singleton
from common.db import db_instance  # noqa: E402
from common.models import LoginRequest, NewUserRequest  # noqa: E402

logger = logging.getLogger(__name__)
router = APIRouter(tags=["auth"])


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/login")
async def login(body: LoginRequest, conn=Depends(db_instance.get_db)):
    """Validate credentials against the DB; returns role on success or 401."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT password, salt, role FROM login WHERE username = %s",
            (body.username,),
        )
        row = cur.fetchone()

    if row is None or not db_instance.verify_password(body.password, row[1], row[0]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    return {"message": "Login successful", "role": row[2]}


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def add_user(
    body: NewUserRequest,
    requesting_user: str,          # calling admin's username (query param)
    conn=Depends(db_instance.get_db),
):
    """
    Add a new user to the login table.
    Only users with role='admin' may call this endpoint.

    Pass the calling user's username as the `requesting_user` query parameter.
    (In production replace this with a JWT / session-based identity check.)
    """
    with conn.cursor() as cur:
        # -- Permission check: only admins can add users -------------------
        cur.execute(
            "SELECT role FROM login WHERE username = %s",
            (requesting_user,),
        )
        caller = cur.fetchone()

        if caller is None or caller[0] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can add new users.",
            )

        # -- Role validation -----------------------------------------------
        if body.role not in ("admin", "user"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="role must be 'admin' or 'user'.",
            )

        # -- Duplicate check -----------------------------------------------
        cur.execute(
            "SELECT 1 FROM login WHERE username = %s",
            (body.username,),
        )
        if cur.fetchone():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Username '{body.username}' already exists.",
            )

        # -- Insert new user -----------------------------------------------
        hashed, salt = db_instance.hash_password(body.password)
        cur.execute(
            "INSERT INTO login (username, password, salt, role) VALUES (%s, %s, %s, %s)",
            (body.username, hashed, salt, body.role),
        )

    conn.commit()
    logger.info(
        "New user '%s' (role=%s) added by '%s'.",
        body.username, body.role, requesting_user,
    )
    return {
        "message": f"User '{body.username}' created successfully.",
        "role": body.role,
    }
