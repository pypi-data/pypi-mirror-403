# EATP Implementation Plan: Orchestration Integration

## Document Control
- **Version**: 1.0
- **Date**: 2025-12-15
- **Status**: Planning
- **Author**: Kaizen Framework Team

---

## Overview

This document describes how EATP integrates with Kaizen's existing orchestration runtime and multi-agent patterns. The goal is to add trust verification and audit capabilities without breaking existing workflow patterns.

---

## Current Orchestration Architecture

### OrchestrationRuntime

```python
# Current: From kaizen/orchestration/runtime.py
class OrchestrationRuntime:
    """Runtime for executing multi-agent workflows."""

    def __init__(
        self,
        agents: Dict[str, BaseAgent],
        patterns: List[Pattern] = None,
        config: RuntimeConfig = None
    ):
        self.agents = agents
        self.patterns = patterns or []
        self.config = config or RuntimeConfig()

    async def execute(
        self,
        input: Any,
        pattern: str = "sequential"
    ) -> Any:
        """Execute agents using specified pattern."""
        pass
```

### Existing Patterns

| Pattern | Description | Trust Requirement |
|---------|-------------|-------------------|
| Sequential | A → B → C | Simple delegation chain |
| Parallel | A → [B, C, D] → E | Multiple parallel delegations |
| Supervisor-Worker | Super → [W1, W2, W3] | Supervisor manages delegation |
| Router | Route → Agent_X | Dynamic capability matching |
| Ensemble | [E1, E2, E3] → Synthesize | Parallel with aggregation |
| Blackboard | Controller ↔ Specialists | Iterative with shared state |

---

## Trust-Aware OrchestrationRuntime

### Enhanced Runtime

```python
from kaizen.orchestration.runtime import OrchestrationRuntime
from kaizen.trust.operations import TrustOperations
from kaizen.trust.agent import TrustedAgent

class TrustAwareOrchestrationRuntime(OrchestrationRuntime):
    """Orchestration runtime with EATP trust verification."""

    def __init__(
        self,
        agents: Dict[str, TrustedAgent],
        trust_ops: TrustOperations,
        patterns: List[TrustAwarePattern] = None,
        config: RuntimeConfig = None,
        verification_level: VerificationLevel = VerificationLevel.STANDARD,
        require_trust: bool = True
    ):
        # Convert to base agents for parent
        super().__init__(
            agents={k: v for k, v in agents.items()},
            patterns=patterns,
            config=config
        )

        self.trust_ops = trust_ops
        self.verification_level = verification_level
        self.require_trust = require_trust
        self._execution_context: Optional[TrustExecutionContext] = None

    async def execute(
        self,
        input: Any,
        pattern: str = "sequential",
        initiator_id: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> OrchestrationResult:
        """
        Execute agents with trust verification.

        Args:
            input: Input data for workflow
            pattern: Orchestration pattern to use
            initiator_id: ID of agent/user initiating execution
            task_id: Task identifier for audit trail

        Returns:
            OrchestrationResult with execution details and audit trail
        """
        # 1. Create execution context
        self._execution_context = TrustExecutionContext(
            task_id=task_id or f"orch-{uuid4()}",
            initiator_id=initiator_id,
            started_at=datetime.utcnow()
        )

        # 2. Verify all agents have trust (if required)
        if self.require_trust:
            await self._verify_all_agents()

        # 3. Get pattern executor
        pattern_executor = self._get_pattern_executor(pattern)

        # 4. Execute with trust context
        try:
            result = await pattern_executor.execute(
                input=input,
                agents=self.agents,
                context=self._execution_context,
                trust_ops=self.trust_ops
            )

            # Record success
            await self._audit_execution_complete(result)

            return OrchestrationResult(
                success=True,
                result=result,
                audit_trail=self._execution_context.audit_trail,
                delegations=self._execution_context.delegations
            )

        except TrustError as e:
            await self._audit_execution_failed(e)
            raise

    async def _verify_all_agents(self):
        """Verify all agents have valid trust chains."""
        for name, agent in self.agents.items():
            if not isinstance(agent, TrustedAgent):
                raise TrustError(f"Agent '{name}' is not a TrustedAgent")

            if not agent.is_trusted:
                raise TrustError(f"Agent '{name}' has no valid trust chain")

            # Full verification
            result = await self.trust_ops.verify(
                agent_id=agent.id,
                action="orchestration_participation",
                level=self.verification_level
            )

            if not result.valid:
                raise TrustError(f"Agent '{name}' failed trust verification: {result.reason}")

    def _get_pattern_executor(self, pattern: str) -> TrustAwarePatternExecutor:
        """Get trust-aware pattern executor."""
        executors = {
            "sequential": TrustAwareSequentialExecutor(),
            "parallel": TrustAwareParallelExecutor(),
            "supervisor_worker": TrustAwareSupervisorWorkerExecutor(),
            "router": TrustAwareRouterExecutor(),
            "ensemble": TrustAwareEnsembleExecutor(),
            "blackboard": TrustAwareBlackboardExecutor(),
            "consensus": TrustAwareConsensusExecutor(),
            "debate": TrustAwareDebateExecutor(),
            "handoff": TrustAwareHandoffExecutor()
        }
        return executors.get(pattern, TrustAwareSequentialExecutor())
```

