# Skipped Tests Implementation Plan

**Document Version**: 1.0
**Created**: 2025-12-29
**Status**: Analysis Complete - Ready for Implementation

## Executive Summary

This document provides a comprehensive implementation plan for addressing skipped tests in Kailash Kaizen. The analysis identifies 6 distinct categories of work, ordered by dependency and complexity.

**Total Scope**:
- 5 test files with skipped tests
- 6 implementation categories
- Estimated effort: 4-6 weeks (1-2 developers)

**Complexity Distribution**:
| Complexity | Categories | Estimated Effort |
|------------|-----------|------------------|
| Simple | 2 | 3-5 days |
| Moderate | 2 | 1-2 weeks |
| Complex | 2 | 2-3 weeks |

---

## Dependency Graph

```
                    +-----------------------+
                    | Category 1            |
                    | Tool Registry (10     |
                    | agents)               |
                    | SIMPLE                |
                    +----------+------------+
                               |
                               v
              +----------------+----------------+
              |                                 |
              v                                 v
+-------------+--------------+   +--------------+-------------+
| Category 2                 |   | Category 3                 |
| Built-in Tools Modules     |   | MCP Integration Refactor   |
| (HTTP/File Security)       |   | (kaizen.mcp -> kailash.mcp)|
| MODERATE                   |   | MODERATE                   |
+-------------+--------------+   +--------------+-------------+
              |                                 |
              +----------------+----------------+
                               |
                               v
                    +----------+------------+
                    | Category 4            |
                    | OrchestrationRuntime  |
                    | Features              |
                    | COMPLEX               |
                    +----------+------------+
                               |
                               v
                    +----------+------------+
                    | Category 5            |
                    | Stub Implementations  |
                    | (from audit)          |
                    | COMPLEX               |
                    +-----------------------+
```

---

## Category 1: Tool Registry Integration (TODO-165)

### Overview
Add `tool_registry` and `mcp_servers` parameters to 10 agents for tool discovery.

**File**: `tests/unit/agents/test_tool_registry_integration_10_agents.py`
**Complexity**: Simple
**Estimated Effort**: 2-3 days
**Specialist Agent**: kaizen-specialist

### Agents Requiring Changes

#### Specialized Agents (4)
| Agent | File Location | Current `__init__` Params | Change Required |
|-------|---------------|---------------------------|-----------------|
| ResilientAgent | `src/kaizen/agents/specialized/resilient.py` | Has `mcp_servers` | Add `tool_registry` |
| MemoryAgent | `src/kaizen/agents/specialized/memory_agent.py` | Needs check | Add both |
| BatchProcessingAgent | `src/kaizen/agents/specialized/batch_processing.py` | Needs check | Add both |
| HumanApprovalAgent | `src/kaizen/agents/specialized/human_approval.py` | Needs check | Add both |

#### Coordination Agents (6)
| Agent | File Location | Change Required |
|-------|---------------|-----------------|
| ProponentAgent | `src/kaizen/orchestration/patterns/debate.py` | Add both params |
| OpponentAgent | `src/kaizen/orchestration/patterns/debate.py` | Add both params |
| JudgeAgent | `src/kaizen/orchestration/patterns/debate.py` | Add both params |
| ProposerAgent | `src/kaizen/orchestration/patterns/consensus.py` | Add both params |
| VoterAgent | `src/kaizen/orchestration/patterns/consensus.py` | Add both params |
| AggregatorAgent | `src/kaizen/orchestration/patterns/consensus.py` | Add both params |

### Implementation Pattern

BaseAgent already supports `mcp_servers` (line 163 in base_agent.py). The `tool_registry` parameter needs to be:
1. Added to BaseAgentConfig or passed through to BaseAgent
2. Used to inject tool documentation into system prompts

```python
# Pattern for each agent:
def __init__(
    self,
    # ... existing params ...
    tool_registry: Optional["ToolRegistry"] = None,
    mcp_servers: Optional[List[Dict[str, Any]]] = None,
    **kwargs,
):
    super().__init__(
        # ... existing params ...
        mcp_servers=mcp_servers,
        **kwargs,
    )
    self.tool_registry = tool_registry

    # Inject tool documentation into prompt if registry provided
    if tool_registry:
        self._inject_tool_documentation()
```

### Test Requirements Verified
1. Agents accept `tool_registry` parameter - constructor signature change
2. Tool documentation appears in system prompts - override `_generate_system_prompt()`
3. Backward compatibility - default `tool_registry=None`
4. MCP servers parameter accepted - already in BaseAgent

