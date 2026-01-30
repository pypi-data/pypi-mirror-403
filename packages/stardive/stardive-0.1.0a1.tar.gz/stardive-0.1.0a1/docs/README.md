# Stardive Documentation

Welcome to the Stardive documentation! This guide will help you integrate audit-grade execution tracking into your AI workflows.

## 📚 Documentation Structure

### Getting Started

**New to Stardive?** Start here:

1. **[Getting Started Guide](./guides/getting-started.md)** ⭐
   - Installation
   - First workflow in 5 minutes
   - Basic concepts
   - Quick wins

2. **[Execution Modes Guide](./guides/execution-modes.md)**
   - SDK Mode (new projects)
   - Instrumentation Mode (existing code)
   - Hybrid Mode (partial adoption)
   - YAML Mode (declarative workflows)

### Reference

**Complete API documentation:**

3. **[API Reference](./guides/api-reference.md)**
   - StardiveContext
   - Core models (RunPlan, RunRecord, Identity)
   - Instrumentation API
   - Storage, Lineage, and Replay APIs

### Integrations

**Framework-specific guides:**

4. **[Integration Guides](./guides/integrations/)**
   - [LangChain](./guides/integrations/langchain.md) - Chains, agents, RAG
   - CrewAI (coming soon)
   - Airflow (coming soon)
   - Jupyter (coming soon)

### Architecture & Design

**Deep dives into how Stardive works:**

5. **[Architecture Overview](./ARCHITECTURE.md)**
   - System design
   - Canonical IR (RunPlan/RunRecord)
   - Data flow
   - Component interactions

6. **[Identity & Provenance](./identity-provenance.md)**
   - Who/when/where tracking
   - Identity models
   - Environment fingerprinting
   - Model provenance

7. **[Artifact Canonicalization](./artifact-canonicalization.md)**
   - Deterministic serialization
   - Content hashing
   - Storage strategies
   - Hash verification

8. **[Execution Modes](./execution-modes.md)** (detailed spec)
   - Mode comparison
   - Implementation details
   - Migration paths

---

## 🚀 Quick Links

