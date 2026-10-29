import sqlite3
from pathlib import Path
from datetime import date, datetime
import pandas as pd
import plotly.express as px
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "productsphere.db"
img='C:\\Users\\Admin\\Desktop\\ProductSphere_PLM_MVP\\Logo.webp'
st.set_page_config(page_title="ProductSphere | PLM", page_icon=img, layout="wide")

STATUSES = ["Idea", "Planned", "In Progress", "In Review", "Done", "Blocked"]
PRIORITIES = ["Critical", "High", "Medium", "Low"]
ROADMAP_STATUSES = ["Proposed", "Planned", "In Progress", "Completed", "On Hold"]
RELEASE_STATUSES = ["Planning", "In Development", "Ready", "Released", "Delayed"]

def connect():
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con

def init_db():
    with connect() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT DEFAULT '',
            owner TEXT DEFAULT '',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS releases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            version TEXT NOT NULL,
            target_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Planning',
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            UNIQUE(product_id, version),
            FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS features (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            priority TEXT NOT NULL DEFAULT 'Medium',
            status TEXT NOT NULL DEFAULT 'Idea',
            impact INTEGER NOT NULL DEFAULT 3,
            effort INTEGER NOT NULL DEFAULT 3,
            owner TEXT DEFAULT '',
            release_id INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE,
            FOREIGN KEY(release_id) REFERENCES releases(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS roadmap_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            objective TEXT DEFAULT '',
            quarter TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Proposed',
            owner TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id INTEGER,
            created_at TEXT NOT NULL
        );
        """)
        count = con.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if count == 0:
            now = datetime.now().isoformat(timespec="seconds")
            con.execute("INSERT INTO products(name, description, owner, created_at) VALUES (?,?,?,?)",
                        ("LaunchPad", "A product discovery and launch workspace.", "Product Team", now))
            pid = con.execute("SELECT id FROM products WHERE name='LaunchPad'").fetchone()[0]
            con.execute("INSERT INTO releases(product_id, version, target_date, status, notes, created_at) VALUES (?,?,?,?,?,?)",
                        (pid, "v1.0", date.today().isoformat(), "In Development", "Initial demo release", now))
            rid = con.execute("SELECT id FROM releases WHERE product_id=? AND version='v1.0'", (pid,)).fetchone()[0]
            samples = [
                (pid, "User onboarding flow", "Reduce friction for new users.", "High", "In Progress", 5, 3, "Design", rid, now),
                (pid, "Usage analytics dashboard", "Help teams understand engagement.", "Medium", "Planned", 4, 4, "Analytics", rid, now),
                (pid, "Export roadmap to CSV", "Enable roadmap sharing with stakeholders.", "Low", "Idea", 2, 2, "Product", None, now),
                (pid, "Role-based access", "Separate admin and contributor permissions.", "Critical", "Blocked", 5, 4, "Engineering", None, now),
            ]
            con.executemany("""INSERT INTO features(product_id,title,description,priority,status,impact,effort,owner,release_id,created_at)
                               VALUES (?,?,?,?,?,?,?,?,?,?)""", samples)
            con.execute("""INSERT INTO roadmap_items(product_id,title,objective,quarter,status,owner,created_at)
                           VALUES (?,?,?,?,?,?,?)""",
                        (pid, "Improve activation", "Increase successful onboarding completion.", "Q4 2026", "In Progress", "Product Team", now))
            con.execute("INSERT INTO activity_log(event,entity_type,entity_id,created_at) VALUES (?,?,?,?)",
                        ("Demo workspace initialized", "system", None, now))

def log_event(event, entity_type, entity_id=None):
    with connect() as con:
        con.execute("INSERT INTO activity_log(event,entity_type,entity_id,created_at) VALUES (?,?,?,?)",
                    (event, entity_type, entity_id, datetime.now().isoformat(timespec="seconds")))

def query(sql, params=()):
    with connect() as con:
        return pd.read_sql_query(sql, con, params=params)

def run(sql, params=()):
    with connect() as con:
        cur = con.execute(sql, params)
        return cur.lastrowid

def products_df():
    return query("SELECT * FROM products ORDER BY name")

def product_options():
    df = products_df()
    return {f"{r['name']} (#{r['id']})": int(r["id"]) for _, r in df.iterrows()}

def choose_product(label="Product"):
    opts = product_options()
    if not opts:
        st.warning("Create a product first.")
        return None
    selected = st.selectbox(label, list(opts.keys()), key=label)
    return opts[selected]

def priority_score(impact, effort):
    return round((impact / max(effort, 1)) * 10, 1)

init_db()

st.markdown("""
<style>
.block-container {padding-top: 1.6rem; padding-bottom: 2rem;}
[data-testid="stMetric"] {background: rgba(120,130,150,.08); padding: 14px; border-radius: 12px;}
div[data-testid="stSidebar"] {border-right: 1px solid rgba(120,130,150,.2);}
.small-muted {color: #7b8494; font-size: .9rem;}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.logo(img)
    st.title(" ProductSphere")
    st.caption("Product Lifecycle Management")
    page = st.radio("Workspace", ["Overview", "Feature Backlog", "Roadmap", "Releases", "Products", "Data & Export"], label_visibility="collapsed")
    st.divider()
    st.caption("Local demo • SQLite persistence")
    st.caption("Seed data is included for demonstration.")

if page == "Overview":
    st.title("Product portfolio")
    st.write("A single workspace to plan, prioritize, and deliver product improvements.")
    products = query("SELECT * FROM products")
    features = query("""SELECT f.*, p.name AS product_name, r.version AS release_version
                        FROM features f JOIN products p ON p.id=f.product_id
                        LEFT JOIN releases r ON r.id=f.release_id""")
    releases = query("""SELECT r.*, p.name AS product_name FROM releases r JOIN products p ON p.id=r.product_id""")
    roadmap = query("SELECT * FROM roadmap_items")
    overdue = 0
    if not releases.empty:
        overdue = int(((pd.to_datetime(releases["target_date"], errors="coerce").dt.date < date.today()) &
                       (~releases["status"].isin(["Released"]))).sum())
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Products", len(products))
    c2.metric("Features", len(features))
    c3.metric("Active roadmap items", int(roadmap["status"].isin(["Planned","In Progress"]).sum()) if not roadmap.empty else 0)
    c4.metric("Open releases", int((~releases["status"].isin(["Released"])).sum()) if not releases.empty else 0)
    left,right = st.columns([1.25,1])
    with left:
        st.subheader("Feature workflow")
        if not features.empty:
            order = ["Idea","Planned","In Progress","In Review","Done","Blocked"]
            flow = features["status"].value_counts().reindex(order, fill_value=0).rename_axis("Status").reset_index(name="Features")
            st.plotly_chart(px.bar(flow, x="Status", y="Features", color="Status", title="Features by status"), use_container_width=True)
        else:
            st.info("Add features to see workflow analytics.")
    with right:
        st.subheader("Priority mix")
        if not features.empty:
            mix = features["priority"].value_counts().rename_axis("Priority").reset_index(name="Count")
            st.plotly_chart(px.pie(mix, names="Priority", values="Count", hole=.5), use_container_width=True)
        else:
            st.info("No features yet.")
    st.subheader("Recently updated workspace")
    if not features.empty:
        view = features[["title","product_name","priority","status","owner","release_version"]].copy()
        view.columns = ["Feature","Product","Priority","Status","Owner","Release"]
        st.dataframe(view, use_container_width=True, hide_index=True)
    st.caption("Metrics are calculated from records in the local database; sample records are labelled as demo data in the README.")

elif page == "Feature Backlog":
    st.title("Feature backlog")
    st.write("Capture requests, rank them by value versus effort, and track delivery status.")
    with st.expander("＋ Add feature", expanded=False):
        pid = choose_product("Feature product")
        with st.form("add_feature_form", clear_on_submit=True):
            title = st.text_input("Feature title")
            description = st.text_area("Description / user problem")
            a,b = st.columns(2)
            priority = a.selectbox("Priority", PRIORITIES, index=2)
            status = b.selectbox("Status", STATUSES)
            c,d = st.columns(2)
            impact = c.slider("Business / user impact", 1, 5, 3)
            effort = d.slider("Estimated effort", 1, 5, 3)
            owner = st.text_input("Owner / team")
            if st.form_submit_button("Add feature", type="primary"):
                if not pid or not title.strip():
                    st.error("Choose a product and enter a feature title.")
                else:
                    fid = run("""INSERT INTO features(product_id,title,description,priority,status,impact,effort,owner,created_at)
                                 VALUES (?,?,?,?,?,?,?,?,?)""",
                               (pid,title.strip(),description.strip(),priority,status,impact,effort,owner.strip(),datetime.now().isoformat(timespec="seconds")))
                    log_event(f"Created feature: {title.strip()}", "feature", fid)
                    st.success("Feature added.")
                    st.rerun()
    data = query("""SELECT f.id, f.title, p.name AS product, f.priority, f.status, f.impact, f.effort,
                    ROUND((CAST(f.impact AS REAL)/MAX(f.effort,1))*10,1) AS score,
                    f.owner, r.version AS release
                    FROM features f JOIN products p ON p.id=f.product_id
                    LEFT JOIN releases r ON r.id=f.release_id ORDER BY
                    CASE f.priority WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END, score DESC""")
    if not data.empty:
        f1,f2,f3 = st.columns(3)
        priority_filter = f1.multiselect("Priority filter", PRIORITIES, default=PRIORITIES)
        status_filter = f2.multiselect("Status filter", STATUSES, default=STATUSES)
        search = f3.text_input("Search features", placeholder="Type a title...")
        filtered = data[data["priority"].isin(priority_filter) & data["status"].isin(status_filter)]
        if search:
            filtered = filtered[filtered["title"].str.contains(search, case=False, na=False)]
        st.dataframe(filtered, use_container_width=True, hide_index=True)
        st.caption("Priority score = impact ÷ effort × 10. It is a simple decision aid, not an automated product decision.")
        st.subheader("Update a feature")
        ids = data["id"].astype(int).tolist()
        selected_id = st.selectbox("Feature ID", ids, format_func=lambda x: f"#{x} — {data.loc[data.id==x,'title'].iloc[0]}")
        selected = data[data["id"] == selected_id].iloc[0]
        with st.form("update_feature_form"):
            u1,u2 = st.columns(2)
            new_status = u1.selectbox("New status", STATUSES, index=STATUSES.index(selected["status"]))
            new_priority = u2.selectbox("New priority", PRIORITIES, index=PRIORITIES.index(selected["priority"]))
            if st.form_submit_button("Save feature changes"):
                run("UPDATE features SET status=?, priority=? WHERE id=?", (new_status,new_priority,int(selected_id)))
                log_event(f"Updated feature #{selected_id}: {new_status}/{new_priority}", "feature", int(selected_id))
                st.success("Feature updated.")
                st.rerun()
        with st.expander("Delete feature"):
            st.warning("Deletion is permanent for this local demo database.")
            confirm = st.checkbox("I understand and want to delete the selected feature.")
            if st.button("Delete selected feature", disabled=not confirm):
                run("DELETE FROM features WHERE id=?", (int(selected_id),))
                log_event(f"Deleted feature #{selected_id}", "feature", int(selected_id))
                st.success("Feature deleted.")
                st.rerun()
    else:
        st.info("No features yet. Add the first feature above.")

elif page == "Roadmap":
    st.title("Product roadmap")
    st.write("Communicate strategic outcomes and delivery horizons; roadmap dates are targets, not guarantees.")
    with st.expander("＋ Add roadmap initiative", expanded=False):
        pid = choose_product("Roadmap product")
        with st.form("roadmap_form", clear_on_submit=True):
            title = st.text_input("Initiative")
            objective = st.text_area("Strategic objective / expected outcome")
            q = st.selectbox("Target quarter", ["Q4 2026","Q1 2027","Q2 2027","Q3 2027","Q4 2027"])
            a,b = st.columns(2)
            status = a.selectbox("Status", ROADMAP_STATUSES)
            owner = b.text_input("Owner / team")
            if st.form_submit_button("Add initiative", type="primary"):
                if not pid or not title.strip():
                    st.error("Choose a product and enter an initiative.")
                else:
                    rid = run("""INSERT INTO roadmap_items(product_id,title,objective,quarter,status,owner,created_at)
                                 VALUES (?,?,?,?,?,?,?)""",
                              (pid,title.strip(),objective.strip(),q,status,owner.strip(),datetime.now().isoformat(timespec="seconds")))
                    log_event(f"Created roadmap initiative: {title.strip()}", "roadmap", rid)
                    st.success("Roadmap initiative added.")
                    st.rerun()
    road = query("""SELECT r.id, p.name AS product, r.title AS initiative, r.objective, r.quarter, r.status, r.owner
                    FROM roadmap_items r JOIN products p ON p.id=r.product_id
                    ORDER BY r.quarter, r.id""")
    if not road.empty:
        st.dataframe(road, use_container_width=True, hide_index=True)
        st.subheader("Roadmap timeline")
        road["Start"] = road["quarter"].map(lambda x: {"Q1": f"{x[-4:]}-01-01","Q2":f"{x[-4:]}-04-01","Q3":f"{x[-4:]}-07-01","Q4":f"{x[-4:]}-10-01"}.get(x[:2],f"{date.today().year}-01-01"))
        road["End"] = pd.to_datetime(road["Start"]) + pd.Timedelta(days=80)
        fig = px.timeline(road, x_start="Start", x_end="End", y="initiative", color="status", hover_data=["product","quarter","owner"])
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)
        st.subheader("Update initiative")
        selected_id = st.selectbox("Initiative ID", road["id"].astype(int).tolist(),
                                   format_func=lambda x: f"#{x} — {road.loc[road.id==x,'initiative'].iloc[0]}")
        selected = road[road["id"]==selected_id].iloc[0]
        with st.form("update_roadmap_form"):
            new_status = st.selectbox("Status", ROADMAP_STATUSES, index=ROADMAP_STATUSES.index(selected["status"]))
            if st.form_submit_button("Update status"):
                run("UPDATE roadmap_items SET status=? WHERE id=?", (new_status,int(selected_id)))
                log_event(f"Updated roadmap initiative #{selected_id}: {new_status}", "roadmap", int(selected_id))
                st.success("Initiative updated.")
                st.rerun()
    else:
        st.info("Add an initiative to start your roadmap.")

elif page == "Releases":
    st.title("Release planning")
    st.write("Plan versions, assign target dates, and associate backlog features with releases.")
    with st.expander("＋ Create release", expanded=False):
        pid = choose_product("Release product")
        with st.form("release_form", clear_on_submit=True):
            version = st.text_input("Version", placeholder="v1.1")
            target = st.date_input("Target release date", value=date.today())
            status = st.selectbox("Release status", RELEASE_STATUSES)
            notes = st.text_area("Release notes / scope")
            if st.form_submit_button("Create release", type="primary"):
                if not pid or not version.strip():
                    st.error("Choose a product and enter a version.")
                else:
                    try:
                        rid = run("""INSERT INTO releases(product_id,version,target_date,status,notes,created_at)
                                     VALUES (?,?,?,?,?,?)""",
                                  (pid,version.strip(),target.isoformat(),status,notes.strip(),datetime.now().isoformat(timespec="seconds")))
                        log_event(f"Created release {version.strip()}", "release", rid)
                        st.success("Release created.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("That version already exists for this product.")
    releases = query("""SELECT r.id, p.name AS product, r.version, r.target_date, r.status, r.notes
                        FROM releases r JOIN products p ON p.id=r.product_id ORDER BY r.target_date""")
    if not releases.empty:
        st.dataframe(releases, use_container_width=True, hide_index=True)
        rel_ids = releases["id"].astype(int).tolist()
        chosen = st.selectbox("Choose release to manage", rel_ids,
                              format_func=lambda x: f"{releases.loc[releases.id==x,'product'].iloc[0]} — {releases.loc[releases.id==x,'version'].iloc[0]}")
        rel = releases[releases.id==chosen].iloc[0]
        linked = query("SELECT id,title,status,priority FROM features WHERE release_id=? ORDER BY priority,title", (int(chosen),))
        st.subheader(f"Scope: {rel['version']}")
        if not linked.empty:
            st.dataframe(linked, use_container_width=True, hide_index=True)
        else:
            st.info("No features assigned to this release yet.")
        product_features = query("SELECT id,title,release_id FROM features WHERE product_id=(SELECT product_id FROM releases WHERE id=?) ORDER BY title", (int(chosen),))
        if not product_features.empty:
            choices = product_features["id"].astype(int).tolist()
            current = product_features[product_features["release_id"]==chosen]["id"].astype(int).tolist()
            with st.form("release_scope_form"):
                selected_features = st.multiselect("Features included in this release", choices,
                    default=current,
                    format_func=lambda x: f"#{x} — {product_features.loc[product_features.id==x,'title'].iloc[0]}")
                if st.form_submit_button("Save release scope"):
                    with connect() as con:
                        con.execute("UPDATE features SET release_id=NULL WHERE product_id=(SELECT product_id FROM releases WHERE id=?) AND release_id=?", (int(chosen),int(chosen)))
                        for fid in selected_features:
                            con.execute("UPDATE features SET release_id=? WHERE id=?", (int(chosen),int(fid)))
                    log_event(f"Updated scope for release {rel['version']}", "release", int(chosen))
                    st.success("Release scope saved.")
                    st.rerun()
        with st.form("release_status_form"):
            new_status = st.selectbox("Update release status", RELEASE_STATUSES, index=RELEASE_STATUSES.index(rel["status"]))
            if st.form_submit_button("Save release status"):
                run("UPDATE releases SET status=? WHERE id=?", (new_status,int(chosen)))
                log_event(f"Updated release {rel['version']}: {new_status}", "release", int(chosen))
                st.success("Release status updated.")
                st.rerun()
    else:
        st.info("Create a release to begin release planning.")

elif page == "Products":
    st.title("Product portfolio")
    with st.expander("＋ Add product", expanded=True):
        with st.form("product_form", clear_on_submit=True):
            name = st.text_input("Product name")
            description = st.text_area("Product vision / description")
            owner = st.text_input("Product owner / team")
            if st.form_submit_button("Create product", type="primary"):
                if not name.strip():
                    st.error("Product name is required.")
                else:
                    try:
                        pid = run("INSERT INTO products(name,description,owner,created_at) VALUES (?,?,?,?)",
                                  (name.strip(),description.strip(),owner.strip(),datetime.now().isoformat(timespec="seconds")))
                        log_event(f"Created product: {name.strip()}", "product", pid)
                        st.success("Product created.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("A product with that name already exists.")
    products = query("""SELECT p.id,p.name,p.description,p.owner,p.created_at,
                        (SELECT COUNT(*) FROM features f WHERE f.product_id=p.id) AS feature_count,
                        (SELECT COUNT(*) FROM releases r WHERE r.product_id=p.id) AS release_count
                        FROM products p ORDER BY p.name""")
    st.dataframe(products, use_container_width=True, hide_index=True)
    st.caption("Products with linked features or releases are protected by relational constraints; delete workflows are intentionally omitted from this demo.")

elif page == "Data & Export":
    st.title("Data & export")
    st.write("Download the current application data for review or submission evidence.")
    exports = {
        "Products": "SELECT * FROM products",
        "Features": """SELECT f.*, p.name AS product_name, r.version AS release_version
                       FROM features f JOIN products p ON p.id=f.product_id LEFT JOIN releases r ON r.id=f.release_id""",
        "Roadmap": """SELECT r.*, p.name AS product_name FROM roadmap_items r JOIN products p ON p.id=r.product_id""",
        "Releases": """SELECT r.*, p.name AS product_name FROM releases r JOIN products p ON p.id=r.product_id""",
        "Activity log": "SELECT * FROM activity_log ORDER BY created_at DESC",
    }
    for label, sql in exports.items():
        df = query(sql)
        st.subheader(label)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button(f"Download {label} CSV", df.to_csv(index=False).encode("utf-8"),
                           file_name=label.lower().replace(" ","_")+".csv", mime="text/csv", key=f"download_{label}")
    st.info("The SQLite database is created in the project folder on first run. Back up productsphere.db to preserve demo data.")

st.divider()
st.caption("ProductSphere MVP • Roadmaps, feature prioritization, and release planning • For academic demonstration")