### Execution Context

```python
@dataclass
class TrustExecutionContext:
    """Context for trust-aware execution."""

    task_id: str
    initiator_id: Optional[str]
    started_at: datetime
    audit_trail: List[AuditAnchor] = field(default_factory=list)
    delegations: List[DelegationRecord] = field(default_factory=list)
    current_agent_id: Optional[str] = None
    parent_anchor_id: Optional[str] = None

    def record_delegation(self, delegation: DelegationRecord):
        """Record a delegation in context."""
        self.delegations.append(delegation)

    def record_audit(self, anchor: AuditAnchor):
        """Record an audit anchor in context."""
        self.audit_trail.append(anchor)
        self.parent_anchor_id = anchor.id
```

---

## Trust-Aware Pattern Executors

### Base Pattern Executor

```python
class TrustAwarePatternExecutor(ABC):
    """Base class for trust-aware pattern execution."""

    @abstractmethod
    async def execute(
        self,
        input: Any,
        agents: Dict[str, TrustedAgent],
        context: TrustExecutionContext,
        trust_ops: TrustOperations
    ) -> Any:
        """Execute pattern with trust verification."""
        pass

    async def delegate_to_agent(
        self,
        from_agent: TrustedAgent,
        to_agent: TrustedAgent,
        capabilities: List[str],
        context: TrustExecutionContext,
        trust_ops: TrustOperations,
        additional_constraints: List[str] = None
    ) -> DelegationRecord:
        """Create delegation between agents."""
        delegation = await trust_ops.delegate(
            delegator_id=from_agent.id,
            delegatee_id=to_agent.id,
            task_id=context.task_id,
            capabilities=capabilities,
            additional_constraints=additional_constraints
        )

        await to_agent.receive_delegation(delegation)
        context.record_delegation(delegation)

        return delegation
```

### Sequential Pattern

```python
class TrustAwareSequentialExecutor(TrustAwarePatternExecutor):
    """Sequential execution with delegation chain."""

    async def execute(
        self,
        input: Any,
        agents: Dict[str, TrustedAgent],
        context: TrustExecutionContext,
        trust_ops: TrustOperations
    ) -> Any:
        """
        Execute agents sequentially with trust delegation.

        A → B → C

        Each agent delegates to the next in sequence.
        """
        agent_list = list(agents.values())
        current_input = input
        previous_agent = None

        for i, agent in enumerate(agent_list):
            context.current_agent_id = agent.id

            # Create delegation from previous agent (or initiator)
            if previous_agent:
                await self.delegate_to_agent(
                    from_agent=previous_agent,
                    to_agent=agent,
                    capabilities=self._infer_capabilities(agent),
                    context=context,
                    trust_ops=trust_ops
                )

            # Execute agent
            current_input = await agent.run(current_input)
            previous_agent = agent

        return current_input

    def _infer_capabilities(self, agent: TrustedAgent) -> List[str]:
        """Infer required capabilities from agent."""
        return agent.capabilities[:1] if agent.capabilities else ["execute"]
```

### Supervisor-Worker Pattern

