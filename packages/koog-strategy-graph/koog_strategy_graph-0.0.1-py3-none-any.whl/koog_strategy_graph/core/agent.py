from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import uuid4

from .core import GraphContext, GraphConfig, Strategy
from .environment import AgentEnvironment
from .features import FeaturePipeline
from .event_handler import _KOOG_RUN_ID_KEY
from .llm_executor import AgentSession, LLMExecutor
from .persistence import PersistenceFeature, PersistenceFeatureConfig, _KOOG_AGENT_ID_KEY, _KOOG_SESSION_KEY


@dataclass
class AIAgent:
    """
    Minimal Koog-like agent wrapper for Python strategy graphs.

    Responsibilities:
    - Own agent identity (agent_id)
    - Own session (prompt history)
    - Own environment (tools)
    - Install features (e.g., Persistence) and attach them to execution via GraphContext pipeline
    """

    strategy: Strategy[Any, Any]
    llm: Optional[LLMExecutor] = None
    environment: AgentEnvironment = field(default_factory=AgentEnvironment)
    agent_id: str = field(default_factory=lambda: str(uuid4()))
    session: AgentSession = field(default_factory=AgentSession)
    pipeline: FeaturePipeline = field(default_factory=FeaturePipeline)
    config: GraphConfig = field(default_factory=GraphConfig)

    def install_persistence(self, config: Optional[PersistenceFeatureConfig] = None) -> PersistenceFeature:
        feature = PersistenceFeature(config=config or PersistenceFeatureConfig())
        self.pipeline.features.append(feature)
        return feature

    def run(self, input_value: Any, *, ctx: Optional[GraphContext] = None) -> Any:
        """
        Execute the agent strategy.

        If a context is not provided, creates a fresh root GraphContext and attaches:
        - pipeline
        - agent_id
        - session
        """
        if ctx is None:
            ctx = GraphContext(config=self.config)

        # Attach agent execution scaffolding expected by features (Persistence).
        ctx.store(_KOOG_AGENT_ID_KEY, self.agent_id)
        ctx.store(_KOOG_SESSION_KEY, self.session)
        # Friendly aliases for node logic (avoid importing private keys).
        ctx.store("agent_id", self.agent_id)
        ctx.store("session", self.session)
        # Run-scoped id for Koog-style eventing.
        run_id = str(ctx.get(_KOOG_RUN_ID_KEY, "") or "")
        if not run_id:
            run_id = str(uuid4())
            ctx.store(_KOOG_RUN_ID_KEY, run_id)
        if self.llm is not None:
            ctx.store("llm", self.llm)
        if self.environment is not None:
            ctx.store("environment", self.environment)
        ctx.set_pipeline(self.pipeline)

        self.pipeline.on_agent_starting(ctx=ctx, agent_id=self.agent_id, run_id=run_id)

        # Koog parity baseline: if no LLM tools have been configured, expose environment tools by default.
        # The actual tool selection strategy is applied by `AIAgentGraphStrategy` / `AIAgentSubgraph` (agent_dsl).
        if isinstance(self.session, AgentSession) and not self.session.llm_tools and self.environment is not None:
            self.session.llm_tools = list(self.environment.tools.descriptors())

        try:
            result = self.strategy.execute(ctx, input_value)
            self.pipeline.on_agent_completed(ctx=ctx, agent_id=self.agent_id, run_id=run_id, result=result)
            return result
        except Exception as e:
            self.pipeline.on_agent_execution_failed(ctx=ctx, agent_id=self.agent_id, run_id=run_id, error=e)
            raise
        finally:
            self.pipeline.on_agent_closing(ctx=ctx, agent_id=self.agent_id)

