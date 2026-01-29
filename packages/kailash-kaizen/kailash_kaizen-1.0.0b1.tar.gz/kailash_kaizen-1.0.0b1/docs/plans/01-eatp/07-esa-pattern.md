# EATP Implementation Plan: ESA Pattern

## Document Control
- **Version**: 1.0
- **Date**: 2025-12-15
- **Status**: Planning
- **Author**: Kaizen Framework Team

---

## Overview

The Enterprise System Agent (ESA) pattern addresses **First Principle 2** from the EATP whitepaper:

> **FP2**: Legacy systems have embedded trust - Solution must inherit, not replace, existing trust

ESAs are special agents that bridge the trust gap between new AI agents and existing enterprise systems. They inherit trust from legacy systems and can delegate that trust to other agents.

---

## The Trust Inheritance Problem

### Current Enterprise Reality

```
┌─────────────────────────────────────────────────────────────┐
│                    ENTERPRISE SYSTEMS                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐     │
│  │   SAP   │   │ Oracle  │   │Salesforce│   │ Custom │     │
│  │   ERP   │   │   DB    │   │   CRM   │   │  Apps  │     │
│  └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘     │
│       │             │             │             │           │
│       └─────────────┴──────┬──────┴─────────────┘           │
│                            │                                 │
│                   Existing Trust                             │
│                   (RBAC, LDAP, SSO)                         │
│                            │                                 │
│                     ┌──────▼──────┐                         │
│                     │   Users &   │                         │
│                     │   Roles     │                         │
│                     └─────────────┘                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘

                         ▲
                         │  HOW?
                         ▼

┌─────────────────────────────────────────────────────────────┐
│                       AI AGENTS                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐     │
│  │ Agent A │   │ Agent B │   │ Agent C │   │ Agent D │     │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘     │
│                                                              │
│                   Need trust to act                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### ESA Solution

```
┌─────────────────────────────────────────────────────────────┐
│                    ENTERPRISE SYSTEMS                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐     │
│  │   SAP   │   │ Oracle  │   │Salesforce│   │ Custom │     │
│  └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘     │
│       │             │             │             │           │
│       └─────────────┴──────┬──────┴─────────────┘           │
│                            │                                 │
│                  ┌─────────▼─────────┐                      │
│                  │                   │                      │
│                  │   ESA (Bridge)    │ ◄── Inherits Trust   │
│                  │                   │                      │
│                  └─────────┬─────────┘                      │
│                            │                                 │
└────────────────────────────┼────────────────────────────────┘
                             │
                   Trust Delegation
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                       AI AGENTS                              │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐     │
│  │ Agent A │   │ Agent B │   │ Agent C │   │ Agent D │     │
│  │ (Trust) │   │ (Trust) │   │ (Trust) │   │ (Trust) │     │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘     │
└─────────────────────────────────────────────────────────────┘
```

---

## ESA Architecture

### Core Concept

An ESA is a TrustedAgent that:
1. **Connects** to a legacy enterprise system
2. **Inherits** that system's trust (via service accounts, API keys, etc.)
3. **Exposes** capabilities as delegatable trust
4. **Audits** all access through EATP audit chain

### ESA Types

| Type | System | Trust Source |
|------|--------|--------------|
| **DatabaseESA** | PostgreSQL, Oracle, etc. | Database credentials |
| **APIÈSA** | REST/GraphQL services | API keys, OAuth |
| **LDAPèSA** | Active Directory | Service account |
| **CloudESA** | AWS, Azure, GCP | IAM roles |
| **ERPESA** | SAP, Oracle Apps | Service user |
| **CustomESA** | Custom applications | Various |

---

## Implementation

### Base ESA Class

```python
from kaizen.trust.agent import TrustedAgent
from kaizen.trust.chain import TrustLineageChain, GenesisRecord, CapabilityAttestation
from kaizen.trust.operations import TrustOperations

