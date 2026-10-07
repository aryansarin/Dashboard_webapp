import calendar, csv, io, os, sqlite3, threading
from functools import lru_cache
from typing import List, Optional

from fastapi import FastAPI, Query
from starlette.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

BASE = os.path.dirname(__file__)
DB = os.path.join(BASE, "..", "data", "analytics.db")

# Build the DB on first boot if the build step didn't run (keeps local dev easy).
if not os.path.exists(DB):
    from app.build_db import main as build
    build()

app = FastAPI(title="Burger Town Analytics")
app.add_middleware(GZipMiddleware, minimum_size=500)

_local = threading.local()

def conn() -> sqlite3.Connection:
    """One read-only connection per thread (SQLite connections aren't thread-safe)."""
    c = getattr(_local, "c", None)
    if c is None:
        c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
        c.execute("PRAGMA cache_size=-65536")    # 64 MB page cache
        c.execute("PRAGMA mmap_size=268435456")  # memory-map the file
        _local.c = c
    return c

def q(sql, params=()):
    return conn().execute(sql, params).fetchall()

# ---------- filters ----------
def where(start, end, outlets, groups, types, settlements):
    clauses, params = [], []
    if start: clauses.append("date >= ?"); params.append(start)
    if end:   clauses.append("date <= ?"); params.append(end)
    for col, vals in (("outlet", outlets), ("grp", groups),
                      ("order_type", types), ("settlement", settlements)):
        if vals:
            clauses.append(f"{col} IN ({','.join('?' * len(vals))})")
            params += list(vals)
    return ("WHERE " + " AND ".join(clauses)) if clauses else "", params

def _f(v: Optional[List[str]]):
    return tuple(sorted(v)) if v else ()   # hashable + order-independent => good cache keys

# ---------- endpoints ----------
@app.get("/api/meta")
def meta():
    return {
        "min_date": q("SELECT MIN(date) FROM lines")[0][0],
        "max_date": q("SELECT MAX(date) FROM lines")[0][0],
        "outlets": [r[0] for r in q("SELECT DISTINCT outlet FROM lines ORDER BY 1")],
        "groups": [r[0] for r in q("SELECT DISTINCT grp FROM lines ORDER BY 1")],
        "order_types": [r[0] for r in q("SELECT DISTINCT order_type FROM lines ORDER BY 1")],
        "settlements": [r[0] for r in q("SELECT DISTINCT settlement FROM lines ORDER BY 1")],
    }

