# Science of Science: UDT Concept Evolution Pipeline

This repository contains the Python implementation accompanying the bachelor thesis:

**Duco Trompert (Universiteit van Amsterdam, Jan 23, 2026)**

*Science of Science: An Integrated Pipeline for Tracing Conceptual Emergence and Evolution in Semantic Space*

The project implements an **integrated pipeline** for science mapping that links:
data collection (OpenAlex) → pre-processing → network & embedding representations → analysis → **interactive dashboard**.

## What it does

- **Collects and caches** publication metadata from the **OpenAlex API** for a target concept (default: *"Urban Digital Twin"*).
- Builds **keyword co-occurrence networks** (overall and per-year slices).
- Builds **semantic similarity networks** from **Word2Vec** embeddings trained on titles/abstracts/keywords.
- (Optional) Builds **concept–method bipartite networks** using an LLM-based keyword labelling step (served via Ollama).
- Provides an interactive **Dash** dashboard with network visualisations (dash-cytoscape) and time series (plotly).

## Installation (Linux/macOS)

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install science-of-science-pipeline-udt
```

## Run the dashboard
```bash
udt-dashboard
```

Open http://127.0.0.1:8050/ in your browser.
