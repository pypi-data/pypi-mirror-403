# Antraft

**The Immune System for Agentic AI.**

Antraft is an enterprise-grade runtime governance framework for AI agents. It serves as the **Governance Layer** that makes autonomous agents safe for production deployment.

Antraft acts as a middleware between your agent's "Brain" (LLM) and its "Hands" (Tools), enforcing specific policies, logging actions, and ensuring compliance. It is designed to be framework-agnostic, working seamlessly with LangChain, AutoGen, CrewAI, and custom implementations.

**Antraft is the reference implementation of the [MI9 Agent Intelligence Protocol](https://arxiv.org/abs/2508.03858).**

---

## Key Capabilities

### 1. Robust Governance
Secure your agents with deterministic rules.
*   **Policy Enforcement**: Approve, deny, or pause every action before execution.
*   **Stateful Control**: Enforce prerequisites (e.g., "Must authenticate before reading data").
*   **Rich Logic Rules**: define complex constraints like `amount > 1000 and not user_verified`.
*   **Path Confinement**: Restrict file access to specific directories.

### 2. Deep Observability
Complete visibility into agent behavior.
*   **Session Recording**: Capture full execution traces (Inputs, Thoughts, Actions, Outputs) for replay debugging.
*   **PII Redaction**: Automatically scrub sensitive data (Emails, SSNs) from logs.
*   **Cognitive Telemetry**: Log the agent's reasoning process, not just its actions.
*   **Drift Detection**: Identify anomalous behavior patterns (loops, spikes) in real-time.

### 4. Distributed Control
Manage fleets of agents at scale.
*   **Swarm Protocol**: Control thousands of agents across different servers from a central API.
*   **Human-in-the-Loop**: Pause high-risk actions and wait for human approval via API.
*   **Dynamic Policies**: Update agent permissions on-the-fly without restarting.

### 5. Universal Compatibility (MCP)
Antraft runs as a **Model Context Protocol (MCP)** server, making it instantly compatible with:
*   Claude Desktop
*   Cursor / Windsurf IDEs
*   Any MCP-compliant client

---

## Installation

```bash
pip install antraft
```

---

## Quick Start ("Fluent" SDK)

The Antraft SDK provides a fluent interface to secure ANY python agent in seconds.

```python
import asyncio
from antraft import Antraft

# 1. Define your Agent & Tools
agent = MyAgent()
tools = {
    "search": google_search_tool,
    "shell": run_shell_tool
}

async def main():
    # 2. Wrap & Secure
    await Antraft.guard(agent, tools) \
        .allow(["search"]) \
        .deny(["shell"]) \
        .record_session("logs/session_01.jsonl", redact_pii=True) \
        .run()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Advanced Usage

### Defining Complex Policies (YAML)
For enterprise use cases, load policies from file.

```yaml
# policy.yaml
allow:
  - read_file
rules:
  - trigger: "action:transfer_money"
    checks:
      - "amount > 10000"
    enforce: "pause"
    message: "High value transfer requires approval."
```

```python
await Antraft.guard(agent, tools) \
    .load_policy("policy.yaml") \
    .run()
```

### Swarm Mode (Remote Control)
Connect an agent to a central Control Plane.

**1. Start the Server:**
```bash
python -m antraft.cli.main serve
```

**2. connect Agents:**
```python
await Antraft.guard(agent, tools) \
    .connect_swarm("http://localhost:8000") \
    .run()
```

---

## Documentation

*   **User Guide**: Comprehensive "How-To".
*   **Architecture**: System design and components.
*   **Threat Model**: Security analysis.
*   **Syntax Guide**: Configuration reference.

## Contributing

We welcome contributions! Please see `CONTRIBUTING.md` for details.

## License

MIT License
