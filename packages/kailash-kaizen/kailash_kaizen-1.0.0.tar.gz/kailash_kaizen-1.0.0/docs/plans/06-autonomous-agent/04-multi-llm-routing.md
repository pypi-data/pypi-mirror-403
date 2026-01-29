# Multi-LLM Routing Architecture

**Document Status:** Architecture Specification for Kaizen Development Team
**Version:** 1.0.0
**Date:** 2026-01-21

---

## Executive Summary

Multi-LLM support is essential for modern AI applications:

1. **Task-specific optimization**: GPT-4 for structured output, Claude for reasoning
2. **Cost optimization**: Cheaper models for simple tasks
3. **Fallback chains**: If one provider fails, try another
4. **Capability routing**: Vision tasks to vision-capable models

The LLM Router provides intelligent model selection without changing application code.

---

## ⚠️ Critical Clarification: Runtime Model Constraints

> **Important Discovery from Claude Agent SDK Investigation:**
>
> External autonomous agent runtimes are **locked to their native LLM providers**:
>
> | Runtime | Model Constraint | Evidence |
> |---------|-----------------|----------|
> | **Claude Code** | Claude only (sonnet/opus/haiku) | `AgentDefinition.model` is `Literal["sonnet", "opus", "haiku", "inherit"]` |
> | **OpenAI Codex** | OpenAI only (GPT-4, etc.) | Uses OpenAI Assistant API |
> | **Gemini CLI** | Gemini only | Uses Vertex AI |
> | **Kaizen Native** | **Any LLM** ✅ | Full provider abstraction |
>
> **This means:**
> - Multi-LLM routing **only applies to Kaizen Native runtime**
> - When using `ClaudeCodeAdapter`, tasks run on Claude models exclusively
> - To achieve true multi-LLM flexibility, use `LocalKaizenAdapter`
>
> **Architecture Decision:**
> Multi-LLM support is achieved at the **runtime selection level**, not within a single runtime:
> - Choose `LocalKaizenAdapter` when you need multi-LLM routing
> - Choose `ClaudeCodeAdapter` when you need Claude Code's tool ecosystem (accepting Claude-only constraint)

---

## The Need for Multi-LLM

### Single-LLM Limitations

```python
# ❌ Limited: Only one model for all tasks
agent = Agent(model="gpt-4")

# All tasks use GPT-4, even simple ones that could use cheaper models
await agent.run("What is 2+2?")  # Overkill
await agent.run("Analyze this 50-page financial report")  # Appropriate
await agent.run("Describe this image")  # GPT-4 can't do vision
```

### Multi-LLM Benefits

