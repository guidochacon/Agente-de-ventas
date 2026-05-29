import uuid
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func as sqlfunc
from sqlalchemy.ext.asyncio import AsyncSession

from models import get_db, SalesAgent, DailyEntry, EODReport
from config import settings

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


# ── Pydantic schemas ────────────────────────────────────────────────────────

class AgentCreate(BaseModel):
    name: str
    email: str
    role: str = "agent"


class DailyEntryUpsert(BaseModel):
    agent_id: str
    date: str                      # YYYY-MM-DD
    new_leads: int = 0
    total_calls: int = 0
    conversations: int = 0
    demos_booked: int = 0
    demos_showed: int = 0
    offers_made: int = 0
    closed_deals: int = 0
    revenue: float = 0.0
    cash_collected: float = 0.0
    notes: Optional[str] = None


class EODReportCreate(BaseModel):
    agent_id: str
    date: str                      # YYYY-MM-DD
    role: str = "agent"
    energy_level: Optional[int] = None
    focus_level: Optional[int] = None
    health_level: Optional[int] = None
    tracker_completed: bool = False
    post_call_forms: bool = False
    biggest_win: Optional[str] = None
    biggest_challenge: Optional[str] = None
    tomorrow_plan: Optional[str] = None


# ── Helpers ─────────────────────────────────────────────────────────────────

def _default_range() -> tuple[str, str]:
    today = date.today()
    return (today - timedelta(days=30)).isoformat(), today.isoformat()


def _safe_pct(num: float, den: float) -> float:
    return round(num / den * 100, 1) if den else 0.0


# ── Agents ──────────────────────────────────────────────────────────────────

@router.get("/agents")
async def list_agents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SalesAgent).where(SalesAgent.is_active == True).order_by(SalesAgent.created_at)
    )
    return [a.to_dict() for a in result.scalars().all()]


