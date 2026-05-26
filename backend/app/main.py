"""
FastAPI application entry point.
Registers all routes, middleware, event handlers, and lifecycle hooks.
"""
import asyncio
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.routes import auth, incidents, websocket, analytics
from app.events.subscriber import start_subscriber
from app.events.publisher import close_publisher
from app.services.notification_service import register_notification_handlers
from app.services.escalation_service import register_escalation_handlers, cancel_all_timers
from app.services.analytics_service import register_analytics_handlers
from app.cache.redis_cache import register_cache_handlers, close_cache

settings = get_settings()

# Configure structured logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer() if settings.DEBUG else structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(0),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown hooks."""
    # === STARTUP ===
    logger.info("Starting Incident Management System", version=settings.APP_VERSION)

    # Initialize database tables
    await init_db()
    logger.info("Database initialized")

    # Register event handlers
    register_notification_handlers()
    register_escalation_handlers()
    register_analytics_handlers()
    register_cache_handlers()
    logger.info("Event handlers registered")

    # Start Redis Pub/Sub subscriber in background
    subscriber_task = asyncio.create_task(start_subscriber())
    logger.info("Event subscriber started")

    yield

    # === SHUTDOWN ===
    logger.info("Shutting down...")
    cancel_all_timers()
    subscriber_task.cancel()
    try:
        await subscriber_task
    except asyncio.CancelledError:
        pass
    await close_publisher()
    await close_cache()
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Event-driven Incident Management System with real-time dashboard, "
                "race condition handling, and AI-powered analytics.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(incidents.router)
app.include_router(websocket.router)
app.include_router(analytics.router)


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "healthy",
    }


@app.get("/health", tags=["Health"])
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG,
    }
