"""
dashboard.ui_layout

Author: Duco Trompert
Course: Afstudeerproject bachelor Informatica
Thesis: Science of Science: An Integrated Pipeline for Tracing Conceptual Emergence and Evolution in Semantic Space
Date: 2026-01-23

Dash UI layout for the thesis dashboard.

This module defines:
- the top-level app layout (tabs + container),
- reusable network panel layouts (overall and temporal),
- the statistics panel layout (KPIs, charts, and tables),
- a simple tab router callback to switch between views.
"""

from __future__ import annotations

from typing import List, Tuple

import dash_cytoscape as cyto
from dash import Dash, Input, Output, dash_table, dcc, html

from sos_pipeline_udt.analysis.metrics import CommunityDetection, EdgeScaling, NodeScaling
from sos_pipeline_udt.config import (
    CONCEPT,
    DEFAULT_MIN_VALUE,
    DEFAULT_SIM_THRESHOLD,
    PRECOMPUTE_LIGHT_NETWORKS,
    USE_CACHE,
)

from sos_pipeline_udt.dashboard.data_store import (
    DEFAULT_TEMP_YEAR,
    KPIS,
    max_year,
    min_year,
    total_pubs,
    unique_keywords,
    years_sorted,
)
from sos_pipeline_udt.dashboard.temporal_helpers import ANIM_INTERVAL_MS
from sos_pipeline_udt.dashboard.vis_styles import CYTO_STYLESHEET

TEMPORAL_OPTIONS = [
    ("Co-occurrence (yearly)", "cooccurrence_yearly"),
    ("Concept-Method (yearly)", "concept_method_yearly"),
    ("Semantic similarity (yearly)", "semantic_yearly"),
]

OVERALL_OPTIONS = [
    ("Co-occurrence (aggregated)", "cooccurrence_overall"),
    ("Concept-Method (aggregated)", "concept_method_overall"),
    ("Semantic similarity (aggregated)", "semantic_overall"),
]

NODE_SCALINGS = [
    ("none", NodeScaling.NONE),
    ("degree", NodeScaling.DEGREE),
    ("weighted_degree", NodeScaling.WEIGHTED_DEGREE),
    ("betweenness", NodeScaling.BETWEENNESS),
    ("closeness", NodeScaling.CLOSENESS),
    ("eigenvector", NodeScaling.EIGENVECTOR),
]

EDGE_SCALINGS = [
    ("none", EdgeScaling.NONE),
    ("linear", EdgeScaling.LINEAR),
    ("sqrt", EdgeScaling.SQRT),
    ("log", EdgeScaling.LOG),
]

COMMUNITIES = [
    ("none", CommunityDetection.NONE),
    ("louvain", CommunityDetection.LOUVAIN),
]


def make_app_layout() -> html.Div:
    """Create and return the top-level Dash app layout container."""
    return html.Div(
        style={
            "fontFamily": "system-ui, -apple-system, Segoe UI, Roboto, sans-serif",
            "padding": "14px",
            "maxWidth": "100vw",
            "overflowX": "hidden",
            "boxSizing": "border-box",
        },
        children=[
            html.H2(f"Concept evolution visualisation dashboard ({CONCEPT})"),
            dcc.Tabs(
                id="tabs",
                value="stats",
                children=[
                    dcc.Tab(label="Network statistics", value="stats"),
                    dcc.Tab(label="Aggregated networks", value="overall"),
                    dcc.Tab(label="Temporal networks", value="temporal"),
                ],
            ),
            html.Div(id="tab-content", style={"marginTop": "10px"}),
        ],
    )


