"""FormCheck FastAPI app."""
from __future__ import annotations

import logging
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from routers import stock, health

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("stalkthestock")

app = FastAPI(title="Stalk the Stock", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


# Serve frontend (sibling directory) so the user can hit one URL.
_FRONTEND_DIR = (Path(__file__).resolve().parent.parent / "frontend")
if _FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(_FRONTEND_DIR)), name="static")
    _ASSETS_DIR = _FRONTEND_DIR / "assets"
    if _ASSETS_DIR.exists():
        app.mount("/assets", StaticFiles(directory=str(_ASSETS_DIR)), name="assets")

    # Tell the browser never to cache these — dev iteration shouldn't fight stale assets.
    _NO_CACHE_HEADERS = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
    }

    @app.get("/")
    async def root():
        return FileResponse(str(_FRONTEND_DIR / "index.html"), headers=_NO_CACHE_HEADERS)

    @app.get("/style.css")
    async def style_css():
        return FileResponse(str(_FRONTEND_DIR / "style.css"), headers=_NO_CACHE_HEADERS)

    @app.get("/app.js")
    async def app_js():
        return FileResponse(str(_FRONTEND_DIR / "app.js"), headers=_NO_CACHE_HEADERS)
else:
    @app.get("/")
    async def root():
        return {"service": "Stalk the Stock", "status": "ok", "frontend": "not found"}
