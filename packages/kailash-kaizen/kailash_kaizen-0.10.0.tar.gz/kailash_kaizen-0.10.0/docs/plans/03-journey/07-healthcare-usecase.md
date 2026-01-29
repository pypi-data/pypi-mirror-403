# Healthcare Referral Journey - Reference Implementation

> **Priority**: P1
> **Effort**: 5 days
> **Files**: `examples/journey/healthcare_referral/`

## Purpose

Implement a complete healthcare referral journey as the reference implementation for Layer 5 Journey Orchestration. This demonstrates all major features:

- Multi-pathway navigation
- Intent-driven transitions
- Context accumulation
- Detour pathways with return
- Persuasion and confirmation patterns

## Use Case Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    HEALTHCARE REFERRAL JOURNEY                                   │
│                                                                                  │
│  User: "I need to see a specialist for my back pain"                            │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                           INTAKE PATHWAY                                    ││
│  │  Collect: symptoms, severity, preferences, insurance                        ││
│  │  Accumulate: symptoms, preferences                                          ││
│  │  Next: booking                                                              ││
│  └────────────────────────────────┬────────────────────────────────────────────┘│
│                                   │                                              │
│                                   ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                          BOOKING PATHWAY                                    ││
│  │  Find: available doctors matching preferences                               ││
│  │  Present: options with times                                                ││
│  │  Handle: doctor rejections → accumulate rejected_doctors                    ││
│  │  Next: confirmation (on selection)                                          ││
│  └────────────────────────────────┬────────────────────────────────────────────┘│
│                                   │                                              │
│          ┌────────────────────────┼────────────────────────┐                    │
│          │                        │                        │                    │
│          ▼                        ▼                        ▼                    │
│  ┌───────────────┐  ┌──────────────────────┐  ┌────────────────────┐           │
│  │  FAQ PATHWAY  │  │ PERSUASION PATHWAY   │  │ CONFIRMATION       │           │
│  │ (detour)      │  │ (when user hesitates)│  │ PATHWAY            │           │
│  │               │  │                      │  │                    │           │
│  │ Return to     │  │ Highlight benefits   │  │ Confirm details    │           │
│  │ previous      │  │ Address concerns     │  │ Send confirmation  │           │
│  │ pathway       │  │ Next: booking        │  │ End journey        │           │
│  └───────────────┘  └──────────────────────┘  └────────────────────┘           │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Implementation

### File Structure

```
examples/journey/healthcare_referral/
├── __init__.py
├── journey.py              # Main journey definition
├── pathways/
│   ├── __init__.py
│   ├── intake.py          # Intake pathway
│   ├── booking.py         # Booking pathway
│   ├── faq.py             # FAQ pathway
│   ├── persuasion.py      # Persuasion pathway
│   └── confirmation.py    # Confirmation pathway
├── signatures/
│   ├── __init__.py
│   ├── intake.py          # Intake signature
│   ├── booking.py         # Booking signature
│   ├── faq.py             # FAQ signature
│   ├── persuasion.py      # Persuasion signature
│   └── confirmation.py    # Confirmation signature
├── agents/
│   ├── __init__.py
│   ├── intake_agent.py    # Intake agent
│   ├── booking_agent.py   # Booking agent
│   ├── faq_agent.py       # FAQ agent
│   └── persuasion_agent.py # Persuasion agent
├── tests/
│   ├── __init__.py
│   ├── test_journey.py        # Journey unit tests
│   ├── test_transitions.py    # Transition tests
│   ├── test_integration.py    # Integration tests
│   └── test_e2e.py            # E2E tests
└── README.md
```

### Signatures