### Risk Assessment
- **Risk Level**: Low
- **Failure Points**: Parameter passing to BaseAgent
- **Mitigation**: Follow ResilientAgent pattern which already has `mcp_servers`

---

## Category 2: Built-in Tools Modules

### Overview
Implement `kaizen.tools.builtin.api` and `kaizen.tools.builtin.file` modules with security validations.

**Files**:
- `tests/unit/tools/test_http_security.py` (20 tests)
- `tests/unit/tools/test_file_security.py` (25 tests)

**Complexity**: Moderate
**Estimated Effort**: 5-7 days
**Specialist Agent**: tdd-implementer, testing-specialist

### Module Structure

```
src/kaizen/tools/
    __init__.py (exists)
    types.py (exists)
    builtin/
        __init__.py (NEW)
        api.py (NEW) - HTTP security validation
        file.py (NEW) - File path security validation
```

### kaizen.tools.builtin.api

**Functions to Implement**:

| Function | Purpose | Test Count |
|----------|---------|------------|
| `validate_url(url: str) -> Tuple[bool, Optional[str]]` | URL scheme validation (http/https only) | 8 |
| `validate_url(url: str) -> Tuple[bool, Optional[str]]` | SSRF protection (block private IPs) | 8 |
| `validate_timeout(timeout: int) -> Tuple[bool, Optional[str]]` | Timeout validation (1-300 seconds) | 6 |

**Security Requirements (from tests)**:
1. **URL Scheme Validation**:
   - Accept: `https://`, `http://`
   - Reject: `ftp://`, `file://`, `javascript:`, `data://`, no scheme, empty

2. **SSRF Protection**:
   - Block: `localhost`, `127.0.0.1`, `10.x.x.x`, `192.168.x.x`, `169.254.x.x`, `[::1]`
   - Allow: Public domains and public IPs

3. **Timeout Validation**:
   - Range: 1-300 seconds
   - Reject: 0, negative, >300

### kaizen.tools.builtin.file

**Functions to Implement**:

| Function | Purpose | Test Count |
|----------|---------|------------|
| `validate_safe_path(path: str, allowed_base: Optional[str] = None) -> Tuple[bool, Optional[str]]` | Path security validation | 25 |

**Security Requirements (from tests)**:
1. **Path Traversal Detection**:
   - Block: `../`, nested `../../`, Windows-style `..\`, encoded paths
   - Allow: Single `.` (current directory)

2. **System Path Blocking**:
   - Block: `/etc`, `/sys`, `/proc`, `/dev`, `/boot`, `/root`
   - Allow: `/tmp`, home directory, relative paths

3. **Sandboxing**:
   - Optional `allowed_base` parameter for restricting to specific directory
   - Block paths outside sandbox

### Implementation Approach

```python
# kaizen/tools/builtin/api.py
import ipaddress
from urllib.parse import urlparse
from typing import Tuple, Optional

def validate_url(url: str) -> Tuple[bool, Optional[str]]:
    """Validate URL for scheme and SSRF protection."""
    if not url:
        return False, "URL cannot be empty"

    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Invalid URL format"

    # Scheme validation
    if parsed.scheme not in ('http', 'https'):
        return False, "URL scheme must be http or https"

    # SSRF protection
    hostname = parsed.hostname
    if hostname in ('localhost', '127.0.0.1', '::1'):
        return False, "Localhost URLs are not allowed (SSRF protection)"

    # Check for private IP ranges
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            return False, "Private/internal IP addresses are not allowed (SSRF protection)"
    except ValueError:
        pass  # Not an IP address, that's fine

    return True, None

def validate_timeout(timeout: int) -> Tuple[bool, Optional[str]]:
    """Validate timeout is within acceptable range."""
    if timeout < 1:
        return False, "Timeout must be at least 1 second"
    if timeout > 300:
        return False, f"Timeout must not exceed 300 seconds"
    return True, None
