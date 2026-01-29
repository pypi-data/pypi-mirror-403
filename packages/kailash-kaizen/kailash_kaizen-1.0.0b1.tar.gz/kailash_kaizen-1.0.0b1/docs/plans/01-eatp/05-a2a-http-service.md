# EATP Implementation Plan: A2A HTTP Service

## Document Control
- **Version**: 1.0
- **Date**: 2025-12-15
- **Status**: Planning
- **Author**: Kaizen Framework Team

---

## Overview

This document describes the implementation of an HTTP service layer for A2A (Agent-to-Agent) protocol compliance. This enables Kaizen agents to be discovered and communicated with by external agents following Google's A2A specification.

---

## A2A Protocol Requirements

### Core Requirements (Google A2A Spec)

| Requirement | Description | Implementation |
|-------------|-------------|----------------|
| Agent Card | JSON at `/.well-known/agent.json` | FastAPI endpoint |
| JSON-RPC 2.0 | Message format | Pydantic models |
| Task Lifecycle | pending → working → completed | State machine |
| Authentication | OAuth2, API Key, JWT | FastAPI security |
| HTTPS | Secure transport | TLS configuration |

### EATP Extensions

| Extension | Description | Purpose |
|-----------|-------------|---------|
| `trust_lineage` | Trust chain in Agent Card | Distributed trust |
| `trust_verify` | JSON-RPC method | Cross-agent verification |
| `audit_anchor` | Audit chain in responses | Accountability |

---

## Architecture

### Service Layer Structure

```
kaizen/
├── a2a/
│   ├── __init__.py
│   ├── service.py           # FastAPI application
│   ├── agent_card.py        # Agent Card generation
│   ├── jsonrpc.py           # JSON-RPC 2.0 handler
│   ├── auth.py              # Authentication
│   ├── tasks.py             # Task lifecycle
│   └── trust_extension.py   # EATP trust extensions
```

### Component Interaction

```
External Agent                    Kaizen A2A Service
      │                                  │
      │  GET /.well-known/agent.json     │
      │─────────────────────────────────►│
      │                                  │
      │  ◄─ Agent Card (with trust)      │
      │◄─────────────────────────────────│
      │                                  │
      │  POST /a2a (task.create)         │
      │─────────────────────────────────►│
      │          │                       │
      │          │  Verify caller trust  │
      │          │                       │
      │  ◄─ Task created (pending)       │
      │◄─────────────────────────────────│
      │                                  │
      │  GET /a2a/tasks/{id} (polling)   │
      │─────────────────────────────────►│
      │                                  │
      │  ◄─ Task status (working)        │
      │◄─────────────────────────────────│
      │                                  │
      │  ◄─ Task result (completed)      │
      │◄─────────────────────────────────│
```

---

## Implementation

### 1. FastAPI Application

