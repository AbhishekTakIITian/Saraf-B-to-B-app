"""
db.py — Database bootstrap for Dukan App B-To-B
-------------------------------------------------
Provides the `Database` class which handles:
  - Creating the PostgreSQL application database if absent
  - Creating the `login` table if absent
  - Seeding the default `admin` user
  - Exposing a FastAPI dependency (`get_db`) for per-request connections
  - Password hashing utilities

Usage:
    from common.db import Database

    db = Database()          # bootstrap runs in __init__
    dep = db.get_db          # pass to FastAPI Depends()
"""

from __future__ import annotations

import hashlib
import logging
import os
import secrets
from pathlib import Path
from typing import Generator

import psycopg2
from dotenv import load_dotenv
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT, connection as PGConnection

logger = logging.getLogger(__name__)

# Load backend/.env explicitly.  This is required because the database singleton
# is created during module import, before FastAPI or uvicorn can see cwd-relative
# environment files.
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH, override=False)


# ---------------------------------------------------------------------------
# Database class
# ---------------------------------------------------------------------------

class Database:
    """
    Encapsulates all PostgreSQL interactions for the Dukan App B-To-B backend.

    Responsibilities
    ----------------
    - Configuration: reads connection params from environment variables.
    - Bootstrap   : ensures the application DB and `login` table exist.
    - Seeding     : creates the default admin user on first run.
    - Dependency  : `get_db()` is a FastAPI generator dependency.
    - Hashing     : static helpers for password salt + SHA-256.
    """

    # ------------------------------------------------------------------
    # Construction & configuration
    # ------------------------------------------------------------------

    def __init__(self) -> None:
        """Load config from env-vars and run the full bootstrap sequence."""

        self._host:           str = os.getenv("DB_HOST",          "localhost")
        self._port:           int = int(os.getenv("DB_PORT",      "5432"))
        self._user:           str = os.getenv("DB_USER",          "postgres")
        self._password:       str = os.getenv("DB_PASSWORD",      "postgres")
        self._db_name:        str = os.getenv("DB_NAME",          "dukan_app")
        self._admin_username: str = os.getenv("ADMIN_USERNAME",   "admin")
        self._admin_password: str = os.getenv("ADMIN_PASSWORD",   "Admin@1234")

        self._bootstrap()

    def __repr__(self) -> str:
        return (
            f"Database(host={self._host!r}, port={self._port}, "
            f"db={self._db_name!r}, user={self._user!r})"
        )

    # ------------------------------------------------------------------
    # Private — connection factories
    # ------------------------------------------------------------------

    def _server_connection(self) -> PGConnection:
        """
        Return a connection to the PostgreSQL *server* (maintenance DB).
        Used only for DDL that must run outside a transaction (CREATE DATABASE).
        """
        return psycopg2.connect(
            host=self._host,
            port=self._port,
            user=self._user,
            password=self._password,
            dbname="postgres",
        )

    def _app_connection(self) -> PGConnection:
        """Return a connection to the application database."""
        return psycopg2.connect(
            host=self._host,
            port=self._port,
            user=self._user,
            password=self._password,
            dbname=self._db_name,
        )

    # ------------------------------------------------------------------
    # Private — bootstrap steps
    # ------------------------------------------------------------------

    def _ensure_database(self) -> None:
        """Create the application database if it does not already exist."""
        conn = self._server_connection()
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s",
                    (self._db_name,),
                )
                if cur.fetchone() is None:
                    cur.execute(f'CREATE DATABASE "{self._db_name}"')
                    logger.info("[DB] Database '%s' created.", self._db_name)
                else:
                    logger.info("[DB] Database '%s' already exists.", self._db_name)
        finally:
            conn.close()

    def _ensure_login_table(self) -> None:
        """
        Create the `login` table inside the application database if absent.

        Schema
        ------
        id         SERIAL PRIMARY KEY
        username   VARCHAR(100) UNIQUE NOT NULL
        password   VARCHAR(64)  NOT NULL   — SHA-256 hex digest
        salt       VARCHAR(32)  NOT NULL   — random per-user salt
        role       VARCHAR(20)  NOT NULL   — 'admin' | 'user'
        created_at TIMESTAMPTZ  NOT NULL   — auto-set to NOW()
        """
        conn = self._app_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS login (
                        id         SERIAL       PRIMARY KEY,
                        username   VARCHAR(100) NOT NULL UNIQUE,
                        password   VARCHAR(64)  NOT NULL,
                        salt       VARCHAR(32)  NOT NULL,
                        role       VARCHAR(20)  NOT NULL DEFAULT 'user'
                                       CHECK (role IN ('admin', 'user')),
                        created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
                    )
                """)
                logger.info("[DB] Table 'login' is ready.")
            conn.commit()
        finally:
            conn.close()

    def _seed_admin(self) -> None:
        """Insert the default admin user if no admin row exists yet."""
        conn = self._app_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM login WHERE username = %s",
                    (self._admin_username,),
                )
                if cur.fetchone()[0] == 0:
                    hashed, salt = self.hash_password(self._admin_password)
                    cur.execute(
                        """
                        INSERT INTO login (username, password, salt, role)
                        VALUES (%s, %s, %s, 'admin')
                        """,
                        (self._admin_username, hashed, salt),
                    )
                    logger.warning(
                        "[DB] Admin user '%s' created — CHANGE THE DEFAULT "
                        "PASSWORD BEFORE DEPLOYING TO PRODUCTION!",
                        self._admin_username,
                    )
                else:
                    logger.info("[DB] Admin user '%s' already exists.", self._admin_username)
            conn.commit()
        finally:
            conn.close()

    def _ensure_clients_table(self) -> None:
        """Create the `clients` table inside the application database if absent."""
        conn = self._app_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS clients (
                        id               SERIAL PRIMARY KEY,
                        owner_username   VARCHAR(100) NOT NULL
                                         REFERENCES login(username) ON DELETE CASCADE,
                        name             VARCHAR(200) NOT NULL,
                        address          TEXT,
                        contact_number   VARCHAR(30),
                        created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        last_edited_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        last_accessed_at TIMESTAMPTZ
                    )
                """)
                logger.info("[DB] Table 'clients' is ready.")
            conn.commit()
        finally:
            conn.close()

    def _bootstrap(self) -> None:
        """Run all initialisation steps in order."""
        logger.info("[DB] Starting database bootstrap …")
        self._ensure_database()
        self._ensure_login_table()
        self._seed_admin()
        self._ensure_clients_table()
        logger.info("[DB] Bootstrap complete. %r", self)

    # ------------------------------------------------------------------
    # Public — password utilities (static, no DB needed)
    # ------------------------------------------------------------------

    @staticmethod
    def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
        """
        Hash *password* with an optional *salt* using SHA-256.

        Parameters
        ----------
        password : plain-text password
        salt     : hex salt string; generated randomly when omitted

        Returns
        -------
        (hashed_password, salt) — both are hex strings
        """
        if salt is None:
            salt = secrets.token_hex(16)
        hashed = hashlib.sha256((salt + password).encode()).hexdigest()
        return hashed, salt

    @staticmethod
    def verify_password(plain: str, salt: str, stored_hash: str) -> bool:
        """
        Return True if *plain* matches *stored_hash* when hashed with *salt*.
        """
        candidate = hashlib.sha256((salt + plain).encode()).hexdigest()
        return candidate == stored_hash

    # ------------------------------------------------------------------
    # Public — FastAPI dependency
    # ------------------------------------------------------------------

    def get_db(self) -> Generator[PGConnection, None, None]:
        """
        FastAPI generator dependency — yields one connection per request
        and guarantees it is closed when the request finishes.

        Usage::

            from fastapi import Depends
            from common.db import db_instance

            @router.get("/something")
            def handler(conn=Depends(db_instance.get_db)):
                with conn.cursor() as cur:
                    cur.execute("SELECT ...")
        """
        conn = self._app_connection()
        try:
            yield conn
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# Module-level singleton — import and use this everywhere
# ---------------------------------------------------------------------------

db_instance = Database()
