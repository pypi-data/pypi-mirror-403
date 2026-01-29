# EATP Implementation Plan: TrustedAgent Integration

## Document Control
- **Version**: 1.0
- **Date**: 2025-12-15
- **Status**: Planning
- **Author**: Kaizen Framework Team

---

## Overview

This document describes how EATP integrates with Kaizen's existing BaseAgent architecture. The goal is to enhance BaseAgent with trust capabilities while maintaining backward compatibility.

---

## Current BaseAgent Architecture

### Existing Structure

```python
# From kaizen/core/base_agent.py
class BaseAgent:
    """Base class for all Kaizen agents."""

    def __init__(
        self,
        name: str,
        signature: Optional[Signature] = None,
        llm_config: Optional[LLMConfig] = None,
        tools: Optional[List[Tool]] = None,
        memory: Optional[Memory] = None,
        **kwargs
    ):
        self.name = name
        self.signature = signature
        self.llm_config = llm_config
        self.tools = tools or []
        self.memory = memory

    async def run(self, input: Any) -> Any:
        """Execute the agent's main logic."""
        pass

    async def call_tool(self, tool_name: str, **kwargs) -> Any:
        """Invoke a tool."""
        pass
```

### Key Observations

1. **No trust layer**: Current agents have no concept of authorization
2. **No delegation tracking**: No record of who assigned tasks
3. **No constraint enforcement**: Agents can do anything their tools allow
4. **No audit trail**: No systematic action logging

---

## TrustedAgent Design

### Design Principles

1. **Inheritance over composition**: TrustedAgent extends BaseAgent
2. **Opt-in trust**: Untrusted agents still work (for backward compatibility)
3. **Automatic verification**: Trust checked before every action
4. **Transparent auditing**: All actions automatically logged

### Class Hierarchy

```
BaseAgent
    │
    ▼
TrustedAgent
    │
    ├── TrustedSupervisorAgent
    ├── TrustedWorkerAgent
    └── TrustedESAAgent (Enterprise System Agent)
```

### TrustedAgent Implementation

