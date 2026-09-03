"""Serverless Telegram Webhook and Mini App handler built for Vercel Python Functions."""

import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional, List
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.responses import HTMLResponse, FileResponse
import sys
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from pydantic import BaseModel
from telegram import Update
from telegram.ext import Application
from src.config import TELEGRAM_BOT_TOKEN, WEBHOOK_SECRET
from src.bot.handlers import register_handlers
from src.db.users import get_user_preferences, update_user_preferences, get_or_create_user
from src.db.jobs import get_matched_jobs_for_user, get_recent_job_listings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("webhook")

_application: Optional[Application] = None


async def get_bot_application() -> Application:
    """Initialize or return the singleton python-telegram-bot Application."""
    global _application
    if _application is None:
        if not TELEGRAM_BOT_TOKEN:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured.")
        _application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        register_handlers(_application)
        await _application.initialize()
        await _application.start()
        logger.info("Initialized bot Application for webhook processing")
    return _application


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown lifecycle."""
    yield
    global _application
    if _application:
        await _application.stop()
        await _application.shutdown()
        _application = None
        logger.info("Shutdown bot Application cleanly")


app = FastAPI(
    title="Career Fit Jobs Bot Webhook",
    lifespan=lifespan,
)


@app.get("/")
@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "ok", "service": "Career Fit Jobs Bot Webhook"}


@app.get("/app", response_class=HTMLResponse)
async def serve_mini_app():
    """Serve the Apple-designed Telegram Mini App."""
    html_path = Path(__file__).resolve().parent / "static" / "app.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Mini App not found")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


class PreferencesPayload(BaseModel):
    telegram_id: int
    preferences: List[str]


@app.get("/api/jobs")
async def get_jobs_feed(telegram_id: Optional[int] = None):
    """Retrieve job matches for a user, or recent vacancies if no ID is specified."""
    if telegram_id:
        prefs = get_user_preferences(telegram_id)
        if prefs:
            jobs = get_matched_jobs_for_user(prefs, limit=50)
            return {"jobs": jobs, "preferences": prefs, "matched": True}
    # Fallback to recent postings
    jobs = get_recent_job_listings(limit=40)
    return {"jobs": jobs, "preferences": [], "matched": False}


@app.get("/api/user-preferences")
async def get_preferences(telegram_id: int):
    """Retrieve saved preferences for a user in the Mini App."""
    prefs = get_user_preferences(telegram_id)
    return {"telegram_id": telegram_id, "preferences": prefs}


@app.post("/api/user-preferences")
async def save_preferences(payload: PreferencesPayload):
    """Save preferences submitted from the Mini App."""
    get_or_create_user(payload.telegram_id)
    success = update_user_preferences(payload.telegram_id, payload.preferences)
    return {"ok": success}


@app.post("/api/webhook")
@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Receive and process incoming Telegram webhook updates."""
    if WEBHOOK_SECRET:
        secret_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if secret_header != WEBHOOK_SECRET:
            logger.warning("Rejected webhook update: invalid secret token header.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid secret token",
            )

    try:
        data = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse incoming JSON payload: {e}")
        return Response(status_code=status.HTTP_400_BAD_REQUEST)

    try:
        application = await get_bot_application()
        update = Update.de_json(data, application.bot)
        if update:
            await application.process_update(update)
        return {"ok": True}
    except Exception as err:
        logger.error(f"Error processing Telegram update: {err}", exc_info=True)
        return {"ok": True, "error": str(err)}