```python
# ✅ Better: Route tasks to appropriate models
agent = Agent(
    model="gpt-4",  # Default
    llm_routing={
        "simple": "gpt-3.5-turbo",      # Simple tasks → cheap
        "complex": "claude-3-opus",      # Complex reasoning → best
        "code": "gpt-4",                 # Code generation
        "vision": "gpt-4-vision",        # Image analysis
        "structured": "gpt-4-turbo"      # JSON output
    }
)
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Agent.run(task)                            │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                            LLM Router                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │   Task      │  │  Routing    │  │  Provider   │                 │
│  │  Analyzer   │──│   Rules     │──│  Selector   │                 │
│  └─────────────┘  └─────────────┘  └─────────────┘                 │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│    OpenAI       │  │   Anthropic     │  │    Google       │
│    Provider     │  │    Provider     │  │    Provider     │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ • GPT-4         │  │ • Claude Opus   │  │ • Gemini Pro    │
│ • GPT-3.5       │  │ • Claude Sonnet │  │ • Gemini Flash  │
│ • GPT-4 Vision  │  │ • Claude Haiku  │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

---

## Core Components

### LLMCapabilities

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class LLMCapabilities:
    """Capabilities of an LLM model."""

    # Identity
    provider: str           # "openai", "anthropic", "google", "ollama"
    model: str              # "gpt-4", "claude-3-opus", etc.

    # Capabilities
    supports_vision: bool = False
    supports_audio: bool = False
    supports_tool_calling: bool = True
    supports_structured_output: bool = False
    supports_streaming: bool = True

    # Context
    max_context: int = 128000
    max_output: int = 4096

    # Cost (per 1000 tokens)
    cost_per_1k_input: float = 0.01
    cost_per_1k_output: float = 0.03

    # Performance
    latency_p50_ms: int = 500
    quality_score: float = 0.9  # 0.0-1.0 relative quality

    # Specialties
    specialties: List[str] = None  # ["code", "math", "reasoning", "creative"]

    def __post_init__(self):
        if self.specialties is None:
            self.specialties = []


# Model registry
MODEL_REGISTRY = {
    # OpenAI
    "gpt-4": LLMCapabilities(
        provider="openai", model="gpt-4",
        supports_tool_calling=True,
        max_context=128000, max_output=4096,
        cost_per_1k_input=0.03, cost_per_1k_output=0.06,
        quality_score=0.95,
        specialties=["code", "reasoning", "math"]
    ),
    "gpt-4-turbo": LLMCapabilities(
        provider="openai", model="gpt-4-turbo",
        supports_tool_calling=True, supports_structured_output=True,
        max_context=128000, max_output=4096,
        cost_per_1k_input=0.01, cost_per_1k_output=0.03,
        quality_score=0.92,
        specialties=["code", "structured"]
    ),
    "gpt-4-vision": LLMCapabilities(
        provider="openai", model="gpt-4-vision-preview",
        supports_vision=True, supports_tool_calling=True,
        max_context=128000, max_output=4096,
        cost_per_1k_input=0.01, cost_per_1k_output=0.03,
        quality_score=0.92,
        specialties=["vision"]
    ),
    "gpt-3.5-turbo": LLMCapabilities(
        provider="openai", model="gpt-3.5-turbo",
        supports_tool_calling=True,
        max_context=16385, max_output=4096,
        cost_per_1k_input=0.0005, cost_per_1k_output=0.0015,
        quality_score=0.75,
        specialties=["simple", "fast"]
    ),

    # Anthropic
    "claude-3-opus": LLMCapabilities(
        provider="anthropic", model="claude-3-opus-20240229",
        supports_vision=True, supports_tool_calling=True,
        max_context=200000, max_output=4096,
        cost_per_1k_input=0.015, cost_per_1k_output=0.075,
        quality_score=0.98,
        specialties=["reasoning", "analysis", "creative"]
    ),
    "claude-3-sonnet": LLMCapabilities(
        provider="anthropic", model="claude-3-sonnet-20240229",
        supports_vision=True, supports_tool_calling=True,
        max_context=200000, max_output=4096,
        cost_per_1k_input=0.003, cost_per_1k_output=0.015,
        quality_score=0.90,
        specialties=["balanced"]
    ),
    "claude-3-haiku": LLMCapabilities(
        provider="anthropic", model="claude-3-haiku-20240307",
        supports_vision=True, supports_tool_calling=True,
        max_context=200000, max_output=4096,
        cost_per_1k_input=0.00025, cost_per_1k_output=0.00125,
        quality_score=0.78,
        specialties=["fast", "simple"]
    ),

    # Google
    "gemini-pro": LLMCapabilities(
        provider="google", model="gemini-pro",
        supports_tool_calling=True,
        max_context=32000, max_output=8192,
        cost_per_1k_input=0.00025, cost_per_1k_output=0.0005,
        quality_score=0.85,
        specialties=["general"]
    ),
}
```

### Task Complexity Analysis

