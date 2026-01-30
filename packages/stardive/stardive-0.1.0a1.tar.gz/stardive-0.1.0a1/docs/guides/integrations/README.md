# Integration Guides

Learn how to integrate Stardive with popular AI frameworks and tools.

## Available Integrations

### AI Frameworks

- **[LangChain](./langchain.md)** - Chains, agents, and RAG systems
- **[CrewAI](./crewai.md)** - Multi-agent orchestration (Coming soon)
- **[AutoGPT](./autogpt.md)** - Autonomous agents (Coming soon)

### Workflow Orchestrators

- **[Apache Airflow](./airflow.md)** - Batch workflows and DAGs (Coming soon)
- **[Prefect](./prefect.md)** - Modern workflow orchestration (Coming soon)
- **[Dagster](./dagster.md)** - Data pipelines (Coming soon)

### Notebooks & Interactive

- **[Jupyter](./jupyter.md)** - Notebook workflows (Coming soon)
- **[Google Colab](./colab.md)** - Cloud notebooks (Coming soon)

### Cloud Platforms

- **[AWS Lambda](./aws-lambda.md)** - Serverless functions (Coming soon)
- **[Google Cloud Functions](./gcp-functions.md)** - Serverless functions (Coming soon)
- **[Azure Functions](./azure-functions.md)** - Serverless functions (Coming soon)

## Integration Patterns

### Pattern 1: SDK Mode (New Projects)

Best for greenfield projects with full control:

```python
from stardive import StardiveContext

ctx = StardiveContext()

@ctx.step_meta(step_id="process", produces=["result"])
def process():
    # Your framework code here
    return {"data": "..."}

record = ctx.execute()
```

### Pattern 2: Instrumentation Mode (Existing Code)

Best for wrapping existing framework code:

```python
from stardive.instrumentation import emit_run_start, emit_step_start, emit_step_end

run_id = emit_run_start(initiator={"user": "alice"})

emit_step_start(run_id, "framework_call", inputs={...})
result = your_framework.run()  # Unchanged
emit_step_end(run_id, "framework_call", outputs={"result": result})
```

### Pattern 3: Callback/Hook Mode (Deep Integration)

Best for frameworks with callback systems:

```python
class StardiveCallback(FrameworkCallback):
    def on_event(self, event):
        # Emit Stardive events based on framework events
        emit_step_start(...)
```

## Common Use Cases

### Use Case 1: LLM Call Auditing

Track every LLM invocation with model provenance:

```python
@ctx.step_meta(step_id="llm_call", produces=["response"])
def call_llm(prompt):
    response = client.messages.create(model="...", messages=[...])
    return {
        "text": response.content[0].text,
        "_model": "claude-sonnet-4-5-20250929",
        "_temperature": 0.7
    }
```

### Use Case 2: RAG Pipeline Auditing

Capture document retrieval and generation:

```python
@ctx.step_meta(step_id="retrieve", produces=["docs"])
def retrieve(query):
    docs = vectorstore.similarity_search(query)
    return {"doc_ids": [d.id for d in docs]}

@ctx.step_meta(step_id="generate", produces=["answer"], depends_on=["docs"])
def generate(docs, query):
    # Generate answer from docs
    return {"answer": "..."}
```

### Use Case 3: Multi-Agent Coordination

Track agent decisions and interactions:

```python
@ctx.step_meta(step_id="agent_plan", produces=["plan"])
def agent_plan(task):
    plan = agent.create_plan(task)
    return {"steps": plan.steps}

@ctx.step_meta(step_id="agent_execute", produces=["result"], depends_on=["plan"])
def agent_execute(plan):
    result = agent.execute(plan)
    return {"output": result}
```

## Best Practices

### 1. Capture Framework Metadata

Always include framework-specific info:

```python
emit_step_end(run_id, step_id, outputs={
    "result": result,
    "_framework": "langchain",
    "_version": "0.1.0",
    "_model": "claude-sonnet-4-5-20250929"
})
```

### 2. Mark Non-Deterministic Steps

LLM calls and sampling are non-deterministic:

```python
from stardive.models import NonDeterminismAttestation

attestation = NonDeterminismAttestation(
    step_id="llm_call",
    reason="LLM sampling",
    disclosure="Output will differ on replay"
)
```

### 3. Track Token Usage

For cost tracking and compliance:

```python
emit_step_end(run_id, "llm_call", outputs={
    "response": response,
    "tokens_input": 150,
    "tokens_output": 75,
    "cost_usd": 0.005
})
```

### 4. Store Prompts

Keep full prompt history for audit:

```python
emit_step_start(run_id, "llm_call", inputs={
    "prompt": full_prompt,
    "system_message": system_msg,
    "user_message": user_msg
})
```

### 5. Implement Error Handling

Ensure failed runs are captured:

```python
try:
    result = framework.run()
    emit_step_end(run_id, "framework_call", outputs={"result": result})
except Exception as e:
    emit_step_end(run_id, "framework_call", outputs={}, error=str(e))
    raise
```

## Testing Your Integration

### 1. Verify Audit Trail

```python
from stardive.storage import SQLiteBackend

backend = SQLiteBackend()
record = backend.get_run_record(run_id)

assert record.run_status == "SUCCESS"
assert len(record.artifacts) > 0
assert record.hash_chain_valid
```

### 2. Test Replay

```python
from stardive.replay import SnapshotReplay

replayer = SnapshotReplay(backend)
replayed = replayer.replay(run_id)

assert replayed.artifacts["result"] == original.artifacts["result"]
```

### 3. Verify Lineage

```python
from stardive.lineage import LineageGraph

graph = LineageGraph(record)
upstream = graph.get_upstream("final_result")

assert "intermediate_step" in upstream
```

## Contributing Integrations

Want to add a new integration? We welcome contributions!

1. Fork the repository
2. Create integration guide in `docs/guides/integrations/`
3. Add example code in `examples/integrations/`
4. Submit PR with tests

See [CONTRIBUTING.md](../../../CONTRIBUTING.md) for details.

## Getting Help

- **Documentation**: [https://docs.stardive.xyz](https://docs.stardive.xyz)
- **GitHub Issues**: [https://github.com/stardive/stardive-core/issues](https://github.com/stardive/stardive-core/issues)
- **Discussions**: [https://github.com/stardive/stardive-core/discussions](https://github.com/stardive/stardive-core/discussions)

---

**Can't find your framework?** Open a [feature request](https://github.com/stardive/stardive-core/issues/new)!
