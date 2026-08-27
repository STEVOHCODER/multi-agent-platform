import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.modules.core import init_db, settings

# Import all module routers
from app.modules.auth import auth_router
from app.modules.workspace import workspace_router
from app.modules.agent import agent_router
from app.modules.skill import skill_router
from app.modules.conversation import conversation_router
from app.modules.conversation.webhook import router as webhook_router
from app.modules.settlement import settlement_router
from app.modules.knowledge import knowledge_router
from app.modules.audit import audit_router
from app.modules.messaging import messaging_router
from app.modules.billing import billing_router
from app.modules.worker import start_worker_loop

# Import models to register them with SQLAlchemy
from app.modules.models import *  # noqa

_worker_task = None


async def _start_worker():
    await start_worker_loop(interval_seconds=settings.poll_interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _worker_task
    init_db()
    _worker_task = asyncio.create_task(_start_worker())
    yield
    if _worker_task:
        _worker_task.cancel()


app = FastAPI(
    title="Multi-Agent AI Communication Platform",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Core modules ──────────────────────────────────────────────────
app.include_router(auth_router)           # /api/auth/*
app.include_router(workspace_router)      # /api/workspaces/*

# ── Agent system ──────────────────────────────────────────────────
app.include_router(agent_router)          # /api/agents/*
app.include_router(skill_router)          # /api/skills/*

# ── Conversations & channels ──────────────────────────────────────
app.include_router(conversation_router)   # /api/conversations/*
app.include_router(webhook_router)        # /api/webhooks/*

# ── Settlement & finance ──────────────────────────────────────────
app.include_router(settlement_router)     # /api/settlement/*

# ── Knowledge base ────────────────────────────────────────────────
app.include_router(knowledge_router)      # /api/knowledge/*

# ── Audit & observability ─────────────────────────────────────────
app.include_router(audit_router)          # /api/audit/*

# ── Legacy modules (backward compat) ─────────────────────────────
app.include_router(messaging_router)      # /api/messaging/*
app.include_router(billing_router)        # /api/billing/*


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "multi-agent-platform",
        "version": "3.0.0",
        "modules": [
            "auth", "workspace", "agent", "skill", "conversation",
            "settlement", "knowledge", "audit", "messaging", "billing", "worker",
        ],
    }