class EnterpriseSystemAgent(TrustedAgent):
    """
    Base class for Enterprise System Agents.

    ESAs bridge trust between legacy systems and AI agents by:
    1. Connecting to legacy systems using existing credentials
    2. Exposing system capabilities as attestable trust
    3. Delegating constrained access to other agents
    """

    def __init__(
        self,
        name: str,
        system_type: str,
        system_connection: SystemConnection,
        trust_ops: TrustOperations,
        **kwargs
    ):
        super().__init__(name=name, trust_ops=trust_ops, **kwargs)

        self.system_type = system_type
        self.system_connection = system_connection
        self._system_capabilities: List[SystemCapability] = []

    async def connect_and_inherit_trust(
        self,
        authority_id: str,
        metadata: Dict[str, Any] = None
    ) -> TrustLineageChain:
        """
        Connect to legacy system and inherit its trust.

        This is the key ESA operation that bridges the trust gap.
        """
        # 1. Connect to legacy system
        await self.system_connection.connect()

        # 2. Discover system capabilities
        self._system_capabilities = await self._discover_capabilities()

        # 3. Create capability requests from system capabilities
        capability_requests = [
            CapabilityRequest(
                capability=cap.name,
                capability_type=cap.capability_type,
                constraints=cap.default_constraints,
                scope=cap.scope
            )
            for cap in self._system_capabilities
        ]

        # 4. Establish trust with inherited capabilities
        self._trust_chain = await self._trust_ops.establish(
            agent_id=self.id,
            authority_id=authority_id,
            capabilities=capability_requests,
            constraints=["esa_audit_required"],
            metadata={
                **(metadata or {}),
                "system_type": self.system_type,
                "system_id": self.system_connection.system_id,
                "inherited_from": self.system_connection.connection_info()
            }
        )

        return self._trust_chain

    async def _discover_capabilities(self) -> List[SystemCapability]:
        """
        Discover capabilities from connected system.

        Override in subclasses for specific system types.
        """
        raise NotImplementedError

    async def delegate_system_access(
        self,
        to_agent: TrustedAgent,
        capabilities: List[str],
        constraints: List[str] = None,
        task_id: str = None
    ) -> DelegationRecord:
        """
        Delegate system access to another agent.

        This is how agents gain access to legacy systems.
        """
        # Verify we have the capabilities to delegate
        for cap in capabilities:
            if not self._has_system_capability(cap):
                raise CapabilityNotFoundError(self.id, cap)

        # Create delegation with ESA-specific constraints
        esa_constraints = [
            "esa_proxied",  # All calls go through ESA
            "audit_required"  # All calls audited
        ]

        return await self.delegate_to(
            worker=to_agent,
            task_id=task_id or f"esa-access-{uuid4()}",
            capabilities=capabilities,
            additional_constraints=(constraints or []) + esa_constraints
        )

    async def execute_on_behalf(
        self,
        agent: TrustedAgent,
        capability: str,
        operation: str,
        params: Dict[str, Any]
    ) -> Any:
        """
        Execute operation on legacy system on behalf of agent.

        All access is proxied through ESA for audit and control.
        """
        # 1. Verify agent has delegation for this capability
        delegation = self._find_active_delegation(agent.id, capability)
        if not delegation:
            raise TrustError(f"No active delegation for {agent.id} to use {capability}")

        # 2. Verify constraints are satisfied
        constraint_result = await self._verify_constraints(
            delegation, operation, params
        )
        if not constraint_result.satisfied:
            raise ConstraintViolationError(constraint_result.violations)

        # 3. Execute on legacy system
        async with self._audit_context(f"esa_proxy:{operation}") as audit:
            audit.context = {
                "on_behalf_of": agent.id,
                "delegation_id": delegation.id,
                "operation": operation,
                "system": self.system_type
            }

            try:
                result = await self._execute_system_operation(operation, params)
                audit.result = ActionResult.SUCCESS
                return result
            except Exception as e:
                audit.result = ActionResult.FAILURE
                audit.context["error"] = str(e)
                raise

    async def _execute_system_operation(
        self,
        operation: str,
        params: Dict[str, Any]
    ) -> Any:
        """Execute operation on connected system. Override in subclasses."""
        raise NotImplementedError