```python
# kaizen/a2a/service.py
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from kaizen.a2a.agent_card import AgentCardGenerator
from kaizen.a2a.jsonrpc import JsonRpcHandler
from kaizen.a2a.auth import A2AAuthenticator
from kaizen.a2a.tasks import TaskManager
from kaizen.trust.operations import TrustOperations

class A2AService:
    """HTTP service for A2A protocol compliance."""

    def __init__(
        self,
        agent: TrustedAgent,
        trust_ops: TrustOperations,
        host: str = "0.0.0.0",
        port: int = 8080,
        enable_cors: bool = True
    ):
        self.agent = agent
        self.trust_ops = trust_ops
        self.app = FastAPI(title=f"{agent.name} A2A Service")
        self.task_manager = TaskManager()
        self.auth = A2AAuthenticator(trust_ops)
        self.jsonrpc = JsonRpcHandler(agent, self.task_manager, trust_ops)

        self._setup_routes()
        self._setup_middleware()

        if enable_cors:
            self._setup_cors()

    def _setup_routes(self):
        """Register A2A protocol routes."""

        # Agent Card endpoint (A2A Core)
        @self.app.get("/.well-known/agent.json")
        async def get_agent_card():
            return AgentCardGenerator.generate(
                agent=self.agent,
                base_url=self._get_base_url()
            )

        # JSON-RPC endpoint (A2A Core)
        @self.app.post("/a2a")
        async def handle_jsonrpc(
            request: Request,
            caller: CallerIdentity = Depends(self.auth.authenticate)
        ):
            body = await request.json()
            return await self.jsonrpc.handle(body, caller)

        # Task status endpoint (A2A Tasks)
        @self.app.get("/a2a/tasks/{task_id}")
        async def get_task_status(
            task_id: str,
            caller: CallerIdentity = Depends(self.auth.authenticate)
        ):
            task = await self.task_manager.get(task_id)
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")

            # Verify caller has access to this task
            if not await self.auth.can_access_task(caller, task):
                raise HTTPException(status_code=403, detail="Access denied")

            return task.to_response()

        # EATP Extension: Trust verification endpoint
        @self.app.get("/a2a/trust")
        async def get_trust_status():
            """Return trust lineage for verification by external agents."""
            if not self.agent.trust_chain:
                return {"trusted": False, "reason": "No trust chain"}

            return {
                "trusted": True,
                "trust_lineage": self.agent.trust_chain.to_a2a_format(),
                "verification": await self.trust_ops.verify(
                    agent_id=self.agent.id,
                    action="a2a_trust_status",
                    level=VerificationLevel.QUICK
                )
            }

    def _setup_middleware(self):
        """Setup request/response middleware."""

        @self.app.middleware("http")
        async def audit_middleware(request: Request, call_next):
            """Audit all incoming A2A requests."""
            start_time = datetime.utcnow()

            # Create audit anchor for request
            if self.agent.trust_chain:
                await self.trust_ops.audit(
                    agent_id=self.agent.id,
                    action=f"a2a_request:{request.method}:{request.url.path}",
                    result=ActionResult.SUCCESS,
                    context={
                        "method": request.method,
                        "path": str(request.url.path),
                        "remote_addr": request.client.host
                    }
                )

            response = await call_next(request)

            # Add audit header to response
            response.headers["X-Audit-Anchor"] = self.agent.trust_chain.audit_anchors[-1].id if self.agent.trust_chain else "none"

            return response

    def _setup_cors(self):
        """Setup CORS for browser-based A2A clients."""
        from fastapi.middleware.cors import CORSMiddleware

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )

    def run(self, **kwargs):
        """Run the A2A service."""
        import uvicorn
        uvicorn.run(self.app, host=self.host, port=self.port, **kwargs)
```

### 2. Agent Card Generation