```python
from kaizen.core.base_agent import BaseAgent
from kaizen.trust.chain import TrustLineageChain
from kaizen.trust.operations import TrustOperations, VerificationLevel
from kaizen.trust.exceptions import TrustError, VerificationFailedError

class TrustedAgent(BaseAgent):
    """Agent with EATP trust capabilities."""

    def __init__(
        self,
        name: str,
        trust_chain: Optional[TrustLineageChain] = None,
        trust_ops: Optional[TrustOperations] = None,
        verification_level: VerificationLevel = VerificationLevel.STANDARD,
        **kwargs
    ):
        super().__init__(name=name, **kwargs)

        self._trust_chain = trust_chain
        self._trust_ops = trust_ops or get_default_trust_ops()
        self._verification_level = verification_level
        self._current_delegation: Optional[DelegationRecord] = None

    @property
    def id(self) -> str:
        """Unique agent identifier for trust operations."""
        return f"agent-{self.name}"

    @property
    def trust_chain(self) -> Optional[TrustLineageChain]:
        """Get agent's trust lineage chain."""
        return self._trust_chain

    @property
    def is_trusted(self) -> bool:
        """Check if agent has valid trust chain."""
        return self._trust_chain is not None and self._trust_chain.verify().valid

    @property
    def capabilities(self) -> List[str]:
        """Get agent's attested capabilities."""
        if not self._trust_chain:
            return []
        return [cap.capability for cap in self._trust_chain.capabilities]

    @property
    def effective_constraints(self) -> List[str]:
        """Get all active constraints."""
        if not self._trust_chain:
            return []
        return self._trust_chain.constraint_envelope.get_all_constraints()

    # =========================================================================
    # Trust Lifecycle Methods
    # =========================================================================

    async def establish_trust(
        self,
        authority_id: str,
        capabilities: List[CapabilityRequest],
        constraints: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> TrustLineageChain:
        """
        Establish initial trust for this agent.

        Args:
            authority_id: Authority granting trust
            capabilities: Requested capabilities
            constraints: Initial constraints
            metadata: Additional context

        Returns:
            TrustLineageChain: The established trust chain
        """
        self._trust_chain = await self._trust_ops.establish(
            agent_id=self.id,
            authority_id=authority_id,
            capabilities=capabilities,
            constraints=constraints,
            metadata=metadata
        )
        return self._trust_chain

    async def receive_delegation(
        self,
        delegation: DelegationRecord
    ) -> None:
        """
        Receive and record a delegation from another agent.

        Args:
            delegation: The delegation record
        """
        if not self._trust_chain:
            raise TrustError("Cannot receive delegation without trust chain")

        # Verify delegation is valid
        if delegation.delegatee_id != self.id:
            raise TrustError(f"Delegation is for {delegation.delegatee_id}, not {self.id}")

        # Update trust chain
        self._trust_chain.delegations.append(delegation)
        self._trust_chain.constraint_envelope = await self._trust_ops.recompute_envelope(
            self._trust_chain
        )
        self._current_delegation = delegation

    # =========================================================================
    # Overridden Methods with Trust Verification
    # =========================================================================

    async def run(self, input: Any) -> Any:
        """
        Execute agent logic with trust verification.

        Overrides BaseAgent.run() to add VERIFY before execution
        and AUDIT after execution.
        """
        # 1. Verify trust to run
        if self._trust_chain:
            await self._verify_action("agent_run", resource=None)

        # 2. Execute with audit context
        async with self._audit_context("agent_run") as audit:
            try:
                result = await super().run(input)
                audit.result = ActionResult.SUCCESS
                return result
            except Exception as e:
                audit.result = ActionResult.FAILURE
                audit.context["error"] = str(e)
                raise

    async def call_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Invoke a tool with trust verification.

        Overrides BaseAgent.call_tool() to verify capability
        before tool invocation.
        """
        # 1. Verify trust for this tool
        if self._trust_chain:
            await self._verify_action(
                f"tool:{tool_name}",
                resource=kwargs.get("resource")
            )

        # 2. Execute with audit
        async with self._audit_context(f"tool:{tool_name}") as audit:
            audit.context["tool_args"] = self._sanitize_for_audit(kwargs)
            try:
                result = await super().call_tool(tool_name, **kwargs)
                audit.result = ActionResult.SUCCESS
                return result
            except Exception as e:
                audit.result = ActionResult.FAILURE
                audit.context["error"] = str(e)
                raise

    # =========================================================================
    # Trust-Aware Delegation
    # =========================================================================

    async def delegate_to(
        self,
        worker: "TrustedAgent",
        task_id: str,
        capabilities: List[str],
        additional_constraints: List[str] = None
    ) -> DelegationRecord:
        """
        Delegate work to another trusted agent.

        Args:
            worker: Agent to delegate to
            task_id: Task identifier
            capabilities: Capabilities to delegate
            additional_constraints: Extra constraints

        Returns:
            DelegationRecord: Record of delegation
        """
        if not self._trust_chain:
            raise TrustError("Cannot delegate without trust chain")

        if not worker.is_trusted:
            raise TrustError(f"Cannot delegate to untrusted agent: {worker.name}")

        # Create delegation
        delegation = await self._trust_ops.delegate(
            delegator_id=self.id,
            delegatee_id=worker.id,
            task_id=task_id,
            capabilities=capabilities,
            additional_constraints=additional_constraints
        )

        # Worker receives delegation
        await worker.receive_delegation(delegation)

        return delegation

    # =========================================================================
    # Internal Trust Methods
    # =========================================================================

    async def _verify_action(
        self,
        action: str,
        resource: Optional[str] = None
    ) -> VerificationResult:
        """Verify trust before action."""
        result = await self._trust_ops.verify(
            agent_id=self.id,
            action=action,
            resource=resource,
            level=self._verification_level,
            context=self._build_verification_context()
        )

        if not result.valid:
            raise VerificationFailedError(
                agent_id=self.id,
                action=action,
                reason=result.reason,
                violations=result.violations
            )

        return result

    @asynccontextmanager
    async def _audit_context(self, action: str):
        """Context manager for action auditing."""
        audit_data = AuditData(
            action=action,
            result=ActionResult.SUCCESS,
            context={}
        )

        try:
            yield audit_data
        finally:
            if self._trust_chain:
                await self._trust_ops.audit(
                    agent_id=self.id,
                    action=audit_data.action,
                    resource=audit_data.resource,
                    result=audit_data.result,
                    context=audit_data.context,
                    parent_anchor_id=self._get_parent_anchor_id()
                )

    def _build_verification_context(self) -> Dict[str, Any]:
        """Build context for constraint evaluation."""
        return {
            "current_time": datetime.utcnow(),
            "delegation_id": self._current_delegation.id if self._current_delegation else None,
            "agent_name": self.name
        }

    def _get_parent_anchor_id(self) -> Optional[str]:
        """Get parent audit anchor for chaining."""
        if self._current_delegation:
            return self._current_delegation.id
        return None

    def _sanitize_for_audit(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive data before auditing."""
        sensitive_keys = {"password", "api_key", "secret", "token"}
        return {
            k: "[REDACTED]" if k.lower() in sensitive_keys else v
            for k, v in data.items()
        }
```