```

### Risk Assessment
- **Risk Level**: Low-Medium
- **Failure Points**: Edge cases in IP validation, path normalization
- **Mitigation**: Use Python standard library (ipaddress, pathlib) for robust handling

---

## Category 3: MCP Integration Refactoring

### Overview
Refactor tests from deprecated `kaizen.mcp` to `kailash.mcp_server` module.

**Files**:
- `tests/unit/examples/test_agent_as_client.py`
- `tests/unit/examples/test_agent_as_server.py`

**Complexity**: Moderate
**Estimated Effort**: 5-7 days
**Specialist Agent**: mcp-specialist

### Migration Mapping

| Old (Deprecated) | New (kailash.mcp_server) |
|------------------|--------------------------|
| `kaizen.mcp.MCPConnection` | `kailash.mcp_server.MCPClient` |
| `kaizen.mcp.MCPRegistry` | N/A (use MCPServer registry) |
| `agent.connections` dict | `BaseAgent.setup_mcp_client()` |
| `connection.call_tool()` | `BaseAgent.call_mcp_tool()` |
| `agent.disconnect_all()` | Client lifecycle management |

### Test Classes Affected

#### test_agent_as_client.py
| Class | Skip Reason | Refactor Approach |
|-------|-------------|-------------------|
| `TestMCPClientAgentConnections` | Uses MCPConnection | Use MCPClient via BaseAgent |
| `TestMCPClientToolInvocation` | Uses MCPConnection | Use `call_mcp_tool()` |
| `TestMCPClientWorkflows` | Full kaizen.mcp | Rebuild with kailash.mcp_server |
| `TestMCPClientPerformance` | Uses MCPConnection | Use MCPClient |

#### test_agent_as_server.py
| Class | Skip Reason | Refactor Approach |
|-------|-------------|-------------------|
| `TestMCPServerLifecycle` | Uses MCPRegistry | Use MCPServer from kailash |
| `TestMCPToolInvocation` | Uses deprecated patterns | Use @server.tool() decorator |
| `TestMCPServerWorkflows` | Full kaizen.mcp | Rebuild with kailash.mcp_server |
| `TestMCPServerPerformance` | Uses deprecated patterns | Use MCPServer |

### Implementation Approach

1. **Update Example Files First**:
   - `examples/5-mcp-integration/agent-as-client/workflow.py`
   - `examples/5-mcp-integration/agent-as-server/workflow.py`

2. **Refactor Tests to Match Examples**:
   ```python
   # Old pattern (deprecated):
   from kaizen.mcp import MCPConnection
   connection = MCPConnection(name="server", url="http://localhost:8080")
   connection.connect()
   result = connection.call_tool("tool_name", {"arg": "value"})

   # New pattern:
   from kailash.mcp_server import MCPClient
   async with MCPClient("http://localhost:8080") as client:
       result = await client.call_tool("tool_name", {"arg": "value"})
   ```

3. **BaseAgent Helpers**:
   ```python
   # Use BaseAgent's built-in MCP support:
   agent = BaseAgent(config=config, mcp_servers=[...])
   await agent.setup_mcp_client()
   result = await agent.call_mcp_tool("tool_name", {"arg": "value"})
   ```

### Risk Assessment
- **Risk Level**: Medium
- **Failure Points**: Protocol differences, async context handling
- **Mitigation**: Follow migration guide in MCP_INTEGRATION_TEST_MIGRATION_STATUS.md

---

## Category 4: OrchestrationRuntime Features

### Overview
Implement missing OrchestrationRuntime features identified by skipped tests.

**File**: `tests/unit/orchestration/test_orchestration_runtime_unit.py`
**Complexity**: Complex
**Estimated Effort**: 1.5-2 weeks
**Specialist Agent**: kaizen-specialist, pattern-expert

### Features by Priority

#### Priority 1: Core Functionality (Must Have)

| Feature | Skip Reason | Implementation Location |
|---------|-------------|------------------------|
| Semantic Routing | "needs actual implementation review" | `_route_semantic()` method |
| Routing Busy Agents | "logic needs implementation review" | `_route_task()` filtering |
| Concurrent Agent Limit | "needs implementation review" | Semaphore enforcement |

**Semantic Routing Enhancement**:
```python
async def _route_semantic(self, task: str, agents: List[tuple]) -> Optional[BaseAgent]:
    """Route using A2A capability matching with improved similarity."""
    # Current: Simple word overlap (Jaccard similarity)
    # Enhanced: Use embedding similarity or capability matching

    # Option 1: Improve _simple_text_similarity with TF-IDF
    # Option 2: Add semantic embedding comparison
    # Option 3: Use A2A capability.matches_requirement() properly
```

#### Priority 2: Error Handling (Should Have)

| Feature | Skip Reason | Implementation Location |
|---------|-------------|------------------------|
| RetryPolicy parameters | "differs from test expectations" | `RetryPolicy` dataclass |
| ErrorHandlingMode.CIRCUIT_BREAKER | "not implemented" | `_execute_with_retry()` |
| Circuit breaker recovery | "differs from expectations" | `_circuit_breaker_state` |

**RetryPolicy Fix**:
```python
# Current (line 140-148):
@dataclass
class RetryPolicy:
    max_retries: int = 3
    initial_delay: float = 1.0
    backoff: str = "exponential"
    max_delay: float = 30.0
    exceptions: tuple = (Exception,)

