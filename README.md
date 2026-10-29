# ProductSphere — Product Lifecycle Management MVP

A local Streamlit application demonstrating core product-management workflows:
- Product portfolio
- Feature backlog with priority, status, impact, effort and a simple impact/effort score
- Roadmap initiatives by quarter
- Release planning with version, target date, status and feature scope
- SQLite persistence, activity log, CSV exports, dashboard charts

## Run locally (Windows)

```powershell
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the local URL shown in the terminal (normally http://localhost:8501).

## Run locally (macOS/Linux)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Data and demo records
On first launch, the app creates `productsphere.db` in the project directory and seeds a small example product, features, roadmap initiative and release. This allows the dashboard to be demonstrated immediately. The data is local and persists across restarts. Delete `productsphere.db` only if you want a fresh demo database; the sample records will be recreated.

## Scope and honest status
Implemented in this MVP: create products, create/update/delete features, impact/effort prioritization score, backlog filters, create/update roadmap initiatives, create releases, assign features to release scope, dashboard charts, activity logging, CSV export, SQLite persistence.

Not implemented: real user authentication/authorization, email notifications, integrations with Jira/GitHub, automated release deployment, AI-based prioritization, multi-user concurrency guarantees, cloud database/deployment, unit test suite. These are potential future enhancements and must not be described as completed.

## Architecture
Streamlit UI -> Python application logic -> SQLite database. Plotly renders charts and Pandas prepares tabular data.

## Notes
This is an academic MVP and local demonstration, not a production-hardened multi-tenant SaaS. Review and test it in your environment before presenting.
