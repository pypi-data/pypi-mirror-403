"""FastAPI dashboard API for Marlo Postgres data."""

from __future__ import annotations

import asyncio
import os

from fastapi import FastAPI
from dotenv import load_dotenv

from marlo.api.dashboard.routes import agents, copilot, learnings, search, sessions, stats, tasks
from marlo.api.ingest.routes import router as ingest_router
from marlo.api.feedback.routes import router as feedback_router
from marlo.core.config.models import StorageConfig
from marlo.core.sentry import init_sentry
from marlo.runtime import register_llm_client
from marlo.runtime.clients.gemini import GeminiClient
from marlo.runtime.worker import load_worker_settings, run_worker
from marlo.storage.postgres.database import Database
from fastapi.middleware.cors import CORSMiddleware

def _database_url() -> str:
    for key in ("MARLO_DATABASE_URL", "DATABASE_URL"):
        value = os.getenv(key)
        if value:
            return value

    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")
    db_sslmode = os.getenv("DB_SSLMODE")

    if db_host and db_port and db_user and db_password and db_name:
        url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        if db_sslmode:
            url += f"?sslmode={db_sslmode}"
        return url

    raise RuntimeError("DATABASE_URL or DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME are required.")


def create_app() -> FastAPI:
    load_dotenv()
    init_sentry()
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://localhost:3000",
            "http://localhost:8080",
            "https://app.marshmallo.ai",
            "https://api.marshmallo.ai",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def startup() -> None:
        database_url = _database_url()
        config = StorageConfig(database_url=database_url, apply_schema_on_connect=False)
        database = Database(config)
        await database.connect()
        app.state.database = database
        app.state.pool = database._require_pool()
        register_llm_client(GeminiClient())
        try:
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
            checkpointer = AsyncPostgresSaver.from_conn_string(database_url)
            await checkpointer.setup()
            app.state.checkpointer = checkpointer
        except Exception:
            app.state.checkpointer = None
        if os.getenv("MARLO_REWARD_WORKER") == "1":
            worker_config, poll_seconds, batch_size = load_worker_settings(database_url)
            stop_event = asyncio.Event()
            app.state.reward_worker_stop = stop_event
            app.state.reward_worker_task = asyncio.create_task(
                run_worker(
                    worker_config,
                    poll_seconds=poll_seconds,
                    batch_size=batch_size,
                    stop_event=stop_event,
                )
            )

    @app.on_event("shutdown")
    async def shutdown() -> None:
        stop_event = getattr(app.state, "reward_worker_stop", None)
        worker_task = getattr(app.state, "reward_worker_task", None)
        if stop_event is not None:
            stop_event.set()
        if worker_task is not None:
            try:
                await asyncio.wait_for(worker_task, timeout=5.0)
            except asyncio.TimeoutError:
                worker_task.cancel()
                try:
                    await worker_task
                except asyncio.CancelledError:
                    pass
        database = getattr(app.state, "database", None)
        if database is not None:
            await database.disconnect()

    app.include_router(agents.router)
    app.include_router(copilot.router)
    app.include_router(sessions.router)
    app.include_router(stats.router)
    app.include_router(tasks.router)
    app.include_router(learnings.router)
    app.include_router(search.router)
    app.include_router(ingest_router)
    app.include_router(feedback_router)

    return app


app = create_app()
