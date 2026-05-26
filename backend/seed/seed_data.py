"""
Seed script — populates the database with realistic sample data.
Generates seed users and 100 historical incidents.
"""
import asyncio
import random
from datetime import datetime, timedelta, timezone

from passlib.context import CryptContext

# We need to set env vars before importing app modules
import os
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@postgres:5432/incident_db")
os.environ.setdefault("REDIS_URL", "redis://redis:6379/0")

from app.database import async_session_maker, init_db
from app.models.user import User, UserRole, UserTier
from app.models.incident import Incident, IncidentSeverity, IncidentStatus

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Realistic incident data
INCIDENT_TEMPLATES = [
    {"title": "Database connection pool exhausted", "tags": "database,postgres,connection", "source": "monitoring"},
    {"title": "Payment gateway timeout (Stripe)", "tags": "payment,stripe,timeout", "source": "monitoring"},
    {"title": "API response time > 5s on /api/orders", "tags": "api,performance,orders", "source": "monitoring"},
    {"title": "Memory leak in user-service container", "tags": "memory,docker,user-service", "source": "monitoring"},
    {"title": "SSL certificate expiring in 24 hours", "tags": "ssl,certificate,security", "source": "monitoring"},
    {"title": "Redis cluster node down (node-3)", "tags": "redis,cluster,infrastructure", "source": "monitoring"},
    {"title": "CDN cache invalidation failure", "tags": "cdn,cache,cloudflare", "source": "webhook"},
    {"title": "Login endpoint returning 500 errors", "tags": "auth,login,error", "source": "monitoring"},
    {"title": "Disk usage > 90% on prod-db-primary", "tags": "disk,database,storage", "source": "monitoring"},
    {"title": "Elasticsearch indexing lag > 30 minutes", "tags": "search,elasticsearch,lag", "source": "monitoring"},
    {"title": "Load balancer health check failures", "tags": "loadbalancer,nginx,health", "source": "monitoring"},
    {"title": "Kafka consumer group lag increasing", "tags": "kafka,consumer,messaging", "source": "monitoring"},
    {"title": "Docker registry pull rate limit exceeded", "tags": "docker,registry,rate-limit", "source": "manual"},
    {"title": "Cronjob for data backup failed", "tags": "cronjob,backup,data", "source": "monitoring"},
    {"title": "DNS resolution timeout for api.partner.com", "tags": "dns,network,partner", "source": "manual"},
    {"title": "Mobile push notification delivery failure", "tags": "mobile,push,notification", "source": "webhook"},
    {"title": "GraphQL query complexity limit exceeded", "tags": "graphql,api,performance", "source": "monitoring"},
    {"title": "S3 bucket access denied for reports service", "tags": "aws,s3,permission", "source": "monitoring"},
    {"title": "Rate limiter misconfiguration blocking valid users", "tags": "rate-limit,config,users", "source": "manual"},
    {"title": "Webhook delivery to partner failing (HTTP 502)", "tags": "webhook,partner,integration", "source": "monitoring"},
    {"title": "Database replication lag > 10 seconds", "tags": "database,replication,lag", "source": "monitoring"},
    {"title": "JWT token validation failing after key rotation", "tags": "jwt,auth,key-rotation", "source": "manual"},
    {"title": "CPU spike on checkout service pods", "tags": "cpu,checkout,kubernetes", "source": "monitoring"},
    {"title": "Email sending service queue backed up", "tags": "email,queue,sendgrid", "source": "monitoring"},
    {"title": "Third-party geocoding API returning errors", "tags": "geocoding,api,third-party", "source": "monitoring"},
]

DESCRIPTIONS = [
    "Multiple alerts triggered across monitoring dashboards. Immediate investigation required.",
    "Users reporting degraded experience. Error rate has increased significantly in the last 15 minutes.",
    "Automated monitoring detected anomaly. No user reports yet but metrics are trending badly.",
    "Partner integration team reported the issue via support channel. Confirmed on our monitoring.",
    "Noticed during routine health check. Impact assessment in progress.",
    "Triggered by deployment pipeline. Rollback may be necessary.",
    "Intermittent failures observed. Pattern suggests resource exhaustion.",
    "Critical path affected. User-facing impact confirmed.",
    "Infrastructure alert triggered. Upstream dependency may be the root cause.",
    "Scheduled maintenance may have caused unintended side effect.",
]


