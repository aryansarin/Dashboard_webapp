# Burger Town Analytics Dashboard
A web-based business analytics dashboard built to transform a 300,000-row restaurant transaction dataset into an interactive, filterable, and performance-oriented analytics application.

The application provides business KPIs, revenue and order trends, outlet/category/channel analysis, top-performing products, automated data-driven insights, and filtered CSV export.

## Links
Live Application: https://dashboard-webapp-dabl.onrender.com/
Repository: https://github.com/aryansarin/Dashboard_webapp

## 1. Project Overview
The provided dataset contains approximately 300,000 line-item records covering restaurant transactions across multiple outlets and ordering channels.

Each row represents a line item, rather than an individual order. A single order can therefore contain multiple rows and is identified using BillNo.

The objective of this project was to build a lightweight business analytics application that:

-> Handles a relatively large transaction dataset efficiently
-> Converts raw transactional data into useful business metrics
-> Provides interactive filtering
-> Visualizes trends and business performance
-> Generates automated insights from the filtered data
-> Allows filtered data to be exported
-> Can be deployed as a live web application

The final application contains:

-> KPI summary cards
-> Revenue trends
-> Revenue by outlet
-> Revenue by category
-> Order-type analysis
-> Payment/channel analysis
-> Orders by hour
-> Top 10 items by revenue
-> Date and categorical filters
-> Automated business insights
-> CSV export

## 2. Dataset
The final dataset contains:
Line-item records:	300,000
Distinct orders:	110,478
Outlets:	6
Brands:	1
Time period:	17 Jun 2025 – 16 Jun 2026
Null values:	0
Duplicate rows:	0
Zero-price/free items:	8,611

The first and last months are partial months. This is important when calculating month-over-month trends because comparing a partial month against a complete month can produce misleading conclusions.

The raw timestamp format supplied by the assessment was:

DD-MM-YYYY HH:MM:SS

The ETL process converts timestamps into a consistent ISO-style format:

YYYY-MM-DD HH:MM:SS

The dataset was also checked for missing values and duplicate records during preprocessing.

## 3. Tech Stack
**Backend**
Python
FastAPI
SQLite
Pandas
Uvicorn
**Frontend**
Vue 3
Chart.js
HTML/CSS/JavaScript
**Data Processing**
Pandas for one-time Excel ingestion and preprocessing
Gzip-compressed CSV as an intermediate representation
SQLite for indexed analytical queries
**Deployment**
Render
**Version Control**
Git
GitHub

## 4. Architecture
The application follows a simple ETL + API + frontend architecture:

                 Raw Excel Dataset
                       │
                       ▼
              Pandas ETL Processing
                       │
                       ▼
              Compressed CSV (.gz)
                       │
                       ▼
                SQLite Database
                       │
              Indexed SQL Queries
                       │
                       ▼
                FastAPI Backend
                       │
                  JSON Responses
                       │
                       ▼
              Vue 3 Dashboard
                       │
                       ▼
                Chart.js Visuals

The frontend does not load all 300,000 rows into the browser.

Instead, the backend performs aggregation and filtering in SQLite and returns only the summarized information required to render the dashboard.

This keeps the browser workload small and allows the application to remain responsive.

## 5. Data Ingestion and ETL
**Why not read Excel directly on every request?**
The source file is an .xlsx workbook containing approximately 300,000 records.

Excel files are convenient for data exchange but are not an efficient format for repeated analytical queries. Parsing the workbook repeatedly would introduce unnecessary overhead because the application would have to process the Excel structure each time.

Therefore, Excel is treated as a one-time source file rather than the application's runtime data source.

The ETL pipeline performs the following steps:

Excel
  ↓
Read with Pandas
  ↓
Validate data quality
  ↓
Parse Order_Datetime
  ↓
Convert to typed/normalized records
  ↓
Write compressed CSV
  ↓
Load into SQLite
  ↓
Create indexes

The conversion script reads the Excel workbook once and writes lines.csv.gz, allowing the application to avoid parsing Excel at runtime.
## 6. Data Transformation

The following derived fields are created during the ETL/database stage:

date — calendar date extracted from the timestamp
month — month-level aggregation key
hour — hour of the day
revenue — calculated as:
Revenue = Price × Quantity

The database stores these derived fields so that common dashboard queries do not repeatedly have to calculate them.

For example:

Price = ₹250
Quantity = 2

Revenue = ₹250 × 2
        = ₹500

The distinction between records and orders is also preserved.