```python
class TrustAwareSupervisorWorkerExecutor(TrustAwarePatternExecutor):
    """Supervisor-worker pattern with explicit delegation."""

    async def execute(
        self,
        input: Any,
        agents: Dict[str, TrustedAgent],
        context: TrustExecutionContext,
        trust_ops: TrustOperations
    ) -> Any:
        """
        Execute supervisor-worker pattern.

                      ┌─→ Worker1 ─┐
        Supervisor ───┼─→ Worker2 ─┼──→ Supervisor (aggregate)
                      └─→ Worker3 ─┘
        """
        # Identify supervisor (first agent or marked as supervisor)
        supervisor = self._get_supervisor(agents)
        workers = self._get_workers(agents, supervisor)

        context.current_agent_id = supervisor.id

        # Supervisor decomposes task
        decomposition = await supervisor.decompose_task(input)

        # Parallel delegation to workers
        worker_tasks = []
        for subtask, worker in zip(decomposition.subtasks, workers):
            # Delegate to worker
            delegation = await self.delegate_to_agent(
                from_agent=supervisor,
                to_agent=worker,
                capabilities=subtask.required_capabilities,
                context=context,
                trust_ops=trust_ops,
                additional_constraints=subtask.constraints
            )

            # Create async task
            worker_tasks.append(
                self._execute_worker(worker, subtask, context)
            )

        # Wait for all workers
        worker_results = await asyncio.gather(*worker_tasks, return_exceptions=True)

        # Handle any failures
        for result in worker_results:
            if isinstance(result, Exception):
                await trust_ops.audit(
                    agent_id=supervisor.id,
                    action="worker_failed",
                    result=ActionResult.FAILURE,
                    context={"error": str(result)}
                )

        # Supervisor aggregates results
        context.current_agent_id = supervisor.id
        final_result = await supervisor.aggregate_results(
            original_input=input,
            worker_results=[r for r in worker_results if not isinstance(r, Exception)]
        )

        return final_result

    async def _execute_worker(
        self,
        worker: TrustedAgent,
        subtask: Subtask,
        context: TrustExecutionContext
    ) -> Any:
        """Execute worker with subtask."""
        return await worker.run(subtask.input)

    def _get_supervisor(self, agents: Dict[str, TrustedAgent]) -> TrustedAgent:
        """Identify supervisor agent."""
        for name, agent in agents.items():
            if isinstance(agent, TrustedSupervisorAgent):
                return agent
            if "supervisor" in name.lower():
                return agent
        return list(agents.values())[0]

    def _get_workers(
        self,
        agents: Dict[str, TrustedAgent],
        supervisor: TrustedAgent
    ) -> List[TrustedAgent]:
        """Get worker agents (excluding supervisor)."""
        return [a for a in agents.values() if a.id != supervisor.id]
```

### Router Pattern

```python
class TrustAwareRouterExecutor(TrustAwarePatternExecutor):
    """Router pattern with capability-based routing."""

    async def execute(
        self,
        input: Any,
        agents: Dict[str, TrustedAgent],
        context: TrustExecutionContext,
        trust_ops: TrustOperations
    ) -> Any:
        """
        Execute router pattern with trust-aware routing.

                    ┌─→ Agent A
        Router ─────┼─→ Agent B (selected)
                    └─→ Agent C
        """
        router = self._get_router(agents)
        target_agents = self._get_target_agents(agents, router)

        context.current_agent_id = router.id

        # Router determines required capability
        routing_decision = await router.route(input)
        required_capability = routing_decision.required_capability

        # Find agent with capability AND trust
        selected_agent = await self._select_trusted_agent(
            target_agents,
            required_capability,
            trust_ops
        )

        if not selected_agent:
            raise NoCapableAgentError(required_capability)

        # Delegate to selected agent
        await self.delegate_to_agent(
            from_agent=router,
            to_agent=selected_agent,
            capabilities=[required_capability],
            context=context,
            trust_ops=trust_ops
        )

        # Execute selected agent
        context.current_agent_id = selected_agent.id
        return await selected_agent.run(input)

    async def _select_trusted_agent(
        self,
        agents: List[TrustedAgent],
        capability: str,
        trust_ops: TrustOperations
    ) -> Optional[TrustedAgent]:
        """Select agent with capability and valid trust."""
        for agent in agents:
            # Check capability
            if capability not in agent.capabilities:
                continue

            # Verify trust for this capability
            result = await trust_ops.verify(
                agent_id=agent.id,
                action=capability,
                level=VerificationLevel.STANDARD
            )

            if result.valid:
                return agent

        return None
```

### Ensemble Pattern

