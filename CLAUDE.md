# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an automated architectural reverse engineering pipeline that reconstructs the real architectural vision of complex distributed systems directly from code, CI/CD pipelines, and integrations — without interviews or workshops. It produces evidence-based transformation artefacts (blueprints, TO-BE models, gap analyses, roadmaps) to support executive decision-making.

**Language:** Python 3  
**Primary AI integration:** Anthropic Claude API (`claude-sonnet-4-20250514`)  
**Source system:** Azure DevOps REST API v7.0

## Environment Setup

Create a `.env` file at the project root:

```bash
ANTHROPIC_API_KEY=sk-ant-...     # Required
AZDO_ORG=your-organization       # Required for scanning
AZDO_PAT=personal-access-token   # Required for scanning
OUTPUT_DIR=outputs               # Optional, defaults to "outputs"
```

## Running the Pipeline

**Full pipeline (recommended):**
```bash
python run_transformation_analysis.py
```
This orchestrator checks prerequisites, skips already-completed stages, and runs TO-BE generation → gap analysis → roadmap generation in order.

**Individual stages (when re-running a specific step):**
```bash
python 01_scanner.py              # Inventories Azure DevOps repos → outputs/json/azure_scanner.json
python 02_integration_mapper.py   # Maps integrations (APIs, DBs, messaging) → outputs/json/integration_map.json
python 03_layer_analyzer.py       # Reconstructs architectural layers → outputs/json/layers_analysis.json
python blueprint_generator_ai.py  # Generates per-app AS-IS blueprints (AI) → outputs/{project}/blueprints/
python to_be_generator.py         # Consolidates future architecture (AI) → outputs/TO_BE_Model_*.md
python gap_analyzer_v5.py         # Evidence-based gap analysis (AI) → outputs/Gap_Analysis_*.md
python roadmap_generator.py       # Transformation roadmap (AI) → outputs/Roadmap_*.md
python clevel_report_agent.py     # Executive summary → outputs/C_Level_Report_*.md
python pitchdeck_agent.py         # HTML presentation → outputs/pitch_deck.html
```

## Architecture

### 7-Stage Sequential Pipeline

```
Azure DevOps Repos
     ↓
[01_scanner]         → azure_scanner.json
     ↓
[02_integration_mapper] → integration_map.json
     ↓
[03_layer_analyzer]  → layers_analysis.json
     ↓ (factual foundation)
     ├→ [blueprint_generator_ai]  → per-app blueprints (AS-IS)
     ↓
[gap_analyzer_v5]    ← consumes blueprints + TO-BE model
[to_be_generator]    → consolidated future architecture
     ↓
[roadmap_generator]  → actionable transformation initiatives
     ↓
[clevel_report_agent / pitchdeck_agent] → executive artefacts
```

### Core Utilities (`core/`)

- **`core/llm.py`** — Anthropic client wrapper with streaming support. Constants: `MODEL`, `MAX_TOKENS = 16000`. All LLM calls go through here.
- **`core/file_utils.py`** — I/O helpers, path management, banner utilities.

### Key Design Constraints

- **AI is a synthesis mechanism, not a source of truth.** The factual foundation (stages 1–3) is derived entirely from code/config analysis; AI only synthesises patterns from that evidence.
- **Anti-hallucination rules are embedded in all LLM prompts.** Every generated artefact must cite its source data. Unknown values use `TBD` placeholders — never invented facts.
- **Multi-part generation** is used for large documents (TO-BE, Gap Analysis, Roadmap) to respect token limits.
- **Evidence mandate:** Every gap, recommendation, and initiative must reference the source data that justifies it.

### Versioned Files

Several pipeline stages have versioned variants (e.g., `gap_analyzer.py` vs `gap_analyzer_v5.py`, `tobe_generator_v5.py`). The `v5` variants are the current versions used by the orchestrator. Older versions are kept for reference.

### Output Directory Structure

```
outputs/
├── json/           # Structured data: scanner, integration map, layers
├── reports/        # Human-readable intermediate reports
├── diagrams/       # Mermaid diagram files
├── to_be_parts/    # Multi-part TO-BE generation fragments
├── {project}/
│   └── blueprints/ # Per-application AS-IS blueprints
└── *.md / *.html   # Final artefacts
```

### Extending to Other VCS Platforms

The scanner (`01_scanner.py`) is designed to be extended to GitHub, Bitbucket, Gitea, or AWS CodeCommit. The Azure DevOps implementation in that file serves as the reference adapter pattern.

### Reference Blueprint

`blueprint_example.md` is the reference template for what a generated blueprint should look like. The `blueprint_generator_ai.py` uses this as a few-shot example in its prompt.