A record is one line item, whereas an order is a distinct BillNo.

Therefore:

Total records = COUNT(*)

Total orders = COUNT(DISTINCT BillNo)

This distinction is particularly important for metrics such as Average Order Value.

## 7. Database Design

SQLite was selected as the database for this assessment.

**Why SQLite?**

The dataset is approximately 300,000 rows and the application is primarily analytical and read-oriented.

SQLite provides:

Zero infrastructure overhead
Fast local analytical queries
SQL-based filtering and aggregation
Indexing
A simple deployment model
No separate database server to configure

For this assessment, SQLite provides a good balance between simplicity and performance.

A larger production system with many concurrent users, frequent writes, or substantially larger datasets would be better suited to a server-based database such as PostgreSQL.

The database contains a central lines table with fields including:

bill_no
outlet
brand
ts
date
month
hour
grp
order_type
item
price
qty
settlement
revenue

Indexes are created on frequently filtered dimensions:

date
outlet
group/category
order_type
settlement

These indexes allow SQLite to narrow down relevant records more efficiently during filtered dashboard queries.

# 8. Backend API

The backend is implemented using FastAPI.

The main endpoints are:

/api/meta

Provides dashboard metadata such as:

Available date range
Outlets
Categories
Order types
Payment/settlement options

This allows the frontend filters to be populated dynamically from the database.

/api/dashboard

Returns the aggregated dashboard data for the currently selected filters.

The endpoint supports:

Start date
End date
Outlet
Category
Order type
Settlement/payment
Monthly or daily trend

Instead of making separate requests for every chart, the application returns the dashboard aggregations through a single API request.

This reduces network round trips and keeps the dashboard architecture simple.

/api/export.csv

Exports the currently filtered records as CSV.

The export is streamed in chunks rather than loading the entire result into memory at once. The implementation fetches records in batches of 5,000 rows.

/healthz

A lightweight health-check endpoint used by the deployment platform.

# 9. Dashboard KPIs

The dashboard displays:

Line-item records

Number of transactional rows after applying the current filters.

Orders

Number of distinct BillNo values.

Revenue

Sum of:

Price × Quantity
Average Order Value

Calculated as:

AOV = Total Revenue / Number of Orders

The denominator is the number of distinct orders rather than the number of line items.

Units Sold

Sum of the Quantity field.

Items per Order

Calculated as:

Items per Order = Total Units / Total Orders

The backend performs these calculations directly through SQL aggregation.

# 10. Visualizations

The dashboard includes multiple visualization types.

Revenue Trend

A line chart showing revenue over time.

The user can switch between:

Monthly
Daily

This helps identify changes in sales performance over time.

Revenue by Outlet

A bar chart ranking outlets by revenue.

Revenue by Category

A bar chart showing revenue contribution from different menu categories.

Order Type Split

A doughnut chart comparing:

Dine-In
Takeaway
Delivery
Payment / Channel

A doughnut chart showing revenue distribution across settlement/payment methods.

Orders by Hour

A bar chart showing the number of orders across hours of the day.

This can help identify peak operating periods.

Top 10 Items

A bar chart showing the top ten menu items by revenue.

These charts are generated on the frontend using Chart.js, while the aggregations themselves are performed by the backend.

# 11. Filtering

The dashboard supports interactive filtering by:

Date range
Outlet
Category
Order type
Payment/settlement

The user can also switch the time-series granularity between daily and monthly.

Filters are sent to the backend as query parameters.

For example, conceptually:

/api/dashboard
    ?start=2025-07-01
    &end=2025-08-01
    &outlet=Outlet A
    &order_type=Delivery

The backend converts the selected filters into parameterized SQL conditions.

This means filtering happens before aggregation, rather than downloading the entire dataset to the browser and filtering it using JavaScript.

12. Automated Insights

The dashboard includes an Auto Insights section.

These insights are intentionally implemented as deterministic, rule-based analytics rather than an external LLM/API.

This design was chosen because the assessment prioritizes correctness, speed, explainability, and production reliability.

No external AI API key is required.

How the insights are generated

The backend first calculates the same filtered aggregations used by the dashboard.

It then applies simple business rules to identify notable observations.

1. Top outlet

The application identifies the outlet with the highest revenue and calculates its percentage contribution to total revenue.

Example:

Outlet A is the top outlet with 28% of revenue.
2. Peak ordering hour

The hourly aggregation is examined to find the hour with the highest number of orders.

Example:

Peak ordering hour is 19:00 (4,250 orders).
3. Best-selling item