```python
class TrustAwareEnsembleExecutor(TrustAwarePatternExecutor):
    """Ensemble pattern with parallel expert consultation."""

    async def execute(
        self,
        input: Any,
        agents: Dict[str, TrustedAgent],
        context: TrustExecutionContext,
        trust_ops: TrustOperations
    ) -> Any:
        """
        Execute ensemble pattern.

                  ┌─→ Expert1 ─┐
        Input ────┼─→ Expert2 ─┼──→ Synthesizer
                  └─→ Expert3 ─┘
        """
        synthesizer = self._get_synthesizer(agents)
        experts = self._get_experts(agents, synthesizer)

        # Parallel expert consultation
        expert_tasks = []
        for expert in experts:
            # Delegate to expert
            await self.delegate_to_agent(
                from_agent=synthesizer,
                to_agent=expert,
                capabilities=["analyze", "consult"],
                context=context,
                trust_ops=trust_ops
            )

            expert_tasks.append(expert.run(input))

        # Gather expert opinions
        expert_results = await asyncio.gather(*expert_tasks, return_exceptions=True)

        # Filter out failures
        valid_results = []
        for i, result in enumerate(expert_results):
            if isinstance(result, Exception):
                await trust_ops.audit(
                    agent_id=experts[i].id,
                    action="expert_consultation_failed",
                    result=ActionResult.FAILURE,
                    context={"error": str(result)}
                )
            else:
                valid_results.append({
                    "expert_id": experts[i].id,
                    "result": result,
                    "capabilities": experts[i].capabilities
                })

        # Synthesizer combines results
        context.current_agent_id = synthesizer.id
        return await synthesizer.synthesize(input, valid_results)
```

### Blackboard Pattern

```python
class TrustAwareBlackboardExecutor(TrustAwarePatternExecutor):
    """Blackboard pattern with controlled shared state."""

    async def execute(
        self,
        input: Any,
        agents: Dict[str, TrustedAgent],
        context: TrustExecutionContext,
        trust_ops: TrustOperations
    ) -> Any:
        """
        Execute blackboard pattern.

                          ┌─→ Analyst   ─┐
        Controller ───────┼─→ Validator ─┼───→ Blackboard ───→ Solution
           ↑              └─→ Optimizer ─┘         ↓
           └────────────────────────────────────────┘
        """
        controller = self._get_controller(agents)
        specialists = self._get_specialists(agents, controller)

        # Initialize blackboard
        blackboard = Blackboard(initial_state=input)

        # Iterative problem-solving
        max_iterations = 10
        for iteration in range(max_iterations):
            context.current_agent_id = controller.id

            # Controller selects specialist
            selection = await controller.select_specialist(
                blackboard.state,
                specialists
            )

            if selection.solved:
                break

            specialist = selection.specialist

            # Verify specialist can contribute
            result = await trust_ops.verify(
                agent_id=specialist.id,
                action="blackboard_contribution",
                level=VerificationLevel.STANDARD
            )

            if not result.valid:
                continue  # Skip untrusted specialist

            # Delegate to specialist
            await self.delegate_to_agent(
                from_agent=controller,
                to_agent=specialist,
                capabilities=["analyze", "contribute"],
                context=context,
                trust_ops=trust_ops,
                additional_constraints=["blackboard_write_only"]
            )

            # Specialist contributes
            context.current_agent_id = specialist.id
            contribution = await specialist.contribute(blackboard.state)

            # Audit contribution
            await trust_ops.audit(
                agent_id=specialist.id,
                action="blackboard_contribution",
                result=ActionResult.SUCCESS,
                context={
                    "iteration": iteration,
                    "contribution_type": contribution.type
                }
            )

            # Update blackboard
            blackboard.update(contribution)

        return blackboard.state
```

---

## Integration with AgentRegistry

### Trust-Aware Registry

```python
class TrustAwareAgentRegistry(AgentRegistry):
    """Agent registry with trust management."""

    def __init__(self, trust_ops: TrustOperations):
        super().__init__()
        self.trust_ops = trust_ops
        self._trust_chains: Dict[str, TrustLineageChain] = {}

    async def register(
        self,
        agent: TrustedAgent,
        authority_id: Optional[str] = None,
        capabilities: List[CapabilityRequest] = None
    ) -> str:
        """Register agent with trust establishment."""
        # Register in base registry
        agent_id = await super().register(agent)

        # Establish trust if authority provided
        if authority_id and capabilities:
            chain = await agent.establish_trust(
                authority_id=authority_id,
                capabilities=capabilities
            )
            self._trust_chains[agent_id] = chain

        return agent_id

    async def find_capable_agent(
        self,
        capability: str,
        require_trust: bool = True
    ) -> Optional[TrustedAgent]:
        """Find agent with capability and valid trust."""
        for agent_id, agent in self._agents.items():
            if not isinstance(agent, TrustedAgent):
                continue

            # Check capability
            if capability not in agent.capabilities:
                continue

            # Verify trust if required
            if require_trust:
                result = await self.trust_ops.verify(
                    agent_id=agent.id,
                    action=capability,
                    level=VerificationLevel.STANDARD
                )
                if not result.valid:
                    continue

            return agent

        return None

    async def get_trust_status(self) -> Dict[str, TrustStatus]:
        """Get trust status for all registered agents."""
        status = {}
        for agent_id, agent in self._agents.items():
            if isinstance(agent, TrustedAgent):
                status[agent_id] = TrustStatus(
                    is_trusted=agent.is_trusted,
                    capabilities=agent.capabilities,
                    constraints=agent.effective_constraints,
                    chain_hash=agent.trust_chain.hash() if agent.trust_chain else None
                )
        return status
```

