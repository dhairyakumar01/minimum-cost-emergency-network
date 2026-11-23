"""Minimum-Cost Emergency Communication Network Using MST.

Four-screen Streamlit application:
  1. Dashboard / project overview
  2. Emergency facilities map (filters + search)
  3. MST network visualization (Prim or Kruskal)
  4. Algorithm comparison and validation

Run from the project folder:  python -m streamlit run app.py
Everything shown is read from the project's data and result files.
"""
import html as html_lib
import inspect
import json
import re
from pathlib import Path

import folium
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(
    page_title="Emergency MST Network | Bengaluru",
    page_icon="🚨",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent
PATHS = {
    "facilities": BASE_DIR / "data" / "processed" / "emergency_facilities.csv",
    "prim": BASE_DIR / "results" / "prim_mst_edges.csv",
    "kruskal": BASE_DIR / "results" / "kruskal_mst_edges.csv",
    "report": BASE_DIR / "results" / "validation_report.json",
    "benchmark": BASE_DIR / "results" / "benchmark.json",
    "quality": BASE_DIR / "reports" / "data_quality_summary.json",
}
ALGO_FILE = {"Prim": "prim", "Kruskal": "kruskal"}
ALGO_COLOR = {"Prim": "#2e7d32", "Kruskal": "#8e24aa"}
TYPE_COLOR = {
    "hospital": "#d62728",
    "police_station": "#1f4fd8",
    "fire_station": "#ff8c00",
}
TYPE_LABEL = {
    "hospital": "Hospital",
    "police_station": "Police station",
    "fire_station": "Fire station",
}
REQUIRED_COLS = {"facility_id", "facility_name", "facility_type", "latitude", "longitude"}
EARTH_KM = 6371.0088

st.markdown(
    """
    <style>
    [data-testid="stMetric"] {
        background: rgba(128,128,128,0.08);
        border: 1px solid rgba(128,128,128,0.25);
        border-radius: 10px;
        padding: 12px 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

_PLOT_HAS_WIDTH = "width" in inspect.signature(st.plotly_chart).parameters
_DF_HAS_WIDTH = "width" in inspect.signature(st.dataframe).parameters


def show_fig(fig):
    if _PLOT_HAS_WIDTH:
        st.plotly_chart(fig, width="stretch")
    else:
        st.plotly_chart(fig, use_container_width=True)


def show_df(df):
    if _DF_HAS_WIDTH:
        st.dataframe(df, width="stretch", hide_index=True)
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)


# ----------------------------------------------------------------------------
# Data loading
# ----------------------------------------------------------------------------
def stop_missing(path, hint="Run `python run_analysis.py` from the project folder first."):
    st.error(f"Required file not found: `{path.relative_to(BASE_DIR)}`")
    st.info(hint)
    st.stop()


@st.cache_data(show_spinner=False)
def _read_csv(path, mtime):
    return pd.read_csv(path)


@st.cache_data(show_spinner=False)
def _read_json(path, mtime):
    return json.loads(Path(path).read_text())


def load_csv(key, required=True):
    path = PATHS[key]
    if not path.exists():
        if required:
            stop_missing(path)
        return None
    return _read_csv(str(path), path.stat().st_mtime).copy()


def load_json(key):
    path = PATHS[key]
    if not path.exists():
        return None
    try:
        return _read_json(str(path), path.stat().st_mtime)
    except ValueError:
        st.warning(f"`{path.relative_to(BASE_DIR)}` could not be read as JSON.")
        return None


def load_facilities():
    df = load_csv("facilities")
    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        st.error(f"Facility file is missing columns: {sorted(missing)}")
        st.write("Columns found:", df.columns.tolist())
        st.stop()
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df.dropna(subset=["facility_id", "latitude", "longitude"]).copy()
    df["facility_id"] = df["facility_id"].astype(str)
    df["facility_name"] = df["facility_name"].fillna("").astype(str).str.strip()
    df.loc[df["facility_name"] == "", "facility_name"] = "Unnamed facility"
    return df.reset_index(drop=True)


def load_mst(algo, required=True):
    df = load_csv(ALGO_FILE[algo], required=required)
    if df is None:
        return None
    missing = {"u", "v", "weight_km"} - set(df.columns)
    if missing:
        st.error(f"{algo} edge file is missing columns: {sorted(missing)}")
        st.stop()
    return df


def haversine_vec(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp = p2 - p1
    dl = np.radians(lon2 - lon1)
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * EARTH_KM * np.arcsin(np.minimum(1, np.sqrt(a)))


def prepare_mst(edges, fac):
    """Attach endpoint coordinates by facility ID and verify each weight."""
    coords = fac.drop_duplicates("facility_id").set_index("facility_id")[["latitude", "longitude"]]
    e = edges.copy()
    e["u"] = e["u"].astype(str)
    e["v"] = e["v"].astype(str)
    e = e.join(coords.add_prefix("u_"), on="u").join(coords.add_prefix("v_"), on="v")
    cols = ["u_latitude", "u_longitude", "v_latitude", "v_longitude"]
    e["matched"] = e[cols].notna().all(axis=1)
    e["recomputed_km"] = np.nan
    ok = e["matched"]
    if ok.any():
        e.loc[ok, "recomputed_km"] = haversine_vec(
            *[e.loc[ok, c].to_numpy(dtype=float) for c in cols]
        )
    return e


# ----------------------------------------------------------------------------
# Map helpers
# ----------------------------------------------------------------------------
def legend_html(edge_algo=None):
    items = [
        f'<span style="display:inline-block;width:12px;height:12px;border-radius:50%;'
        f'background:{TYPE_COLOR[t]};margin-right:6px;"></span>{TYPE_LABEL[t]}'
        for t in TYPE_COLOR
    ]
    if edge_algo:
        items.append(
            f'<span style="display:inline-block;width:24px;height:3px;'
            f'background:{ALGO_COLOR[edge_algo]};margin-right:6px;vertical-align:middle;"></span>'
            f"{edge_algo} MST connection"
        )
    return (
        '<div style="display:flex;gap:20px;flex-wrap:wrap;font-size:0.9rem;margin:2px 0 8px 0;">'
        + "".join(f"<span>{i}</span>" for i in items)
        + "</div>"
    )


def new_map(fac, focus=None):
    if focus is not None:
        return folium.Map(
            location=[float(focus["latitude"]), float(focus["longitude"])],
            zoom_start=16,
            control_scale=True,
        )
    m = folium.Map(
        location=[fac["latitude"].mean(), fac["longitude"].mean()],
        zoom_start=11,
        control_scale=True,
    )
    m.fit_bounds(
        [
            [fac["latitude"].min(), fac["longitude"].min()],
            [fac["latitude"].max(), fac["longitude"].max()],
        ]
    )
    return m


def add_markers(m, df, radius=4, highlight_id=None):
    """Draw facilities as ONE GeoJSON layer (much faster than one object per marker)."""
    esc = html_lib.escape
    feats = []
    for r in df.itertuples(index=False):
        feats.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [r.longitude, r.latitude]},
                "properties": {
                    "name": esc(str(r.facility_name)),
                    "type": esc(TYPE_LABEL.get(r.facility_type, str(r.facility_type))),
                    "id": esc(str(r.facility_id)),
                    "lat": f"{r.latitude:.6f}",
                    "lon": f"{r.longitude:.6f}",
                    "color": TYPE_COLOR.get(r.facility_type, "#666666"),
                },
            }
        )
    folium.GeoJson(
        {"type": "FeatureCollection", "features": feats},
        name="Facilities",
        marker=folium.CircleMarker(radius=radius, weight=1, fill=True, fill_opacity=0.85),
        style_function=lambda f: {
            "color": f["properties"]["color"],
            "fillColor": f["properties"]["color"],
        },
        tooltip=folium.GeoJsonTooltip(fields=["name"], labels=False),
        popup=folium.GeoJsonPopup(
            fields=["name", "type", "id", "lat", "lon"],
            aliases=["Name", "Type", "ID", "Latitude", "Longitude"],
            max_width=320,
        ),
    ).add_to(m)
    if highlight_id is not None:
        row = df[df["facility_id"] == highlight_id]
        if not row.empty:
            folium.CircleMarker(
                location=[float(row.iloc[0]["latitude"]), float(row.iloc[0]["longitude"])],
                radius=14,
                color="black",
                weight=3,
                fill=False,
            ).add_to(m)


def add_edges(m, e, color):
    """Draw all matched MST edges as ONE GeoJSON layer."""
    esc = html_lib.escape
    feats = []
    for r in e[e["matched"]].itertuples(index=False):
        un = esc(str(getattr(r, "u_name", r.u)))
        vn = esc(str(getattr(r, "v_name", r.v)))
        feats.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[r.u_longitude, r.u_latitude], [r.v_longitude, r.v_latitude]],
                },
                "properties": {"link": f"{un} ↔ {vn}: {r.weight_km:.3f} km"},
            }
        )
    folium.GeoJson(
        {"type": "FeatureCollection", "features": feats},
        name="MST connections",
        style_function=lambda f: {"color": color, "weight": 2, "opacity": 0.65},
        tooltip=folium.GeoJsonTooltip(fields=["link"], labels=False, sticky=True),
    ).add_to(m)


def runtime_info(algo):
    """Return (value_string, label, caption) for the selected algorithm."""
    bench = load_json("benchmark")
    report = load_json("report")
    key = f"{algo.lower()}_seconds"
    if bench and key in bench:
        runs = bench.get("runs", "?")
        return (
            f"{bench[key]['median']:.4f} s",
            f"Median runtime ({runs} runs)",
            "Median of repeated timings from benchmark.py on one machine; edge generation excluded.",
        )
    single = f"{algo.lower()}_runtime_seconds"
    if report and single in report:
        return (
            f"{report[single]:.4f} s",
            "Recorded runtime (single run)",
            "One recorded run from run_analysis.py. Run benchmark.py for repeated timings.",
        )
    return "n/a", "Runtime", "No runtime file found."


# ----------------------------------------------------------------------------
# SCREEN 1: Dashboard
# ----------------------------------------------------------------------------
def page_overview():
    fac = load_facilities()
    n = len(fac)
    counts = fac["facility_type"].value_counts()
    report = load_json("report")
    prim = load_mst("Prim", required=False)
    kruskal = load_mst("Kruskal", required=False)

    st.title("🚨 Minimum-Cost Emergency Communication Network")
    st.caption("Discrete Mathematics and Graph Theory (DMGT) project  |  Bengaluru, Karnataka, India")

    st.info(
        "**Problem statement.** Hospitals, police stations and fire stations in Bengaluru "
        "must be connected into a single network. Among all ways to connect them, which "
        "set of links has the smallest total length? A Minimum Spanning Tree (MST) of the "
        "facility graph answers this exactly."
    )

    st.subheader("Facilities")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total facilities", f"{n:,}")
    c2.metric("Hospitals", f"{int(counts.get('hospital', 0)):,}")
    c3.metric("Police stations", f"{int(counts.get('police_station', 0)):,}")
    c4.metric("Fire stations", f"{int(counts.get('fire_station', 0)):,}")

    st.subheader("Network")
    ref = prim if prim is not None else kruskal
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("MST edges", f"{len(ref):,}" if ref is not None else "n/a", help=f"A spanning tree on V vertices has V − 1 edges (V = {n:,}).")
    c2.metric("Total network distance", f"{ref['weight_km'].sum():,.4f} km" if ref is not None else "n/a")
    c3.metric("Candidate edges (complete graph)", f"{n * (n - 1) // 2:,}", help="V(V − 1)/2 possible facility pairs.")
    if report is None:
        status = "Not available"
    else:
        status = "Passed" if report.get("validation_passed") else "Failed"
    c4.metric("Validation", status)
    if prim is not None and kruskal is not None:
        diff = abs(float(prim["weight_km"].sum()) - float(kruskal["weight_km"].sum()))
        st.caption(
            f"Prim and Kruskal total distances differ by {diff:.2e} km (floating-point rounding). "
            "Distances are Haversine straight-line kilometres."
        )

    left, right = st.columns([1.5, 1], gap="large")
    with left:
        st.subheader("Objective")
        st.markdown(
            """
            Build a **minimum-total-distance network** that connects every emergency
            facility, and compare two classic algorithms that compute it.

            **How the model works**
            - **Vertices:** each hospital, police station and fire station.
            - **Edges:** every pair of facilities can be linked (a complete graph).
            - **Weights:** the Haversine great-circle distance between the two facilities, in km.
            - **MST:** the subset of edges that connects all vertices, has no cycles, and has the smallest total weight.
            - **Algorithms:** Prim's (grows one tree outward) and Kruskal's (adds the shortest edges that create no cycle).

            **Where to look**
            - **Facilities Map:** all facilities, filters and search.
            - **MST Network:** the Prim or Kruskal network drawn on the map.
            - **Comparison & Validation:** side-by-side results, charts and checks.
            """
        )
    with right:
        labels = [TYPE_LABEL.get(t, t) for t in counts.index]
        fig = go.Figure(
            go.Pie(
                labels=labels,
                values=counts.values,
                hole=0.55,
                marker=dict(colors=[TYPE_COLOR.get(t, "#888888") for t in counts.index]),
                sort=False,
            )
        )
        fig.update_layout(
            title="Facilities by type",
            margin=dict(l=10, r=10, t=50, b=10),
            height=330,
            legend=dict(orientation="h", y=-0.05),
        )
        show_fig(fig)

    st.warning(
        "**Interpretation.** Edge weights are straight-line (Haversine) distances. They are not "
        "financial installation costs, road distances, travel times or emergency response times. "
        "\"Minimum-cost\" here means minimum total straight-line distance."
    )


# ----------------------------------------------------------------------------
# SCREEN 2: Facilities map
# ----------------------------------------------------------------------------
def page_map():
    st.title("🗺️ Emergency Facilities Map")
    fac = load_facilities()
    all_types = sorted(fac["facility_type"].dropna().unique().tolist())

    left, right = st.columns([1, 2.6], gap="large")
    focus = None
    with left:
        selected = st.multiselect(
            "Facility types",
            all_types,
            default=all_types,
            format_func=lambda t: TYPE_LABEL.get(t, t),
            key="map_types",
        )
        view = fac[fac["facility_type"].isin(selected)]
        query = st.text_input(
            "Search by name or ID",
            placeholder="e.g. Victoria, unnamed, way/12345",
            key="map_query",
        )
        if query.strip():
            q = query.strip()
            hit = view[
                view["facility_name"].str.contains(q, case=False, regex=False)
                | view["facility_id"].str.contains(q, case=False, regex=False)
            ]
            if hit.empty:
                st.warning("No facility matches that search in the selected types.")
            else:
                shown = hit.head(200)
                st.caption(
                    f"{len(hit):,} match(es)" + (", showing the first 200" if len(hit) > 200 else "")
                )
                pick = st.selectbox(
                    "Select a match",
                    shown.index.tolist(),
                    format_func=lambda i: (
                        f"{fac.at[i, 'facility_name']}  ·  "
                        f"{TYPE_LABEL.get(fac.at[i, 'facility_type'], fac.at[i, 'facility_type'])}  ·  "
                        f"{fac.at[i, 'facility_id']}"
                    ),
                    key="map_pick",
                )
                focus = fac.loc[pick]

        st.metric("Facilities shown", f"{len(view):,}", help=f"of {len(fac):,} in the dataset")
        breakdown = view["facility_type"].value_counts()
        st.caption(
            "  ·  ".join(f"{TYPE_LABEL.get(t, t)}: {int(c):,}" for t, c in breakdown.items())
        )
        st.caption(
            "Filters and search change only which markers are displayed. They never "
            "change the graph or the MST."
        )

        if focus is not None:
            st.markdown("**Facility details**")
            d = focus.to_dict()
            details = pd.DataFrame(
                {"Field": [str(k) for k in d], "Value": [str(v) for v in d.values()]}
            )
            show_df(details)
            if re.match(r"^(node|way|relation)/\d+$", str(focus["facility_id"])):
                st.link_button(
                    "Open source record on OpenStreetMap",
                    f"https://www.openstreetmap.org/{focus['facility_id']}",
                )

    with right:
        if view.empty:
            st.warning("Select at least one facility type.")
            return
        st.markdown(legend_html(), unsafe_allow_html=True)
        m = new_map(fac, focus)
        add_markers(
            m, view, radius=4,
            highlight_id=None if focus is None else focus["facility_id"],
        )
        st_folium(m, width=None, height=640, returned_objects=[], key="facilities_map")
        st.caption("Click a marker to see its details. Hover to see the facility name.")


# ----------------------------------------------------------------------------
# SCREEN 3: MST network
# ----------------------------------------------------------------------------
def page_mst():
    st.title("🕸️ MST Network Visualization")
    fac = load_facilities()

    c1, c2, c3 = st.columns([2, 1, 1])
    algo = c1.radio("Algorithm", ["Prim", "Kruskal"], horizontal=True, key="mst_algo")
    show_edges = c2.checkbox("Show MST connections", value=True, key="mst_edges")
    show_markers = c3.checkbox("Show facility markers", value=True, key="mst_markers")

    raw = load_mst(algo)
    e = prepare_mst(raw, fac)
    matched = int(e["matched"].sum())
    unmatched = len(e) - matched
    total = float(raw["weight_km"].sum())
    value, label, caption = runtime_info(algo)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric(f"{algo} MST edges", f"{len(raw):,}", help=f"Expected V − 1 = {len(fac) - 1:,}")
    m2.metric("Total network distance", f"{total:,.4f} km")
    m3.metric(label, value)
    m4.metric("Edges with unmatched IDs", f"{unmatched:,}")

    diff = (e["weight_km"] - e["recomputed_km"]).abs().max()
    diff_text = "n/a" if pd.isna(diff) else f"{diff:.2e} km"
    st.caption(
        f"ID check: {matched:,} of {len(e):,} edges matched facility IDs in the dataset. "
        f"Largest gap between stored and recomputed edge length: {diff_text}. {caption}"
    )

    st.markdown(legend_html(algo if show_edges else None), unsafe_allow_html=True)
    m = new_map(fac)
    if show_edges:
        add_edges(m, e, ALGO_COLOR[algo])
    if show_markers:
        add_markers(m, fac, radius=3)
    st_folium(m, width=None, height=640, returned_objects=[], key=f"mst_map_{algo}")
    st.caption(
        f"All {matched:,} {algo} MST connections are drawn, over all {len(fac):,} facilities. "
        "Hover a line to see the two facilities and the distance."
    )

    with st.expander("Longest 10 connections in this MST"):
        longest = (
            raw.assign(weight_km=raw["weight_km"].astype(float))
            .sort_values("weight_km", ascending=False)
            .head(10)
        )
        cols = [c for c in ["u_name", "u_type", "v_name", "v_type", "weight_km"] if c in longest.columns]
        table = longest[cols].copy()
        table["weight_km"] = table["weight_km"].map(lambda x: f"{x:.3f}")
        show_df(table.astype(str))

    path = PATHS[ALGO_FILE[algo]]
    st.download_button(
        f"Download {algo} MST edges (CSV)",
        data=path.read_bytes(),
        file_name=path.name,
        mime="text/csv",
    )


# ----------------------------------------------------------------------------
# SCREEN 4: Comparison and validation
# ----------------------------------------------------------------------------
def edge_keys(df):
    return {tuple(sorted(x)) for x in zip(df["u"].astype(str), df["v"].astype(str))}


def pair_labels(df):
    return [
        " – ".join(sorted([str(a).replace("_", " "), str(b).replace("_", " ")]))
        for a, b in zip(df["u_type"], df["v_type"])
    ]


def page_compare():
    st.title("⚖️ Algorithm Comparison and Validation")
    fac = load_facilities()
    n = len(fac)
    prim = load_mst("Prim")
    kruskal = load_mst("Kruskal")
    report = load_json("report")
    bench = load_json("benchmark")

    tp, tk = float(prim["weight_km"].sum()), float(kruskal["weight_km"].sum())
    shared = len(edge_keys(prim) & edge_keys(kruskal))

    k1, k2, k3 = st.columns(3)
    k1.metric("Total distance difference", f"{abs(tp - tk):.2e} km", help="Rounding noise; both are minimum spanning trees.")
    k2.metric("Edges in both MSTs", f"{shared:,} of {len(prim):,}", help="An MST can differ when edge weights tie, while the total stays equal.")
    if report is None:
        status = "Not available"
    else:
        status = "Passed" if report.get("validation_passed") else "Failed"
    k3.metric("Validation", status)

    st.subheader("Results")
    rows = [
        ("Vertices (facilities)", f"{n:,}", f"{n:,}"),
        ("Candidate edges (complete graph)", f"{n * (n - 1) // 2:,}", f"{n * (n - 1) // 2:,}"),
        (f"MST edges (expected V − 1 = {n - 1:,})", f"{len(prim):,}", f"{len(kruskal):,}"),
        ("Total distance (km)", f"{tp:.6f}", f"{tk:.6f}"),
    ]
    if bench and "prim_seconds" in bench and "kruskal_seconds" in bench:
        runs = bench.get("runs", "?")
        rows.append((f"Median runtime, {runs} runs (s)", f"{bench['prim_seconds']['median']:.4f}", f"{bench['kruskal_seconds']['median']:.4f}"))
        rows.append(("Runtime std. deviation (s)", f"{bench['prim_seconds']['stdev']:.4f}", f"{bench['kruskal_seconds']['stdev']:.4f}"))
    if report and "prim_runtime_seconds" in report and "kruskal_runtime_seconds" in report:
        rows.append(("Single recorded run (s)", f"{report['prim_runtime_seconds']:.4f}", f"{report['kruskal_runtime_seconds']:.4f}"))
    pc = report.get("prim_checks") if report else None
    kc = report.get("kruskal_checks") if report else None
    if pc and kc:
        rows.append(("Independent validation checks", "Passed" if all(pc.values()) else "Failed", "Passed" if all(kc.values()) else "Failed"))
    show_df(pd.DataFrame(rows, columns=["Metric", "Prim", "Kruskal"]))
    st.caption(
        "Runtimes depend on this implementation, this dataset and this machine. They are not "
        "general claims about which algorithm is faster."
    )

    st.subheader("Charts")
    ch1, ch2 = st.columns(2, gap="large")
    with ch1:
        if bench and "prim_seconds" in bench and "kruskal_seconds" in bench:
            fig = go.Figure(
                go.Bar(
                    x=["Prim", "Kruskal"],
                    y=[bench["prim_seconds"]["median"], bench["kruskal_seconds"]["median"]],
                    error_y=dict(type="data", array=[bench["prim_seconds"]["stdev"], bench["kruskal_seconds"]["stdev"]]),
                    marker_color=[ALGO_COLOR["Prim"], ALGO_COLOR["Kruskal"]],
                    text=[f"{bench['prim_seconds']['median']:.3f}", f"{bench['kruskal_seconds']['median']:.3f}"],
                    textposition="outside",
                )
            )
            fig.update_layout(title="Median runtime (s), error bars = std. deviation", yaxis_title="seconds", height=380, margin=dict(t=60, b=20))
            show_fig(fig)
        elif report and "prim_runtime_seconds" in report:
            fig = go.Figure(
                go.Bar(
                    x=["Prim", "Kruskal"],
                    y=[report["prim_runtime_seconds"], report["kruskal_runtime_seconds"]],
                    marker_color=[ALGO_COLOR["Prim"], ALGO_COLOR["Kruskal"]],
                )
            )
            fig.update_layout(title="Recorded runtime, single run (s)", yaxis_title="seconds", height=380, margin=dict(t=60, b=20))
            show_fig(fig)
        else:
            st.info("No runtime data found.")
    with ch2:
        fig = go.Figure()
        for name, df in (("Prim", prim), ("Kruskal", kruskal)):
            fig.add_trace(go.Histogram(x=df["weight_km"].astype(float), name=name, opacity=0.6, marker_color=ALGO_COLOR[name], nbinsx=40))
        fig.update_layout(barmode="overlay", title="Distribution of MST edge lengths", xaxis_title="edge length (km)", yaxis_title="number of MST edges", height=380, margin=dict(t=60, b=20), legend=dict(orientation="h", y=1.1))
        show_fig(fig)

    if {"u_type", "v_type"} <= set(prim.columns) and {"u_type", "v_type"} <= set(kruskal.columns):
        fig = go.Figure()
        for name, df in (("Prim", prim), ("Kruskal", kruskal)):
            s = pd.Series(pair_labels(df)).value_counts()
            fig.add_trace(go.Bar(x=s.index.tolist(), y=s.values, name=name, marker_color=ALGO_COLOR[name]))
        fig.update_layout(barmode="group", title="MST edges by facility-type pair", yaxis_title="number of MST edges", height=360, margin=dict(t=60, b=20), legend=dict(orientation="h", y=1.1))
        show_fig(fig)

    st.subheader("Validation results")
    if pc and kc:
        table = pd.DataFrame(
            {
                "Check": [k.replace("_", " ") for k in pc],
                "Prim": ["✅ Pass" if v else "❌ Fail" for v in pc.values()],
                "Kruskal": ["✅ Pass" if kc.get(k) else "❌ Fail" for k in pc],
            }
        )
        show_df(table)
        st.caption(
            "These checks inspect each MST's edge list and the facility coordinates, "
            "independently of how the algorithms produced the trees. The two total distances "
            "also agree within a numerical tolerance."
        )
    elif report is not None:
        st.warning("Per-check validation results are missing. Re-run `python run_analysis.py` to generate them.")
    else:
        st.warning("`results/validation_report.json` not found. Run `python run_analysis.py` first.")

    quality = load_json("quality")
    if quality:
        st.subheader("Data quality notes")
        q1, q2, q3, q4 = st.columns(4)
        q1.metric("Facilities with no name", f"{quality.get('missing_names', 'n/a')}")
        q2.metric("Records sharing exact coordinates", f"{quality.get('records_sharing_exact_coordinates', 'n/a')}")
        q3.metric("Facility pairs within 50 m", f"{quality.get('pairs_closer_than_km', {}).get('50m', 'n/a')}")
        q4.metric("Prim MST edges ≤ 50 m", f"{quality.get('prim_mst_edges_at_or_below_km', {}).get('50m', 'n/a')}")
        st.caption(
            "Closely spaced records may be separate buildings of one campus, duplicate map entries, "
            "or distinct facilities; the data cannot tell which. No records were removed."
        )

    st.subheader("Limitations")
    st.markdown(
        """
        - **Straight-line distance.** Edge weights are Haversine distances. They are not road distances, travel times, installation costs or emergency response times.
        - **What an MST guarantees.** It connects all facilities with the smallest total edge length. It does not give shortest paths between two facilities, the fastest ambulance route, redundancy if a link fails, or fault tolerance.
        - **Complete-graph assumption.** Any two facilities may be linked directly. This is a mathematical model, not a map of verified communication links.
        - **Data.** Locations come from OpenStreetMap-derived exports and have not been independently verified. Some features are centre points of building outlines.
        - **Runtimes.** They are specific to these implementations, this dataset and the machine used.
        - **Historical incidents** are a separate dataset and are not part of the facility MST.
        """
    )


# ----------------------------------------------------------------------------
# Navigation
# ----------------------------------------------------------------------------
def main():
    pages = [
        st.Page(page_overview, title="Dashboard", icon="📊", url_path="dashboard", default=True),
        st.Page(page_map, title="Facilities Map", icon="🗺️", url_path="facilities-map"),
        st.Page(page_mst, title="MST Network", icon="🕸️", url_path="mst-network"),
        st.Page(page_compare, title="Comparison & Validation", icon="⚖️", url_path="comparison"),
    ]
    nav = st.navigation(pages)
    st.sidebar.caption("Edge weight = Haversine straight-line distance (km).")
    nav.run()


if __name__ == "__main__":
    main()