The item with the highest revenue is identified from the filtered dataset.

Example:

Best-selling item by revenue: Chicken Burger.
4. Delivery contribution

If Delivery exists as an order type, its revenue contribution is calculated as a percentage of total revenue.

Example:

Delivery accounts for 18% of revenue.
5. Month-over-month revenue change

For monthly analysis, the application compares the most recent complete month with the preceding complete month.

Partial months are intentionally excluded from this comparison.

This prevents misleading conclusions caused by incomplete periods.

For example, the supplied dataset ends on 16 June 2026, so June 2026 is not treated as a complete month.

Why rule-based instead of an LLM?

For this application, deterministic insights have several advantages:

No API key
No external dependency
No additional latency
No inference cost
Reproducible results
Easy to validate
Every insight can be traced back to a database aggregation

This is effectively an explainable analytics layer rather than a black-box text-generation layer.

# 13. Performance Strategy

Performance was considered at multiple levels.

13.1 Avoid Excel at runtime

Excel is converted once into a compact intermediate format.

The server does not repeatedly parse the original workbook.

13.2 SQLite indexes

Indexes are created on commonly filtered columns:

date
outlet
group
order_type
settlement
13.3 Server-side aggregation

The browser does not receive all 300,000 records.

Instead, SQL performs:

Counts
Sums
Distinct order calculations
Grouping
Ranking
Filtering

Only the aggregated results needed for the charts are returned.

13.4 Query caching

The dashboard aggregation function uses an LRU cache.

Repeated requests for the same filter combination can therefore reuse an existing result instead of recomputing the same SQL aggregations.

The cache supports up to 256 dashboard query combinations.

13.5 SQLite memory optimizations

The backend uses a read-only SQLite connection and configures:

SQLite page cache
Memory mapping

This is appropriate because the deployed application is primarily performing analytical reads.

13.6 Gzip compression

FastAPI responses larger than the configured threshold are gzip-compressed, reducing network transfer size.

13.7 Debounced filtering

The frontend waits briefly after filter changes before making the API request.

This prevents a separate request from being triggered for every rapid interaction when the user is changing multiple filters.

# 14. Performance Observations

During local testing:

The 300,000-row dataset loads into the processing pipeline in approximately 2 seconds.
Uncached dashboard filter combinations were observed at approximately 0.25–0.9 seconds.
Cached combinations can return in approximately 2 milliseconds.

These measurements are environment-dependent and should be considered local development observations rather than formal production benchmarks.

# 15. Data Quality and Assumptions

The following checks were performed during ingestion:

Null values

No null values were found in the supplied dataset.

Duplicate records

No duplicate rows were found.

Zero-price records

8,611 rows have a price of zero.

These were not removed because they are valid transactional records representing free items/discounted or promotional items.

Removing them would change the underlying transaction data.

Partial months

The dataset covers:

17 Jun 2025 → 16 Jun 2026

Therefore:

June 2025 is partial
June 2026 is partial

The dashboard still displays these periods in trend charts, but automated month-over-month comparisons avoid using an incomplete final month.

Order definition

An order is defined as a unique BillNo.

A line-item record is not treated as an order.

Revenue definition

Revenue is calculated as:

Price × Quantity

No additional tax, discount, or cost information was assumed because those fields were not provided in the dataset.

# 16. Key Technical Trade-offs
**SQLite vs PostgreSQL
SQLite advantages**
No external database server
Very simple deployment
Low operational overhead
Suitable for a 300K-row read-heavy assessment
Easy to reproduce locally
**PostgreSQL advantages**

For a larger production application, PostgreSQL would be preferable because it provides:

Better concurrent access
More scalable infrastructure
Stronger production database capabilities

**For the scope of this assessment, SQLite was considered sufficient.**

**Pre-converted data vs direct Excel ingestion**

Direct Excel ingestion would minimize preprocessing steps but would make runtime performance less predictable.

The chosen approach pays the Excel parsing cost once and stores the data in a more query-friendly representation.

**One dashboard API vs multiple APIs**

A single /api/dashboard request returns the KPI and chart aggregations required by the page.

This reduces the number of network round trips.

The trade-off is that the response contains several aggregations even when the user may only be looking at one chart.

**For this dashboard size, the simplicity and reduced request count were considered worthwhile.**

**Rule-based insights vs LLM-generated insights**

An LLM could generate more natural-language or sophisticated explanations.

However, it would introduce:

External API dependency
API credentials
Additional latency
Additional cost
Potentially non-deterministic output

