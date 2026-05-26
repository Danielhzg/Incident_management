"""
Analytics routes — AI post-mortem and insight endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.postmortem import PostMortem
from app.schemas.postmortem import PostMortemResponse
from app.services.analytics_service import AnalyticsService
from app.auth.dependencies import get_current_user
from app.cache.redis_cache import cache_get, cache_set, _make_cache_key

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.post("/postmortem/{incident_id}", response_model=PostMortemResponse)
async def generate_postmortem(
    incident_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Generate an AI post-mortem report for a resolved incident."""
    service = AnalyticsService(db)
    postmortem = await service.generate_postmortem(incident_id)
    if not postmortem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    return PostMortemResponse.model_validate(postmortem)


@router.get("/postmortem/{incident_id}", response_model=list[PostMortemResponse])
async def get_postmortems(
    incident_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get all post-mortem reports for an incident."""
    result = await db.execute(
        select(PostMortem)
        .where(PostMortem.incident_id == incident_id)
        .order_by(PostMortem.created_at.desc())
    )
    postmortems = result.scalars().all()
    return [PostMortemResponse.model_validate(pm) for pm in postmortems]


@router.get("/clusters")
async def get_clusters(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get incident clustering analysis."""
    cache_key = _make_cache_key("analytics", "clusters")
    cached = await cache_get(cache_key)
    if cached:
        return cached

    service = AnalyticsService(db)
    clusters = await service.get_incident_clusters()
    await cache_set(cache_key, clusters, ttl=120)
    return clusters


@router.get("/insights")
async def get_insights(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get AI-generated insights from incident patterns."""
    cache_key = _make_cache_key("analytics", "insights")
    cached = await cache_get(cache_key)
    if cached:
        return cached

    service = AnalyticsService(db)
    insights = await service.get_ai_insights()
    await cache_set(cache_key, insights, ttl=300)
    return insights
