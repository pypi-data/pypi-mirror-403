# Stardive

> **Audit-grade execution truth layer for AI workflows**

[![PyPI version](https://img.shields.io/pypi/v/stardive.svg)](https://pypi.org/project/stardive/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Test Coverage](https://img.shields.io/badge/coverage-96%25-brightgreen.svg)]()
[![Status: Alpha](https://img.shields.io/badge/status-alpha-orange.svg)]()

**Quick Links:** [Installation](#installation) • [Quick Start](#quick-start) • [Key Features](#key-features) • [Use Cases](#use-cases) • [Documentation](https://docs.stardive.xyz) • [GitHub](https://github.com/stardive/stardive-core)

---

## What is Stardive?

**Stardive makes AI execution provable — not smarter, faster, or more automated.**

Stardive is an **execution & observation kernel** that provides audit-grade truth for AI workflows. It captures execution provenance, stores artifacts immutably, and enables replay — without replacing your existing orchestration or agents.

**Perfect for regulated industries** (finance, healthcare, legal, government) that need defensible AI systems with complete audit trails.

### Core Principle

> **Observation and provenance, not control.**
>
> We capture truth, we don't orchestrate.

---

## Why Stardive?

**Add ~10-20 lines of Python to your existing AI workflow and get:**

- **Immutable audit trails** - Every step, artifact, and decision recorded with hash chains
- **Complete provenance** - Know exactly what produced each output, when, and by whom
- **Lineage graphs** - Visual DAG of Step → Artifact → Step relationships
- **Snapshot replay** - Reproduce past executions from stored artifacts
- **Non-determinism transparency** - Explicit marking of non-reproducible steps (LLM calls, etc.)
- **Zero replacement** - Keep your existing orchestration (LangChain, CrewAI, custom code)

---

## Installation

```bash
pip install stardive
```

**Requirements:** Python 3.10+

**New to Stardive?** Start with the [5-minute quick start](#quick-start) below, then explore the [documentation](https://docs.stardive.xyz).

---

## Quick Start

### 5-Minute Example

Track your AI workflow with just a few decorators:

```python
from stardive import StardiveContext

# Create audit context
ctx = StardiveContext()

# Decorate your functions
@ctx.step_meta(step_id="fetch", produces=["raw_data"])
def fetch_data():
    return {"data": [1, 2, 3]}

@ctx.step_meta(step_id="analyze", produces=["result"], depends_on=["raw_data"])
def analyze(raw_data):
    return {"sum": sum(raw_data["data"])}

# Execute with full audit trail
record = ctx.execute()

# Every step, artifact, and decision is now auditable
print(f"Run ID: {record.run_id}")
print(f"Complete audit trail stored with hash chain integrity")
```

That's it! You now have:
- Immutable execution records
- Artifact provenance
- Lineage graphs (API access)
- Replay capability

### Alternative: Zero-Replacement Instrumentation

Already have working code? Add audit trails without refactoring:

```python
from stardive.instrumentation import emit_run_start, emit_step_start, emit_step_end

# Wrap your existing workflow
run_id = emit_run_start(initiator={"user": "bob"})

emit_step_start(run_id, step_id="process", inputs={"data": [1, 2, 3]})
result = your_existing_function(data)  # Your code stays UNCHANGED
emit_step_end(run_id, step_id="process", outputs={"result": result})

# Full audit trail generated with zero business logic changes
```

**Perfect for**:
- LangChain/CrewAI workflows
- Jupyter notebooks
- Legacy batch jobs
- Gradual migration to full SDK

---

## Key Features

| Feature | Description | Status |
|---------|-------------|--------|
| **Python SDK** | Metadata decorators for audit capture | ✅ Alpha |
| **Instrumentation API** | Event ingestion for existing workflows | ✅ Alpha |
| **Artifact Storage** | Deterministic serialization + SHA256 hashing | ✅ Alpha |
| **Immutable Storage** | Append-only SQLite backend | ✅ Alpha |
| **Hash Chain Integrity** | Tamper-evident audit trails | ✅ Alpha |
| **Lineage Graphs** | Automatic DAG construction (API) | ✅ Alpha |
| **Snapshot Replay** | Reproduce executions from artifacts | ✅ Alpha |
| **Audit UI** | Web interface for trails & lineage | ✅ Alpha |
| **PostgreSQL Backend** | Enterprise storage | 🔜 v0.2 |
| **Framework Integrations** | LangChain, CrewAI adapters | 🔜 v0.2 |

### What Stardive Does NOT Do

Stardive is **observation-only**. We don't replace your existing tools:

- ❌ No workflow orchestration (use your existing orchestrator)
- ❌ No agent planning (we observe, not control)
- ❌ No dependency inference (you declare dependencies)
- ❌ No AI models or business logic (bring your own)
- ❌ No correctness checking (we capture truth, not judge it)

---

## Architecture

```
┌──────────────────────────────────────┐
│   Your AI Workflow / Agent           │
│   (Existing Code + Stardive SDK)     │
└──────────────────────────────────────┘
                  │
                  │ metadata + events
                  ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃   STARDIVE OBSERVATION KERNEL      ┃
┃   ─────────────────────────────────┃
┃   • Capture execution truth        ┃
┃   • Hash artifacts                 ┃
┃   • Build lineage                  ┃
┃   • Store immutably                ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                  │
                  │ immutable trail
                  ▼
┌──────────────────────────────────────┐
│  Artifacts • Lineage • Replay        │
│  (Audit Evidence, Provenance)        │
└──────────────────────────────────────┘
```

---

## Audit UI

Run the web UI for audits and lineage:

```bash
# Frontend
cd frontend && npm run dev

# Backend
uv run python -m backend
```

### Audit UI Screenshots

![Run list](pics/runs.png)
![Run info](pics/run_info.png)
![Run lineage](pics/run_lineage.png)
![Run replay](pics/run_replay.png)
![Run export](pics/run_export.png)

---

## Use Cases

Stardive is designed for **regulated environments** where AI decisions must be defensible:

### Industry Examples

| Industry | Use Case | Why Stardive? |
|----------|----------|---------------|
| **Financial Services** | Credit scoring, fraud detection, algorithmic trading | Prove model decisions to regulators (FCRA, ECOA) |
| **Healthcare** | Clinical decision support, diagnosis assistance | Document AI's role in patient care (HIPAA, FDA) |
| **Legal** | Contract analysis, case research, e-discovery | Maintain chain of custody for AI evidence |
| **Government** | Benefits determination, policy analysis | Transparency & accountability (APA, FOIA) |
| **Insurance** | Claims processing, underwriting | Audit AI decisions for fairness & compliance |

### Key Requirements Stardive Solves

- **Regulatory compliance**: Full audit trail for GDPR, AI Act, FDA, FCRA, etc.
- **Reproducibility**: Prove AI decisions can be replayed from stored artifacts
- **Accountability**: Answer "How did the AI reach this conclusion?"
- **Defensibility**: Provide evidence in disputes, audits, or litigation
- **Trust**: Demonstrate responsible AI deployment to stakeholders

---

## How Stardive Compares

| Tool | Purpose | Relationship to Stardive |
|------|---------|-------------------------|
| **LangChain / CrewAI** | Agent orchestration | Use together - Stardive observes their execution |
| **MLflow / Weights & Biases** | ML experiment tracking | Different focus - Stardive is for production audit trails |
| **Apache Airflow** | Workflow orchestration | Use together - Stardive captures provenance |
| **OpenTelemetry** | Observability/telemetry | Complementary - Stardive adds artifact provenance |
| **DVC / Pachyderm** | Data versioning | Different - Stardive tracks execution, not just data |

**Stardive's unique value**: Immutable audit trails with artifact provenance and replay capability, specifically designed for regulated AI.

---

## Explicit Boundaries

### Stardive Will NEVER

- Infer dependencies (user must declare)
- Plan workflows (user provides plan)
- Optimize execution (no auto-optimization)
- Judge correctness (only capture truth)
- Replace orchestrators or agents (observation only)

### Stardive ONLY Does

- Capture execution truth
- Store artifacts immutably
- Build lineage graphs
- Enable replay from snapshots
- Provide audit evidence

---

## Development

### Prerequisites

- Python 3.11+
- uv (recommended) or pip

### Setup

```bash
# Clone the repository
git clone https://github.com/stardive/stardive.git
cd stardive/stardive-core

# Create virtual environment with uv
uv venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Run linters
black src tests
ruff check src tests
mypy src
```

### Project Structure

```
stardive-core/
├── src/stardive/
│   ├── models/          # Canonical IR (RunPlan/RunRecord)
│   ├── sdk/             # Python SDK (context, decorators)
│   ├── instrumentation/ # Event ingestion API
│   ├── storage/         # Storage backends (SQLite)
│   ├── lineage/         # Lineage graph construction
│   ├── replay/          # Snapshot replay engine
│   └── cli/             # Legacy CLI (not used)
├── tests/
│   ├── unit/            # Unit tests (99% coverage)
│   └── integration/     # Integration tests
├── docs/                # Documentation
└── pyproject.toml       # Project config
```

---

## Project Status

**Current Version**: `0.1.0a1` (Alpha)

### ✅ v0.1 Complete (375 tests, 96% coverage)
- Canonical IR (RunPlan/RunRecord)
- Identity & Provenance tracking
- Artifact management with deterministic hashing
- SQLite append-only storage
- Python SDK with context-scoped decorators
- Instrumentation API for zero-replacement adoption
- Lineage graph API
- Snapshot replay engine
- Audit UI (web interface)

### 🔜 v0.2 Roadmap
- PostgreSQL backend for enterprise scale
- Framework integrations (LangChain, CrewAI)
- YAML workflow compiler
- Enhanced lineage visualization
- Multi-tenant isolation
- Advanced replay modes (partial, conditional)

See [PROJECT_STATUS.md](PROJECT_STATUS.md) for detailed roadmap.

### Test Coverage

```
Phase 2 (Core Models):    127 tests, 98% coverage
Phase 3.1 (Storage):       63 tests, 91% coverage
Phase 3.2 (Artifacts):    165 tests, 96% coverage
─────────────────────────────────────────────────
Total:                    375 tests, 96% coverage
```

---

## Contributing

We welcome contributions! Stardive is open source (AGPL-3.0) and community-driven.

**How to contribute**:
1. Check [open issues](https://github.com/stardive/stardive-core/issues) or [start a discussion](https://github.com/stardive/stardive-core/discussions)
2. Fork the repository and create a feature branch
3. Write tests (we maintain >90% coverage)
4. Submit a PR with clear description

**Priority areas for v0.2**:
- PostgreSQL backend implementation
- LangChain/CrewAI integration adapters
- Documentation improvements
- Example workflows for regulated industries
- Performance optimizations

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## License

This project is licensed under the **GNU Affero General Public License v3.0 or later (AGPL-3.0-or-later)**.

See [LICENSE](LICENSE) for details.

### Why AGPL?

We chose AGPL to ensure that:
- The code remains open source
- Cloud providers offering Stardive-as-a-service must contribute improvements back
- Enterprises modifying Stardive must either open source changes or obtain a commercial license

For commercial licensing options, contact: [jiaye@stardive.xyz](mailto:jiaye@stardive.xyz)

---

## Links & Resources

- 🌐 **Website**: [https://stardive.xyz](https://stardive.xyz)
- 📚 **Documentation**: [https://docs.stardive.xyz](https://docs.stardive.xyz)
- 📦 **PyPI**: [https://pypi.org/project/stardive/](https://pypi.org/project/stardive/)
- 💻 **GitHub**: [https://github.com/stardive/stardive-core](https://github.com/stardive/stardive-core)
- 🐛 **Issues**: [https://github.com/stardive/stardive-core/issues](https://github.com/stardive/stardive-core/issues)
- 💬 **Discussions**: [https://github.com/stardive/stardive-core/discussions](https://github.com/stardive/stardive-core/discussions)

### Support

- **Commercial licensing**: [jiaye@stardive.xyz](mailto:jiaye@stardive.xyz)
- **Security issues**: [security@stardive.xyz](mailto:security@stardive.xyz)
- **General questions**: [GitHub Discussions](https://github.com/stardive/stardive-core/discussions)

---

**Making AI execution provable, not perfect.**