---

## Specialized TrustedAgent Types

### TrustedSupervisorAgent

```python
class TrustedSupervisorAgent(TrustedAgent):
    """Supervisor agent with enhanced delegation capabilities."""

    def __init__(
        self,
        name: str,
        workers: List[TrustedAgent] = None,
        delegation_strategy: DelegationStrategy = None,
        **kwargs
    ):
        super().__init__(name=name, **kwargs)
        self._workers = workers or []
        self._delegation_strategy = delegation_strategy or DefaultDelegationStrategy()
        self._active_delegations: Dict[str, DelegationRecord] = {}

    async def assign_task(
        self,
        task: Task,
        worker: Optional[TrustedAgent] = None
    ) -> TaskResult:
        """
        Assign task to worker with trust delegation.

        If no worker specified, uses delegation strategy to select.
        """
        # 1. Select worker
        if worker is None:
            worker = await self._delegation_strategy.select_worker(
                task=task,
                workers=self._workers,
                trust_ops=self._trust_ops
            )

        if worker is None:
            raise NoSuitableWorkerError(task.id)

        # 2. Delegate with appropriate constraints
        delegation = await self.delegate_to(
            worker=worker,
            task_id=task.id,
            capabilities=task.required_capabilities,
            additional_constraints=task.constraints
        )

        self._active_delegations[task.id] = delegation

        # 3. Execute task
        result = await worker.execute_task(task)

        # 4. Verify result integrity
        await self._verify_task_result(task, worker, result)

        return result

    async def _verify_task_result(
        self,
        task: Task,
        worker: TrustedAgent,
        result: TaskResult
    ) -> None:
        """Verify worker's result matches constraints."""
        if task.output_constraints:
            for constraint in task.output_constraints:
                if not constraint.validate(result):
                    raise ConstraintViolationError(
                        f"Task {task.id} result violates constraint: {constraint}"
                    )
```

### TrustedWorkerAgent

