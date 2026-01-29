"""
dashboard.vis_styles

Author: Duco Trompert
Course: Afstudeerproject bachelor Informatica
Thesis: Science of Science: An Integrated Pipeline for Tracing Conceptual Emergence and Evolution in Semantic Space
Date: 2026-01-23

Cytoscape stylesheet definitions for the Dash dashboard.

This module contains the CYTO_STYLESHEET list, defining default node/edge styling
and CSS-like classes used during temporal transitions (inactive/incoming, etc.).
"""

from __future__ import annotations

CYTO_STYLESHEET = [
    {
        "selector": "node",
        "style": {
            "label": "data(label)",
            "width": "data(size)",
            "height": "data(size)",
            "background-color": "data(color)",
            "shape": "data(shape)",
            "font-size": 12,
            "text-wrap": "wrap",
            "text-max-width": 140,
            "border-width": 0,
            "transition-property": "opacity, border-width, border-color, width, height",
            "transition-duration": "520ms",
            "opacity": 1,
        },
    },
    {
        "selector": "node:selected",
        "style": {
            "border-width": 2,
            "border-color": "rgb(60,60,60)",
        },
    },
    {
        "selector": "edge",
        "style": {
            "width": "data(width)",
            "curve-style": "bezier",
            "opacity": 0.55,
            "transition-property": "opacity, width",
            "transition-duration": "520ms",
        },
    },
    {
        "selector": "edge:selected",
        "style": {
            "opacity": 0.9,
        },
    },
    {"selector": ".inactive", "style": {"opacity": 0.06, "label": "", "events": "no"}},
    {"selector": ".inactive-edge", "style": {"opacity": 0.05, "events": "no"}},
    {"selector": ".incoming", "style": {"opacity": 0.06}},
    {"selector": ".incoming-edge", "style": {"opacity": 0.05}},
    {"selector": ".birth", "style": {"border-width": 0}},
    {"selector": ".death", "style": {"border-width": 0}},
]