```python
# File: examples/journey/healthcare_referral/signatures/intake.py

from kaizen.signatures import Signature, InputField, OutputField
from typing import List, Dict, Optional


class IntakeSignature(Signature):
    """Gather patient information for healthcare referral."""

    __intent__ = "Collect comprehensive patient symptoms and preferences for specialist referral"

    __guidelines__ = [
        "Start by acknowledging the patient's concern",
        "Ask about symptoms before demographics",
        "Use empathetic, non-clinical language",
        "Identify both physical symptoms and patient preferences",
        "Confirm understanding before proceeding to booking"
    ]

    # Inputs
    patient_message: str = InputField(
        desc="Patient's description of their condition and needs"
    )
    conversation_history: List[Dict] = InputField(
        desc="Previous conversation turns for context",
        default=[]
    )

    # Outputs
    symptoms: List[str] = OutputField(
        desc="Extracted list of symptoms (e.g., ['back pain', 'stiffness'])"
    )
    severity: str = OutputField(
        desc="Assessed severity level: 'mild', 'moderate', 'severe', or 'urgent'"
    )
    preferences: Dict[str, any] = OutputField(
        desc="Patient preferences (time_preference, gender_preference, telehealth_ok)"
    )
    insurance_info: Optional[str] = OutputField(
        desc="Insurance information if mentioned"
    )
    response: str = OutputField(
        desc="Natural language response to the patient"
    )
    ready_for_booking: bool = OutputField(
        desc="Whether sufficient information collected to proceed"
    )
```

```python
# File: examples/journey/healthcare_referral/signatures/booking.py

from kaizen.signatures import Signature, InputField, OutputField
from typing import List, Dict, Optional


class BookingSignature(Signature):
    """Present and handle doctor booking options."""

    __intent__ = "Match patients with appropriate specialists and facilitate booking"

    __guidelines__ = [
        "Present no more than 3 options at a time",
        "Highlight relevant specialties for the symptoms",
        "Respect patient preferences (time, gender, telehealth)",
        "If a doctor is rejected, acknowledge and offer alternatives",
        "Never suggest previously rejected doctors",
        "Explain why each doctor is a good match"
    ]

    # Inputs
    patient_message: str = InputField(desc="Patient's booking-related message")
    symptoms: List[str] = InputField(desc="Patient symptoms from intake")
    preferences: Dict = InputField(desc="Patient preferences from intake")
    rejected_doctors: List[str] = InputField(
        desc="List of doctor IDs the patient has rejected",
        default=[]
    )

    # Outputs
    suggested_doctors: List[Dict] = OutputField(
        desc="List of suggested doctors with availability"
    )
    selected_doctor: Optional[Dict] = OutputField(
        desc="Doctor selected by patient (if selection made)"
    )
    selected_slot: Optional[str] = OutputField(
        desc="Appointment slot selected (if selection made)"
    )
    new_rejected_doctors: List[str] = OutputField(
        desc="New doctors rejected in this turn",
        default=[]
    )
    response: str = OutputField(
        desc="Natural language response presenting options or confirming selection"
    )
    booking_complete: bool = OutputField(
        desc="Whether booking is complete and ready for confirmation"
    )
```

```python
# File: examples/journey/healthcare_referral/signatures/faq.py

from kaizen.signatures import Signature, InputField, OutputField
from typing import List, Dict


class FAQSignature(Signature):
    """Answer patient questions about the referral process."""

    __intent__ = "Provide helpful answers to patient questions about healthcare referrals"

    __guidelines__ = [
        "Answer questions clearly and concisely",
        "If the question is outside scope, explain limitations",
        "Offer to return to the booking process when ready",
        "Don't make medical recommendations - refer to specialists"
    ]

    # Inputs
    question: str = InputField(desc="Patient's question")
    current_context: Dict = InputField(
        desc="Current journey context for relevant answers"
    )

    # Outputs
    answer: str = OutputField(desc="Answer to the patient's question")
    question_resolved: bool = OutputField(
        desc="Whether the question is fully answered"
    )
    response: str = OutputField(
        desc="Full response including answer and offer to continue"
    )
```