```python
# kaizen/a2a/agent_card.py
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from kaizen.trust.agent import TrustedAgent

@dataclass
class AgentCard:
    """A2A Agent Card representation."""
    name: str
    description: str
    url: str
    version: str
    capabilities: Dict[str, Any]
    skills: List[Dict[str, Any]]
    defaultInputModes: List[str]
    defaultOutputModes: List[str]
    provider: Dict[str, str]
    authentication: Dict[str, Any]
    # EATP Extension
    trust_lineage: Optional[Dict[str, Any]] = None

class AgentCardGenerator:
    """Generate A2A-compliant Agent Cards."""

    @staticmethod
    def generate(agent: TrustedAgent, base_url: str) -> Dict[str, Any]:
        """Generate Agent Card for a TrustedAgent."""

        card = {
            "name": agent.name,
            "description": agent.signature.description if agent.signature else "",
            "url": base_url,
            "version": "1.0",
            "capabilities": {
                "streaming": False,
                "pushNotifications": False,
                "stateTransitionHistory": True
            },
            "skills": AgentCardGenerator._generate_skills(agent),
            "defaultInputModes": ["text/plain", "application/json"],
            "defaultOutputModes": ["text/plain", "application/json"],
            "provider": {
                "organization": "Kaizen Framework",
                "url": "https://kailash.ai"
            },
            "authentication": {
                "schemes": [
                    {
                        "type": "apiKey",
                        "in": "header",
                        "name": "X-API-Key"
                    },
                    {
                        "type": "oauth2",
                        "flows": {
                            "clientCredentials": {
                                "tokenUrl": f"{base_url}/oauth/token",
                                "scopes": {
                                    "agent:execute": "Execute agent tasks",
                                    "agent:read": "Read agent status"
                                }
                            }
                        }
                    }
                ]
            }
        }

        # EATP Extension: Add trust lineage
        if agent.trust_chain:
            card["trust_lineage"] = AgentCardGenerator._generate_trust_lineage(agent)

        return card

    @staticmethod
    def _generate_skills(agent: TrustedAgent) -> List[Dict[str, Any]]:
        """Generate skills from agent capabilities and tools."""
        skills = []

        # From capabilities
        if agent.trust_chain:
            for cap in agent.trust_chain.capabilities:
                skills.append({
                    "id": cap.id,
                    "name": cap.capability,
                    "description": f"Capability: {cap.capability}",
                    "tags": cap.constraints,
                    "examples": []
                })

        # From tools
        for tool in agent.tools:
            skills.append({
                "id": f"tool-{tool.name}",
                "name": tool.name,
                "description": tool.description,
                "tags": ["tool"],
                "examples": tool.examples if hasattr(tool, "examples") else []
            })

        return skills

    @staticmethod
    def _generate_trust_lineage(agent: TrustedAgent) -> Dict[str, Any]:
        """Generate EATP trust lineage for Agent Card."""
        chain = agent.trust_chain

        return {
            "genesis": {
                "id": chain.genesis.id,
                "authority_id": chain.genesis.authority_id,
                "authority_type": chain.genesis.authority_type.value,
                "created_at": chain.genesis.created_at.isoformat(),
                "expires_at": chain.genesis.expires_at.isoformat() if chain.genesis.expires_at else None,
                "signature_algorithm": chain.genesis.signature_algorithm,
                # Note: Signature itself not exposed in card for security
                "signature_hash": hashlib.sha256(chain.genesis.signature.encode()).hexdigest()[:16]
            },
            "capabilities": [
                {
                    "capability": cap.capability,
                    "capability_type": cap.capability_type.value,
                    "constraints": cap.constraints,
                    "expires_at": cap.expires_at.isoformat() if cap.expires_at else None
                }
                for cap in chain.capabilities
            ],
            "active_constraints": chain.constraint_envelope.get_all_constraints(),
            "chain_hash": chain.hash(),
            "verification_endpoint": "/.well-known/agent.json/trust/verify"
        }
```

### 3. JSON-RPC 2.0 Handler

