# ANTRAFT

**Policy-enforced runtime for autonomous AI agents.**

Antraft is a secure runtime environment designed to execute autonomous AI agents with strict, policy-based governance. It ensures that agents operate within defined boundaries, enforcing explicit allow/deny rules, resource limits, and comprehensive audit logging.

Unlike standard agent frameworks that prioritize capability, Antraft prioritizes **control and safety**.

---

## Key Features

*   **Policy Enforcement**: Every action proposed by an agent is evaluated against a strict policy before execution.
*   **Secure by Default**: Actions are denied by default unless explicitly allowed.
*   **Hard & Soft Limits**: Enforce maximum action checks (Hard/DENY) and runtime duration (Soft/PAUSE).
*   **Immutable Audit Logs**: All agent decisions and runtime enforcements are recorded in an append-only audit log.
*   **Tool Gateway**: A controlled interface for external tool execution, preventing unauthorized access.

## Installation

Requires Python 3.10+.

```bash
# Clone the repository
git clone https://github.com/AshrafGalibShaik/ANTRAFT.git
cd ANTRAFT

# Install dependencies
pip install .
```

## Quick Start

Here is a simple example of how to run an agent within the Antraft runtime.

```python
from antraft.core.runtime import antraftRuntime
from antraft.core.agent import SimpleAgent
from antraft.policy.engine import PolicyEngine
from antraft.gateway.gateway import ToolGateway

# 1. Define the Policy
policy = {
    "allow": ["run_tests", "read_file"],
    "deny": ["shell_execute", "delete_file"],
    "limits": {
        "hard": {"max_actions": 10},     # Kill agent if exceeded
        "soft": {"max_runtime_seconds": 60} # Pause agent if exceeded
    },
}

# 2. Setup the Components
agent = SimpleAgent()
engine = PolicyEngine(policy)
gateway = ToolGateway(tools={
    "run_tests": lambda: print("Running tests..."),
    "read_file": lambda path: print(f"Reading {path}...")
})

# 3. Initialize Runtime
runtime = antraftRuntime(
    agent=agent,
    policy_engine=engine,
    tool_gateway=gateway
)

# 4. Execute
runtime.run()
```

## Architecture

Antraft operates on a rigorous cycle: **Propose > Evaluate > Enforce > Execute**.

1.  **Agent**: Proposes an `Action` (e.g., "delete file").
2.  **PolicyEngine**: The proposed action is passed to the Policy Engine, which evaluates it against the loaded ruleset. Evaluation fails fast and moves in a strict order:
    1.  **Explicit Deny**: Checks if the action is in the `deny` list. If found, returns `DENY`.
    2.  **Hard Limits**: Checks if global counters (e.g., `max_actions`) have been exceeded. If so, returns `DENY`.
    3.  **Soft Limits**: Checks if soft thresholds (e.g., `max_runtime_seconds`) have been exceeded. If so, returns `PAUSE`.
    4.  **Explicit Allow**: Checks if the action is in the `allow` list. If found, returns `ALLOW`.
    5.  **Default Deny**: If no rules match, the action is denied by default for security.
3.  **AuditLogger**: The `AuditEvent` is constructed, capturing the Agent ID, proposed Action, Decision (ALLOW/DENY/PAUSE), and the Reason. This is written to an append-only log file.
4.  **Runtime**: Enforces the decision:
    *   **ALLOW**: The action is passed to the `ToolGateway` for actual execution. The result is observed by the Agent.
    *   **DENY**: The runtime immediately terminates the agent loop (`context.kill()`).
    *   **PAUSE**: The runtime suspends the agent loop safely (`context.pause()`).

## Policy Configuration

Policies are defined as Python dictionaries or JSON objects. They dictate the exact boundaries of the agent's capabilities.

### Example Configuration

```json
{
    "allow": [
        "list_dir",
        "read_file",
        "analyze_code"
    ],
    "deny": [
        "connect_internet",
        "exec_subprocess",
        "write_file"
    ],
    "limits": {
        "hard": {
            "max_actions": 50
        },
        "soft": {
            "max_runtime_seconds": 300
        }
    }
}
```

### Limit Types

*   **Hard Limits**: These define the absolute maximums for an execution session. If a hard limit is breached, the agent is considered compromised or malfunctioning, and the runtime will `DENY` further actions and terminate.
*   **Soft Limits**: These define safe operating thresholds. If a soft limit is reached, the runtime will `PAUSE` execution. This allows for state inspection or manual intervention without killing the agent process entirely.

## API Reference

### antraft.core.runtime.antraftRuntime

The main entry point for executing an agent.

*   `__init__(agent, policy_engine, tool_gateway, auditor=None)`: Initializes the runtime components.
*   `run() -> RuntimeContext`: Starts the main execution loop. It continues until the agent finishes or a policy decision stops it.

### antraft.policy.engine.PolicyEngine

Stateless evaluator of actions.

*   `evaluate(action, context) -> PolicyDecision`: Takes a proposed action and current runtime statistics (action count, runtime duration) and returns an enforcement decision.

### antraft.gateway.gateway.ToolGateway

The security boundary for external tools.

*   `execute(action) -> Any`: Executes the verified action. This method is only called *after* the PolicyEngine has returned `ALLOW`.

## Contributing

Contributions are welcome. Please feel free to submit a Pull Request.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.