```python
# File: examples/journey/healthcare_referral/signatures/persuasion.py

from kaizen.signatures import Signature, InputField, OutputField
from typing import List, Dict, Optional


class PersuasionSignature(Signature):
    """Address hesitation and highlight booking benefits."""

    __intent__ = "Help hesitant patients feel confident about booking their appointment"

    __guidelines__ = [
        "Acknowledge the patient's hesitation or concern",
        "Don't be pushy - respect their decision",
        "Highlight specific benefits relevant to their symptoms",
        "Address common concerns (cost, time commitment, etc.)",
        "Offer specific next steps if they want to proceed"
    ]

    # Inputs
    patient_message: str = InputField(desc="Patient's hesitant message")
    symptoms: List[str] = InputField(desc="Patient symptoms for relevance")
    hesitation_reason: Optional[str] = InputField(
        desc="Identified reason for hesitation"
    )

    # Outputs
    response: str = OutputField(desc="Empathetic response addressing concerns")
    concerns_addressed: List[str] = OutputField(
        desc="List of concerns addressed in response"
    )
    ready_to_proceed: bool = OutputField(
        desc="Whether patient indicates readiness to continue"
    )
```

```python
# File: examples/journey/healthcare_referral/signatures/confirmation.py

from kaizen.signatures import Signature, InputField, OutputField
from typing import Dict, Optional


class ConfirmationSignature(Signature):
    """Confirm and finalize the appointment booking."""

    __intent__ = "Provide clear appointment confirmation with all necessary details"

    __guidelines__ = [
        "Summarize all booking details clearly",
        "Include date, time, doctor name, location/telehealth link",
        "Mention what to bring or prepare",
        "Provide cancellation/rescheduling information",
        "End with a warm, reassuring message"
    ]

    # Inputs
    doctor: Dict = InputField(desc="Selected doctor details")
    slot: str = InputField(desc="Selected appointment slot")
    patient_info: Dict = InputField(desc="Patient information collected")

    # Outputs
    confirmation_number: str = OutputField(desc="Generated confirmation number")
    confirmation_summary: str = OutputField(desc="Full confirmation details")
    preparation_instructions: str = OutputField(desc="What to prepare/bring")
    response: str = OutputField(desc="Complete confirmation message to patient")
```

### Journey Definition