async def seed():
    """Seed the database with sample data."""
    await init_db()

    async with async_session_maker() as db:
        # Clear existing data first to make seeding repeatable
        from sqlalchemy import text
        await db.execute(text("TRUNCATE TABLE postmortems, incidents, users RESTART IDENTITY CASCADE;"))
        await db.commit()

        # --- Seed Users ---
        users = [
            User(
                email="alice@company.com", name="Alice Chen", role=UserRole.ENGINEER,
                tier=UserTier.TIER_1, password_hash=pwd_context.hash("password123"),
            ),
            User(
                email="bob@company.com", name="Bob Raharjo", role=UserRole.ENGINEER,
                tier=UserTier.TIER_1, password_hash=pwd_context.hash("password123"),
            ),
            User(
                email="charlie@company.com", name="Charlie Wirawan", role=UserRole.ENGINEER,
                tier=UserTier.TIER_1, password_hash=pwd_context.hash("password123"),
            ),
            User(
                email="diana@company.com", name="Diana Putri", role=UserRole.LEAD,
                tier=UserTier.TIER_2, password_hash=pwd_context.hash("password123"),
            ),
            User(
                email="edward@company.com", name="Edward Santoso", role=UserRole.LEAD,
                tier=UserTier.TIER_2, password_hash=pwd_context.hash("password123"),
            ),
            User(
                email="fiona@company.com", name="Fiona Hartono", role=UserRole.MANAGER,
                tier=UserTier.TIER_3, password_hash=pwd_context.hash("password123"),
            ),
        ]

        for user in users:
            db.add(user)
        await db.flush()

        print(f"✅ Seeded {len(users)} users")

        # --- Seed 100 Historical Incidents ---
        severities = [IncidentSeverity.P1, IncidentSeverity.P2, IncidentSeverity.P3, IncidentSeverity.P4]
        severity_weights = [10, 25, 40, 25]  # P3 is most common

        now = datetime.now(timezone.utc)

        for i in range(100):
            template = random.choice(INCIDENT_TEMPLATES)
            severity = random.choices(severities, weights=severity_weights, k=1)[0]

            # Random time in the last 30 days
            created_at = now - timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
            )

            # Determine status and related timestamps
            status_roll = random.random()
            if status_roll < 0.6:
                status = IncidentStatus.RESOLVED
                ack_delay = timedelta(minutes=random.randint(1, 30))
                resolve_delay = timedelta(minutes=random.randint(10, 480))
                acknowledged_at = created_at + ack_delay
                resolved_at = created_at + resolve_delay
                acknowledged_by = random.choice(users[:3]).id  # Engineers
                resolved_by = random.choice(users[:3]).id
            elif status_roll < 0.75:
                status = IncidentStatus.CLOSED
                ack_delay = timedelta(minutes=random.randint(1, 20))
                resolve_delay = timedelta(minutes=random.randint(10, 240))
                acknowledged_at = created_at + ack_delay
                resolved_at = created_at + resolve_delay
                acknowledged_by = random.choice(users[:3]).id
                resolved_by = random.choice(users[:3]).id
            elif status_roll < 0.85:
                status = IncidentStatus.ACKNOWLEDGED
                ack_delay = timedelta(minutes=random.randint(1, 15))
                acknowledged_at = created_at + ack_delay
                resolved_at = None
                acknowledged_by = random.choice(users[:3]).id
                resolved_by = None
            elif status_roll < 0.93:
                status = IncidentStatus.INVESTIGATING
                ack_delay = timedelta(minutes=random.randint(1, 10))
                acknowledged_at = created_at + ack_delay
                resolved_at = None
                acknowledged_by = random.choice(users[:3]).id
                resolved_by = None
            else:
                status = IncidentStatus.OPEN
                acknowledged_at = None
                resolved_at = None
                acknowledged_by = None
                resolved_by = None

            escalation_count = 0
            escalation_tier = 1
            if severity in [IncidentSeverity.P1, IncidentSeverity.P2] and random.random() < 0.3:
                escalation_count = random.randint(1, 2)
                escalation_tier = min(1 + escalation_count, 3)

            incident = Incident(
                title=f"{template['title']} #{i+1:03d}",
                description=random.choice(DESCRIPTIONS),
                severity=severity,
                status=status,
                source=template["source"],
                tags=template["tags"],
                created_at=created_at,
                acknowledged_at=acknowledged_at,
                resolved_at=resolved_at,
                acknowledged_by=acknowledged_by,
                resolved_by=resolved_by,
                assigned_to=random.choice(users[:5]).id if random.random() < 0.7 else None,
                escalation_count=escalation_count,
                escalation_tier=escalation_tier,
            )
            db.add(incident)

        await db.flush()
        print("✅ Seeded 100 historical incidents")

        await db.commit()
        print("✅ Database seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed())