```python
# kaizen/a2a/jsonrpc.py
from dataclasses import dataclass
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel

class JsonRpcRequest(BaseModel):
    """JSON-RPC 2.0 Request."""
    jsonrpc: str = "2.0"
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Union[str, int, None] = None

class JsonRpcResponse(BaseModel):
    """JSON-RPC 2.0 Response."""
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    id: Union[str, int, None] = None

class JsonRpcError:
    """Standard JSON-RPC 2.0 errors."""
    PARSE_ERROR = {"code": -32700, "message": "Parse error"}
    INVALID_REQUEST = {"code": -32600, "message": "Invalid Request"}
    METHOD_NOT_FOUND = {"code": -32601, "message": "Method not found"}
    INVALID_PARAMS = {"code": -32602, "message": "Invalid params"}
    INTERNAL_ERROR = {"code": -32603, "message": "Internal error"}

    # EATP-specific errors
    TRUST_VERIFICATION_FAILED = {"code": -32001, "message": "Trust verification failed"}
    CAPABILITY_NOT_FOUND = {"code": -32002, "message": "Capability not found"}
    CONSTRAINT_VIOLATION = {"code": -32003, "message": "Constraint violation"}

class JsonRpcHandler:
    """Handle JSON-RPC 2.0 requests for A2A protocol."""

    def __init__(
        self,
        agent: TrustedAgent,
        task_manager: TaskManager,
        trust_ops: TrustOperations
    ):
        self.agent = agent
        self.task_manager = task_manager
        self.trust_ops = trust_ops

        # Register method handlers
        self._methods = {
            # A2A Core Methods
            "task.create": self._handle_task_create,
            "task.status": self._handle_task_status,
            "task.cancel": self._handle_task_cancel,

            # EATP Extension Methods
            "trust.verify": self._handle_trust_verify,
            "trust.delegate": self._handle_trust_delegate,
            "audit.query": self._handle_audit_query
        }

    async def handle(
        self,
        request: Dict[str, Any],
        caller: CallerIdentity
    ) -> Dict[str, Any]:
        """Handle incoming JSON-RPC request."""
        try:
            # Parse request
            rpc_request = JsonRpcRequest(**request)

            # Find method handler
            handler = self._methods.get(rpc_request.method)
            if not handler:
                return JsonRpcResponse(
                    error=JsonRpcError.METHOD_NOT_FOUND,
                    id=rpc_request.id
                ).dict()

            # Execute handler
            result = await handler(rpc_request.params or {}, caller)

            return JsonRpcResponse(
                result=result,
                id=rpc_request.id
            ).dict()

        except ValidationError as e:
            return JsonRpcResponse(
                error={**JsonRpcError.INVALID_PARAMS, "data": str(e)},
                id=request.get("id")
            ).dict()
        except TrustError as e:
            return JsonRpcResponse(
                error={**JsonRpcError.TRUST_VERIFICATION_FAILED, "data": str(e)},
                id=request.get("id")
            ).dict()
        except Exception as e:
            return JsonRpcResponse(
                error={**JsonRpcError.INTERNAL_ERROR, "data": str(e)},
                id=request.get("id")
            ).dict()

    # =========================================================================
    # A2A Core Methods
    # =========================================================================

    async def _handle_task_create(
        self,
        params: Dict[str, Any],
        caller: CallerIdentity
    ) -> Dict[str, Any]:
        """Handle task.create method."""

        # 1. Validate caller's trust if available
        if caller.trust_lineage:
            verification = await self.trust_ops.verify(
                agent_id=caller.agent_id,
                action="create_task",
                level=VerificationLevel.STANDARD
            )
            if not verification.valid:
                raise TrustError(f"Caller trust verification failed: {verification.reason}")

        # 2. Extract task parameters
        input_data = params.get("input", {})
        required_capabilities = params.get("capabilities", [])
        constraints = params.get("constraints", [])

        # 3. Verify this agent has required capabilities
        for cap in required_capabilities:
            if cap not in self.agent.capabilities:
                raise CapabilityNotFoundError(self.agent.id, cap)

        # 4. Create delegation if caller has trust
        delegation = None
        if caller.trust_lineage:
            delegation = await self.trust_ops.delegate(
                delegator_id=caller.agent_id,
                delegatee_id=self.agent.id,
                task_id=f"task-{uuid4()}",
                capabilities=required_capabilities,
                additional_constraints=constraints
            )
            await self.agent.receive_delegation(delegation)

        # 5. Create and queue task
        task = await self.task_manager.create(
            input=input_data,
            caller_id=caller.agent_id,
            delegation_id=delegation.id if delegation else None
        )

        # 6. Start async execution
        asyncio.create_task(self._execute_task(task))

        return {
            "task_id": task.id,
            "status": task.status.value,
            "created_at": task.created_at.isoformat(),
            "delegation_id": delegation.id if delegation else None
        }

    async def _handle_task_status(
        self,
        params: Dict[str, Any],
        caller: CallerIdentity
    ) -> Dict[str, Any]:
        """Handle task.status method."""
        task_id = params.get("task_id")
        if not task_id:
            raise ValueError("task_id is required")

        task = await self.task_manager.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        return {
            "task_id": task.id,
            "status": task.status.value,
            "progress": task.progress,
            "result": task.result if task.status == TaskStatus.COMPLETED else None,
            "error": task.error if task.status == TaskStatus.FAILED else None,
            "audit_anchors": [a.id for a in task.audit_anchors]
        }

    async def _handle_task_cancel(
        self,
        params: Dict[str, Any],
        caller: CallerIdentity
    ) -> Dict[str, Any]:
        """Handle task.cancel method."""
        task_id = params.get("task_id")
        if not task_id:
            raise ValueError("task_id is required")

        task = await self.task_manager.cancel(task_id)

        # Audit cancellation
        await self.trust_ops.audit(
            agent_id=self.agent.id,
            action="task_cancelled",
            resource=task_id,
            result=ActionResult.SUCCESS,
            context={"cancelled_by": caller.agent_id}
        )

        return {"task_id": task.id, "status": "cancelled"}

    # =========================================================================
    # EATP Extension Methods
    # =========================================================================

    async def _handle_trust_verify(
        self,
        params: Dict[str, Any],
        caller: CallerIdentity
    ) -> Dict[str, Any]:
        """Handle trust.verify method - verify another agent's trust."""
        target_agent_id = params.get("agent_id")
        action = params.get("action", "general")

        verification = await self.trust_ops.verify(
            agent_id=target_agent_id or self.agent.id,
            action=action,
            level=VerificationLevel.FULL
        )

        return {
            "valid": verification.valid,
            "reason": verification.reason if not verification.valid else None,
            "capability_used": verification.capability_used,
            "effective_constraints": verification.effective_constraints
        }

    async def _handle_trust_delegate(
        self,
        params: Dict[str, Any],
        caller: CallerIdentity
    ) -> Dict[str, Any]:
        """Handle trust.delegate method - delegate trust to this agent."""
        if not caller.trust_lineage:
            raise TrustError("Caller must have trust to delegate")

        capabilities = params.get("capabilities", [])
        constraints = params.get("constraints", [])
        task_id = params.get("task_id", f"delegation-{uuid4()}")

        delegation = await self.trust_ops.delegate(
            delegator_id=caller.agent_id,
            delegatee_id=self.agent.id,
            task_id=task_id,
            capabilities=capabilities,
            additional_constraints=constraints
        )

        await self.agent.receive_delegation(delegation)

        return {
            "delegation_id": delegation.id,
            "delegated_capabilities": capabilities,
            "effective_constraints": delegation.constraint_subset,
            "expires_at": delegation.expires_at.isoformat() if delegation.expires_at else None
        }

    async def _handle_audit_query(
        self,
        params: Dict[str, Any],
        caller: CallerIdentity
    ) -> Dict[str, Any]:
        """Handle audit.query method - query audit history."""
        # Only allow querying own audit history or if caller is authority
        if caller.agent_id != self.agent.id:
            if not await self._is_authority(caller):
                raise TrustError("Not authorized to query audit history")

        start_time = datetime.fromisoformat(params["start_time"]) if params.get("start_time") else None
        end_time = datetime.fromisoformat(params["end_time"]) if params.get("end_time") else None

        anchors = await self.trust_ops.audit_store.query(
            agent_id=self.agent.id,
            start_time=start_time,
            end_time=end_time,
            limit=params.get("limit", 100)
        )

        return {
            "anchors": [
                {
                    "id": a.id,
                    "action": a.action,
                    "timestamp": a.timestamp.isoformat(),
                    "result": a.result.value,
                    "trust_chain_hash": a.trust_chain_hash
                }
                for a in anchors
            ],
            "total": len(anchors)
        }

    # =========================================================================
    # Helper Methods
    # =========================================================================

    async def _execute_task(self, task: A2ATask):
        """Execute task asynchronously."""
        try:
            # Update status
            task.status = TaskStatus.WORKING
            await self.task_manager.update(task)

            # Execute agent
            result = await self.agent.run(task.input)

            # Update with result
            task.status = TaskStatus.COMPLETED
            task.result = result
            await self.task_manager.update(task)

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            await self.task_manager.update(task)

            # Audit failure
            await self.trust_ops.audit(
                agent_id=self.agent.id,
                action="task_failed",
                resource=task.id,
                result=ActionResult.FAILURE,
                context={"error": str(e)}
            )
```