```python
class TrustedWorkerAgent(TrustedAgent):
    """Worker agent optimized for task execution."""

    def __init__(
        self,
        name: str,
        specializations: List[str] = None,
        **kwargs
    ):
        super().__init__(name=name, **kwargs)
        self._specializations = specializations or []

    @property
    def specializations(self) -> List[str]:
        """Get agent's specializations for task matching."""
        return self._specializations

    async def execute_task(self, task: Task) -> TaskResult:
        """
        Execute a delegated task.

        Automatically verifies delegation is still valid.
        """
        # 1. Verify delegation is active
        if not self._current_delegation:
            raise TrustError("No active delegation for task execution")

        if self._current_delegation.task_id != task.id:
            raise TrustError(f"Delegation is for task {self._current_delegation.task_id}, not {task.id}")

        # 2. Verify delegation hasn't expired
        if self._current_delegation.expires_at:
            if datetime.utcnow() > self._current_delegation.expires_at:
                raise DelegationExpiredError(self._current_delegation.id)

        # 3. Execute task steps
        results = []
        for step in task.steps:
            async with self._audit_context(f"task_step:{step.name}") as audit:
                audit.context["task_id"] = task.id
                audit.context["step_index"] = step.index

                # Verify capability for this step
                await self._verify_action(step.required_capability, step.resource)

                # Execute step
                result = await self._execute_step(step)
                results.append(result)

        return TaskResult(task_id=task.id, step_results=results)
```

---

## Integration with Orchestration Patterns

### Trust-Aware Supervisor-Worker Pattern

```python
async def trust_aware_supervisor_worker(
    supervisor: TrustedSupervisorAgent,
    workers: List[TrustedWorkerAgent],
    tasks: List[Task]
) -> List[TaskResult]:
    """
    Execute supervisor-worker pattern with EATP.

    All delegations are tracked and verified.
    """
    results = []

    for task in tasks:
        # Find capable worker
        worker = await supervisor._delegation_strategy.select_worker(
            task=task,
            workers=workers,
            trust_ops=supervisor._trust_ops
        )

        if not worker:
            raise NoCapableWorkerError(task)

        # Delegate and execute
        result = await supervisor.assign_task(task, worker)
        results.append(result)

    return results
```

### Trust-Aware Router Pattern

```python
class TrustAwareRouter(TrustedAgent):
    """Router that routes based on trust and capability."""

    async def route(
        self,
        input: Any,
        agents: List[TrustedAgent]
    ) -> TrustedAgent:
        """Route to agent with required capability and trust."""
        required_capability = await self._determine_capability(input)

        # Filter by trust
        trusted_agents = [a for a in agents if a.is_trusted]

        # Filter by capability
        capable_agents = [
            a for a in trusted_agents
            if required_capability in a.capabilities
        ]

        if not capable_agents:
            raise NoCapableAgentError(required_capability)

        # Route using strategy
        return await self._select_agent(capable_agents, input)
```

---

## Backward Compatibility

### Untrusted Agent Behavior

```python
# Untrusted agents work exactly as before
agent = BaseAgent(name="legacy-agent")
await agent.run("do something")  # Works, no trust checks

# Trusted agents require establishment
trusted_agent = TrustedAgent(name="new-agent")
await trusted_agent.run("do something")  # Works, but no audit trail

# Fully trusted agent
trusted_agent = TrustedAgent(name="enterprise-agent")
await trusted_agent.establish_trust(
    authority_id="org-enterprise",
    capabilities=[...],
    constraints=[...]
)
await trusted_agent.run("do something")  # Full trust verification + audit
```

### Migration Path

```python
# Phase 1: Add TrustedAgent as option
# Existing code continues to work

# Phase 2: Wrap existing agents
class LegacyAgentWrapper(TrustedAgent):
    def __init__(self, legacy_agent: BaseAgent, **trust_kwargs):
        super().__init__(name=legacy_agent.name, **trust_kwargs)
        self._legacy = legacy_agent

    async def run(self, input: Any) -> Any:
        # Trust verification happens in super()
        return await self._legacy.run(input)

# Phase 3: Native TrustedAgent implementations
```

---

## A2A Integration

### Agent Card Generation