@lru_cache(maxsize=256)
def _dashboard(start, end, outlets, groups, types, settlements, grain):
    w, p = where(start, end, outlets, groups, types, settlements)
    records, orders, revenue, units = q(
        f"SELECT COUNT(*), COUNT(DISTINCT bill_no), COALESCE(SUM(revenue),0), COALESCE(SUM(qty),0) "
        f"FROM lines {w}", p)[0]
    kpis = {
        "records": records, "orders": orders, "revenue": revenue, "units": units,
        "aov": round(revenue / orders, 2) if orders else 0,
        "items_per_order": round(units / orders, 2) if orders else 0,
    }
    bucket = "date" if grain == "day" else "month"
    trend = [{"x": r[0], "revenue": r[1], "orders": r[2]} for r in q(
        f"SELECT {bucket}, SUM(revenue), COUNT(DISTINCT bill_no) FROM lines {w} GROUP BY 1 ORDER BY 1", p)]

    def dim(col):
        sql = (f"SELECT {col}, SUM(revenue), COUNT(DISTINCT bill_no) FROM lines {w} "
               f"GROUP BY 1 ORDER BY 2 DESC")
        return [{"label": r[0], "revenue": r[1], "orders": r[2]} for r in q(sql, p)]

    hourly = [{"label": f"{r[0]:02d}:00", "orders": r[1], "revenue": r[2]} for r in q(
        f"SELECT hour, COUNT(DISTINCT bill_no), SUM(revenue) FROM lines {w} GROUP BY 1 ORDER BY 1", p)]
    top_items = [{"label": r[0], "revenue": r[1], "units": r[2]} for r in q(
        f"SELECT item, SUM(revenue), SUM(qty) FROM lines {w} GROUP BY 1 ORDER BY 2 DESC LIMIT 10", p)]
    by_outlet, by_group, by_type, by_settle = dim("outlet"), dim("grp"), dim("order_type"), dim("settlement")

    # Rule-based insights: deterministic, free, no API key needed.
    insights = []
    if records:
        tot = revenue or 1
        insights.append(f"{by_outlet[0]['label']} is the top outlet with {by_outlet[0]['revenue']/tot:.0%} of revenue.")
        peak = max(hourly, key=lambda h: h["orders"])
        insights.append(f"Peak ordering hour is {peak['label']} ({peak['orders']:,} orders).")
        insights.append(f"Best-selling item by revenue: {top_items[0]['label']}.")
        dl = next((t for t in by_type if t["label"] == "Delivery"), None)
        if dl:
            insights.append(f"Delivery accounts for {dl['revenue']/tot:.0%} of revenue.")
        if grain == "month" and len(trend) >= 2:
            # Don't compare against a partial month (data may start/end mid-month).
            last_date = q(f"SELECT MAX(date) FROM lines {w}", p)[0][0]
            y, m, d = map(int, last_date.split("-"))
            full = trend if d == calendar.monthrange(y, m)[1] else trend[:-1]
            if len(full) >= 2 and full[-2]["revenue"]:
                a, b = full[-2]["revenue"], full[-1]["revenue"]
                insights.append(f"Last full month ({full[-1]['x']}) revenue is {(b-a)/a:+.1%} vs the month before.")

    return {"kpis": kpis, "trend": trend, "by_outlet": by_outlet, "by_group": by_group,
            "by_type": by_type, "by_settlement": by_settle, "hourly": hourly,
            "top_items": top_items, "insights": insights}

@app.get("/api/dashboard")
def dashboard(start: Optional[str] = None, end: Optional[str] = None,
              outlet: Optional[List[str]] = Query(None), group: Optional[List[str]] = Query(None),
              order_type: Optional[List[str]] = Query(None), settlement: Optional[List[str]] = Query(None),
              grain: str = "month"):
    return _dashboard(start, end, _f(outlet), _f(group), _f(order_type), _f(settlement),
                      "day" if grain == "day" else "month")

@app.get("/api/export.csv")
def export(start: Optional[str] = None, end: Optional[str] = None,
           outlet: Optional[List[str]] = Query(None), group: Optional[List[str]] = Query(None),
           order_type: Optional[List[str]] = Query(None), settlement: Optional[List[str]] = Query(None)):
    w, p = where(start, end, _f(outlet), _f(group), _f(order_type), _f(settlement))

    def gen():
        buf = io.StringIO()
        csv.writer(buf).writerow(["BillNo", "Outlet", "Datetime", "Group", "Order_Type",
                                  "Item", "Price", "Quantity", "Settlement", "Revenue"])
        yield buf.getvalue()
        cur = conn().execute(
            f"SELECT bill_no,outlet,ts,grp,order_type,item,price,qty,settlement,revenue "
            f"FROM lines {w} ORDER BY ts", p)
        while True:                      # stream in chunks: constant memory, even for 300K rows
            rows = cur.fetchmany(5000)
            if not rows:
                break
            buf = io.StringIO()
            csv.writer(buf).writerows(rows)
            yield buf.getvalue()

    return StreamingResponse(gen(), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=filtered_lines.csv"})

@app.on_event("startup")
def warm_cache():
    """Pre-compute the default (unfiltered) dashboard so the first visitor gets a cache hit."""
    _dashboard(None, None, (), (), (), (), "month")

@app.get("/healthz")
def health():
    return {"ok": True}

app.mount("/static", StaticFiles(directory=os.path.join(BASE, "static")), name="static")

@app.get("/")
def index():
    return FileResponse(os.path.join(BASE, "static", "index.html"))