```

### Database ESA

```python
class DatabaseESA(EnterpriseSystemAgent):
    """ESA for database systems."""

    def __init__(
        self,
        name: str,
        connection_string: str,
        db_type: str = "postgresql",
        **kwargs
    ):
        connection = DatabaseConnection(
            connection_string=connection_string,
            db_type=db_type
        )
        super().__init__(
            name=name,
            system_type=f"database:{db_type}",
            system_connection=connection,
            **kwargs
        )

    async def _discover_capabilities(self) -> List[SystemCapability]:
        """Discover database capabilities from schema."""
        capabilities = []

        # Get tables/views accessible by connection
        tables = await self.system_connection.get_accessible_tables()

        for table in tables:
            # Read capability
            capabilities.append(SystemCapability(
                name=f"read_{table.name}",
                capability_type=CapabilityType.ACCESS,
                default_constraints=["read_only"],
                scope={"table": table.name, "columns": table.columns}
            ))

            # Write capability (if permitted)
            if table.writable:
                capabilities.append(SystemCapability(
                    name=f"write_{table.name}",
                    capability_type=CapabilityType.ACTION,
                    default_constraints=["audit_required"],
                    scope={"table": table.name}
                ))

        return capabilities

    async def _execute_system_operation(
        self,
        operation: str,
        params: Dict[str, Any]
    ) -> Any:
        """Execute database operation."""
        if operation.startswith("query:"):
            query = params.get("query")
            return await self.system_connection.execute_query(query)
        elif operation.startswith("insert:"):
            table = operation.split(":")[1]
            return await self.system_connection.insert(table, params.get("data"))
        elif operation.startswith("update:"):
            table = operation.split(":")[1]
            return await self.system_connection.update(
                table, params.get("data"), params.get("where")
            )
        else:
            raise ValueError(f"Unknown operation: {operation}")
```

### API ESA

```python
class APIESA(EnterpriseSystemAgent):
    """ESA for REST/GraphQL APIs."""

    def __init__(
        self,
        name: str,
        base_url: str,
        auth_config: APIAuthConfig,
        openapi_spec_url: Optional[str] = None,
        **kwargs
    ):
        connection = APIConnection(
            base_url=base_url,
            auth_config=auth_config
        )
        super().__init__(
            name=name,
            system_type="api:rest",
            system_connection=connection,
            **kwargs
        )
        self.openapi_spec_url = openapi_spec_url

    async def _discover_capabilities(self) -> List[SystemCapability]:
        """Discover capabilities from OpenAPI spec or probing."""
        capabilities = []

        if self.openapi_spec_url:
            # Parse OpenAPI spec
            spec = await self._fetch_openapi_spec()
            for path, methods in spec.paths.items():
                for method, operation in methods.items():
                    capabilities.append(SystemCapability(
                        name=f"api:{method.upper()}:{path}",
                        capability_type=CapabilityType.ACTION if method != "get" else CapabilityType.ACCESS,
                        default_constraints=self._infer_constraints(operation),
                        scope={
                            "path": path,
                            "method": method,
                            "required_scopes": operation.security
                        }
                    ))
        else:
            # Basic capabilities if no spec
            capabilities.append(SystemCapability(
                name="api:request",
                capability_type=CapabilityType.ACTION,
                default_constraints=["rate_limited"],
                scope={"base_url": self.system_connection.base_url}
            ))

        return capabilities

    async def _execute_system_operation(
        self,
        operation: str,
        params: Dict[str, Any]
    ) -> Any:
        """Execute API request."""
        method = params.get("method", "GET")
        path = params.get("path", "/")
        body = params.get("body")
        headers = params.get("headers", {})

        return await self.system_connection.request(
            method=method,
            path=path,
            body=body,
            headers=headers
        )
```

### Cloud ESA

```python
class AWSCloudESA(EnterpriseSystemAgent):
    """ESA for AWS services."""

    def __init__(
        self,
        name: str,
        role_arn: str,
        region: str = "us-east-1",
        services: List[str] = None,
        **kwargs
    ):
        connection = AWSConnection(
            role_arn=role_arn,
            region=region
        )
        super().__init__(
            name=name,
            system_type="cloud:aws",
            system_connection=connection,
            **kwargs
        )
        self.services = services or ["s3", "dynamodb", "lambda"]

    async def _discover_capabilities(self) -> List[SystemCapability]:
        """Discover capabilities from IAM role."""
        capabilities = []

        # Get effective permissions for assumed role
        permissions = await self.system_connection.get_effective_permissions()

        for service in self.services:
            service_permissions = permissions.get(service, [])
            for action in service_permissions:
                capabilities.append(SystemCapability(
                    name=f"aws:{service}:{action}",
                    capability_type=CapabilityType.ACTION,
                    default_constraints=["aws_resource_bounded"],
                    scope={
                        "service": service,
                        "action": action,
                        "region": self.system_connection.region
                    }
                ))

        return capabilities

    async def _execute_system_operation(
        self,
        operation: str,
        params: Dict[str, Any]
    ) -> Any:
        """Execute AWS operation."""
        # Parse operation: aws:s3:GetObject
        parts = operation.split(":")
        if len(parts) != 3:
            raise ValueError(f"Invalid AWS operation format: {operation}")

        _, service, action = parts
        return await self.system_connection.call_service(
            service=service,
            action=action,
            params=params
        )
