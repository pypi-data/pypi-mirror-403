from typing import Dict, List, Any, Callable
from antraft.core.agent import BaseAgent
from antraft.policy.engine import PolicyEngine
from antraft.gateway.gateway import ToolGateway
from antraft.audit.recorder import SessionRecorder
from antraft.security.pii import PIIRedactor
from antraft.core.runtime import antraftRuntime
from antraft.policy.loader import PolicyLoader

class AntraftBuilder:
    def __init__(self, agent, tools: Dict[str, Callable]):
        self.agent = agent
        self.tools = tools
        self.policy_data = {"allow": [], "deny": [], "rules": []}
        self.recorder_path = None
        self.redact_pii = False
        self.control_url = None
        
    def allow(self, actions: List[str]):
        """Quickly allow a list of actions."""
        self.policy_data["allow"].extend(actions)
        return self

    def deny(self, actions: List[str]):
        """Quickly deny a list of actions."""
        self.policy_data["deny"].extend(actions)
        return self

    def load_policy(self, path: str):
        """Load complex policy from YAML file."""
        self.policy_data = PolicyLoader.load_from_file(path)
        return self
        
    def record_session(self, path: str, redact_pii: bool = True):
        """Enable session recording to a JSONL file."""
        self.recorder_path = path
        self.redact_pii = redact_pii
        return self

    def connect_swarm(self, url: str):
        """Connect to a remote Control Plane (Swarm Mode)."""
        self.control_url = url
        return self

    def build(self) -> antraftRuntime:
        """Construct the Runtime environment."""
        # 1. Setup Policy
        engine = PolicyEngine(self.policy_data)
        
        # 2. Setup Gateway
        gateway = ToolGateway(self.tools)
        
        # 3. Setup Recorder
        recorder = None
        if self.recorder_path:
            redactor = PIIRedactor() if self.redact_pii else None
            recorder = SessionRecorder(self.recorder_path, redactor=redactor)
            
        # 4. Build Runtime
        return antraftRuntime(
            agent=self.agent,
            policy_engine=engine,
            tool_gateway=gateway,
            recorder=recorder,
            control_url=self.control_url
        )

    async def run(self):
        """Build and Run immediately."""
        runtime = self.build()
        return await runtime.run()


class Antraft:
    """
    Main Entry Point for Antraft Governance.
    """
    @staticmethod
    def guard(agent, tools: Dict[str, Callable]) -> AntraftBuilder:
        return AntraftBuilder(agent, tools)
