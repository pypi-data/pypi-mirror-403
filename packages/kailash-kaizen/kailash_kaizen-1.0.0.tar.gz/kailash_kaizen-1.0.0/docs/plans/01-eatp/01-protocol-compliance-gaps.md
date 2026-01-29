# EATP Implementation Plan: Protocol Compliance Gaps

## Document Control
- **Version**: 1.0
- **Date**: 2025-12-15
- **Status**: Analysis Complete
- **Author**: Kaizen Framework Team

---

## Overview

Before implementing EATP, we must ensure full compliance with:
1. **A2A (Agent-to-Agent Protocol)** - Google's agent communication standard
2. **MCP (Model Context Protocol)** - Anthropic's tool access standard

This document details the gaps between current Kaizen implementation and these standards.

---

## A2A Protocol Compliance

### Reference Specification
- **Source**: Google A2A Protocol Specification
- **Version**: Current as of December 2025
- **Key Document**: Agent Card Schema, JSON-RPC 2.0 Requirements

### Current Kaizen A2A Status: IN-PROCESS ONLY

Per ADR-067, Kaizen deliberately implements A2A as **in-process coordination** rather than HTTP-based discovery. This was a conscious architectural decision for:
- Performance in single-process deployments
- Simpler orchestration patterns
- Reduced network overhead

However, EATP requires **distributed agent trust verification**, which necessitates HTTP-based A2A.

### Gap Analysis

| Requirement | Spec Reference | Current Status | Gap |
|-------------|---------------|----------------|-----|
| Agent Cards at `/.well-known/agent.json` | A2A Core | Not implemented | **CRITICAL** |
| JSON-RPC 2.0 message format | A2A Core | In-process only | **CRITICAL** |
| HTTP(S) transport | A2A Transport | Not implemented | **CRITICAL** |
| Authentication via OpenAPI schemes | A2A Security | Not implemented | **HIGH** |
| Capability negotiation | A2A Handshake | Partial (AgentRegistry) | **MEDIUM** |
| Task lifecycle (pending/working/completed) | A2A Tasks | In-process only | **MEDIUM** |

### Required Changes for A2A Compliance

#### 1. Agent Card HTTP Endpoint
```python
# Required: HTTP service exposing Agent Cards
@app.get("/.well-known/agent.json")
async def get_agent_card():
    return {
        "name": agent.name,
        "description": agent.description,
        "capabilities": agent.capabilities,
        "skills": agent.skills,
        "trust_lineage": agent.trust_lineage,  # EATP extension
        "endpoints": {
            "task": "/a2a/task",
            "status": "/a2a/status"
        }
    }
```

#### 2. JSON-RPC 2.0 Message Handler
```python
# Required: JSON-RPC 2.0 compliant message handling
@app.post("/a2a/task")
async def handle_task(request: JsonRpcRequest):
    if request.method == "task.create":
        # Create and execute task
        pass
    elif request.method == "task.status":
        # Return task status
        pass
```

#### 3. Authentication Layer
```python
# Required: OpenAPI security scheme support
class A2AAuthenticator:
    async def authenticate(self, request: Request) -> AgentIdentity:
        # Support OAuth2, API Key, JWT
        pass
```

### EATP Extension to A2A

EATP adds a `trust_lineage` field to Agent Cards:

```json
{
  "name": "DataAnalystAgent",
  "trust_lineage": {
    "genesis": {
      "id": "gen-001",
      "authority_id": "auth-enterprise-001",
      "created_at": "2025-12-15T10:00:00Z",
      "signature": "..."
    },
    "capabilities": [
      {
        "capability": "analyze_financial_data",
        "constraints": ["read_only", "no_pii_export"],
        "attestation_signature": "..."
      }
    ],
    "delegation_chain": [
      {
        "from_agent": "SupervisorAgent",
        "constraint_subset": ["read_only"]
      }
    ]
  }
}
```

---

## MCP Protocol Compliance

### Reference Specification
- **Source**: Anthropic Model Context Protocol
- **Version**: Current as of December 2025
- **Key Document**: MCP Specification, Transport Requirements

### Current Kaizen MCP Status: PARTIALLY COMPLIANT

Kaizen's MCP server implementation provides functional tool access but lacks some advanced features.

### Gap Analysis

| Requirement | Spec Reference | Current Status | Gap |
|-------------|---------------|----------------|-----|
| JSON-RPC 2.0 transport | MCP Core | Implemented | None |
| Tool discovery | MCP Tools | Implemented (12 tools) | None |
| Tool execution | MCP Tools | Implemented | None |
| Stdio transport | MCP Transport | Implemented | None |
| SSE transport | MCP Transport | Not implemented | **LOW** |
| Resource subscriptions | MCP Resources | Not implemented | **MEDIUM** |
| Prompts | MCP Prompts | Not implemented | **LOW** |
| Sampling | MCP Sampling | Not implemented | **LOW** |
| User consent for data/tools | MCP Security | Partial | **MEDIUM** |
| Capability negotiation | MCP Handshake | Implemented | None |