```

---

## ESA Registry

### Managing Multiple ESAs

```python
class ESARegistry:
    """Registry for managing Enterprise System Agents."""

    def __init__(self, trust_ops: TrustOperations):
        self.trust_ops = trust_ops
        self._esas: Dict[str, EnterpriseSystemAgent] = {}
        self._capability_index: Dict[str, List[str]] = {}  # capability -> ESA IDs

    async def register(
        self,
        esa: EnterpriseSystemAgent,
        authority_id: str
    ) -> str:
        """Register and initialize ESA."""
        # Connect and inherit trust
        await esa.connect_and_inherit_trust(authority_id)

        # Register in registry
        self._esas[esa.id] = esa

        # Index capabilities
        for cap in esa.capabilities:
            if cap not in self._capability_index:
                self._capability_index[cap] = []
            self._capability_index[cap].append(esa.id)

        return esa.id

    def find_esa_for_capability(
        self,
        capability: str
    ) -> Optional[EnterpriseSystemAgent]:
        """Find ESA that can provide a capability."""
        esa_ids = self._capability_index.get(capability, [])
        if not esa_ids:
            return None
        return self._esas.get(esa_ids[0])

    async def delegate_access(
        self,
        capability: str,
        to_agent: TrustedAgent,
        constraints: List[str] = None
    ) -> DelegationRecord:
        """Delegate system access through appropriate ESA."""
        esa = self.find_esa_for_capability(capability)
        if not esa:
            raise CapabilityNotFoundError("ESA Registry", capability)

        return await esa.delegate_system_access(
            to_agent=to_agent,
            capabilities=[capability],
            constraints=constraints
        )

    async def execute_proxied(
        self,
        agent: TrustedAgent,
        capability: str,
        operation: str,
        params: Dict[str, Any]
    ) -> Any:
        """Execute operation through appropriate ESA."""
        esa = self.find_esa_for_capability(capability)
        if not esa:
            raise CapabilityNotFoundError("ESA Registry", capability)

        return await esa.execute_on_behalf(
            agent=agent,
            capability=capability,
            operation=operation,
            params=params
        )
```

---

## Usage Examples

### Example 1: Database Access via ESA

```python
# Setup ESA for finance database
finance_db_esa = DatabaseESA(
    name="finance-db-esa",
    connection_string="postgresql://svc_account:****@finance-db:5432/finance",
    db_type="postgresql",
    trust_ops=trust_ops
)

# Connect and inherit trust
await finance_db_esa.connect_and_inherit_trust(
    authority_id="org-enterprise",
    metadata={"department": "Finance", "system": "Finance Database"}
)

# Create data analyst agent
analyst = TrustedAgent(name="data-analyst")
await analyst.establish_trust(
    authority_id="org-enterprise",
    capabilities=[CapabilityRequest(capability="analyze_data", ...)],
    constraints=["read_only"]
)

# Delegate database access to analyst
delegation = await finance_db_esa.delegate_system_access(
    to_agent=analyst,
    capabilities=["read_transactions", "read_accounts"],
    constraints=["q4_data_only", "no_pii"]
)

# Analyst queries through ESA
result = await finance_db_esa.execute_on_behalf(
    agent=analyst,
    capability="read_transactions",
    operation="query:transactions",
    params={"query": "SELECT * FROM transactions WHERE quarter='Q4' LIMIT 100"}
)
```

### Example 2: Multi-System Workflow

```python
# Register multiple ESAs
esa_registry = ESARegistry(trust_ops)

await esa_registry.register(
    DatabaseESA(name="crm-db", connection_string="..."),
    authority_id="org-enterprise"
)

await esa_registry.register(
    APIESA(name="payment-api", base_url="https://payments.internal", ...),
    authority_id="org-enterprise"
)