### 4. Authentication

```python
# kaizen/a2a/auth.py
from fastapi import Request, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from typing import Optional

class CallerIdentity:
    """Identity of A2A caller."""
    def __init__(
        self,
        agent_id: str,
        trust_lineage: Optional[TrustLineageChain] = None,
        auth_method: str = "api_key"
    ):
        self.agent_id = agent_id
        self.trust_lineage = trust_lineage
        self.auth_method = auth_method

class A2AAuthenticator:
    """Authenticate A2A requests."""

    def __init__(self, trust_ops: TrustOperations):
        self.trust_ops = trust_ops
        self.api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/oauth/token", auto_error=False)

    async def authenticate(
        self,
        request: Request,
        api_key: Optional[str] = Depends(APIKeyHeader(name="X-API-Key", auto_error=False)),
        token: Optional[str] = Depends(OAuth2PasswordBearer(tokenUrl="/oauth/token", auto_error=False))
    ) -> CallerIdentity:
        """Authenticate incoming request."""

        # Try API Key auth
        if api_key:
            identity = await self._authenticate_api_key(api_key)
            if identity:
                return identity

        # Try OAuth2 auth
        if token:
            identity = await self._authenticate_oauth(token)
            if identity:
                return identity

        # Try Agent Card verification (for agent-to-agent)
        agent_card_url = request.headers.get("X-Agent-Card-URL")
        if agent_card_url:
            identity = await self._authenticate_agent_card(agent_card_url)
            if identity:
                return identity

        # No valid auth
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing authentication"
        )

    async def _authenticate_api_key(self, api_key: str) -> Optional[CallerIdentity]:
        """Authenticate via API key."""
        # Look up API key in store
        key_record = await self.api_key_store.get(api_key)
        if not key_record:
            return None

        # Get associated trust chain if any
        trust_chain = await self.trust_ops.trust_store.get_chain(key_record.agent_id)

        return CallerIdentity(
            agent_id=key_record.agent_id,
            trust_lineage=trust_chain,
            auth_method="api_key"
        )

    async def _authenticate_oauth(self, token: str) -> Optional[CallerIdentity]:
        """Authenticate via OAuth2 token."""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            agent_id = payload.get("sub")

            trust_chain = await self.trust_ops.trust_store.get_chain(agent_id)

            return CallerIdentity(
                agent_id=agent_id,
                trust_lineage=trust_chain,
                auth_method="oauth2"
            )
        except jwt.InvalidTokenError:
            return None

    async def _authenticate_agent_card(self, agent_card_url: str) -> Optional[CallerIdentity]:
        """Authenticate by fetching and verifying Agent Card."""
        try:
            # Fetch agent card
            async with aiohttp.ClientSession() as session:
                async with session.get(agent_card_url) as response:
                    if response.status != 200:
                        return None
                    agent_card = await response.json()

            # Extract trust lineage from card
            trust_lineage_data = agent_card.get("trust_lineage")
            if not trust_lineage_data:
                # Agent has no trust, but can still call (with limitations)
                return CallerIdentity(
                    agent_id=agent_card.get("name", "unknown"),
                    trust_lineage=None,
                    auth_method="agent_card"
                )

            # Reconstruct and verify trust chain
            trust_chain = TrustLineageChain.from_a2a_format(trust_lineage_data)
            verification = trust_chain.verify(self.trust_ops.authority_registry)

            if not verification.valid:
                return None

            return CallerIdentity(
                agent_id=agent_card.get("name"),
                trust_lineage=trust_chain,
                auth_method="agent_card"
            )

        except Exception:
            return None

    async def can_access_task(
        self,
        caller: CallerIdentity,
        task: A2ATask
    ) -> bool:
        """Check if caller can access a specific task."""
        # Task creator can always access
        if task.caller_id == caller.agent_id:
            return True

        # Authority can access all tasks
        if await self._is_authority(caller):
            return True

        return False
```