def _network_panel(
    panel_id: str, options: List[Tuple[str, str]], include_year: bool
) -> html.Div:
    """
    Build a reusable network panel layout (controls + Cytoscape + details sidebar).

    The IDs must remain stable: callbacks depend on them.
    """
    controls = [
        html.Div(
            children=[
                html.Label("Network"),
                dcc.Dropdown(
                    id=f"{panel_id}-network",
                    options=[{"label": lbl, "value": val} for lbl, val in options],
                    value=options[0][1],
                    clearable=False,
                    style={"width": "320px"},
                ),
            ]
        ),
        html.Div(
            children=[
                html.Label("Min co-occurrence / min edge weight"),
                dcc.Slider(
                    id=f"{panel_id}-min-value",
                    min=0,
                    max=20,
                    step=1,
                    value=DEFAULT_MIN_VALUE,
                ),
            ],
            style={"minWidth": "280px"},
        ),
        html.Div(
            children=[
                html.Label("Node scaling"),
                dcc.Dropdown(
                    id=f"{panel_id}-node-scaling",
                    options=[
                        {"label": lbl, "value": val} for lbl, val in NODE_SCALINGS
                    ],
                    value=NodeScaling.DEGREE,
                    clearable=False,
                    style={"width": "220px"},
                ),
            ]
        ),
        html.Div(
            children=[
                html.Label("Edge scaling"),
                dcc.Dropdown(
                    id=f"{panel_id}-edge-scaling",
                    options=[
                        {"label": lbl, "value": val} for lbl, val in EDGE_SCALINGS
                    ],
                    value=EdgeScaling.LINEAR,
                    clearable=False,
                    style={"width": "180px"},
                ),
            ]
        ),
        html.Div(
            children=[
                html.Label("Communities"),
                dcc.Dropdown(
                    id=f"{panel_id}-community",
                    options=[{"label": lbl, "value": val} for lbl, val in COMMUNITIES],
                    value=CommunityDetection.LOUVAIN,
                    clearable=False,
                    style={"width": "170px"},
                ),
            ]
        ),
        html.Div(
            children=[
                html.Label("Semantic threshold"),
                dcc.Slider(
                    id=f"{panel_id}-sim-threshold",
                    min=0.1,
                    max=0.9,
                    step=0.01,
                    value=DEFAULT_SIM_THRESHOLD,
                    marks={i / 10: str(i / 10) for i in range(1, 10, 2)},
                ),
            ],
            style={"minWidth": "280px"},
        ),
    ]

    if panel_id == "temp":
        controls.append(
            html.Div(
                children=[
                    html.Label("Export"),
                    html.Button("Download SVG", id="temp-btn-svg", n_clicks=0),
                ],
                style={"minWidth": "140px"},
            )
        )

    if panel_id == "overall":
        controls.append(
            html.Div(
                children=[
                    html.Label("Export"),
                    html.Button("Download SVG", id="overall-btn-svg", n_clicks=0),
                ],
                style={"minWidth": "140px"},
            )
        )

    if include_year:
        controls.insert(
            1,
            html.Div(
                children=[
                    html.Label("Year"),
                    dcc.Slider(
                        id=f"{panel_id}-year",
                        min=min_year,
                        max=max_year,
                        value=DEFAULT_TEMP_YEAR,
                        step=1,
                        marks=(
                            {
                                y: str(y)
                                for y in years_sorted[:: max(1, len(years_sorted) // 8)]
                            }
                            if years_sorted
                            else {}
                        ),
                        tooltip={"placement": "bottom", "always_visible": False},
                    ),
                ],
                style={"minWidth": "420px", "flex": "1"},
            ),
        )

    return html.Div(
        children=[
            (
                dcc.Store(id="temp-current-year", data=DEFAULT_TEMP_YEAR)
                if panel_id == "temp"
                else html.Div()
            ),
            (
                dcc.Store(id="temp-pos-store", data={})
                if panel_id == "temp"
                else html.Div()
            ),
            (
                dcc.Store(id="temp-transition-store", data=None)
                if panel_id == "temp"
                else html.Div()
            ),
            (
                dcc.Interval(
                    id="temp-interval",
                    interval=ANIM_INTERVAL_MS,
                    n_intervals=0,
                    disabled=True,
                )
                if panel_id == "temp"
                else html.Div()
            ),
            html.Div(
                style={
                    "display": "flex",
                    "gap": "14px",
                    "alignItems": "flex-end",
                    "flexWrap": "wrap",
                },
                children=controls,
            ),
            html.Hr(),
            html.Div(
                style={
                    "display": "grid",
                    "gridTemplateColumns": "2fr 1fr",
                    "gap": "14px",
                },
                children=[
                    html.Div(
                        style={"minWidth": 0},
                        children=[
                            html.Div(
                                id=f"{panel_id}-bipartite-headers",
                                style={
                                    "display": "none",
                                    "justifyContent": "space-between",
                                    "padding": "0 18px 6px 18px",
                                    "fontWeight": 600,
                                    "color": "#444",
                                },
                                children=[
                                    html.Div("Concepts"),
                                    html.Div("Methods"),
                                ],
                            ),
                            cyto.Cytoscape(
                                id=f"{panel_id}-cyto",
                                layout=(
                                    {"name": "preset", "fit": True, "padding": 20}
                                    if panel_id in ("temp", "overall")
                                    else {
                                        "name": "cose",
                                        "animate": True,
                                        "animationDuration": 650,
                                    }
                                ),
                                style={
                                    "width": "100%",
                                    "height": "650px",
                                    "border": "1px solid #ddd",
                                    "borderRadius": "10px",
                                },
                                elements=[],
                                stylesheet=CYTO_STYLESHEET,
                                minZoom=0.2,
                                maxZoom=3,
                            ),
                        ],
                    ),
                    html.Div(
                        style={
                            "minWidth": 0,
                            "border": "1px solid #ddd",
                            "borderRadius": "10px",
                            "padding": "10px",
                            "height": "650px",
                            "overflow": "auto",
                            "overflowWrap": "anywhere",
                        },
                        children=[
                            html.H4("Selection details"),
                            html.Div(
                                id=f"{panel_id}-meta", style={"marginBottom": "10px"}
                            ),
                            html.Div(id=f"{panel_id}-details"),
                        ],
                    ),
                ],
            ),
        ]
    )


def _kpi_card(title: str, value: str) -> html.Div:
    """Create a simple KPI card element."""
    return html.Div(
        style={
            "border": "1px solid #ddd",
            "borderRadius": "10px",
            "padding": "10px",
            "minWidth": "260px",
        },
        children=[html.H4(title), html.Div(value)],
    )


def _stats_panel() -> html.Div:
    """Build the layout for the statistics tab (KPIs, figures, and tables)."""
    DT_STYLE = dict(
        style_table={"overflowX": "auto"},
        style_header={
            "textAlign": "left",
            "fontWeight": "600",
            "whiteSpace": "normal",
        },
        style_cell={
            "textAlign": "left",
            "padding": "6px 10px",
            "whiteSpace": "normal",
            "height": "auto",
            "lineHeight": "1.25",
            "minWidth": "60px",
            "width": "auto",
            "maxWidth": "600px",
        },
        css=[
            {
                "selector": ".dash-spreadsheet-container .dash-spreadsheet-inner table",
                "rule": "table-layout: auto; width: 100%;",
            },
            {
                "selector": ".dash-cell div.dash-cell-value",
                "rule": "white-space: normal; height: auto; line-height: 1.25;",
            },
        ],
    )

    return html.Div(
        children=[
            html.Div(
                style={"display": "flex", "gap": "18px", "flexWrap": "wrap"},
                children=[
                    _kpi_card("Total publications", str(KPIS["total_pubs"])),
                    _kpi_card("Time span", str(KPIS["time_span"])),
                    _kpi_card("Unique keywords", str(KPIS["n_keywords"])),
                    _kpi_card("Unique authors", str(KPIS["n_authors"])),
                ],
            ),
            html.Hr(),
            html.H3("Publications over time"),
            html.Div(
                style={"maxWidth": "720px"},
                children=[
                    html.Label("Smoothing window (days)"),
                    dcc.Slider(
                        id="pubs-smooth-window",
                        min=1,
                        max=365,
                        step=1,
                        value=90,
                        marks={
                            1: "1",
                            **{
                                int(i * 30.44): str(int(i * 30.44))
                                for i in range(1, 13)
                            },
                        },
                    ),
                ],
            ),
            dcc.Graph(id="pubs-ts-fig"),
            html.Hr(),
            html.H3("Keyword movers & top keywords"),
            html.Div(
                style={"display": "flex", "gap": "18px", "flexWrap": "wrap"},
                children=[
                    html.Div(
                        style={"minWidth": "320px"},
                        children=[
                            html.Label("Lookback (years)"),
                            dcc.Slider(
                                id="kw-lookback",
                                min=1,
                                max=10,
                                step=1,
                                value=3,
                                tooltip={
                                    "placement": "bottom",
                                    "always_visible": False,
                                },
                            ),
                            html.Div(style={"height": "14px"}),
                            html.Label("Min total occurrences (in window)"),
                            dcc.Slider(
                                id="kw-min-total",
                                min=1,
                                max=50,
                                step=1,
                                value=5,
                                marks={
                                    1: "1",
                                    **{i: str(i) for i in range(5, 50 + 1, 5)},
                                },
                                tooltip={
                                    "placement": "bottom",
                                    "always_visible": False,
                                },
                            ),
                        ],
                    ),
                ],
            ),
            html.H4("Emerging keywords"),
            dash_table.DataTable(
                id="kw-emerging-table",
                columns=[
                    {"name": "keyword", "id": "keyword"},
                    {"name": "total", "id": "total"},
                    {"name": "slope", "id": "slope"},
                    {"name": "last", "id": "last"},
                    {"name": "prev", "id": "prev"},
                ],
                page_size=15,
                sort_action="native",
                **DT_STYLE,
            ),
            html.H4("Fading keywords"),
            dash_table.DataTable(
                id="kw-fading-table",
                columns=[
                    {"name": "keyword", "id": "keyword"},
                    {"name": "total", "id": "total"},
                    {"name": "slope", "id": "slope"},
                    {"name": "last", "id": "last"},
                    {"name": "prev", "id": "prev"},
                ],
                page_size=15,
                sort_action="native",
                **DT_STYLE,
            ),
            html.H4("Top keywords (aggregated)"),
            dash_table.DataTable(
                id="kw-top-table",
                columns=[
                    {"name": "keyword", "id": "keyword"},
                    {"name": "count", "id": "count"},
                ],
                page_size=20,
                sort_action="native",
                **DT_STYLE,
            ),
            html.Hr(),
            html.H3("Network evolution over time"),
            html.Div(
                style={
                    "display": "flex",
                    "gap": "18px",
                    "flexWrap": "wrap",
                    "maxWidth": "920px",
                },
                children=[
                    html.Div(
                        style={"minWidth": "360px"},
                        children=[
                            html.Label(
                                "Min co-occurrence / min edge weight (for stats networks)"
                            ),
                            dcc.Slider(
                                id="stats-min-value",
                                min=0,
                                max=20,
                                step=1,
                                value=DEFAULT_MIN_VALUE,
                                tooltip={
                                    "placement": "bottom",
                                    "always_visible": False,
                                },
                            ),
                        ],
                    ),
                    html.Div(
                        style={"minWidth": "360px"},
                        children=[
                            html.Label("Smoothing window (years)"),
                            dcc.Slider(
                                id="net-smooth-years",
                                min=1,
                                max=5,
                                step=1,
                                value=1,
                                marks={1: "1", 2: "2", 3: "3", 4: "4", 5: "5"},
                                tooltip={
                                    "placement": "bottom",
                                    "always_visible": False,
                                },
                            ),
                        ],
                    ),
                ],
            ),
            dcc.Graph(id="net-similarity-fig"),
            dcc.Graph(id="net-size-fig"),
            dcc.Graph(id="net-structure-fig"),
        ]
    )


def register_tab_router(app: Dash) -> None:
    """Register the tab router callback to swap layouts when the active tab changes."""

    @app.callback(Output("tab-content", "children"), Input("tabs", "value"))
    def render_tab(tab):
        """Render the appropriate layout based on the currently selected tab."""
        if tab == "temporal":
            return _network_panel("temp", TEMPORAL_OPTIONS, include_year=True)
        if tab == "overall":
            return _network_panel("overall", OVERALL_OPTIONS, include_year=False)

        return _stats_panel()
