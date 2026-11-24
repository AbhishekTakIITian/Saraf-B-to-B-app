# Dukan App B-To-B

A full-stack B2B management portal built with **FastAPI** (Python) on the backend and **Angular 21** on the frontend, backed by **PostgreSQL**.

---

## Project Structure

```
Dukan App B-To-B/
├── backend/
│   ├── api.py                  # FastAPI application entry point
│   ├── requirements.txt        # Python dependencies
│   ├── .env.example            # Environment variable template
│   ├── common/
│   │   └── db.py               # Database class — bootstrap, hashing, FastAPI dep
│   └── routers/
│       └── login.py            # Auth routes: POST /login, POST /users
│
├── frontend/
│   └── dukan-app-saraf/        # Angular 21 app
│       └── src/
│           └── app/
│               ├── services.ts         # ApiService — all HTTP calls to backend
│               ├── login/
│               │   ├── login.ts        # Login component logic
│               │   ├── login.html      # Login template
│               │   └── login.scss      # Login styles
│               ├── app.ts              # Root component
│               ├── app.config.ts       # Angular providers (HttpClient, Router)
│               └── app.routes.ts       # Route definitions
│
├── launcher.pyw                # Optional launcher script
└── README.md
```

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.11+ | [python.org](https://python.org) |
| PostgreSQL | 14+ | [postgresql.org](https://postgresql.org) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) |
| npm | 9+ | Bundled with Node.js |
| Angular CLI | 21 | `npm install -g @angular/cli` |

---

## Local Setup

### 1 — Clone / open the project

```bash
cd "d:\WebDev\Dukan App B-To-B"
```

---

### 2 — Backend

#### 2a. Create & activate the virtual environment

```bash
# Create (only needed once)
python -m venv .venv

# Activate — Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Activate — Windows CMD
.\.venv\Scripts\activate.bat
```

#### 2b. Install Python dependencies

```bash
pip install -r backend/requirements.txt
```

#### 2c. Configure environment variables

```bash
# Copy the template
copy backend\.env.example backend\.env
```

Then edit `backend/.env` and set your PostgreSQL password:

```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=YOUR_POSTGRES_PASSWORD
DB_NAME=dukan_app

ADMIN_USERNAME=admin
ADMIN_PASSWORD=Admin@1234   # ← change this!
```

> [!IMPORTANT]
> Make sure the PostgreSQL service is **running** before starting the backend.
> On Windows: `Start-Service postgresql*`

#### 2d. Start the backend

```bash
cd backend

# Load .env automatically via uvicorn (python-dotenv reads it)
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

On first run the backend will:
- Create the `dukan_app` database if absent
- Create the `login` table if absent
- Insert the default **admin** user
- Create the `clients` table with foreign key `owner_username -> login(username)`

> API docs available at → **http://localhost:8000/docs**

---

### 3 — Frontend

```bash
cd frontend/dukan-app-saraf

# Install dependencies (only needed once)
npm install

# Start the dev server
npm start
```
Open chrome cors disabled : 
```
"C:\Program Files\Google\Chrome\Application\chrome.exe" --user-data-dir="C:\chrome-dev-data" --disable-web-security
```
The app will be available at → **http://localhost:4200**

---

## Default Login

| Field | Value |
|-------|-------|
| Username | `admin` |
| Password | `Admin@1234` |

> [!CAUTION]
> Change the admin password immediately in `.env` before deploying to any shared or production environment.

---

## API Reference

### `POST /login`
Authenticate a user.

**Request body:**
```json
{ "username": "admin", "password": "Admin@1234" }
```

**Response (200):**
```json
{ "message": "Login successful", "role": "admin" }
```

**Error (401):** Invalid credentials.

---

### `POST /users?requesting_user={admin_username}`
Add a new user. Requires the calling user to have role `admin`.

**Request body:**
```json
{ "username": "newuser", "password": "Secret@123", "role": "user" }
```

**Response (201):**
```json
{ "message": "User 'newuser' created successfully.", "role": "user" }
```

**Errors:** `401` Unauthorized · `403` Forbidden · `409` Username taken.

---

### `GET /clients?username={username}`
Fetch all clients belonging exclusively to the specified user.

---

### `GET /clients/stats?username={username}`
Returns count of clients, last edited client, and last accessed client for the specified user.

---

### `POST /clients?username={username}`
Create a new client record for the user.

**Request body:**
```json
{
  "name": "Acme Traders",
  "address": "123 Market Street",
  "contact_number": "+91 9876543210"
}
```

---

### `GET /clients/{client_id}?username={username}`
Fetch single client details and automatically record `last_accessed_at` timestamp.

---

### `DELETE /clients/{client_id}?username={username}`
Delete a client record owned by the user.

---

## Running Both Together (Quick Start)

Open **two** terminal windows:

```bash
# Terminal 1 — Backend
cd "d:\WebDev\Dukan App B-To-B\backend"
..\.venv\Scripts\uvicorn api:app --reload --port 8000

# Terminal 2 — Frontend
cd "d:\WebDev\Dukan App B-To-B\frontend\dukan-app-saraf"
npm start
```

Then open **http://localhost:4200** in your browser.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Angular 21 (standalone components, signals) |
| Styling | SCSS with CSS custom properties |
| HTTP Client | Angular `HttpClient` via `provideHttpClient()` |
| Backend | FastAPI 0.165 + Uvicorn |
| Database | PostgreSQL 14+ via psycopg2 |
| Auth | SHA-256 + random salt (upgrade to bcrypt/JWT for production) |

## Build frontend 

``` shell
cd frontend/dukan-app-saraf
npm run build dukan-app-saraf -- --base-href ./
```

## To launch app view in dev
```bash
.\.venv\Scripts\python.exe launcher.pyw
```

## Pyinstaller script to build app

```powershell
pyinstaller --noconsole --onedir --noconfirm `
  --name "Saraf-Moneylending-App" `
  --icon "frontend\dukan-app-saraf\public\favicon.ico" `
  --add-data "backend;system" `
  --add-data "frontend/dukan-app-saraf/dist/dukan-app-saraf/browser;dist" `
  --hidden-import "uvicorn.logging" `
  --hidden-import "uvicorn.loops" `
  --hidden-import "uvicorn.loops.auto" `
  --hidden-import "uvicorn.protocols" `
  --hidden-import "uvicorn.protocols.http" `
  --hidden-import "uvicorn.protocols.http.auto" `
  --hidden-import "uvicorn.protocols.websockets" `
  --hidden-import "uvicorn.protocols.websockets.auto" `
  --hidden-import "uvicorn.lifespans" `
  --hidden-import "uvicorn.lifespans.on" `
  --hidden-import "uvicorn.lifespans.off" `
  --hidden-import "psycopg2" `
  --hidden-import "dotenv" `
  --collect-all "fastapi" `
  --collect-all "starlette" `
  --collect-all "pydantic" `
  --collect-all "pydantic_core" `
  --collect-all "uvicorn" `
  --collect-all "anyio" `
  launcher.pyw
```