```python
from enum import Enum
import re

class TaskComplexity(Enum):
    TRIVIAL = "trivial"      # One-word answers, yes/no
    SIMPLE = "simple"        # Basic Q&A, lookups
    MODERATE = "moderate"    # Analysis, summaries
    COMPLEX = "complex"      # Multi-step reasoning
    EXPERT = "expert"        # Domain expertise required

class TaskType(Enum):
    GENERAL = "general"
    CODE = "code"
    MATH = "math"
    CREATIVE = "creative"
    ANALYSIS = "analysis"
    STRUCTURED = "structured"
    VISION = "vision"

class TaskAnalyzer:
    """Analyze tasks to determine routing requirements."""

    def analyze(self, task: str, context: dict = None) -> dict:
        """
        Analyze a task and return routing hints.

        Returns:
            {
                "complexity": TaskComplexity,
                "type": TaskType,
                "requires_vision": bool,
                "requires_tools": bool,
                "requires_structured": bool,
                "estimated_tokens": int,
                "specialties_needed": List[str]
            }
        """
        task_lower = task.lower()

        return {
            "complexity": self._analyze_complexity(task, context),
            "type": self._analyze_type(task_lower),
            "requires_vision": self._requires_vision(task_lower, context),
            "requires_tools": self._requires_tools(task_lower, context),
            "requires_structured": self._requires_structured(task_lower),
            "estimated_tokens": self._estimate_tokens(task),
            "specialties_needed": self._get_specialties(task_lower)
        }

    def _analyze_complexity(self, task: str, context: dict) -> TaskComplexity:
        """Determine task complexity."""
        task_lower = task.lower()

        # Trivial indicators
        if len(task) < 50 and task.endswith("?"):
            if any(w in task_lower for w in ["what is", "define", "who is"]):
                return TaskComplexity.SIMPLE

        # Expert indicators
        expert_patterns = [
            r"(analyze|evaluate|assess).*(complex|comprehensive|detailed)",
            r"(compare|contrast).*(multiple|several)",
            r"(design|architect|implement).*(system|solution)",
            r"(financial|legal|medical).*(analysis|assessment)"
        ]
        for pattern in expert_patterns:
            if re.search(pattern, task_lower):
                return TaskComplexity.EXPERT

        # Complex indicators
        complex_words = ["analyze", "synthesize", "evaluate", "compare", "reason", "explain why"]
        if any(word in task_lower for word in complex_words):
            return TaskComplexity.COMPLEX

        # Moderate indicators
        if len(task) > 200 or any(word in task_lower for word in ["summarize", "describe", "list"]):
            return TaskComplexity.MODERATE

        return TaskComplexity.SIMPLE

    def _analyze_type(self, task_lower: str) -> TaskType:
        """Determine primary task type."""
        # Code indicators
        if any(w in task_lower for w in ["code", "implement", "function", "class", "debug", "script"]):
            return TaskType.CODE

        # Math indicators
        if any(w in task_lower for w in ["calculate", "compute", "formula", "equation", "solve"]):
            return TaskType.MATH

        # Creative indicators
        if any(w in task_lower for w in ["write", "create", "story", "poem", "generate content"]):
            return TaskType.CREATIVE

        # Analysis indicators
        if any(w in task_lower for w in ["analyze", "evaluate", "assess", "review"]):
            return TaskType.ANALYSIS

        # Structured output indicators
        if any(w in task_lower for w in ["json", "table", "csv", "structured", "format as"]):
            return TaskType.STRUCTURED

        return TaskType.GENERAL

    def _requires_vision(self, task_lower: str, context: dict) -> bool:
        """Check if task requires vision capabilities."""
        if any(w in task_lower for w in ["image", "picture", "screenshot", "photo", "diagram", "chart"]):
            return True
        if context and context.get("has_images"):
            return True
        return False

    def _get_specialties(self, task_lower: str) -> List[str]:
        """Get list of specialties needed."""
        specialties = []
        if any(w in task_lower for w in ["code", "programming", "script"]):
            specialties.append("code")
        if any(w in task_lower for w in ["math", "calculate", "formula"]):
            specialties.append("math")
        if any(w in task_lower for w in ["reason", "analyze", "think"]):
            specialties.append("reasoning")
        if any(w in task_lower for w in ["create", "write", "compose"]):
            specialties.append("creative")
        return specialties
```

### LLM Router