```python
# File: examples/journey/healthcare_referral/journey.py

from kaizen.journey import (
    Journey,
    Pathway,
    Transition,
    IntentTrigger,
    ConditionTrigger,
    JourneyConfig,
    ReturnToPrevious,
)

from .signatures.intake import IntakeSignature
from .signatures.booking import BookingSignature
from .signatures.faq import FAQSignature
from .signatures.persuasion import PersuasionSignature
from .signatures.confirmation import ConfirmationSignature


class HealthcareReferralJourney(Journey):
    """
    Healthcare specialist referral journey.

    Guides patients through:
    1. Intake - Collecting symptoms and preferences
    2. Booking - Finding and selecting a doctor
    3. Confirmation - Finalizing the appointment

    With detour pathways for:
    - FAQ - Answering questions (returns to previous)
    - Persuasion - Addressing hesitation
    """

    __entry_pathway__ = "intake"

    __transitions__ = [
        # Global FAQ transition - triggers from any pathway
        Transition(
            trigger=IntentTrigger(
                intents=["faq", "question", "help", "what_is", "how_does"],
                description="User has a question about the process"
            ),
            to_pathway="faq",
            preserve_context=True
        ),

        # Hesitation detection - triggers during booking
        Transition(
            trigger=IntentTrigger(
                intents=["hesitation", "unsure", "maybe_later", "not_sure"],
                description="User is hesitant about proceeding"
            ),
            to_pathway="persuasion",
            preserve_context=True,
            from_pathways=["booking"]  # Only from booking
        ),

        # Cancellation request
        Transition(
            trigger=IntentTrigger(
                intents=["cancel", "stop", "nevermind"],
                description="User wants to cancel the process"
            ),
            to_pathway=None,  # End journey
            preserve_context=False
        ),
    ]

    # ─────────────────────────────────────────────────────────
    # INTAKE PATHWAY
    # ─────────────────────────────────────────────────────────
    class IntakePath(Pathway):
        """Collect patient symptoms and preferences."""

        __signature__ = IntakeSignature
        __agents__ = ["intake_agent"]
        __pipeline__ = "sequential"

        # Accumulate these fields for later pathways
        __accumulate__ = ["symptoms", "severity", "preferences", "insurance_info"]

        # Pathway-specific guidelines (merged with signature)
        __guidelines__ = [
            "If patient provides minimal info, ask clarifying questions",
            "Proceed to booking only when ready_for_booking is True"
        ]

        # Transition to booking when ready
        __next__ = "booking"

    # ─────────────────────────────────────────────────────────
    # BOOKING PATHWAY
    # ─────────────────────────────────────────────────────────
    class BookingPath(Pathway):
        """Present doctor options and handle selection."""

        __signature__ = BookingSignature
        __agents__ = ["booking_agent"]
        __pipeline__ = "sequential"

        # Track rejected doctors across turns
        __accumulate__ = ["rejected_doctors", "selected_doctor", "selected_slot"]

        __guidelines__ = [
            "Filter out rejected doctors from suggestions",
            "Present at most 3 options per turn"
        ]

        # Transition to confirmation when complete
        __next__ = "confirmation"

    # ─────────────────────────────────────────────────────────
    # FAQ PATHWAY (Detour)
    # ─────────────────────────────────────────────────────────
    class FAQPath(Pathway):
        """Answer patient questions."""

        __signature__ = FAQSignature
        __agents__ = ["faq_agent"]
        __pipeline__ = "sequential"

        # Return to previous pathway after answering
        __return_behavior__ = ReturnToPrevious(
            preserve_context=True,
            max_depth=3
        )

        __guidelines__ = [
            "After answering, offer to return to booking process"
        ]

    # ─────────────────────────────────────────────────────────
    # PERSUASION PATHWAY
    # ─────────────────────────────────────────────────────────
    class PersuasionPath(Pathway):
        """Address hesitation and encourage booking."""

        __signature__ = PersuasionSignature
        __agents__ = ["persuasion_agent"]
        __pipeline__ = "sequential"

        __guidelines__ = [
            "Be empathetic, not pushy",
            "Acknowledge their concerns before addressing them"
        ]

        # Return to booking after addressing concerns
        __next__ = "booking"

    # ─────────────────────────────────────────────────────────
    # CONFIRMATION PATHWAY
    # ─────────────────────────────────────────────────────────
    class ConfirmationPath(Pathway):
        """Confirm the booking."""

        __signature__ = ConfirmationSignature
        __agents__ = ["confirmation_agent"]
        __pipeline__ = "sequential"

        # Terminal pathway - no __next__


# ─────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────

default_config = JourneyConfig(
    # Intent detection
    intent_detection_model="gpt-4o-mini",
    intent_confidence_threshold=0.75,
    intent_cache_ttl_seconds=300,

    # Pathway execution
    max_pathway_depth=15,
    pathway_timeout_seconds=60.0,

    # Context
    max_context_size_bytes=1024 * 512,  # 512KB
    context_persistence="dataflow",

    # Error handling
    error_recovery="graceful",
    max_retries=3
)
```

### Agents

