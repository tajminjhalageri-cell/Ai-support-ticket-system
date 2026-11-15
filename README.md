# AI-Powered Customer Support Ticket Management System

Phase 1 provides a persistent ticket-management API. It uses SQLite by default
so the service runs locally without a separate database server. PostgreSQL
support, including its driver and migration workflow, is planned for Phase 2.

## Run locally

From this directory, create and activate a virtual environment, then install
the dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the interactive API documentation.
Ticket records are stored in `ticket_system.db` unless `DATABASE_URL` is set.

## Open the dashboard

Keep the backend running, then open a second PowerShell terminal in the
project directory and serve the frontend files locally:

```powershell
cd frontend
python -m http.server 5500
```

Open `http://127.0.0.1:5500` in your browser. The dashboard connects to the
FastAPI server at `http://127.0.0.1:8000` and uses the existing ticket API.

## Ticket API

All ticket endpoints are under `/api/v1/tickets`:

- `POST /api/v1/tickets` creates a ticket.
- `GET /api/v1/tickets` lists tickets with `q`, `status`, `priority`,
  `sort_by`, `sort_order`, `skip`, and `limit` query parameters.
- `GET /api/v1/tickets/{ticket_id}` retrieves one ticket.
- `PATCH /api/v1/tickets/{ticket_id}` updates supplied fields.
- `DELETE /api/v1/tickets/{ticket_id}` deletes a ticket when a valid
  `X-Delete-API-Key` header is provided.

Deletion is disabled unless `TICKET_DELETE_API_KEY` is configured. This
temporary Phase 1 guard will be replaced by role-based JWT authorization in
Phase 3. Never commit `.env` or share the configured key.

## Tests

```powershell
python -m pytest
```

Tests use a separate in-memory SQLite database and do not call external
services.