# Test expects (line 447-451):
RetryPolicy(
    max_retries=3,
    initial_delay=0.1,
    backoff_factor=1.5,  # Different parameter name
)

# Fix: Rename `backoff` to `backoff_factor` or add alias
```

#### Priority 3: Monitoring (Nice to Have)

| Feature | Skip Reason | Implementation Location |
|---------|-------------|------------------------|
| Workflow tracking | "implementation needs review" | `_execution_history` |
| Workflow metrics | "implementation needs review" | `get_metrics()` |
| Workflow history | "implementation needs review" | `get_execution_history()` |

#### Priority 4: Lifecycle (Nice to Have)

| Feature | Skip Reason | Implementation Location |
|---------|-------------|------------------------|
| Graceful shutdown | "signature differs" | `shutdown()` method |
| Immediate shutdown | "signature differs" | `shutdown()` method |
| Resource cleanup | "signature differs" | `shutdown()` method |

**Shutdown Signature Fix**:
```python
# Current (line 1111):
async def shutdown(self, mode: str = "graceful", timeout: float = 30.0):

# Test expects (line 653, 688):
await runtime.shutdown(graceful=True, timeout=2.0)
await runtime.shutdown(graceful=False)

# Fix: Change signature to:
async def shutdown(self, graceful: bool = True, timeout: float = 30.0):
```

### Implementation Order

1. **Week 1**:
   - Fix shutdown signature (breaking API change - coordinate with users)
   - Fix RetryPolicy parameter names
   - Implement circuit breaker states properly

2. **Week 2**:
   - Enhance semantic routing
   - Add busy agent exclusion
   - Implement concurrent limit enforcement
   - Add workflow tracking

### Risk Assessment
- **Risk Level**: Medium-High
- **Failure Points**: Breaking API changes (shutdown, RetryPolicy)
- **Mitigation**:
  - Add deprecation warnings for old signatures
  - Use parameter aliasing for backward compatibility
  - Document changes in CHANGELOG

---

## Category 5: Stub Implementations (from Audit)

### Overview
Replace stub/placeholder implementations with functional code.

**Complexity**: Complex
**Estimated Effort**: 2-3 weeks
**Specialist Agents**: kaizen-specialist, dataflow-specialist

### Stubs Identified

#### Priority 1: Core Agent Functionality

| Stub | Location | Current Behavior | Required Implementation |
|------|----------|------------------|------------------------|
| BaseAgent mixins (7) | `src/kaizen/core/base_agent.py` | `self._mixins_applied.append()` only | Implement actual mixin behavior |
| Token counting | Claude Code agent | Uses cycle count | Use tiktoken or provider API |
| Framework init | Various | Placeholders | Initialize subsystems |

**Mixin Implementation**:
```python
# Current (lines 377-403):
def _apply_logging_mixin(self):
    """Apply logging mixin (placeholder until Phase 3)."""
    self._mixins_applied.append("LoggingMixin")

# Required:
def _apply_logging_mixin(self):
    """Apply logging mixin with actual logging behavior."""
    from kaizen.core.mixins.logging import LoggingMixin
    LoggingMixin.apply(self)
    self._mixins_applied.append("LoggingMixin")