```python
# File: examples/journey/healthcare_referral/agents/intake_agent.py

from dataclasses import dataclass
from kaizen.core.base_agent import BaseAgent

from ..signatures.intake import IntakeSignature


@dataclass
class IntakeAgentConfig:
    llm_provider: str = "openai"
    model: str = "gpt-4o"
    temperature: float = 0.7


class IntakeAgent(BaseAgent):
    """Agent for patient intake."""

    def __init__(self, config: IntakeAgentConfig = None):
        config = config or IntakeAgentConfig()
        super().__init__(
            config=config,
            signature=IntakeSignature()
        )

    async def process_intake(
        self,
        patient_message: str,
        conversation_history: list = None
    ) -> dict:
        """Process patient message during intake."""
        return await self.run_async(
            patient_message=patient_message,
            conversation_history=conversation_history or []
        )
```

```python
# File: examples/journey/healthcare_referral/agents/booking_agent.py

from dataclasses import dataclass
from typing import List, Dict
from kaizen.core.base_agent import BaseAgent

from ..signatures.booking import BookingSignature


@dataclass
class BookingAgentConfig:
    llm_provider: str = "openai"
    model: str = "gpt-4o"
    temperature: float = 0.7


class BookingAgent(BaseAgent):
    """Agent for doctor booking."""

    def __init__(
        self,
        config: BookingAgentConfig = None,
        doctor_database: "DoctorDatabase" = None
    ):
        config = config or BookingAgentConfig()
        super().__init__(
            config=config,
            signature=BookingSignature()
        )
        self.doctor_db = doctor_database

    async def find_doctors(
        self,
        patient_message: str,
        symptoms: List[str],
        preferences: Dict,
        rejected_doctors: List[str] = None
    ) -> dict:
        """Find matching doctors and present options."""
        # Get available doctors (excluding rejected)
        available = await self._get_available_doctors(
            symptoms,
            preferences,
            rejected_doctors or []
        )

        return await self.run_async(
            patient_message=patient_message,
            symptoms=symptoms,
            preferences=preferences,
            rejected_doctors=rejected_doctors or [],
            available_doctors=available  # Passed as context
        )

    async def _get_available_doctors(
        self,
        symptoms: List[str],
        preferences: Dict,
        rejected: List[str]
    ) -> List[Dict]:
        """Query doctor database for matching specialists."""
        if self.doctor_db:
            return await self.doctor_db.find_specialists(
                symptoms=symptoms,
                preferences=preferences,
                exclude_ids=rejected
            )
        return []  # Mock data would be used in tests
```

### Usage Example

```python
# File: examples/journey/healthcare_referral/main.py

import asyncio
from dataflow import DataFlow

from .journey import HealthcareReferralJourney, default_config
from .agents.intake_agent import IntakeAgent, IntakeAgentConfig
from .agents.booking_agent import BookingAgent, BookingAgentConfig
from .agents.faq_agent import FAQAgent, FAQAgentConfig
from .agents.persuasion_agent import PersuasionAgent, PersuasionAgentConfig


async def main():
    # Initialize DataFlow for persistence
    db = DataFlow("postgresql://...", auto_migrate=False)
    await db.create_tables_async()

    # Create agents
    intake_agent = IntakeAgent(IntakeAgentConfig())
    booking_agent = BookingAgent(BookingAgentConfig())
    faq_agent = FAQAgent(FAQAgentConfig())
    persuasion_agent = PersuasionAgent(PersuasionAgentConfig())

    # Create journey instance
    journey = HealthcareReferralJourney(
        session_id="patient-12345",
        config=default_config
    )

    # Register agents
    journey.manager.register_agent("intake_agent", intake_agent)
    journey.manager.register_agent("booking_agent", booking_agent)
    journey.manager.register_agent("faq_agent", faq_agent)
    journey.manager.register_agent("persuasion_agent", persuasion_agent)

    # Start session
    session = await journey.start()
    print(f"Started journey at pathway: {session.current_pathway_id}")

    # Simulate conversation
    messages = [
        "I've been having back pain for a few weeks now",
        "It's moderate, worse in the mornings. I prefer a female doctor if possible.",
        "Yes, I have Blue Cross insurance",
        "What are my options?",
        # Intent: booking → presents doctors
        "Actually, what's the difference between an orthopedist and a chiropractor?",
        # Intent: faq → answers question → returns to booking
        "Thanks! I'll go with Dr. Smith",
        "Hmm, actually I'm not sure if I want to do this right now...",
        # Intent: hesitation → persuasion pathway
        "You're right, I should take care of this. Let's book Dr. Smith.",
        "Confirm the appointment please",
    ]

    for message in messages:
        print(f"\n👤 Patient: {message}")
        response = await journey.process_message(message)
        print(f"🤖 Assistant: {response.message}")
        print(f"   [Pathway: {response.pathway_id}]")
        if response.pathway_changed:
            print(f"   [Transitioned!]")

    # Show accumulated context
    session = await journey.manager.get_session_state()
    print(f"\n📋 Accumulated Context:")
    for key, value in session.accumulated_context.items():
        print(f"   {key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())
```

