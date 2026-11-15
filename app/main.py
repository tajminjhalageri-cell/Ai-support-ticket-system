from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.tickets import router as tickets_router
from app.database import Base, engine
from app import models  # noqa: F401 - register ORM models before table creation

LOCAL_FRONTEND_ORIGINS = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="AI-Powered Customer Support Ticket Management System",
    version="0.1.0",
    description="Phase 1: persistent ticket management API.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=LOCAL_FRONTEND_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type"],
)


@app.get("/", tags=["Home"])
async def home():
    return {
        "message": "Welcome to the AI-Powered Customer Support Ticket Management System!",
        "status": "running",
        "version": "0.1.0",
        "documentation": "/docs",
        "available_endpoints": {
            "create_ticket": "POST /api/v1/tickets",
            "list_tickets": "GET /api/v1/tickets",
            "get_ticket": "GET /api/v1/tickets/{ticket_id}",
            "update_ticket": "PATCH /api/v1/tickets/{ticket_id}",
            "delete_ticket": "DELETE /api/v1/tickets/{ticket_id}",
        },
    }


app.include_router(tickets_router)