```python
from typing import Callable, Optional, Dict, List, Any

class RoutingRule:
    """A rule for routing tasks to specific models."""

    def __init__(
        self,
        name: str,
        condition: Callable[[str, dict], bool],
        model: str,
        priority: int = 0
    ):
        self.name = name
        self.condition = condition
        self.model = model
        self.priority = priority


class LLMRouter:
    """
    Intelligent LLM routing based on task requirements.

    Routing strategies:
    1. RULES: Apply explicit routing rules
    2. TASK_COMPLEXITY: Route by analyzed complexity
    3. COST_OPTIMIZED: Minimize cost while meeting requirements
    4. QUALITY_OPTIMIZED: Maximize quality
    5. BALANCED: Balance cost and quality
    6. FALLBACK_CHAIN: Try models in order until success
    """

    def __init__(
        self,
        providers: Dict[str, "LLMProvider"],
        default_model: str = "gpt-4"
    ):
        self.providers = providers
        self.default_model = default_model
        self.rules: List[RoutingRule] = []
        self.task_analyzer = TaskAnalyzer()

        # Model capabilities lookup
        self.model_caps: Dict[str, LLMCapabilities] = {}
        for name, provider in providers.items():
            if hasattr(provider, 'capabilities'):
                self.model_caps[name] = provider.capabilities

    def add_rule(
        self,
        name: str,
        condition: Callable[[str, dict], bool],
        model: str,
        priority: int = 0
    ) -> "LLMRouter":
        """
        Add a routing rule.

        Args:
            name: Rule name for logging
            condition: Function (task, context) -> bool
            model: Model to route to if condition matches
            priority: Higher priority rules checked first

        Returns:
            Self for chaining
        """
        self.rules.append(RoutingRule(name, condition, model, priority))
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        return self

    def add_keyword_rule(
        self,
        keywords: List[str],
        model: str,
        priority: int = 0
    ) -> "LLMRouter":
        """Add a rule based on keywords in task."""
        name = f"keyword_{','.join(keywords[:3])}"

        def condition(task: str, ctx: dict) -> bool:
            task_lower = task.lower()
            return any(kw in task_lower for kw in keywords)

        return self.add_rule(name, condition, model, priority)

    def route(
        self,
        task: str,
        context: Dict[str, Any] = None,
        strategy: str = "balanced",
        required_capabilities: List[str] = None
    ) -> str:
        """
        Route task to appropriate model.

        Args:
            task: The task/prompt
            context: Additional context
            strategy: Routing strategy
            required_capabilities: Must-have capabilities

        Returns:
            Model name to use
        """
        context = context or {}

        # 1. Check explicit rules first
        for rule in self.rules:
            if rule.condition(task, context):
                if self._model_capable(rule.model, required_capabilities):
                    return rule.model

        # 2. Analyze task
        analysis = self.task_analyzer.analyze(task, context)

        # 3. Filter by required capabilities
        candidates = self._filter_capable_models(
            required_capabilities or [],
            analysis
        )

        if not candidates:
            return self.default_model

        # 4. Apply strategy
        if strategy == "cost_optimized":
            return self._select_cheapest(candidates)
        elif strategy == "quality_optimized":
            return self._select_best_quality(candidates)
        elif strategy == "task_complexity":
            return self._select_by_complexity(candidates, analysis)
        else:  # balanced
            return self._select_balanced(candidates, analysis)

    def _filter_capable_models(
        self,
        requirements: List[str],
        analysis: dict
    ) -> List[str]:
        """Filter models that meet requirements."""
        capable = []

        for model_name, caps in self.model_caps.items():
            # Check explicit requirements
            meets_reqs = True
            for req in requirements:
                if req == "vision" and not caps.supports_vision:
                    meets_reqs = False
                elif req == "tools" and not caps.supports_tool_calling:
                    meets_reqs = False
                elif req == "structured" and not caps.supports_structured_output:
                    meets_reqs = False

            # Check analysis-based requirements
            if analysis["requires_vision"] and not caps.supports_vision:
                meets_reqs = False
            if analysis["requires_structured"] and not caps.supports_structured_output:
                meets_reqs = False

            if meets_reqs:
                capable.append(model_name)

        return capable

    def _select_by_complexity(
        self,
        candidates: List[str],
        analysis: dict
    ) -> str:
        """Select model based on task complexity."""
        complexity = analysis["complexity"]

        if complexity == TaskComplexity.TRIVIAL:
            # Use cheapest
            return self._select_cheapest(candidates)

        elif complexity == TaskComplexity.SIMPLE:
            # Use cheap but capable
            simple_models = [m for m in candidates if self.model_caps[m].quality_score < 0.85]
            if simple_models:
                return simple_models[0]
            return self._select_cheapest(candidates)

        elif complexity == TaskComplexity.EXPERT:
            # Use best quality
            return self._select_best_quality(candidates)

        else:  # MODERATE or COMPLEX
            return self._select_balanced(candidates, analysis)

    def _select_cheapest(self, candidates: List[str]) -> str:
        """Select cheapest model."""
        return min(
            candidates,
            key=lambda m: self.model_caps[m].cost_per_1k_input
        )

    def _select_best_quality(self, candidates: List[str]) -> str:
        """Select highest quality model."""
        return max(
            candidates,
            key=lambda m: self.model_caps[m].quality_score
        )

    def _select_balanced(self, candidates: List[str], analysis: dict) -> str:
        """Balance quality and cost."""
        # Score = quality / cost (value for money)
        def score(model: str) -> float:
            caps = self.model_caps[model]
            cost = caps.cost_per_1k_input + caps.cost_per_1k_output
            return caps.quality_score / (cost + 0.001)

        # Bonus for matching specialties
        def specialty_score(model: str) -> float:
            caps = self.model_caps[model]
            needed = set(analysis.get("specialties_needed", []))
            has = set(caps.specialties or [])
            overlap = len(needed & has)
            return overlap * 0.1  # 10% bonus per matching specialty

        return max(
            candidates,
            key=lambda m: score(m) + specialty_score(m)
        )
```