await esa_registry.register(
    AWSCloudESA(name="aws-s3", role_arn="arn:aws:iam::...", services=["s3"]),
    authority_id="org-enterprise"
)

# Create workflow agent
workflow_agent = TrustedAgent(name="order-processor")
await workflow_agent.establish_trust(...)

# Delegate access from all required systems
await esa_registry.delegate_access("read_customers", workflow_agent)
await esa_registry.delegate_access("api:POST:/payments", workflow_agent)
await esa_registry.delegate_access("aws:s3:PutObject", workflow_agent)

# Execute workflow
customers = await esa_registry.execute_proxied(
    workflow_agent, "read_customers", "query:customers", {"filter": "active"}
)

for customer in customers:
    payment = await esa_registry.execute_proxied(
        workflow_agent, "api:POST:/payments", "api_call",
        {"method": "POST", "path": "/payments", "body": {"customer_id": customer.id}}
    )

    await esa_registry.execute_proxied(
        workflow_agent, "aws:s3:PutObject", "s3_put",
        {"bucket": "receipts", "key": f"{customer.id}/receipt.pdf", "body": receipt_pdf}
    )
```

---

## Security Considerations

### Credential Management

```python
class ESACredentialManager:
    """Secure credential management for ESAs."""

    def __init__(self, vault_client: VaultClient):
        self.vault = vault_client

    async def get_credentials(
        self,
        system_id: str,
        credential_type: str
    ) -> Dict[str, str]:
        """Retrieve credentials from vault."""
        return await self.vault.read_secret(
            path=f"esa/{system_id}/{credential_type}"
        )

    async def rotate_credentials(
        self,
        system_id: str
    ) -> None:
        """Rotate ESA credentials."""
        # Rotate in vault
        new_creds = await self.vault.rotate_secret(f"esa/{system_id}")

        # Update ESA connection
        esa = self.esa_registry.get(system_id)
        await esa.update_credentials(new_creds)
```

### Access Logging

```python
# All ESA access is logged through EATP audit chain
# Additional enterprise-specific logging
class ESAAuditLogger:
    def __init__(self, splunk_client: SplunkClient):
        self.splunk = splunk_client

    async def log_access(
        self,
        esa_id: str,
        agent_id: str,
        operation: str,
        result: str,
        audit_anchor_id: str
    ):
        """Log ESA access to enterprise SIEM."""
        await self.splunk.log({
            "source": "eatp_esa",
            "esa_id": esa_id,
            "agent_id": agent_id,
            "operation": operation,
            "result": result,
            "eatp_audit_anchor": audit_anchor_id,
            "timestamp": datetime.utcnow().isoformat()
        })
```

---

## Testing Strategy

### ESA Unit Tests

```python
class TestDatabaseESA:
    async def test_capability_discovery(self):
        """Test database capability discovery."""
        esa = DatabaseESA(name="test-db", connection_string="...")
        await esa.connect_and_inherit_trust(authority_id="test-auth")

        # Should discover read/write capabilities for tables
        assert any(c.startswith("read_") for c in esa.capabilities)

    async def test_delegation_constraints(self):
        """Test delegation enforces constraints."""
        esa = DatabaseESA(...)
        agent = TrustedAgent(name="test-agent")

        await esa.delegate_system_access(
            to_agent=agent,
            capabilities=["read_users"],
            constraints=["no_pii"]
        )

        # Should fail if trying to access PII
        with pytest.raises(ConstraintViolationError):
            await esa.execute_on_behalf(
                agent, "read_users", "query:users",
                {"query": "SELECT ssn FROM users"}  # SSN is PII
            )

    async def test_audit_chain(self):
        """Test all access creates audit trail."""
        esa = DatabaseESA(...)
        agent = TrustedAgent(...)

        await esa.execute_on_behalf(agent, "read_users", "query:users", {...})

        # Should have audit anchor
        anchors = await trust_ops.audit_store.query(agent_id=agent.id)
        assert len(anchors) > 0
        assert anchors[-1].action.startswith("esa_proxy:")
```

---

## Next Steps

1. **Document 08**: Testing Strategy
2. **Document 09**: Phased Implementation
3. Implement ESA base class in `kaizen.trust.esa`
4. Create ESA-specific adapters for common enterprise systems