---

## Deployment Configuration

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  kaizen-a2a:
    build: .
    ports:
      - "8080:8080"
    environment:
      - A2A_HOST=0.0.0.0
      - A2A_PORT=8080
      - TRUST_STORE_URL=postgresql://...
      - AUDIT_STORE_URL=postgresql://...
      - JWT_SECRET=${JWT_SECRET}
    volumes:
      - ./certs:/app/certs  # TLS certificates
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/.well-known/agent.json"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Kubernetes

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kaizen-a2a
spec:
  replicas: 3
  selector:
    matchLabels:
      app: kaizen-a2a
  template:
    metadata:
      labels:
        app: kaizen-a2a
    spec:
      containers:
      - name: kaizen-a2a
        image: kaizen-a2a:latest
        ports:
        - containerPort: 8080
        env:
        - name: A2A_PORT
          value: "8080"
        readinessProbe:
          httpGet:
            path: /.well-known/agent.json
            port: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: kaizen-a2a
spec:
  selector:
    app: kaizen-a2a
  ports:
  - port: 443
    targetPort: 8080
  type: LoadBalancer
```

---

## Security Considerations

### TLS Configuration

```python
# Always use HTTPS in production
if not settings.DEBUG:
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(
        certfile=settings.TLS_CERT_PATH,
        keyfile=settings.TLS_KEY_PATH
    )