---

## Integration with Runtimes

### Runtime-Aware Routing Strategy

Since external runtimes are locked to their native models, multi-LLM routing operates at a **higher level**:

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Runtime + LLM Selection                         │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
              ┌──────────────────┴──────────────────┐
              ▼                                     ▼
┌─────────────────────────────┐    ┌─────────────────────────────────┐
│  Need Multi-LLM Routing?    │    │  Need External Runtime Tools?   │
│                             │    │  (File/Bash/MCP from Claude)    │
│  YES → LocalKaizenAdapter   │    │  YES → ClaudeCodeAdapter        │
│        (full LLM routing)   │    │        (Claude models only)     │
└─────────────────────────────┘    └─────────────────────────────────┘
```

**Decision Matrix:**

| Requirement | Recommended Runtime | LLM Options |
|-------------|-------------------|-------------|
| Multi-LLM routing | LocalKaizenAdapter | Any provider |
| Claude Code tools (file, bash, MCP) | ClaudeCodeAdapter | Claude only |
| OpenAI Code Interpreter | OpenAICodexAdapter | OpenAI only |
| Google Cloud integration | GeminiCLIAdapter | Gemini only |
| Maximum flexibility | LocalKaizenAdapter | Any provider |

### Hybrid Execution (Kaizen Native Only)

Within `LocalKaizenAdapter`, we can route different sub-tasks to different LLMs:

```python
class HybridExecutor:
    """
    Execute with hybrid LLM routing.

    Use autonomous runtime for main execution,
    but route specific sub-tasks to other LLMs.
    """

    def __init__(
        self,
        runtime: RuntimeAdapter,
        llm_router: LLMRouter
    ):
        self.runtime = runtime
        self.router = llm_router

    async def execute(
        self,
        task: str,
        context: Dict[str, Any],
        routing_overrides: Dict[str, str] = None
    ) -> ExecutionResult:
        """
        Execute with intelligent routing.

        Args:
            task: Main task
            context: Execution context
            routing_overrides: {task_type: model} overrides

        Returns:
            Execution result
        """
        # Analyze main task
        analysis = self.router.task_analyzer.analyze(task, context)

        # Decide execution path
        if analysis["complexity"] in [TaskComplexity.TRIVIAL, TaskComplexity.SIMPLE]:
            # Simple task: use direct LLM call (skip autonomous overhead)
            model = self.router.route(task, context, strategy="cost_optimized")
            return await self._direct_llm_call(task, model, context)

        else:
            # Complex task: use autonomous runtime
            # But configure routing for any sub-calls
            context["llm_routing"] = routing_overrides or self._build_routing_config(analysis)
            return await self.runtime.execute(
                ExecutionContext(task=task, **context)
            )

    def _build_routing_config(self, analysis: dict) -> Dict[str, str]:
        """Build routing config based on analysis."""
        config = {}

        # Route sub-tasks by type
        if "code" in analysis.get("specialties_needed", []):
            config["code_generation"] = "gpt-4"

        if analysis["requires_structured"]:
            config["structured_output"] = "gpt-4-turbo"

        if analysis["requires_vision"]:
            config["vision"] = "gpt-4-vision"

        return config
