"""
run_dashboard

Author: Duco Trompert
Course: Afstudeerproject bachelor Informatica
Thesis: Science of Science: An Integrated Pipeline for Tracing Conceptual Emergence and Evolution in Semantic Space
Date: 2026-01-23

Entry point for running the Dash dashboard used in the thesis project.

This script:
- initialises the Dash app and Cytoscape layouts,
- registers all dashboard callbacks,
- starts the development server when executed as __main__.
"""

import dash_cytoscape as cyto
from dash import Dash

cyto.load_extra_layouts()

from sos_pipeline_udt.dashboard.callbacks_overall import register as register_overall
from sos_pipeline_udt.dashboard.callbacks_stats import register as register_stats
from sos_pipeline_udt.dashboard.callbacks_temporal import register as register_temporal
from sos_pipeline_udt.dashboard.ui_layout import make_app_layout, register_tab_router


def create_app() -> Dash:
    """Create and configure the Dash application instance."""
    app = Dash(__name__, suppress_callback_exceptions=True)
    app.layout = make_app_layout()

    register_tab_router(app)
    register_temporal(app)
    register_overall(app)
    register_stats(app)

    return app


def main() -> None:
    """Run the dashboard app (development server)."""
    app = create_app()
    app.run()


if __name__ == "__main__":
    main()