## Test Scenarios

### Unit Tests

```python
# File: examples/journey/healthcare_referral/tests/test_journey.py

import pytest
from ..journey import HealthcareReferralJourney, default_config


class TestJourneyDefinition:
    """Test journey class definition."""

    def test_journey_has_correct_pathways(self):
        assert "intake" in HealthcareReferralJourney._pathways
        assert "booking" in HealthcareReferralJourney._pathways
        assert "faq" in HealthcareReferralJourney._pathways
        assert "persuasion" in HealthcareReferralJourney._pathways
        assert "confirmation" in HealthcareReferralJourney._pathways

    def test_entry_pathway_is_intake(self):
        assert HealthcareReferralJourney._entry_pathway == "intake"

    def test_has_global_transitions(self):
        transitions = HealthcareReferralJourney._transitions
        assert len(transitions) >= 3  # FAQ, hesitation, cancel


class TestPathwayConfiguration:
    """Test pathway configurations."""

    def test_intake_accumulates_symptoms(self):
        intake = HealthcareReferralJourney.IntakePath
        assert "symptoms" in intake._accumulate
        assert "preferences" in intake._accumulate

    def test_booking_accumulates_rejected_doctors(self):
        booking = HealthcareReferralJourney.BookingPath
        assert "rejected_doctors" in booking._accumulate

    def test_faq_has_return_behavior(self):
        faq = HealthcareReferralJourney.FAQPath
        assert faq._return_behavior is not None

    def test_confirmation_is_terminal(self):
        confirmation = HealthcareReferralJourney.ConfirmationPath
        assert confirmation._next is None
```

### Transition Tests

```python
# File: examples/journey/healthcare_referral/tests/test_transitions.py

import pytest
from kaizen.journey import IntentDetector, JourneyConfig

from ..journey import HealthcareReferralJourney


@pytest.fixture
def intent_detector():
    config = JourneyConfig(
        intent_detection_model="gpt-4o-mini",
        intent_confidence_threshold=0.7
    )
    return IntentDetector(config)


class TestFAQTransition:
    """Test FAQ intent detection and transition."""

    @pytest.mark.asyncio
    async def test_question_triggers_faq(self, intent_detector):
        messages = [
            "What is a specialist?",
            "How does insurance work?",
            "Can you explain the process?"
        ]

        for msg in messages:
            result = await intent_detector.detect(msg, {})
            assert result.intent in ["faq", "question", "help", "what_is"]
            assert result.confidence >= 0.7

    @pytest.mark.asyncio
    async def test_booking_message_does_not_trigger_faq(self, intent_detector):
        messages = [
            "I'll take the 3pm slot",
            "Book me with Dr. Smith",
            "Not Dr. Jones, anyone else"
        ]

        for msg in messages:
            result = await intent_detector.detect(msg, {})
            # Should NOT match FAQ intents
            assert result.intent not in ["faq", "question", "help"]


class TestHesitationTransition:
    """Test hesitation detection."""

    @pytest.mark.asyncio
    async def test_hesitation_detected(self, intent_detector):
        messages = [
            "I'm not sure about this",
            "Maybe I should wait",
            "Let me think about it"
        ]

        for msg in messages:
            result = await intent_detector.detect(msg, {})
            assert result.intent in ["hesitation", "unsure", "maybe_later"]


class TestReturnBehavior:
    """Test return to previous pathway."""

    @pytest.mark.asyncio
    async def test_faq_returns_to_booking(self, mock_agents):
        journey = HealthcareReferralJourney("test-session", default_config)

        # Register mock agents
        for agent_id, agent in mock_agents.items():
            journey.manager.register_agent(agent_id, agent)

        await journey.start()

        # Advance to booking
        await journey.process_message("I have back pain, moderate severity")
        assert journey.manager._session.current_pathway_id == "booking"

        # Trigger FAQ
        await journey.process_message("What's the difference between specialists?")
        assert journey.manager._session.current_pathway_id == "faq"

        # Answer returns to booking
        await journey.process_message("Thanks, that helps!")
        assert journey.manager._session.current_pathway_id == "booking"
```