```

#### Priority 2: Document Extraction

| Stub | Location | Current Behavior | Required Implementation |
|------|----------|------------------|------------------------|
| OpenAI vision | Document extraction | Returns mock data | Call OpenAI API |
| Ollama vision | Document extraction | Returns mock data | Call Ollama API |
| Landing AI | Document extraction | Returns mock data | Call Landing AI API |

#### Priority 3: State Management

| Stub | Location | Current Behavior | Required Implementation |
|------|----------|------------------|------------------------|
| Approval history | Autonomous agent | Returns empty | Track approvals |
| Tool usage | Autonomous agent | Returns empty | Track tool calls |
| Workflow state | Autonomous agent | Returns empty | Track state transitions |

#### Priority 4: Persistence

| Stub | Location | Current Behavior | Required Implementation |
|------|----------|------------------|------------------------|
| Governance approval | Governance service | Not persisted | Store in DataFlow |
| MCP session | BaseAgent | Not implemented | Track MCP connections |

### Implementation Approach

1. **Identify All Stubs**:
   ```bash
   grep -r "placeholder" src/kaizen/ --include="*.py"
   grep -r "TODO" src/kaizen/ --include="*.py"
   grep -r "NotImplementedError" src/kaizen/ --include="*.py"
   ```

2. **Prioritize by Usage**:
   - High: Stubs in frequently-used code paths
   - Medium: Stubs in optional features
   - Low: Stubs in edge case handling

3. **Test Before Implementing**:
   - Write integration tests for each stub
   - Follow TDD approach

### Risk Assessment
- **Risk Level**: Medium
- **Failure Points**: Breaking existing behavior, provider API changes
- **Mitigation**:
  - Feature flags for new implementations
  - Fallback to stub behavior on errors

---

## Category 6: Test Infrastructure

### Overview
Ensure test infrastructure supports all test categories.

**Complexity**: Simple
**Estimated Effort**: 2-3 days
**Specialist Agent**: testing-specialist

### Requirements

1. **MCP Test Server**:
   - Needed for Categories 3 and 4
   - Should provide test tools for integration testing

2. **Mock Tool Registry**:
   - Needed for Category 1
   - Already exists in test file (MockToolRegistry class)

3. **Test Fixtures**:
   - Shared fixtures for agent creation
   - Shared fixtures for runtime configuration

---

## Implementation Schedule

### Phase 1: Foundation (Week 1-2)

| Category | Task | Owner | Status |
|----------|------|-------|--------|
| 1 | Tool Registry Integration | kaizen-specialist | Pending |
| 6 | Test Infrastructure | testing-specialist | Pending |
| 2 | Built-in Tools Modules | tdd-implementer | Pending |

### Phase 2: Core Features (Week 2-3)

| Category | Task | Owner | Status |
|----------|------|-------|--------|
| 3 | MCP Integration Refactor | mcp-specialist | Pending |
| 4 (P1) | OrchestrationRuntime Core | kaizen-specialist | Pending |

### Phase 3: Advanced Features (Week 4-5)

| Category | Task | Owner | Status |
|----------|------|-------|--------|
| 4 (P2-4) | OrchestrationRuntime Full | kaizen-specialist | Pending |
| 5 (P1) | Critical Stub Implementations | kaizen-specialist | Pending |

### Phase 4: Polish (Week 5-6)

| Category | Task | Owner | Status |
|----------|------|-------|--------|
| 5 (P2-4) | Remaining Stubs | Various | Pending |
| All | Integration Testing | testing-specialist | Pending |
| All | Documentation Updates | documentation-validator | Pending |

---

## Success Criteria

### Per Category

1. **Category 1**: All 10 agents accept tool_registry, tests pass
2. **Category 2**: HTTP/File security modules exist, 45 tests pass
3. **Category 3**: MCP tests use kailash.mcp_server, all tests pass
4. **Category 4**: OrchestrationRuntime tests pass (25 tests)
5. **Category 5**: No placeholder returns in critical paths
6. **Category 6**: Test infrastructure supports all categories

### Overall

- **Test Pass Rate**: 100% of previously skipped tests passing
- **No Regressions**: Existing passing tests still pass
- **Documentation**: All new features documented
- **Coverage**: Maintain or improve test coverage percentage

---

## Appendix A: Test File Locations

```
tests/
  unit/
    agents/
      test_tool_registry_integration_10_agents.py  # Category 1
    tools/
      test_http_security.py                        # Category 2
      test_file_security.py                        # Category 2
    examples/
      test_agent_as_client.py                      # Category 3
      test_agent_as_server.py                      # Category 3
    orchestration/
      test_orchestration_runtime_unit.py           # Category 4
```

## Appendix B: Source File Locations

```
src/kaizen/
  agents/
    coordination/
      __init__.py           # Re-exports from orchestration/patterns
    specialized/
      resilient.py          # Category 1
      memory_agent.py       # Category 1
      batch_processing.py   # Category 1
      human_approval.py     # Category 1
  core/
    base_agent.py           # Categories 1, 5
    config.py               # Category 1
  orchestration/
    runtime.py              # Category 4
    patterns/
      debate.py             # Category 1
      consensus.py          # Category 1
  tools/
    __init__.py             # Exists
    types.py                # Exists
    builtin/                # Category 2 (NEW)
      __init__.py
      api.py
      file.py
```

## Appendix C: Command Reference

```bash
# Run specific test category
pytest tests/unit/agents/test_tool_registry_integration_10_agents.py -v
pytest tests/unit/tools/ -v
pytest tests/unit/examples/ -v
pytest tests/unit/orchestration/test_orchestration_runtime_unit.py -v

# Run with coverage
pytest tests/unit/ --cov=src/kaizen --cov-report=html

# Find skipped tests
pytest tests/ --collect-only -q | grep "skipped"
```