---

## Workflow Builder Integration

### Trust-Aware Workflow

```python
class TrustAwareWorkflowBuilder:
    """Build workflows with trust requirements."""

    def __init__(self, trust_ops: TrustOperations):
        self.trust_ops = trust_ops
        self._agents: List[TrustedAgent] = []
        self._connections: List[AgentConnection] = []
        self._trust_requirements: Dict[str, List[str]] = {}

    def add_agent(
        self,
        agent: TrustedAgent,
        required_capabilities: List[str] = None
    ) -> "TrustAwareWorkflowBuilder":
        """Add agent with trust requirements."""
        self._agents.append(agent)
        if required_capabilities:
            self._trust_requirements[agent.id] = required_capabilities
        return self

    def connect(
        self,
        from_agent: TrustedAgent,
        to_agent: TrustedAgent,
        capabilities_to_delegate: List[str] = None
    ) -> "TrustAwareWorkflowBuilder":
        """Connect agents with capability delegation."""
        self._connections.append(AgentConnection(
            from_agent=from_agent,
            to_agent=to_agent,
            capabilities=capabilities_to_delegate or []
        ))
        return self

    async def build(self) -> TrustAwareWorkflow:
        """Build and validate workflow."""
        # Validate all agents have required trust
        for agent in self._agents:
            required = self._trust_requirements.get(agent.id, [])
            for cap in required:
                if cap not in agent.capabilities:
                    raise WorkflowValidationError(
                        f"Agent {agent.id} missing required capability: {cap}"
                    )

        # Validate delegation connections
        for conn in self._connections:
            for cap in conn.capabilities:
                if cap not in conn.from_agent.capabilities:
                    raise WorkflowValidationError(
                        f"Cannot delegate '{cap}' from {conn.from_agent.id}: capability not held"
                    )

        return TrustAwareWorkflow(
            agents=self._agents,
            connections=self._connections,
            trust_requirements=self._trust_requirements
        )
```

---

## Usage Examples

### Basic Trust-Aware Orchestration

```python
# Setup
trust_ops = TrustOperations(...)
authority = await create_enterprise_authority()

# Create trusted agents
analyst = TrustedAgent(name="analyst")
await analyst.establish_trust(
    authority_id=authority.id,
    capabilities=[CapabilityRequest(capability="analyze_data", ...)],
    constraints=["read_only"]
)

summarizer = TrustedAgent(name="summarizer")
await summarizer.establish_trust(
    authority_id=authority.id,
    capabilities=[CapabilityRequest(capability="summarize", ...)],
    constraints=["text_output_only"]
)

# Create runtime
runtime = TrustAwareOrchestrationRuntime(
    agents={"analyst": analyst, "summarizer": summarizer},
    trust_ops=trust_ops
)

# Execute with trust
result = await runtime.execute(
    input={"data": financial_data},
    pattern="sequential",
    task_id="analysis-001"
)

# Result includes audit trail
print(f"Delegations: {len(result.delegations)}")
print(f"Audit entries: {len(result.audit_trail)}")
```

### Pipeline with Trust Verification

```python
# Build workflow
workflow = (
    TrustAwareWorkflowBuilder(trust_ops)
    .add_agent(researcher, required_capabilities=["search"])
    .add_agent(analyst, required_capabilities=["analyze"])
    .add_agent(writer, required_capabilities=["write"])
    .connect(researcher, analyst, capabilities_to_delegate=["analyze"])
    .connect(analyst, writer, capabilities_to_delegate=["write"])
    .build()
)

# Execute
result = await workflow.execute(input_data)
```

---

## Next Steps

1. **Document 07**: ESA Pattern Implementation
2. **Document 08**: Testing Strategy
3. Implement TrustAwareOrchestrationRuntime in `kaizen.orchestration`
4. Create pattern-specific tests