The current rule-based approach provides deterministic, auditable insights directly from the filtered data.

**An LLM layer could be added later as an optional enhancement.**

# 17. Project Structure
burger-town-analytics/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── build_db.py
│   │
│   └── static/
│       ├── index.html
│       ├── app.js
│       └── style.css
│
├── scripts/
│   └── xlsx_to_csv.py
│
├── data/
│   ├── data.xlsx
│   ├── lines.csv.gz
│   └── analytics.db
│
├── requirements.txt
├── requirements-dev.txt
├── render.yaml
├── .gitignore
└── README.md
# 18. Local Setup
Prerequisites
Python 3.12+
Git
1. Clone the repository
git clone https://github.com/aryansarin/Dashboard_webapp
cd burger-town-analytics
2. Create a virtual environment**
**Windows**
python -m venv .venv
.venv\Scripts\activate
**macOS/Linux**
python3 -m venv .venv
source .venv/bin/activate
3. Install dependencies
pip install -r requirement.txt

For local data conversion:

pip install -r requirements-dev.txt
4. Add the raw dataset

Place the supplied Excel file at:

data/data.xlsx
5. Convert Excel to compressed CSV
python scripts/xlsx_to_csv.py

This creates:

data/lines.csv.gz
6. Build the SQLite database
python -m app.build_db

This creates:

data/analytics.db
7. Start the application
uvicorn app.main:app --reload

Open:

http://127.0.0.1:8000
# 19. Deployment

The application is configured for deployment on Render.

The deployment configuration is contained in:

render.yaml

The build process installs the Python dependencies and builds the SQLite database:

pip install -r requirement.txt && python -m app.build_db

The application is started with:

uvicorn app.main:app --host 0.0.0.0 --port $PORT

A health-check endpoint is available at:

/healthz

This allows the deployment platform to verify that the application is running correctly.

# 20. Deployment Considerations

The application is deployed as a lightweight Python web service.

Because the application uses SQLite and is read-oriented, no separate managed database is required for this assessment.

**The free hosting tier may put the application to sleep after periods of inactivity. Consequently, the first request after a period of inactivity may take longer than subsequent requests.**

# 21. Future Improvements

If this application were developed beyond the assessment scope, possible improvements would include:

Database

Move from SQLite to PostgreSQL for larger datasets and higher concurrent usage.

Authentication

Add role-based authentication for internal business users.

Advanced analytics

Add:

Customer/order cohort analysis
Repeat-order analysis
Outlet benchmarking
Basket analysis
Forecasting
Anomaly detection
AI-assisted insights

A future version could optionally send aggregated dashboard results to an LLM and ask it to generate natural-language business recommendations.

For example:

Data aggregation
      ↓
Statistical/anomaly detection
      ↓
Structured insight objects
      ↓
LLM
      ↓
Natural-language business summary

The LLM would receive aggregated results rather than the full 300,000-row dataset.

This would preserve the current analytical architecture while adding a natural-language explanation layer.

Infrastructure

For a larger production deployment:

React/Vue frontend
        ↓
API service
        ↓
PostgreSQL
        ↓
Redis/cache
        ↓
Cloud monitoring

could replace the lightweight assessment architecture.

# 22. Assessment Requirements Checklist
Requirement	Implementation
~300K row dataset	300,000 records processed
Data ingestion	Pandas ETL
Efficient serving	SQLite
Database/indexing	SQLite indexes
Summary metrics	KPI cards
Multiple visualizations	Line, bar and doughnut charts
Filtering	Date, outlet, category, order type, payment
Performance	SQL aggregation, indexes, caching
Smooth UX	Debounced filtering and lightweight API responses
Automated insights	Deterministic rule-based insights
CSV export	Streaming filtered export
Responsive UI	Responsive CSS layout
Version control	Git + GitHub
Deployment	Render
Documentation	Architecture, setup, assumptions and trade-offs

# 23. Conclusion

The application intentionally prioritizes a simple, explainable architecture over unnecessary complexity.

The core design decision was to avoid sending the full 300,000-row dataset to the browser. Instead, the raw Excel data is processed once, stored in an indexed SQLite database, and queried through a FastAPI backend.

The frontend receives only the aggregated information required for the dashboard.

This provides a practical balance between:

Development speed
Performance
Maintainability
Explainability
Deployment simplicity
Scalability for the current dataset size

For the scope of this assessment, the resulting architecture provides a lightweight but production-oriented foundation for business analytics.
