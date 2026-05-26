"""
Analytics Service — Service 4
AI-powered analytics using Gemini API (via direct REST calls).
Generates post-mortem reports, clusters incidents, and predicts recurrence.
"""
import json

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.incident import Incident
from app.models.postmortem import PostMortem
from app.events.contracts import EventType
from app.events.subscriber import register_handler

logger = structlog.get_logger(__name__)
settings = get_settings()

# Models to try in order (cheapest/most available first)
GEMINI_MODELS = [
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
]
GEMINI_REST_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


async def _call_gemini(prompt: str) -> str:
    """
    Call Gemini REST API directly via httpx.
    Tries multiple models in order until one succeeds.
    Returns the response text.
    """
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured")

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 2048,
        },
    }

    last_error = None
    async with httpx.AsyncClient(timeout=60.0) as client:
        for model in GEMINI_MODELS:
            url = f"{GEMINI_REST_BASE}/{model}:generateContent?key={settings.GEMINI_API_KEY}"
            try:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                elif resp.status_code == 429:
                    # Quota exhausted — try next model
                    last_error = f"Model {model} quota exhausted (429)"
                    await logger.awarning("Gemini quota exhausted, trying next model", model=model)
                    continue
                elif resp.status_code == 404:
                    last_error = f"Model {model} not found (404)"
                    continue
                else:
                    last_error = f"Model {model} returned HTTP {resp.status_code}: {resp.text[:200]}"
                    continue
            except httpx.TimeoutException:
                last_error = f"Model {model} timed out"
                continue
            except Exception as e:
                last_error = f"Model {model} error: {str(e)}"
                continue

    raise RuntimeError(f"All Gemini models failed. Last error: {last_error}")