### Current MCP Implementation

```python
# From kailash/mcp_server/
# Current: 12 tools implemented
- build_workflow
- add_node
- connect_nodes
- execute_workflow
- list_node_types
- get_node_info
- validate_workflow
- get_workflow_status
- save_workflow
- load_workflow
- get_execution_result
- cancel_execution
```

### Required Changes for EATP Integration

#### 1. Trust Verification Before Tool Invocation
```python
# Required: Verify trust before executing MCP tools
class TrustAwareMCPServer:
    async def handle_tool_call(self, tool_name: str, args: dict, caller: AgentIdentity):
        # EATP: Verify caller has trust to invoke this tool
        trust_result = await self.verify_trust(caller, tool_name)
        if not trust_result.is_valid:
            return MCPError(code=-32001, message="Trust verification failed")

        # Execute tool
        return await self.execute_tool(tool_name, args)
```

#### 2. Audit Anchors for Tool Calls
```python
# Required: Create audit trail for all MCP tool invocations
class AuditedMCPServer:
    async def handle_tool_call(self, tool_name: str, args: dict, caller: AgentIdentity):
        audit_anchor = AuditAnchor(
            operation="mcp_tool_call",
            agent_id=caller.id,
            action=f"tool:{tool_name}",
            timestamp=datetime.utcnow(),
            trust_chain_hash=caller.trust_lineage.hash()
        )
        await self.audit_store.record(audit_anchor)

        return await self.execute_tool(tool_name, args)
```

#### 3. Resource Subscriptions (Optional Enhancement)
```python
# Nice-to-have: Real-time resource updates
class MCPResourceServer:
    async def subscribe(self, resource_uri: str, callback: Callable):
        # Allow clients to subscribe to resource changes
        pass
```

---

## Compliance Roadmap

### Phase 1: A2A HTTP Service (Weeks 1-2)
1. Create FastAPI-based A2A HTTP service
2. Implement Agent Card endpoint at `/.well-known/agent.json`
3. Implement JSON-RPC 2.0 task endpoints
4. Add OAuth2/API Key authentication

### Phase 2: MCP Trust Integration (Weeks 3-4)
1. Add trust verification layer to MCP server
2. Implement audit anchors for tool calls
3. Enhance user consent mechanisms

### Phase 3: Protocol Testing (Week 5)
1. Test A2A interoperability with external agents
2. Test MCP compliance with Claude Desktop
3. Validate EATP extensions work correctly

---

## Architectural Decision

### Maintaining Dual Mode

Kaizen will support **both** modes:

1. **In-Process Mode** (existing): For single-process, high-performance scenarios
2. **HTTP Mode** (new): For distributed, EATP-enabled scenarios

```python
# Configuration-driven mode selection
class AgentRegistry:
    def __init__(self, mode: Literal["in_process", "http"] = "in_process"):
        if mode == "http":
            self.discovery = HTTPAgentDiscovery()
            self.communication = A2AHttpClient()
        else:
            self.discovery = InProcessAgentDiscovery()
            self.communication = InProcessCommunication()
```

This preserves backward compatibility while enabling EATP features.

---

## Testing Requirements

### A2A Compliance Tests
```python
class TestA2ACompliance:
    async def test_agent_card_endpoint(self):
        """Agent Card must be available at /.well-known/agent.json"""

    async def test_jsonrpc_format(self):
        """All messages must be valid JSON-RPC 2.0"""

    async def test_task_lifecycle(self):
        """Tasks must follow pending -> working -> completed lifecycle"""
```

### MCP Compliance Tests
```python
class TestMCPCompliance:
    async def test_tool_discovery(self):
        """Tools must be discoverable via tools/list"""

    async def test_tool_execution(self):
        """Tool calls must return structured results"""

    async def test_trust_verification(self):
        """Trust must be verified before tool execution"""
```

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Breaking existing in-process workflows | Medium | High | Maintain dual mode, extensive testing |
| A2A spec changes | Low | Medium | Abstract A2A layer, monitor spec updates |
| MCP spec changes | Low | Medium | Abstract MCP layer, monitor spec updates |
| Performance degradation in HTTP mode | Medium | Medium | Caching, connection pooling |

---

## Next Steps

1. **Document 02**: Trust Lineage Chain Design
2. **Document 05**: A2A HTTP Service Implementation
3. Create A2A compliance test suite
4. Create MCP trust integration tests