### Integration Tests

```python
# File: examples/journey/healthcare_referral/tests/test_integration.py

import pytest
from dataflow import DataFlow

from ..journey import HealthcareReferralJourney, default_config
from ..agents.intake_agent import IntakeAgent
from ..agents.booking_agent import BookingAgent


@pytest.fixture
async def dataflow_db():
    """Create test database."""
    db = DataFlow("sqlite:///:memory:", auto_migrate=True)
    yield db
    await db.close_async()


@pytest.fixture
def real_agents():
    """Create real agents with Ollama."""
    return {
        "intake_agent": IntakeAgent(IntakeAgentConfig(
            llm_provider="ollama",
            model="llama3.2:3b"
        )),
        "booking_agent": BookingAgent(BookingAgentConfig(
            llm_provider="ollama",
            model="llama3.2:3b"
        ))
    }


class TestJourneyIntegration:
    """Integration tests with real LLM (Ollama)."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_intake_flow(self, real_agents):
        """Test complete intake conversation."""
        config = JourneyConfig(
            intent_detection_model="ollama/llama3.2:3b",
            context_persistence="memory"
        )

        journey = HealthcareReferralJourney("test-session", config)

        for agent_id, agent in real_agents.items():
            journey.manager.register_agent(agent_id, agent)

        await journey.start()

        # Initial symptom description
        response = await journey.process_message(
            "I've been having severe headaches for a week"
        )
        assert response.pathway_id == "intake"
        assert "headache" in str(response.accumulated_context).lower()

        # Add preferences
        response = await journey.process_message(
            "I prefer morning appointments and have Aetna insurance"
        )
        assert "preferences" in response.accumulated_context

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_rejected_doctors_accumulate(self, real_agents, dataflow_db):
        """Test that rejected doctors are tracked across turns."""
        config = JourneyConfig(
            context_persistence="dataflow"
        )

        journey = HealthcareReferralJourney("test-session", config)

        # Setup with DataFlow backend
        from kaizen.journey.state import DataFlowStateBackend
        journey.manager._state_manager.set_backend(
            DataFlowStateBackend(dataflow_db)
        )

        for agent_id, agent in real_agents.items():
            journey.manager.register_agent(agent_id, agent)

        await journey.start()

        # Skip to booking
        journey.manager._session.current_pathway_id = "booking"
        journey.manager._session.accumulated_context = {
            "symptoms": ["back pain"],
            "preferences": {"time": "morning"}
        }

        # Reject first doctor
        response = await journey.process_message(
            "Not Dr. Smith, I've heard mixed reviews"
        )

        # Reject second doctor
        response = await journey.process_message(
            "Dr. Jones doesn't work either, different location please"
        )

        # Verify accumulation
        rejected = response.accumulated_context.get("rejected_doctors", [])
        assert len(rejected) >= 2
```