class AnalyticsService:
    """AI-powered incident analytics and post-mortem generation."""

    def __init__(self, db: AsyncSession):
        self.db = db

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

            response_text = await _call_gemini(prompt)

            # Parse JSON from response
            response_text = response_text.strip()
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
                ai_model="gemini-via-rest",
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
        """Get AI-generated insights from incident patterns.
        Falls back to smart rule-based analysis when Gemini quota is exhausted.
        """
        clusters = await self.get_incident_clusters()

        if not settings.GEMINI_API_KEY:
            return {
                "insights": self._generate_statistical_insights(clusters),
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
            response_text = await _call_gemini(prompt)
            response_text = response_text.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("\n", 1)[1]
                response_text = response_text.rsplit("```", 1)[0]

            insights = json.loads(response_text)
            return {"insights": insights, "clusters": clusters}
        except Exception as e:
            err_msg = str(e)
            await logger.awarning("Gemini unavailable, using statistical insights", error=err_msg[:200])
            # Graceful degradation: generate rule-based insights from real data
            return {
                "insights": self._generate_statistical_insights(clusters),
                "clusters": clusters,
            }

    def _generate_statistical_insights(self, clusters: dict) -> list:
        """Generate rule-based insights from statistical analysis when AI is unavailable."""
        insights = []
        total = clusters.get("total_analyzed", 0)
        sev_dist = clusters.get("severity_distribution", {})
        status_dist = clusters.get("status_distribution", {})
        avg_mttr = clusters.get("avg_mttr_by_severity", {})
        top_tags = clusters.get("top_tags", [])
        peak_hour = clusters.get("peak_hour")

        if total == 0:
            return [{"insight": "No incidents to analyze", "severity": "low",
                     "recommendation": "System is running normally. Continue monitoring."}]

        # Insight 1: Critical incident rate
        p1_count = sev_dist.get("P1", 0)
        p2_count = sev_dist.get("P2", 0)
        critical_pct = round((p1_count + p2_count) / total * 100, 1) if total > 0 else 0
        if critical_pct > 30:
            insights.append({
                "insight": f"{critical_pct}% of incidents are high severity (P1/P2 = {p1_count + p2_count} incidents)",
                "severity": "critical",
                "recommendation": "Immediate infrastructure review needed. High critical incident rate suggests systemic issues. Conduct root cause analysis and implement proactive monitoring alerts."
            })
        elif critical_pct > 15:
            insights.append({
                "insight": f"Elevated critical incident rate: {critical_pct}% are P1/P2 ({p1_count + p2_count} of {total} incidents)",
                "severity": "high",
                "recommendation": "Review on-call escalation procedures and add circuit breakers for high-frequency failure points. Consider chaos engineering to identify weaknesses proactively."
            })
        else:
            insights.append({
                "insight": f"Healthy severity distribution: only {critical_pct}% critical incidents ({p1_count + p2_count} of {total})",
                "severity": "low",
                "recommendation": "Maintain current monitoring coverage. Focus on reducing P3/P4 incidents to keep operational load manageable."
            })

        # Insight 2: MTTR analysis
        if avg_mttr:
            slowest_sev = max(avg_mttr, key=lambda k: avg_mttr[k] or 0)
            slowest_mins = round((avg_mttr[slowest_sev] or 0) / 60, 1)
            p1_mttr_mins = round((avg_mttr.get("P1", 0) or 0) / 60, 1)

            if p1_mttr_mins > 60:
                insights.append({
                    "insight": f"P1 MTTR is {p1_mttr_mins} minutes — exceeding 1-hour SLA threshold",
                    "severity": "high",
                    "recommendation": f"P1 resolution is taking {p1_mttr_mins:.0f} min on average. Implement automated runbooks, improve on-call response with paging escalation, and establish dedicated war-room protocols for critical incidents."
                })
            elif slowest_mins > 120:
                insights.append({
                    "insight": f"{slowest_sev} incidents average {slowest_mins} minutes to resolve",
                    "severity": "medium",
                    "recommendation": f"Mean time to resolution for {slowest_sev} is {slowest_mins:.0f} minutes. Investigate bottlenecks in the resolution workflow — consider pre-written runbooks and automated remediation scripts."
                })
            else:
                insights.append({
                    "insight": f"Resolution times within acceptable range (worst: {slowest_sev} at {slowest_mins:.0f} min avg)",
                    "severity": "low",
                    "recommendation": "Good MTTR performance. Document successful resolution patterns as runbooks to maintain this benchmark as system complexity grows."
                })

        # Insight 3: Recurring problem areas (top tags)
        if top_tags and len(top_tags) >= 2:
            top1 = top_tags[0]
            top2 = top_tags[1]
            insights.append({
                "insight": f"Top recurring problem areas: '{top1['tag']}' ({top1['count']} incidents), '{top2['tag']}' ({top2['count']} incidents)",
                "severity": "medium",
                "recommendation": f"Components tagged '{top1['tag']}' and '{top2['tag']}' are high-frequency failure points. Prioritize stability improvements, add dedicated health checks, and consider ownership reviews for these services."
            })

        # Insight 4: Peak hour clustering
        if peak_hour is not None:
            peak_next = (peak_hour + 1) % 24
            is_business_hours = 8 <= peak_hour <= 18
            if is_business_hours:
                insights.append({
                    "insight": f"Peak incident window is {peak_hour:02d}:00–{peak_next:02d}:00 UTC (business hours overlap)",
                    "severity": "medium",
                    "recommendation": "Incidents peak during business hours — likely correlated with deployment activity or peak user traffic. Enforce deployment freeze windows during high-traffic periods and increase monitoring sensitivity during these hours."
                })
            else:
                insights.append({
                    "insight": f"Peak incident window is {peak_hour:02d}:00–{peak_next:02d}:00 UTC (off-hours)",
                    "severity": "medium",
                    "recommendation": "Off-hours peak suggests batch jobs, scheduled tasks, or reduced oversight are contributing factors. Review scheduled job configurations and ensure on-call coverage is adequately staffed for this window."
                })

        # Insight 5: Open/unresolved incidents
        open_count = status_dist.get("open", 0) + status_dist.get("acknowledged", 0) + status_dist.get("investigating", 0)
        if open_count > 0 and total > 0:
            open_pct = round(open_count / total * 100, 1)
            if open_pct > 20:
                insights.append({
                    "insight": f"{open_count} incidents ({open_pct}%) are still active/unresolved",
                    "severity": "high",
                    "recommendation": "High backlog of unresolved incidents. Conduct a triage session to close stale incidents, reassign unowned ones, and implement SLA auto-escalation for incidents open beyond their severity threshold."
                })

        return insights[:5]  # Cap at 5 insights


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