```

### Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/a2a")
@limiter.limit("100/minute")
async def handle_jsonrpc(request: Request):
    # ...
```

### Input Validation

```python
# All inputs validated via Pydantic models
class TaskCreateParams(BaseModel):
    input: Dict[str, Any]
    capabilities: List[str] = []
    constraints: List[str] = []

    @validator('capabilities')
    def validate_capabilities(cls, v):
        if len(v) > 10:
            raise ValueError("Too many capabilities requested")
        return v
```

---

## Testing

### A2A Compliance Tests

```python
class TestA2ACompliance:
    """Test A2A protocol compliance."""

    async def test_agent_card_endpoint(self, client):
        """Agent Card available at well-known URL."""
        response = await client.get("/.well-known/agent.json")
        assert response.status_code == 200

        card = response.json()
        assert "name" in card
        assert "capabilities" in card
        assert "skills" in card

    async def test_jsonrpc_format(self, client):
        """JSON-RPC 2.0 format compliance."""
        response = await client.post("/a2a", json={
            "jsonrpc": "2.0",
            "method": "task.create",
            "params": {"input": {"text": "test"}},
            "id": 1
        })

        result = response.json()
        assert result["jsonrpc"] == "2.0"
        assert "id" in result
        assert "result" in result or "error" in result

    async def test_task_lifecycle(self, client):
        """Task follows proper lifecycle."""
        # Create
        create_response = await client.post("/a2a", json={
            "jsonrpc": "2.0",
            "method": "task.create",
            "params": {"input": {"text": "test"}},
            "id": 1
        })
        task_id = create_response.json()["result"]["task_id"]

        # Poll for completion
        for _ in range(10):
            status_response = await client.get(f"/a2a/tasks/{task_id}")
            status = status_response.json()["status"]
            if status in ["completed", "failed"]:
                break
            await asyncio.sleep(0.5)

        assert status == "completed"
```

---

## Next Steps

1. **Document 06**: Orchestration Runtime Integration
2. **Document 07**: ESA Pattern Implementation
3. Implement A2A service in `kaizen.a2a`
4. Create interoperability tests with external A2A agents
