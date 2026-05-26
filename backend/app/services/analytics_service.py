"""
Analytics Service — Service 4
AI-powered analytics using Gemini 2.0 Flash.
Generates post-mortem reports, clusters incidents, and predicts recurrence.
"""
import json

import structlog
import google.generativeai as genai
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.incident import Incident
from app.models.postmortem import PostMortem
from app.events.contracts import EventType
from app.events.subscriber import register_handler

logger = structlog.get_logger(__name__)
settings = get_settings()


def _configure_genai():
    """Configure Gemini API client."""
    if settings.GEMINI_API_KEY:
        genai.configure(api_key=settings.GEMINI_API_KEY)


class AnalyticsService:
    """AI-powered incident analytics and post-mortem generation."""

    def __init__(self, db: AsyncSession):
        self.db = db
        _configure_genai()

    async def generate_postmortem(self, incident_id: int) -> PostMortem | None:
        """Generate an AI post-mortem report for a resolved incident."""
        result = await self.db.execute(
            select(Incident).where(Incident.id == incident_id)
        )
        incident = result.scalar_one_or_none()
        if not incident:
            return None

        # Build prompt with incident context
        ttr = None
        if incident.resolved_at and incident.created_at:
            ttr = (incident.resolved_at - incident.created_at).total_seconds()

        prompt = f"""You are an expert Site Reliability Engineer. Generate a detailed post-mortem report for the following production incident. Write in a professional, concise style.

## Incident Details
- **Title**: {incident.title}
- **Description**: {incident.description}
- **Severity**: {incident.severity.value}
- **Status**: {incident.status.value}
- **Created At**: {incident.created_at.isoformat() if incident.created_at else 'Unknown'}
- **Acknowledged At**: {incident.acknowledged_at.isoformat() if incident.acknowledged_at else 'N/A'}
- **Resolved At**: {incident.resolved_at.isoformat() if incident.resolved_at else 'N/A'}
- **Time to Resolve**: {f'{ttr:.0f} seconds ({ttr/60:.1f} minutes)' if ttr else 'N/A'}
- **Escalation Count**: {incident.escalation_count}
- **Tags**: {incident.tags or 'None'}

Please generate a post-mortem with the following sections. Return ONLY valid JSON:
{{
    "title": "Post-mortem title",
    "summary": "Executive summary (2-3 sentences)",
    "root_cause": "Detailed root cause analysis",
    "impact": "Impact assessment (users affected, duration, severity)",
    "timeline": "Chronological timeline of events",
    "action_items": "Concrete action items to prevent recurrence (numbered list)",
    "lessons_learned": "Key lessons learned"
}}"""

        try:
            if not settings.GEMINI_API_KEY:
                # Fallback: generate a template post-mortem without AI
                return await self._generate_template_postmortem(incident, ttr)

            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(prompt)

            # Parse JSON from response
            response_text = response.text.strip()
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("\n", 1)[1]
                response_text = response_text.rsplit("```", 1)[0]

            pm_data = json.loads(response_text)

            postmortem = PostMortem(
                incident_id=incident_id,
                title=pm_data.get("title", f"Post-mortem: {incident.title}"),
                summary=pm_data.get("summary", ""),
                root_cause=pm_data.get("root_cause", ""),
                impact=pm_data.get("impact", ""),
                timeline=pm_data.get("timeline", ""),
                action_items=pm_data.get("action_items", ""),
                lessons_learned=pm_data.get("lessons_learned"),
                generated_by_ai=True,
                ai_model="gemini-2.0-flash",
            )

            self.db.add(postmortem)
            await self.db.flush()
            await self.db.refresh(postmortem)

            await logger.ainfo(
                "AI post-mortem generated",
                incident_id=incident_id,
                postmortem_id=postmortem.id,
            )
            return postmortem

        except Exception as e:
            await logger.aerror("Failed to generate AI post-mortem", error=str(e), incident_id=incident_id)
            return await self._generate_template_postmortem(incident, ttr)

    async def _generate_template_postmortem(self, incident: Incident, ttr: float | None) -> PostMortem:
        """Generate a template post-mortem when AI is unavailable."""
        postmortem = PostMortem(
            incident_id=incident.id,
            title=f"Post-mortem: {incident.title}",
            summary=f"This is an auto-generated post-mortem template for incident '{incident.title}' "
                    f"(Severity: {incident.severity.value}). Please review and fill in details.",
            root_cause="[To be determined — please fill in the root cause analysis]",
            impact=f"Severity {incident.severity.value} incident. "
                   f"{'Escalated ' + str(incident.escalation_count) + ' time(s). ' if incident.escalation_count > 0 else ''}"
                   f"{'Time to resolve: ' + str(round(ttr / 60, 1)) + ' minutes.' if ttr else ''}",
            timeline=f"- {incident.created_at.isoformat() if incident.created_at else 'Unknown'}: Incident created\n"
                     f"- {incident.acknowledged_at.isoformat() if incident.acknowledged_at else 'N/A'}: Acknowledged\n"
                     f"- {incident.resolved_at.isoformat() if incident.resolved_at else 'N/A'}: Resolved",
            action_items="1. [Fill in action items]\n2. [Fill in action items]",
            lessons_learned="[Fill in lessons learned]",
            generated_by_ai=False,
            ai_model=None,
        )
        self.db.add(postmortem)
        await self.db.flush()
        await self.db.refresh(postmortem)
        return postmortem

    async def get_incident_clusters(self) -> dict:
        """Analyze incident patterns and return clustering insights."""
        # Get all incidents for analysis
        result = await self.db.execute(
            select(Incident).where(Incident.is_deleted.is_(False)).order_by(Incident.created_at.desc()).limit(200)
        )
        incidents = result.scalars().all()

        if not incidents:
            return {"clusters": [], "insights": "No incidents to analyze."}

        # Severity distribution
        severity_dist: dict[str, int] = {}
        status_dist: dict[str, int] = {}
        source_dist: dict[str, int] = {}
        tag_freq: dict[str, int] = {}
        hourly_dist = [0] * 24

        for inc in incidents:
            severity_dist[inc.severity.value] = severity_dist.get(inc.severity.value, 0) + 1
            status_dist[inc.status.value] = status_dist.get(inc.status.value, 0) + 1
            source_dist[inc.source] = source_dist.get(inc.source, 0) + 1

            if inc.tags:
                for tag in inc.tags.split(","):
                    tag = tag.strip().lower()
                    if tag:
                        tag_freq[tag] = tag_freq.get(tag, 0) + 1

            if inc.created_at:
                hourly_dist[inc.created_at.hour] += 1

        # Calculate MTTR per severity
        mttr_by_severity: dict[str, list[float]] = {}
        for inc in incidents:
            if inc.resolved_at and inc.created_at:
                sev = inc.severity.value
                ttr = (inc.resolved_at - inc.created_at).total_seconds()
                if sev not in mttr_by_severity:
                    mttr_by_severity[sev] = []
                mttr_by_severity[sev].append(ttr)

        avg_mttr = {}
        for sev, ttrs in mttr_by_severity.items():
            avg_mttr[sev] = round(sum(ttrs) / len(ttrs), 2) if ttrs else None

        # Top tags (potential problem areas)
        top_tags = sorted(tag_freq.items(), key=lambda x: x[1], reverse=True)[:10]

        # Peak hours
        peak_hour = hourly_dist.index(max(hourly_dist)) if any(hourly_dist) else None

        return {
            "total_analyzed": len(incidents),
            "severity_distribution": severity_dist,
            "status_distribution": status_dist,
            "source_distribution": source_dist,
            "avg_mttr_by_severity": avg_mttr,
            "top_tags": [{"tag": t, "count": c} for t, c in top_tags],
            "hourly_distribution": hourly_dist,
            "peak_hour": peak_hour,
        }

    async def get_ai_insights(self) -> dict:
        """Get AI-generated insights from incident patterns."""
        clusters = await self.get_incident_clusters()

        if not settings.GEMINI_API_KEY:
            return {
                "insights": "AI insights require a Gemini API key. Configure GEMINI_API_KEY to enable.",
                "clusters": clusters,
            }

        prompt = f"""You are an expert SRE analyst. Analyze the following incident data and provide actionable insights.

## Incident Data
- Total incidents analyzed: {clusters['total_analyzed']}
- Severity distribution: {json.dumps(clusters['severity_distribution'])}
- Status distribution: {json.dumps(clusters['status_distribution'])}
- Average MTTR by severity: {json.dumps(clusters['avg_mttr_by_severity'])}
- Top problem tags: {json.dumps(clusters['top_tags'])}
- Peak incident hour (UTC): {clusters['peak_hour']}

Provide 3-5 actionable insights as a JSON array:
[
    {{"insight": "description", "severity": "high/medium/low", "recommendation": "what to do"}}
]"""

        try:
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(prompt)
            response_text = response.text.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("\n", 1)[1]
                response_text = response_text.rsplit("```", 1)[0]

            insights = json.loads(response_text)
            return {"insights": insights, "clusters": clusters}
        except Exception as e:
            await logger.aerror("Failed to generate AI insights", error=str(e))
            return {"insights": "Failed to generate AI insights", "clusters": clusters}


# === Event Handler ===

async def handle_incident_resolved_for_analytics(data: dict):
    """Auto-generate post-mortem when an incident is resolved."""
    incident_id = data.get("incident_id")
    if not incident_id:
        return
    await logger.ainfo("Auto-generating post-mortem for resolved incident", incident_id=incident_id)
    # Note: This needs a DB session, so we create one
    from app.database import async_session_maker
    async with async_session_maker() as db:
        service = AnalyticsService(db)
        await service.generate_postmortem(incident_id)
        await db.commit()


def register_analytics_handlers():
    """Register analytics event handlers."""
    register_handler(EventType.INCIDENT_RESOLVED, handle_incident_resolved_for_analytics)
    logger.info("Analytics handlers registered")