### E2E Tests

```python
# File: examples/journey/healthcare_referral/tests/test_e2e.py

import pytest

from ..journey import HealthcareReferralJourney, default_config
from ..agents.intake_agent import IntakeAgent, IntakeAgentConfig
from ..agents.booking_agent import BookingAgent, BookingAgentConfig
from ..agents.faq_agent import FAQAgent, FAQAgentConfig
from ..agents.persuasion_agent import PersuasionAgent, PersuasionAgentConfig


class TestE2EJourney:
    """End-to-end tests with real OpenAI."""

    @pytest.fixture
    def openai_agents(self):
        """Create agents with OpenAI."""
        return {
            "intake_agent": IntakeAgent(IntakeAgentConfig(
                llm_provider="openai",
                model="gpt-4o"
            )),
            "booking_agent": BookingAgent(BookingAgentConfig(
                llm_provider="openai",
                model="gpt-4o"
            )),
            "faq_agent": FAQAgent(FAQAgentConfig(
                llm_provider="openai",
                model="gpt-4o"
            )),
            "persuasion_agent": PersuasionAgent(PersuasionAgentConfig(
                llm_provider="openai",
                model="gpt-4o"
            ))
        }

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_complete_booking_journey(self, openai_agents):
        """Test complete journey from intake to confirmation."""
        journey = HealthcareReferralJourney("e2e-test", default_config)

        for agent_id, agent in openai_agents.items():
            journey.manager.register_agent(agent_id, agent)

        await journey.start()

        # Intake
        r1 = await journey.process_message(
            "I need to see a specialist for chronic back pain"
        )
        assert r1.pathway_id == "intake"

        r2 = await journey.process_message(
            "It's been going on for 3 months, moderate pain. "
            "I prefer morning appointments with a female doctor."
        )

        # Should advance to booking
        r3 = await journey.process_message(
            "Yes, that's everything. I have Blue Cross."
        )
        assert r3.pathway_id == "booking"

        # FAQ detour
        r4 = await journey.process_message(
            "Quick question - what's the difference between an orthopedist "
            "and a physical therapist?"
        )
        assert r4.pathway_id == "faq"

        # Return to booking
        r5 = await journey.process_message("Got it, thanks!")
        assert r5.pathway_id == "booking"

        # Select doctor
        r6 = await journey.process_message(
            "I'll go with the first option, Dr. Chen"
        )

        # Confirmation
        r7 = await journey.process_message("Yes, confirm the appointment")
        assert r7.pathway_id == "confirmation"

        # Verify accumulated context
        session = await journey.manager.get_session_state()
        assert "symptoms" in session.accumulated_context
        assert "selected_doctor" in session.accumulated_context
```

## Implementation Tasks

| Task | Effort | Dependencies |
|------|--------|--------------|
| Create file structure | 0.25 day | None |
| Implement signatures (5) | 1 day | Layer 2 enhancements |
| Implement journey definition | 0.5 day | Journey core |
| Implement intake agent | 0.5 day | Signatures |
| Implement booking agent | 0.5 day | Signatures |
| Implement FAQ agent | 0.25 day | Signatures |
| Implement persuasion agent | 0.25 day | Signatures |
| Unit tests | 0.5 day | All implementation |
| Integration tests (Ollama) | 0.5 day | Unit tests |
| E2E tests (OpenAI) | 0.5 day | Integration tests |
| README documentation | 0.25 day | All tests passing |

## Success Criteria

1. **Functional**: Complete conversation flow from intake to confirmation
2. **Transitions**: FAQ detour works from any pathway and returns correctly
3. **Accumulation**: Rejected doctors tracked and excluded from suggestions
4. **Persistence**: Session survives restart with DataFlow backend
5. **Performance**: Intent detection < 500ms with caching
6. **Tests**: 100% coverage, all tiers passing