@router.post("/agents", status_code=201)
async def create_agent(body: AgentCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SalesAgent).where(SalesAgent.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(400, "Ya existe un agente con ese email")
    agent = SalesAgent(id=str(uuid.uuid4()), name=body.name, email=body.email, role=body.role)
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent.to_dict()


# ── Overview ─────────────────────────────────────────────────────────────────

@router.get("/overview")
async def overview(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    if not date_from or not date_to:
        date_from, date_to = _default_range()

    result = await db.execute(
        select(DailyEntry).where(
            DailyEntry.date >= date_from,
            DailyEntry.date <= date_to,
        )
    )
    entries = result.scalars().all()

    totals = {
        "new_leads": sum(e.new_leads for e in entries),
        "total_calls": sum(e.total_calls for e in entries),
        "conversations": sum(e.conversations for e in entries),
        "demos_booked": sum(e.demos_booked for e in entries),
        "demos_showed": sum(e.demos_showed for e in entries),
        "offers_made": sum(e.offers_made for e in entries),
        "closed_deals": sum(e.closed_deals for e in entries),
        "revenue": round(sum(e.revenue for e in entries), 2),
        "cash_collected": round(sum(e.cash_collected for e in entries), 2),
    }
    totals["lead_to_demo_pct"] = _safe_pct(totals["demos_booked"], totals["new_leads"])
    totals["show_rate_pct"] = _safe_pct(totals["demos_showed"], totals["demos_booked"])
    totals["offer_to_close_pct"] = _safe_pct(totals["closed_deals"], totals["offers_made"])

    # per-agent breakdown
    agent_map: dict[str, dict] = {}
    for e in entries:
        if e.agent_id not in agent_map:
            agent_map[e.agent_id] = {k: 0 for k in ["new_leads", "total_calls", "conversations",
                                                      "demos_booked", "demos_showed", "offers_made",
                                                      "closed_deals", "revenue", "cash_collected"]}
        for k in agent_map[e.agent_id]:
            agent_map[e.agent_id][k] += getattr(e, k)

    # resolve agent names
    if agent_map:
        agents_result = await db.execute(
            select(SalesAgent).where(SalesAgent.id.in_(list(agent_map.keys())))
        )
        agents = {a.id: a for a in agents_result.scalars().all()}
        per_agent = [
            {"agent_id": aid, "name": agents[aid].name if aid in agents else aid, "role": agents[aid].role if aid in agents else "", **data}
            for aid, data in agent_map.items()
        ]
    else:
        per_agent = []

    return {"date_from": date_from, "date_to": date_to, "totals": totals, "per_agent": per_agent}


# ── Sales Tracker ─────────────────────────────────────────────────────────────

@router.get("/sales-tracker")
async def get_sales_tracker(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    agent_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    if not date_from or not date_to:
        # default: current week Mon-Sun
        today = date.today()
        date_from = (today - timedelta(days=today.weekday())).isoformat()
        date_to = today.isoformat()

    q = select(DailyEntry).where(
        DailyEntry.date >= date_from,
        DailyEntry.date <= date_to,
    )
    if agent_id:
        q = q.where(DailyEntry.agent_id == agent_id)
    q = q.order_by(DailyEntry.date, DailyEntry.agent_id)

    result = await db.execute(q)
    entries = result.scalars().all()

    # attach agent names
    agent_ids = list({e.agent_id for e in entries})
    if agent_ids:
        agents_result = await db.execute(select(SalesAgent).where(SalesAgent.id.in_(agent_ids)))
        agents = {a.id: a for a in agents_result.scalars().all()}
    else:
        agents = {}

    rows = []
    for e in entries:
        d = e.to_dict()
        a = agents.get(e.agent_id)
        d["agent_name"] = a.name if a else e.agent_id
        d["agent_role"] = a.role if a else ""
        rows.append(d)

    return {"date_from": date_from, "date_to": date_to, "entries": rows}


@router.post("/sales-tracker", status_code=201)
async def upsert_daily_entry(body: DailyEntryUpsert, db: AsyncSession = Depends(get_db)):
    # check agent exists
    result = await db.execute(select(SalesAgent).where(SalesAgent.id == body.agent_id))
    if not result.scalar_one_or_none():
        raise HTTPException(404, "Agente no encontrado")

    # try update existing
    result = await db.execute(
        select(DailyEntry).where(
            DailyEntry.agent_id == body.agent_id,
            DailyEntry.date == body.date,
        )
    )
    entry = result.scalar_one_or_none()

    if entry:
        for field in ["new_leads", "total_calls", "conversations", "demos_booked",
                      "demos_showed", "offers_made", "closed_deals", "revenue",
                      "cash_collected", "notes"]:
            setattr(entry, field, getattr(body, field))
    else:
        entry = DailyEntry(
            id=str(uuid.uuid4()),
            agent_id=body.agent_id,
            date=body.date,
            new_leads=body.new_leads,
            total_calls=body.total_calls,
            conversations=body.conversations,
            demos_booked=body.demos_booked,
            demos_showed=body.demos_showed,
            offers_made=body.offers_made,
            closed_deals=body.closed_deals,
            revenue=body.revenue,
            cash_collected=body.cash_collected,
            notes=body.notes,
        )
        db.add(entry)

    await db.commit()
    await db.refresh(entry)
    return entry.to_dict()


# ── Team Performance ──────────────────────────────────────────────────────────

@router.get("/team-performance")
async def team_performance(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    if not date_from or not date_to:
        date_from, date_to = _default_range()

    agents_result = await db.execute(select(SalesAgent).where(SalesAgent.is_active == True))
    agents = {a.id: a for a in agents_result.scalars().all()}

    entries_result = await db.execute(
        select(DailyEntry).where(
            DailyEntry.date >= date_from,
            DailyEntry.date <= date_to,
        )
    )
    entries = entries_result.scalars().all()

    stats: dict[str, dict] = {aid: {
        "agent_id": aid, "name": a.name, "role": a.role,
        "new_leads": 0, "total_calls": 0, "conversations": 0,
        "demos_booked": 0, "demos_showed": 0, "offers_made": 0,
        "closed_deals": 0, "revenue": 0.0, "cash_collected": 0.0,
    } for aid, a in agents.items()}

    for e in entries:
        if e.agent_id not in stats:
            continue
        for k in ["new_leads", "total_calls", "conversations", "demos_booked",
                  "demos_showed", "offers_made", "closed_deals", "revenue", "cash_collected"]:
            stats[e.agent_id][k] += getattr(e, k)

    ranked = sorted(stats.values(), key=lambda x: x["revenue"], reverse=True)
    for i, r in enumerate(ranked):
        r["rank"] = i + 1
        r["lead_to_demo_pct"] = _safe_pct(r["demos_booked"], r["new_leads"])
        r["show_rate_pct"] = _safe_pct(r["demos_showed"], r["demos_booked"])
        r["offer_to_close_pct"] = _safe_pct(r["closed_deals"], r["offers_made"])

    return {"date_from": date_from, "date_to": date_to, "agents": ranked}


# ── EOD Reports ───────────────────────────────────────────────────────────────

@router.post("/eod-report", status_code=201)
async def submit_eod(body: EODReportCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SalesAgent).where(SalesAgent.id == body.agent_id))
    if not result.scalar_one_or_none():
        raise HTTPException(404, "Agente no encontrado")

    report = EODReport(
        id=str(uuid.uuid4()),
        agent_id=body.agent_id,
        date=body.date,
        role=body.role,
        energy_level=body.energy_level,
        focus_level=body.focus_level,
        health_level=body.health_level,
        tracker_completed=body.tracker_completed,
        post_call_forms=body.post_call_forms,
        biggest_win=body.biggest_win,
        biggest_challenge=body.biggest_challenge,
        tomorrow_plan=body.tomorrow_plan,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report.to_dict()


@router.get("/eod-reports")
async def list_eod_reports(
    date: Optional[str] = None,
    agent_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(EODReport).order_by(EODReport.submitted_at.desc())
    if date:
        q = q.where(EODReport.date == date)
    if agent_id:
        q = q.where(EODReport.agent_id == agent_id)
    result = await db.execute(q)
    reports = result.scalars().all()

    # attach agent names
    agent_ids = list({r.agent_id for r in reports})
    if agent_ids:
        agents_result = await db.execute(select(SalesAgent).where(SalesAgent.id.in_(agent_ids)))
        agents = {a.id: a for a in agents_result.scalars().all()}
    else:
        agents = {}

    rows = []
    for r in reports:
        d = r.to_dict()
        a = agents.get(r.agent_id)
        d["agent_name"] = a.name if a else r.agent_id
        rows.append(d)
    return rows


# ── External sync ─────────────────────────────────────────────────────────────

@router.post("/sync-sheets")
async def sync_sheets(db: AsyncSession = Depends(get_db)):
    from services.sheets import sync_from_sheet

    result = await sync_from_sheet(
        settings.google_service_account_json,
        settings.google_sheets_id,
    )
    if "error" in result:
        raise HTTPException(400, result["error"])

    # upsert each row into DailyEntry
    synced = 0
    for row in result.get("rows", []):
        agent_email = row.get("agent_email", "")
        entry_date = row.get("date", "")
        if not agent_email or not entry_date:
            continue

        agent_result = await db.execute(select(SalesAgent).where(SalesAgent.email == agent_email))
        agent = agent_result.scalar_one_or_none()
        if not agent:
            continue

        existing = await db.execute(
            select(DailyEntry).where(
                DailyEntry.agent_id == agent.id,
                DailyEntry.date == entry_date,
            )
        )
        entry = existing.scalar_one_or_none()

        def _int(k): return int(row.get(k) or 0)
        def _float(k): return float(row.get(k) or 0)

        if entry:
            entry.new_leads = _int("new_leads")
            entry.total_calls = _int("total_calls")
            entry.conversations = _int("conversations")
            entry.demos_booked = _int("demos_booked")
            entry.demos_showed = _int("demos_showed")
            entry.offers_made = _int("offers_made")
            entry.closed_deals = _int("closed_deals")
            entry.revenue = _float("revenue")
            entry.cash_collected = _float("cash_collected")
        else:
            entry = DailyEntry(
                id=str(uuid.uuid4()),
                agent_id=agent.id,
                date=entry_date,
                new_leads=_int("new_leads"),
                total_calls=_int("total_calls"),
                conversations=_int("conversations"),
                demos_booked=_int("demos_booked"),
                demos_showed=_int("demos_showed"),
                offers_made=_int("offers_made"),
                closed_deals=_int("closed_deals"),
                revenue=_float("revenue"),
                cash_collected=_float("cash_collected"),
            )
            db.add(entry)
        synced += 1

    await db.commit()
    return {"message": f"Sincronizado {synced} entradas desde Google Sheets"}


@router.post("/sync-ghl")
async def sync_ghl(db: AsyncSession = Depends(get_db)):
    from services.ghl import sync_leads_from_ghl

    result = await sync_leads_from_ghl(db, settings.ghl_api_key, settings.ghl_location_id)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result
