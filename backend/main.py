"""stalk. — FastAPI app (API only; frontend served by Vercel)."""
from __future__ import annotations

import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import database
from routers import stock, health
from routers import auth as auth_router
from routers import saved as saved_router
from routers import usage as usage_router
from services import nse_master as nse_master_svc

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("stalkthestock")

# Initialise DB before anything else
database.init_db()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Pre-load the NSE equity master in the background so search is snappy
    asyncio.create_task(asyncio.to_thread(nse_master_svc.load_master))
    yield


app = FastAPI(title="stalk.", version="1.0.0", lifespan=lifespan)


# ─── CORS ────────────────────────────────────────────────────────────────────
# Default to permissive for local dev. In prod set CORS_ORIGINS to a comma-
# separated list of allowed origins (e.g. "https://stalk.vercel.app").
_cors_env = os.getenv("CORS_ORIGINS", "*").strip()
_allowed_origins = ["*"] if _cors_env in ("", "*") else [o.strip() for o in _cors_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    try:
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s -> %s in %.1fms", request.method, request.url.path, response.status_code, elapsed_ms
        )
        return response
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.exception("%s %s failed in %.1fms: %s", request.method, request.url.path, elapsed_ms, e)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(health.router, prefix="")
app.include_router(stock.router, prefix="/api")
app.include_router(auth_router.router, prefix="/api/auth")
app.include_router(saved_router.router, prefix="/api/saved")
app.include_router(usage_router.router, prefix="/api/usage")


@app.get("/")
async def root():
    return {"service": "stalk.", "status": "ok", "frontend": "deployed separately on Vercel"}