```

---

## Usage Examples

### Basic Routing

```python
from kaizen.llm import LLMRouter

router = LLMRouter(providers, default_model="gpt-4")

# Add routing rules
router.add_keyword_rule(["calculate", "formula"], "gpt-4", priority=10)
router.add_keyword_rule(["simple", "quick"], "gpt-3.5-turbo", priority=5)
router.add_rule(
    name="vision_required",
    condition=lambda t, c: "image" in t.lower() or c.get("has_images"),
    model="gpt-4-vision",
    priority=20
)

# Route tasks
model = router.route("Calculate the IRP forward rate")  # → gpt-4
model = router.route("What is 2+2?")  # → gpt-3.5-turbo (simple)
model = router.route("Analyze this chart", {"has_images": True})  # → gpt-4-vision
```

### With Agent

```python
from kaizen.agent import Agent

# Configure routing at agent level
agent = Agent(
    model="gpt-4",  # Default
    execution_mode="autonomous",
    llm_routing={
        "simple_queries": "gpt-3.5-turbo",
        "code_generation": "gpt-4",
        "analysis": "claude-3-opus",
        "vision": "gpt-4-vision",
        "structured": "gpt-4-turbo"
    },
    routing_strategy="balanced"
)

# Tasks automatically routed
await agent.run("What is IRP?")  # → gpt-3.5-turbo (simple)
await agent.run("Implement an IRP calculator in Python")  # → gpt-4 (code)
await agent.run("Analyze this complex hedging scenario...")  # → claude-3-opus (analysis)
```

### Cost Optimization

```python
# Optimize for cost
agent = Agent(
    model="gpt-3.5-turbo",  # Cheap default
    routing_strategy="cost_optimized",
    llm_routing={
        # Only upgrade for specific cases
        "expert": "gpt-4",
        "vision": "gpt-4-vision"
    }
)

# Automatic cost optimization
await agent.run("Define covered interest parity")  # → gpt-3.5-turbo (~$0.001)
await agent.run("Analyze the complex interplay of...")  # → gpt-4 (~$0.03)
```

---

## Fallback Chains

Handle provider failures gracefully:

```python
class FallbackRouter(LLMRouter):
    """Router with automatic fallback on failure."""

    def __init__(self, *args, fallback_chain: List[str] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fallback_chain = fallback_chain or ["gpt-4", "claude-3-sonnet", "gemini-pro"]

    async def route_with_fallback(
        self,
        task: str,
        context: dict,
        execute_fn: Callable
    ) -> Any:
        """Route and execute with automatic fallback."""
        # Get primary model
        model = self.route(task, context)
        chain = [model] + [m for m in self.fallback_chain if m != model]

        last_error = None
        for model in chain:
            try:
                return await execute_fn(model)
            except Exception as e:
                last_error = e
                continue

        raise last_error
```

---

## Summary

Multi-LLM routing provides:

1. **Task Optimization**: Right model for each task
2. **Cost Savings**: Cheap models for simple tasks
3. **Capability Matching**: Vision/audio/tools routing
4. **Resilience**: Fallback chains
5. **Transparency**: Consistent API regardless of backend

**Key Insights:**

1. **Model as Resource**: The model is a resource to be optimized, not a fixed choice
2. **Runtime Determines Options**: External runtimes (Claude Code, Codex, Gemini CLI) are locked to their native models
3. **Kaizen Native for Flexibility**: Use `LocalKaizenAdapter` for true multi-LLM routing
4. **Trade-off Awareness**: Claude Code's tool ecosystem vs. multi-LLM flexibility—choose based on requirements

**Practical Guidance:**
- If you need Claude Code's file/bash/MCP tools: Accept Claude-only constraint
- If you need multi-LLM routing: Use Kaizen Native with custom tool implementations
- If you need both: Consider a hybrid approach with runtime switching per task type

---

**Next Document**: [05-memory-integration.md](./05-memory-integration.md) - How memory integrates as a cross-cutting concern.