| I want to... | Go to... |
|--------------|----------|
| **Install Stardive** | [Getting Started - Installation](./guides/getting-started.md#installation) |
| **Create my first workflow** | [Getting Started - Quick Start](./guides/getting-started.md#quick-start) |
| **Choose the right integration mode** | [Execution Modes Guide](./guides/execution-modes.md#choosing-the-right-mode) |
| **Integrate with LangChain** | [LangChain Integration](./guides/integrations/langchain.md) |
| **Look up API methods** | [API Reference](./guides/api-reference.md) |
| **Understand the architecture** | [Architecture Overview](./ARCHITECTURE.md) |
| **Deploy to production** | [Best Practices](./guides/best-practices.md) (coming soon) |
| **Contribute** | [CONTRIBUTING.md](../CONTRIBUTING.md) |

---

## 🎯 By Use Case

### For Regulated Industries

You need **defensible AI** with complete audit trails:

1. Start with [Getting Started Guide](./guides/getting-started.md)
2. Understand [Identity & Provenance](./identity-provenance.md) tracking
3. Review [Execution Modes](./guides/execution-modes.md) for your architecture
4. Deploy with [Best Practices](./guides/best-practices.md)

**Key features:**
- Immutable audit trails
- Hash chain integrity
- Complete provenance (who/when/where)
- Replay capability

### For LLM Applications

You need to **audit LLM decisions** and track prompts/responses:

1. Quick start with [Getting Started Guide](./guides/getting-started.md)
2. Choose your framework:
   - [LangChain Integration](./guides/integrations/langchain.md)
   - CrewAI Integration (coming soon)
3. Mark non-deterministic steps appropriately
4. Track model identity and token usage

**Key features:**
- Model provenance tracking
- Prompt/response capture
- Non-determinism attestation
- Tool usage tracking

### For Existing Workflows

You need to **add audit trails without refactoring**:

1. Read [Instrumentation Mode](./guides/execution-modes.md#mode-2-instrumentation-mode-zero-code-changes)
2. Wrap your existing code with events
3. Test with [Getting Started Guide](./guides/getting-started.md#viewing-audit-trails)
4. Gradually migrate to SDK mode if desired

**Key features:**
- Zero code changes to business logic
- Wrapper-based integration
- Gradual migration path
- Framework compatibility

### For Data Scientists

You need to **track experiments and reproduce results**:

1. Start with [Getting Started Guide](./guides/getting-started.md)
2. Use [Jupyter Integration](./guides/integrations/jupyter.md) (coming soon)
3. Track model training with [API Reference](./guides/api-reference.md)
4. Replay experiments for validation

**Key features:**
- Artifact provenance
- Reproducible executions
- Lineage graphs
- Snapshot replay

---

## 📖 Learning Path

### Beginner

**Goal:** Create your first auditable workflow

1. ✅ [Install Stardive](./guides/getting-started.md#installation)
2. ✅ [Run first workflow](./guides/getting-started.md#your-first-workflow-5-minutes)
3. ✅ [View audit trail](./guides/getting-started.md#viewing-audit-trails)
4. ✅ [Understand core concepts](./guides/getting-started.md#understanding-the-sdk)

**Time:** ~30 minutes

### Intermediate

**Goal:** Integrate with your existing framework

1. ✅ Choose your [execution mode](./guides/execution-modes.md#choosing-the-right-mode)
2. ✅ Review [integration guide](./guides/integrations/) for your framework
3. ✅ Implement identity tracking with [Identity models](./guides/api-reference.md#identity)
4. ✅ Test lineage and replay

**Time:** ~2-4 hours

### Advanced

**Goal:** Production deployment with full governance

1. ✅ Understand [Architecture](./ARCHITECTURE.md) deeply
2. ✅ Implement [Artifact Canonicalization](./artifact-canonicalization.md)
3. ✅ Setup [Best Practices](./guides/best-practices.md) (coming soon)
4. ✅ Configure PostgreSQL backend (coming in v0.2)
5. ✅ Deploy with monitoring and alerting

**Time:** ~1-2 days

---

## 🔍 Concepts

### Core Concepts

- **RunPlan**: Execution intent (what SHOULD happen)
- **RunRecord**: Execution truth (what ACTUALLY happened)
- **Artifact**: Immutable data produced by a step
- **Lineage**: DAG showing data flow between steps
- **Hash Chain**: Tamper-evident event linking

Learn more: [Architecture Overview](./ARCHITECTURE.md)

### Key Principles

1. **Observation, not control** - Stardive captures truth, doesn't orchestrate
2. **Immutability** - Audit trails are append-only and tamper-evident
3. **Provenance first** - Always capture who/when/where/with what
4. **Replay capability** - Every execution can be reproduced from artifacts
5. **Non-determinism transparency** - Explicitly mark non-reproducible steps

Learn more: [Getting Started - Core Concepts](./guides/getting-started.md#understanding-the-sdk)

---

## 🛠️ Tools & Resources

### CLI Tools (Coming in v0.2)

```bash
# Execute workflow
stardive run workflow.yaml

# View audit trail
stardive audit show <run_id>

# View lineage
stardive lineage trace <run_id>

# Replay execution
stardive replay <run_id>
```

### Audit UI

Visual interface for audit trails and lineage:

```bash
# Start web UI
cd frontend && npm run dev
cd backend && uv run python -m backend
```

Open [http://localhost:5173](http://localhost:5173)

### Python API

Complete programmatic access:

```python
from stardive import StardiveContext
from stardive.storage import SQLiteBackend
from stardive.lineage import LineageGraph
from stardive.replay import SnapshotReplay
```

See [API Reference](./guides/api-reference.md)

---

## 📚 Additional Documentation

### Technical Specifications

- [Canonical IR Specification](./canonical-ir.md) - RunPlan/RunRecord schemas
- [Identity & Provenance Spec](./identity-provenance.md) - Who/when/where tracking
- [Artifact Canonicalization](./artifact-canonicalization.md) - Deterministic hashing

### Project Information

- [README](../README.md) - Project overview
- [CHANGELOG](../CHANGELOG.md) - Version history
- [CONTRIBUTING](../CONTRIBUTING.md) - How to contribute
- [LICENSE](../LICENSE) - AGPL-3.0-or-later

### Implementation Status

- [PROJECT_STATUS](../PROJECT_STATUS.md) - Current status and roadmap
- [Implementation Priorities](./IMPLEMENTATION_PRIORITIES.md) - Critical gaps

---

## 💬 Getting Help

### Documentation Not Clear?

- Open a [documentation issue](https://github.com/stardive/stardive-core/issues/new?labels=documentation)
- Start a [discussion](https://github.com/stardive/stardive-core/discussions)

### Found a Bug?

- Check [existing issues](https://github.com/stardive/stardive-core/issues)
- Open a [bug report](https://github.com/stardive/stardive-core/issues/new?labels=bug)

### Feature Request?

- Search [existing requests](https://github.com/stardive/stardive-core/issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement)
- Open a [feature request](https://github.com/stardive/stardive-core/issues/new?labels=enhancement)

### Need Support?

- **General questions**: [GitHub Discussions](https://github.com/stardive/stardive-core/discussions)
- **Commercial support**: [jiaye@stardive.xyz](mailto:jiaye@stardive.xyz)
- **Security issues**: [security@stardive.xyz](mailto:security@stardive.xyz)

---

## 🤝 Contributing

We welcome contributions! Areas where you can help:

- **Documentation**: Improve guides, add examples
- **Integrations**: Add support for new frameworks
- **Bug fixes**: Help squash bugs
- **Features**: Implement planned features

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

---

## 🗺️ Roadmap

### v0.1 (Current - Alpha)

✅ Core IR models
✅ Python SDK
✅ Instrumentation API
✅ SQLite storage
✅ Lineage API
✅ Snapshot replay
✅ Audit UI

### v0.2 (Next - 2-3 months)

🔜 PostgreSQL backend
🔜 LangChain/CrewAI adapters
🔜 YAML compiler
🔜 Enhanced lineage UI
🔜 Multi-tenant isolation

See [PROJECT_STATUS.md](../PROJECT_STATUS.md) for detailed roadmap.

---

**Ready to get started?** Jump to the [Getting Started Guide](./guides/getting-started.md)! 🚀