```python
class TrustedAgent(BaseAgent):
    # ... existing code ...

    def to_agent_card(self) -> AgentCard:
        """Generate A2A Agent Card with trust lineage."""
        return AgentCard(
            name=self.name,
            description=self.signature.description if self.signature else "",
            capabilities=[cap.capability for cap in self._trust_chain.capabilities] if self._trust_chain else [],
            skills=self._get_skills_from_tools(),
            trust_lineage=self._trust_chain.to_a2a_format() if self._trust_chain else None,
            endpoints={
                "task": f"/agents/{self.id}/task",
                "status": f"/agents/{self.id}/status"
            }
        )
```

### Trust Verification for A2A Requests

```python
class A2ARequestHandler:
    """Handle incoming A2A requests with trust verification."""

    async def handle_task_request(
        self,
        request: A2ATaskRequest,
        target_agent: TrustedAgent
    ) -> A2ATaskResponse:
        """Handle task request from external agent."""

        # 1. Verify caller's trust lineage
        caller_chain = await self._fetch_caller_trust(request.caller_agent_card_url)
        if not caller_chain or not caller_chain.verify().valid:
            return A2ATaskResponse(
                status="error",
                error={"code": "TRUST_VERIFICATION_FAILED"}
            )

        # 2. Create delegation for this request
        delegation = await self.trust_ops.delegate(
            delegator_id=request.caller_id,
            delegatee_id=target_agent.id,
            task_id=request.task_id,
            capabilities=request.required_capabilities,
            additional_constraints=request.constraints
        )

        # 3. Execute task
        await target_agent.receive_delegation(delegation)
        result = await target_agent.run(request.input)

        return A2ATaskResponse(
            status="success",
            result=result,
            audit_anchor_id=target_agent._trust_chain.audit_anchors[-1].id
        )
```

---

## Testing Strategy

### Unit Tests

```python
class TestTrustedAgent:
    async def test_establish_trust(self):
        """Test trust establishment."""
        agent = TrustedAgent(name="test-agent")
        chain = await agent.establish_trust(
            authority_id="test-authority",
            capabilities=[CapabilityRequest(capability="test_cap", ...)],
            constraints=["test_constraint"]
        )
        assert agent.is_trusted
        assert "test_cap" in agent.capabilities

    async def test_verification_before_action(self):
        """Test that actions are verified."""
        agent = TrustedAgent(name="test-agent")
        await agent.establish_trust(...)

        # Should succeed
        await agent.call_tool("allowed_tool")

        # Should fail
        with pytest.raises(VerificationFailedError):
            await agent.call_tool("disallowed_tool")

    async def test_delegation_tightens_constraints(self):
        """Test constraint tightening in delegation."""
        supervisor = TrustedSupervisorAgent(name="supervisor")
        worker = TrustedWorkerAgent(name="worker")

        # Setup trust
        await supervisor.establish_trust(...)
        await worker.establish_trust(...)

        # Delegate with extra constraints
        await supervisor.delegate_to(
            worker=worker,
            task_id="test-task",
            capabilities=["analyze"],
            additional_constraints=["read_only"]
        )

        assert "read_only" in worker.effective_constraints
```

### Integration Tests

```python
class TestTrustIntegration:
    async def test_full_supervisor_worker_flow(self):
        """Test complete trust-aware workflow."""
        # Setup
        authority = await create_test_authority()
        supervisor = TrustedSupervisorAgent(name="supervisor")
        worker = TrustedWorkerAgent(name="worker")

        # Establish trust
        await supervisor.establish_trust(authority_id=authority.id, ...)
        await worker.establish_trust(authority_id=authority.id, ...)

        # Execute task
        task = Task(id="test-task", ...)
        result = await supervisor.assign_task(task, worker)

        # Verify audit trail
        anchors = await get_audit_anchors(task_id="test-task")
        assert len(anchors) >= 2  # delegation + execution
```

---

## Next Steps

1. **Document 05**: A2A HTTP Service Implementation
2. **Document 06**: Orchestration Runtime Integration
3. Implement TrustedAgent in `kaizen.trust.agent`
4. Create comprehensive test suite
