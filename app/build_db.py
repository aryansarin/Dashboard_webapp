"""ETL: lines.csv.gz -> SQLite (analytics.db). Runs at deploy/build time (~5-10s)."""
import csv, gzip, sqlite3, os, time

HERE = os.path.dirname(__file__)
SRC = os.path.join(HERE, "..", "data", "lines.csv.gz")
DB = os.path.join(HERE, "..", "data", "analytics.db")

SCHEMA = """
CREATE TABLE lines (
  bill_no INTEGER, outlet TEXT, brand TEXT,
  ts TEXT, date TEXT, month TEXT, hour INTEGER,
  grp TEXT, order_type TEXT, item TEXT,
  price INTEGER, qty INTEGER, settlement TEXT, revenue INTEGER
);
"""
INDEXES = [
    "CREATE INDEX ix_date ON lines(date)",
    "CREATE INDEX ix_outlet ON lines(outlet)",
    "CREATE INDEX ix_grp ON lines(grp)",
    "CREATE INDEX ix_type ON lines(order_type)",
    "CREATE INDEX ix_settle ON lines(settlement)",
]

def rows():
    with gzip.open(SRC, "rt", newline="") as f:
        for r in csv.DictReader(f):
            ts = r["Order_Datetime"]  # 'YYYY-MM-DD HH:MM:SS'
            price, qty = int(r["Price"]), int(r["Quantity"])
            yield (int(r["BillNo"]), r["Outlet_Name"], r["Brand"], ts, ts[:10], ts[:7],
                   int(ts[11:13]), r["Group"], r["Order_Type"], r["Item"],
                   price, qty, r["Settlement"], price * qty)  # revenue = price * qty

def main():
    t = time.time()
    if os.path.exists(DB):
        os.remove(DB)
    con = sqlite3.connect(DB)
    con.executescript(SCHEMA)
    con.executemany("INSERT INTO lines VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows())
    for ix in INDEXES:
        con.execute(ix)
    con.execute("ANALYZE")
    con.commit()
    n = con.execute("SELECT COUNT(*) FROM lines").fetchone()[0]
    con.close()
    print(f"built {DB}: {n:,} rows in {time.time()-t:.1f}s")

if __name__ == "__main__":
    main()