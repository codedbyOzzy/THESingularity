# Intelligence Stones — Installation & Integration Guide

> This guide helps developers integrate VIGIL Stones, THE ARC, ORACLE, SPECTRE, and ARCHIVE systems into their own AI assistant projects.

> **Requirements:** Python 3.9+, zero external dependencies.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Installation](#2-installation)
3. [Integration Architecture](#3-integration-architecture)
4. [Step-by-Step Integration](#4-step-by-step-integration)
5. [Detailed Module Usage](#5-detailed-module-usage)
6. [Combined Usage Example](#6-combined-usage-example)
7. [Full Query Cycle Diagram](#7-full-query-cycle-diagram)
8. [API Reference](#8-api-reference)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. System Overview

These systems form the **awareness layers** of an AI assistant:

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 0 — ORACLE (Intelligent Model Router)                     │
│  → Which model to use? gpt-4.1-mini / gemini / groq            │
│    Complexity × Depth × Urgency × Repetition routing            │
├─────────────────────────────────────────────────────────────────┤
│  Layer 0 — SPECTRE (Proactive Context Synthesizer)             │
│  → What will the user ask next?                                │
│    Inference + Trajectory + Persona prediction fusion            │
├─────────────────────────────────────────────────────────────────┤
│  Layer 0 — ARCHIVE (Longitudinal Memory)                        │
│  → How does FRIDAY remember long-term?                          │
│    Medium/Long-term context, emotional profile, patience level    │
├─────────────────────────────────────────────────────────────────┤
│  Layer 1 — Narrative (THE ARC)                                   │
│  → Where has this conversation been?                            │
│    Decisions made, topics explored, ghost threads, growth        │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2 — User State (TideStone)                                │
│  → How does the user feel right now?                             │
│    Energy, pace, focus                                          │
├─────────────────────────────────────────────────────────────────┤
│  Layer 3 — Goals (CompassStone)                                  │
│  → What are the user's goals? Progress made?                     │
├─────────────────────────────────────────────────────────────────┤
│  Layer 4 — Recurrence (EmberStone)                               │
│  → Which topics keep coming back?                                │
│    Hot topics, unresolved threads                                │
├─────────────────────────────────────────────────────────────────┤
│  Layer 5 — Self-Awareness (MirrorStone)                          │
│  → How confident is the assistant on this topic?                  │
│    Hedge detection, uncertainty flagging                          │
└─────────────────────────────────────────────────────────────────┘
```

### Module Purpose

| Module | Purpose |
|--------|---------|
| **ORACLE** | Intelligent Model Router — selects best LLM per query |
| **SPECTRE** | Proactive Predictor — predicts next user questions |
| **ARCHIVE** | Longitudinal Memory — medium/long-term context + emotional profile |
| **THE ARC** | Long-Term Narrative Tracker — decisions, ghost threads, growth |
| **TideStone** | Real-Time User State Reader — energy/pace/focus |
| **CompassStone** | Multi-Turn Goal Tracker — goal progress |
| **EmberStone** | Recurring Topic Heat Tracker — hot topics |
| **MirrorStone** | Self-Confidence Tracker — hedge detection |

---

## 2. Installation

### 2.1 Copy Files to Your Project

All modules in a single folder. Recommended structure:

```
my_ai_project/
├── intelligence_stones/    # ← New folder
│   ├── oracle.py
│   ├── spectre.py
│   ├── archive.py
│   ├── the_arc.py
│   ├── tide_stone.py
│   ├── compass_stone.py
│   ├── ember_stone.py
│   ├── mirror_stone.py
│   └── signals_vigil.py    # (optional)
├── your_assistant.py        # ← Your assistant file
├── system_prompt.py
└── main.py
```

### 2.2 Files to Copy

All files from the `Github/` folder:

- `oracle.py` — ORACLE Intelligent Model Router
- `spectre.py` — SPECTRE Proactive Context Synthesizer
- `archive.py` — ARCHIVE Longitudinal Memory
- `the_arc.py` — THE ARC Long-Term Narrative Tracker
- `tide_stone.py` — TideStone Real-Time User State
- `compass_stone.py` — CompassStone Goal Tracker
- `ember_stone.py` — EmberStone Recurring Topic Tracker
- `mirror_stone.py` — MirrorStone Self-Confidence Tracker
- `signals_vigil.py` — Signal sets (EN + TR)
- `example.py` — Usage examples

### 2.3 Zero Dependencies

These modules use **only the Python standard library**. No `requirements.txt` needed.

```bash
# Nothing to install
pip install  # Can be left empty
```

---

## 3. Integration Architecture

### 3.1 Query Cycle Concept

Each module activates at two points:

```
User Message
       │
       ▼
┌──────────────────┐
│  OBSERVE          │  ← Called on every message
│  (absorb/observe) │
└──────────────────┘
       │
       ▼
  ┌─────────┐
  │   LLM   │  ← Assistant generates response
  └─────────┘
       │
       ▼
┌──────────────────┐
│  OBSERVE          │  ← Called on every response
│  (absorb/observe) │
└──────────────────┘
       │
       ▼
┌──────────────────┐
│  CONSULT          │  ← Called BEFORE next LLM call
│  (consult/directive)│  Add all context to system prompt
└──────────────────┘
```

### 3.2 When Each Module Is Called

| Module | Observe Time | Consult Time |
|--------|--------------|--------------|
| **ORACLE** | — | Before LLM call (model selection) |
| **SPECTRE** | After response | Before LLM call (predictions) |
| **ARCHIVE** | After response | Before LLM call (query) |
| **THE ARC** | Every turn end | Before LLM call |
| **TideStone** | Every user message | Before LLM call |
| **CompassStone** | Every turn end | Before LLM call |
| **EmberStone** | Every turn end | Before LLM call |
| **MirrorStone** | After every assistant response | Before LLM call |

---

## 4. Step-by-Step Integration

### Step 1 — Import Modules

```python
# If using a subfolder:
from intelligence_stones.oracle import Oracle, ModelChoice, ComplexityLevel
from intelligence_stones.spectre import Spectre, SpectrePrediction
from intelligence_stones.archive import Archive, MemoryTier
from intelligence_stones.the_arc import TheArc, TurnRecord
from intelligence_stones.tide_stone import TideStone
from intelligence_stones.compass_stone import CompassStone
from intelligence_stones.ember_stone import EmberStone
from intelligence_stones.mirror_stone import MirrorStone

# If files are in root folder:
from oracle import Oracle, ModelChoice, ComplexityLevel
from spectre import Spectre, SpectrePrediction
from archive import Archive, MemoryTier
from the_arc import TheArc, TurnRecord
from tide_stone import TideStone
from compass_stone import CompassStone
from ember_stone import EmberStone
from mirror_stone import MirrorStone

import time
```

### Step 2 — Initialize Modules

In your assistant's `__init__` or initialization section:

```python
class MyAssistant:
    def __init__(self):
        # ORACLE — Intelligent Model Router
        self.oracle = Oracle()

        # THE ARC — Long-Term Narrative Tracker
        self.arc = TheArc(path=".the_arc.json")

        # SPECTRE — Proactive Context Synthesizer
        self.spectre = Spectre(the_arc=self.arc)

        # ARCHIVE — Longitudinal Memory
        self.archive = Archive(the_arc=self.arc)

        # VIGIL Stones
        self.tide = TideStone()
        self.compass = CompassStone(path=".compass_stone.json")
        self.ember = EmberStone(path=".ember_stone.json")
        self.mirror = MirrorStone(path=".mirror_stone.json")

        self._turn_id = 0
        self._conversation_history = []  # For SPECTRE
```

### Step 3 — Observe (Collection)

Called on every conversation turn:

```python
def on_user_message(self, user_msg: str):
    self._turn_id += 1
    timestamp = time.time()

    # THE ARC — absorb user turn
    self.arc.absorb(TurnRecord(
        turn_id=self._turn_id,
        role="user",
        content=user_msg,
        timestamp=timestamp,
    ))

    # SPECTRE — learn from conversation
    self._conversation_history.append({
        "content": user_msg,
        "role": "user",
        "timestamp": timestamp,
    })

    # ARCHIVE — optional: record emotional signals
    self.archive.record_emotional_signal("patience", 0.5)

    # VIGIL — TideStone (user message only)
    self.tide.observe_user(user_msg)

    # VIGIL — CompassStone (goal tracking)
    self.compass.observe(user_msg, "")

    # VIGIL — EmberStone (hot topic tracking)
    self.ember.observe(user_msg, "")
```

### Step 4 — Observe After Assistant Response

```python
def on_assistant_response(self, user_msg: str, assistant_msg: str):
    self._turn_id += 1
    timestamp = time.time()

    # THE ARC — absorb assistant turn
    self.arc.absorb(TurnRecord(
        turn_id=self._turn_id,
        role="assistant",
        content=assistant_msg,
        timestamp=timestamp,
    ))

    # SPECTRE — learn from full conversation
    self._conversation_history.append({
        "content": assistant_msg,
        "role": "assistant",
        "timestamp": timestamp,
    })
    self.spectre.learn_from_conversation(self._conversation_history)

    # ARCHIVE — absorb THE ARC episodes
    self.archive.run_upgrade_cycle()

    # VIGIL — CompassStone (user + assistant)
    self.compass.observe(user_msg, assistant_msg)

    # VIGIL — EmberStone (user + assistant)
    self.ember.observe(user_msg, assistant_msg)

    # VIGIL — MirrorStone (assistant response)
    self.mirror.observe(user_msg, assistant_msg)
```

### Step 5 — Build System Prompt (Consult)

Before every LLM call:

```python
def build_system_prompt(self, base_prompt: str, user_msg: str) -> str:
    additions = []

    # ORACLE — Model selection
    decision = self.oracle.get_best_available_model(user_msg)
    model_name = decision.primary_model.value.split(":")[1]  # e.g., "gpt-4.1-mini"
    print(f"[ORACLE] Routing: {model_name} ({decision.complexity.value}) — {decision.reasoning}")

    # SPECTRE — Proactive predictions
    if self._conversation_history:
        predictions = self.spectre.predict_next(self._conversation_history, max_predictions=2)
        if predictions:
            proactive = self.spectre.get_proactive_prompt(predictions)
            additions.append(proactive)

    # ARCHIVE — Longitudinal context
    archive_ctx = self.archive.query(user_msg, depth="all")
    if archive_ctx:
        additions.append(archive_ctx)

    # THE ARC — Narrative context
    if ctx := self.arc.consult(user_msg):
        additions.append(ctx)

    # VIGIL — User state
    if d := self.tide.get_state_directive():
        additions.append(d)

    # VIGIL — Goals
    if d := self.compass.get_goal_directive():
        additions.append(d)

    # VIGIL — Hot topics
    if ctx := self.ember.get_active_context():
        additions.append(ctx)

    # VIGIL — Assistant confidence
    if d := self.mirror.get_mirror_directive(user_msg):
        additions.append(d)

    if additions:
        return base_prompt + "\n\n" + "\n\n".join(additions)
    return base_prompt
```

### Step 6 — LLM Call

```python
def chat(self, user_msg: str, llm_call_fn) -> str:
    # 1. Observe (user message)
    self.on_user_message(user_msg)

    # 2. Build system prompt
    enhanced_prompt = self.build_system_prompt(
        base_prompt="You are a helpful AI assistant.",
        user_msg=user_msg,
    )

    # 3. Get ORACLE's model decision
    decision = self.oracle.get_best_available_model(user_msg)
    model_name = decision.primary_model.value.split(":")[1]

    # 4. Call LLM (your own function with model selection)
    response = llm_call_fn(enhanced_prompt, user_msg, model=model_name)

    # 5. Observe (assistant response)
    self.on_assistant_response(user_msg, response)

    # 6. Record ORACLE outcome
    self.oracle.record_outcome(decision, user_satisfaction=0.8)

    return response
```

---

## 5. Detailed Module Usage

### 5.1 ORACLE — Intelligent Model Router

ORACLE analyzes each query and selects the best LLM model:

```python
from oracle import Oracle, ModelChoice, ComplexityLevel

oracle = Oracle()

# Simple routing
decision = oracle.route("What is Python?")
print(f"Model: {decision.primary_model.value}")  # openai:gpt-4.1-mini
print(f"Complexity: {decision.complexity.value}")  # trivial
print(f"Reasoning: {decision.reasoning}")

# Circuit-breaker aware routing
decision = oracle.get_best_available_model("Explain async Python")
print(f"Best available: {decision.primary_model.value}")

# Record outcome for learning
oracle.record_outcome(decision, user_satisfaction=0.9)

# Cost tracking
cost = oracle.get_cost_report()
print(f"Total tokens: {cost['total_tokens']}")
print(f"By model: {cost['by_model']}")

# Accuracy report
accuracy = oracle.get_accuracy_report()
print(f"Accuracy: {accuracy['accuracy_rate']}")
```

**ORACLE Routing Table:**

| Complexity | Primary Model | Fallback |
|------------|--------------|----------|
| TRIVIAL | gpt-4.1-mini | gpt-4.1-mini |
| SIMPLE | gpt-4.1-mini | gemini-2.5-flash |
| MODERATE | gemini-2.5-flash | gpt-4.1-mini |
| COMPLEX | gemini-2.5-flash | groq-llama |
| DEEP | groq-llama | gemini-2.5-flash |

**ORACLE Decision Signals:**
- **ComplexityStone (40%)**: word count, technical terms, code, questions
- **DepthStone (30%)**: expert terms, prerequisites, deep topics
- **UrgencyStone (10%)**: time-of-day, urgency phrases
- **RepetitionStone (20%)**: THE ARC episode history

### 5.2 SPECTRE — Proactive Context Synthesizer

SPECTRE predicts what the user will ask next:

```python
from spectre import Spectre, SpectrePrediction

spectre = Spectre(the_arc=arc)

# Predict next questions
history = [
    {"content": "I'm learning Python async", "role": "user", "timestamp": time.time()},
    {"content": "Async Python uses an event loop...", "role": "assistant", "timestamp": time.time()},
]
predictions = spectre.predict_next(history, max_predictions=3)

for p in predictions:
    print(f"Suggestion: {p.suggestion}")
    print(f"Confidence: {p.confidence:.2f}")
    print(f"Source: {p.source}")  # trajectory | inference | persona

# Get proactive prompt
prompt = spectre.get_proactive_prompt(predictions)
# "[SPECTRE] User may ask about:\n  - How does event loop work? (source: inference)"

# Record prediction outcome (for learning)
spectre.record_prediction_outcome("event loop", was_asked=True)

# Accuracy report
accuracy = spectre.get_accuracy_report()
print(f"Accuracy: {accuracy['accuracy_rate']}")
print(f"Most missed: {accuracy['most_missed_topics']}")

# Inference chain
chain = spectre.get_inference_chain("python")
print(f"Inference chain: {chain}")  # ["async", "flask", "django", ...]
```

**SPECTRE Prediction Sources:**
- **InferenceEngine**: Predefined rules linking concepts (python→async→await)
- **TrajectoryEngine**: Learned conversation flow patterns from THE ARC
- **PersonaEngine**: User's question style (detailed/concise/why-how focused)
- **FusionBrain**: Combines all three, deduplicates, ranks by confidence

### 5.3 ARCHIVE — Longitudinal Memory

ARCHIVE extends THE ARC into permanent memory layers:

```python
from archive import Archive, MemoryTier

archive = Archive(the_arc=arc)

# Record emotional signals
archive.record_emotional_signal("frustration", 0.9)  # High frustration → patience=low
archive.record_emotional_signal("energy", 0.8)  # Peak productivity hour tracking
archive.record_emotional_signal("satisfaction", 0.9)  # Positive outcome

# Query for context
context = archive.query("what was I working on 3 weeks ago?", depth="all")
print(f"Context length: {len(context)} chars")

# Query specific depth
short_ctx = archive.query("python", depth="short")    # THE ARC episodes
medium_ctx = archive.query("projects", depth="medium")  # 14-60 day projects
long_ctx = archive.query("tools", depth="long")        # 60+ day profile
emotional_ctx = archive.query("anything", depth="emotional")  # Emotional profile

# Get emotional prompt for system prompt
emotional_prompt = archive.get_emotional_prompt()
print(f"Emotional: {emotional_prompt}")
# "[ARCHIVE - User Profile]\nThis user prefers detailed responses..."
# "User is impatient — short and direct responses are appropriate."
# "Frustration triggers: late_night_coding, deployment_failures"

# Statistics
stats = archive.get_stats()
print(f"Medium entries: {stats['medium_term_entries']}")
print(f"Patience: {stats['patience_level']}")  # low | medium | high
print(f"Peak hours: {stats['peak_hours']}")    # [14, 15, 16]

# Decay (call periodically)
archive.decay_medium_term()

# Reset a specific tier
archive.reset_tier(MemoryTier.MEDIUM_TERM)
```

**Memory Tiers:**

| Tier | Duration | Content |
|------|----------|---------|
| SHORT_TERM | 0-14 days | THE ARC episodes |
| MEDIUM_TERM | 14-60 days | Active projects, learning progress |
| LONG_TERM | 60+ days | Occupation, tools stack, preferences |
| EMOTIONAL | Permanent | Communication style, triggers, patience |

### 5.4 THE ARC — Long-Term Narrative Tracker

THE ARC tracks conversation history as episodes:

```python
from the_arc import TheArc, TurnRecord

arc = TheArc(path=".the_arc.json")

# Absorb conversation turns
arc.absorb(TurnRecord(
    turn_id=1,
    role="user",
    content="I'm building a React Native app",
    timestamp=time.time(),
))

arc.absorb(TurnRecord(
    turn_id=2,
    role="assistant",
    content="Great choice! React Native uses JavaScript...",
    timestamp=time.time(),
))

# Consult for context
context = arc.consult("React Native")
if context:
    print(f"THE ARC: {context}")

# Decision context
decisions = arc.get_decision_context("React Native")
print(f"Past decisions: {decisions}")

# Statistics
stats = arc.get_stats()
print(f"Total episodes: {stats['total_episodes']}")
print(f"Active: {stats['active']}, Dormant: {stats['dormant']}")

# Run decay (call daily)
arc.run_decay()

# Reset
arc.reset()
```

**Signal Detection:** THE ARC automatically detects:
- **DECISION**: "I'll use", "I decided", "I'm going with"
- **PROGRESS**: "finished", "completed", "done"
- **REVISION**: "changed my mind", "actually not"
- **FRUSTRATION**: "can't figure out", "error", "stuck"
- **QUESTION**: Messages ending with "?"

### 5.5 TideStone — Real-Time User State

```python
from tide_stone import TideStone, TideState

tide = TideStone(min_turns=3)

# Observe user message
tide.observe_user("This is a long and detailed question about async Python...")

# Get current state
state = tide.get_state()
# state = None (insufficient data yet, needs min_turns=3 observations)
# state = TideState(energy="high", pace="measured", focus="sharp", turns=5)

if state:
    print(f"Energy: {state.energy}")  # high | medium | low
    print(f"Pace: {state.pace}")      # brisk | measured | relaxed
    print(f"Focus: {state.focus}")    # sharp | normal | scattered

# Get system prompt directive
directive = tide.get_state_directive()
# "" = normal / insufficient data
# "[TIDE] User is highly engaged — depth is appropriate."
```

### 5.6 CompassStone — Goal Tracking

```python
from compass_stone import CompassStone

compass = CompassStone(path=".compass_stone.json")

# Observe turn
compass.observe(
    user_text="I want to learn Rust this month",
    ai_text="Rust is great for systems programming!",
)

# Get active goals
goals = compass.get_active_goals()
for goal in goals:
    print(f"- {goal.text} ({goal.status})")

# System prompt directive
directive = compass.get_goal_directive()
# "[COMPASS] User goals:\n  - Learn Rust this month (active)"

# Reset session
compass.reset_session()
```

### 5.7 EmberStone — Recurring Topic Heat

```python
from ember_stone import EmberStone

ember = EmberStone(path=".ember_stone.json")

# Observe
ember.observe("I'm working on async Python", "Async is powerful...")

# Get active context
context = ember.get_active_context()
# "[EMBER] Recurring topics:\n  - async python [HOT, 3 mentions, 2d]"

# Get all embers
all_embers = ember.get_embers()
for e in all_embers:
    print(f"{e.key}: heat={e.heat:.2f}")
```

**Heat Cycle:**
```
Topic first mentioned     → HEAT = 0.30
Repeated mention           → HEAT += 0.15 (max 1.00)
5 days of silence          → HEAT -= 0.02/day
User says "done"           → HEAT -= 0.30 (resolved)
30 days of silence         → Archived (ghost thread)
```

### 5.8 MirrorStone — Self-Confidence

```python
from mirror_stone import MirrorStone

mirror = MirrorStone(path=".mirror_stone.json")

# Observe after assistant response
mirror.observe(
    user_text="How does async work?",
    ai_text="I think it uses an event loop... it might be based on coroutines...",
)

# Estimate confidence
result = mirror.estimate_confidence("async")
print(f"Confidence: {result.score:.2f}")  # 0.0 - 1.0
print(f"Flag: {result.flag}")            # low_data | confident | uncertain | low_confidence
print(f"Hedge: {result.hedge}")          # "i think", "might be", etc.

# Get directive if uncertain
if result.flag in ("uncertain", "low_confidence"):
    directive = mirror.get_mirror_directive("async")
    # "You're using hedging language (i think) — be more direct."
```

---

## 6. Combined Usage Example

Full chatbot integration:

```python
"""Intelligence Stones Integration with Your AI Assistant"""

import time
from oracle import Oracle, ModelChoice
from spectre import Spectre, SpectrePrediction
from archive import Archive
from the_arc import TheArc, TurnRecord
from tide_stone import TideStone
from compass_stone import CompassStone
from ember_stone import EmberStone
from mirror_stone import MirrorStone


class IntelligenceAssistant:
    """AI Assistant with all Intelligence Stones integrated."""

    def __init__(self, data_dir: str = "./data"):
        import os
        os.makedirs(data_dir, exist_ok=True)

        # Core systems
        self.oracle = Oracle()
        self.arc = TheArc(path=f"{data_dir}/the_arc.json")
        self.spectre = Spectre(the_arc=self.arc)
        self.archive = Archive(the_arc=self.arc)

        # VIGIL Stones
        self.tide = TideStone()
        self.compass = CompassStone(path=f"{data_dir}/compass_stone.json")
        self.ember = EmberStone(path=f"{data_dir}/ember_stone.json")
        self.mirror = MirrorStone(path=f"{data_dir}/mirror_stone.json")

        self._turn_id = 0
        self._conversation_history = []
        self.base_prompt = "You are a helpful AI assistant."

    # ── Observe (Collection) ─────────────────────────────────────────

    def _observe_user(self, user_msg: str) -> None:
        self._turn_id += 1
        ts = time.time()

        self.arc.absorb(TurnRecord(
            turn_id=self._turn_id,
            role="user",
            content=user_msg,
            timestamp=ts,
        ))
        self._conversation_history.append({"content": user_msg, "role": "user", "timestamp": ts})
        self.tide.observe_user(user_msg)
        self.compass.observe(user_msg, "")
        self.ember.observe(user_msg, "")

    def _observe_assistant(self, user_msg: str, assistant_msg: str) -> None:
        self._turn_id += 1
        ts = time.time()

        self.arc.absorb(TurnRecord(
            turn_id=self._turn_id,
            role="assistant",
            content=assistant_msg,
            timestamp=ts,
        ))
        self._conversation_history.append({"content": assistant_msg, "role": "assistant", "timestamp": ts})
        self.spectre.learn_from_conversation(self._conversation_history)
        self.archive.run_upgrade_cycle()
        self.compass.observe(user_msg, assistant_msg)
        self.ember.observe(user_msg, assistant_msg)
        self.mirror.observe(user_msg, assistant_msg)

    # ── Consult (System Prompt Building) ────────────────────────────

    def _consult(self, user_msg: str) -> str:
        additions = []

        # ORACLE — Model selection (print only, actual routing done in chat())
        decision = self.oracle.get_best_available_model(user_msg)
        print(f"[ORACLE] {decision.primary_model.value} ({decision.complexity.value}) — {decision.reasoning}")

        # SPECTRE — Proactive predictions
        if self._conversation_history:
            preds = self.spectre.predict_next(self._conversation_history, max_predictions=2)
            if preds:
                proactive = self.spectre.get_proactive_prompt(preds)
                additions.append(proactive)

        # ARCHIVE — Longitudinal context
        if archive_ctx := self.archive.query(user_msg, depth="all"):
            additions.append(archive_ctx)

        # THE ARC — Narrative context
        if ctx := self.arc.consult(user_msg):
            additions.append(ctx)

        # VIGIL
        if d := self.tide.get_state_directive():
            additions.append(d)
        if d := self.compass.get_goal_directive():
            additions.append(d)
        if ctx := self.ember.get_active_context():
            additions.append(ctx)
        if d := self.mirror.get_mirror_directive(user_msg):
            additions.append(d)

        if not additions:
            return self.base_prompt
        return self.base_prompt + "\n\n" + "\n\n".join(additions)

    # ── Main Loop ───────────────────────────────────────────────────

    def chat(self, user_msg: str, llm_call_fn) -> str:
        # 1. Observe user
        self._observe_user(user_msg)

        # 2. Build system prompt
        system_prompt = self._consult(user_msg)

        # 3. Get model from ORACLE
        decision = self.oracle.get_best_available_model(user_msg)
        model_name = decision.primary_model.value.split(":")[1]

        # 4. Call LLM
        response = llm_call_fn(system_prompt, user_msg, model=model_name)

        # 5. Observe assistant
        self._observe_assistant(user_msg, response)

        # 6. Record ORACLE outcome
        self.oracle.record_outcome(decision, user_satisfaction=0.8)

        return response


# ── Usage ───────────────────────────────────────────────────────

def my_llm_call(system_prompt: str, user_msg: str, model: str = "gpt-4.1-mini"):
    """Connect your own LLM here (OpenAI, Gemini, etc.)."""
    # return openai.ChatCompletion.create(model=model, messages=[...])
    return "[LLM response here]"
```

---

## 7. Full Query Cycle Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│  USER: "I'm learning async Python, it's not working"           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  OBSERVE (User Turn)                                            │
│                                                                  │
│  THE ARC      → absorb(TurnRecord)           [episode created]  │
│  SPECTRE      → learn_from_conversation()    [trajectory]       │
│  TideStone    → observe_user()               [energy=high]       │
│  CompassStone → observe()                   [goal: learn async]  │
│  EmberStone   → observe()                   [heat=0.30]          │
│  MirrorStone  → (not yet)                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  CONSULT (System Prompt)                                        │
│                                                                  │
│  ORACLE      → get_best_available_model() → gemini-2.5-flash   │
│  SPECTRE      → predict_next() → "How does event loop work?"   │
│  ARCHIVE      → query(depth="all") → medium_term context        │
│  THE ARC      → consult() → "User mentioned 'async python'..."  │
│  TideStone    → get_state_directive() → "User focus is sharp"  │
│  CompassStone → get_goal_directive() → "[COMPASS] goals..."    │
│  EmberStone   → get_active_context() → "[EMBER] topics..."     │
│  MirrorStone  → get_mirror_directive() → "" (insufficient data) │
│                                                                  │
│  System prompt += all of the above                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  LLM CALL                                                        │
│                                                                  │
│  Model: gemini-2.5-flash (selected by ORACLE)                   │
│  Response: "I think async Python uses an event loop..."        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  OBSERVE (Assistant Turn)                                       │
│                                                                  │
│  THE ARC      → absorb(TurnRecord)                             │
│  SPECTRE      → learn_from_conversation()                       │
│  ARCHIVE      → run_upgrade_cycle()                            │
│  CompassStone → observe(user, assistant)                        │
│  EmberStone   → observe(user, assistant)                       │
│  MirrorStone  → observe(user, assistant)  [HEDGE DETECTED!]     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. API Reference

### Oracle

```python
Oracle(the_arc=None, tide_stone=None, persistence_path=".oracle.json")

# Methods
oracle.route(user_input: str) -> RoutingDecision
oracle.get_best_available_model(user_input: str) -> RoutingDecision
oracle.record_outcome(decision: RoutingDecision, user_satisfaction: float) -> None
oracle.record_tokens(model: str, tokens: int) -> None
oracle.get_cost_report() -> dict
oracle.get_accuracy_report() -> dict
oracle.get_stats() -> dict
oracle.reset() -> None

# RoutingDecision
RoutingDecision.primary_model: ModelChoice  # GPT_MINI | GEMINI_FLASH | GROQ_LLAMA
RoutingDecision.fallback_model: ModelChoice
RoutingDecision.complexity: ComplexityLevel  # TRIVIAL | SIMPLE | MODERATE | COMPLEX | DEEP
RoutingDecision.reasoning: str
RoutingDecision.confidence: float
RoutingDecision.estimated_tokens: tuple[int, int]
```

### Spectre

```python
Spectre(the_arc=None, bond_stone=None, persistence_path=".spectre.json")

# Methods
spectre.predict_next(conversation_history: list[dict], max_predictions=3) -> list[SpectrePrediction]
spectre.learn_from_conversation(conversation: list[dict]) -> None
spectre.get_proactive_prompt(predictions: list[SpectrePrediction]) -> str
spectre.should_suggest(prediction: SpectrePrediction, answered_topics: list[str]) -> bool
spectre.record_prediction_outcome(predicted_topic: str, was_asked: bool, actual_question: str | None) -> None
spectre.get_inference_chain(topic: str) -> list[str]
spectre.suggest_follow_up_questions(current_topic: str, max_suggestions=3) -> list[str]
spectre.get_accuracy_report() -> dict
spectre.get_stats() -> dict
spectre.reset() -> None

# SpectrePrediction
SpectrePrediction.suggestion: str
SpectrePrediction.reason: str
SpectrePrediction.source: str  # trajectory | inference | persona
SpectrePrediction.confidence: float
```

### Archive

```python
Archive(the_arc=None, persistence_path=".archive.json")

# Methods
archive.absorb_episode(episode) -> None
archive.record_emotional_signal(signal_type: str, value: float) -> None
# signal_type: "frustration" | "satisfaction" | "patience" | "energy"
archive.query(query: str, depth="all") -> str
# depth: "short" | "medium" | "long" | "emotional" | "all"
archive.get_emotional_prompt() -> str
archive.run_upgrade_cycle() -> None
archive.decay_medium_term() -> None
archive.get_stats() -> dict
archive.summary() -> str
archive.reset_tier(tier: MemoryTier) -> None
archive.reset() -> None

# MemoryTier
MemoryTier.SHORT_TERM   # 0-14 days
MemoryTier.MEDIUM_TERM  # 14-60 days
MemoryTier.LONG_TERM    # 60+ days
MemoryTier.EMOTIONAL    # Permanent
```

### TheArc

```python
TheArc(path=".the_arc.json", decay_per_day=0.005, archive_after_days=30,
       dormant_threshold_days=7, max_episodes=500, max_turns_per_episode=50,
       ghost_threshold_days=30)

# Methods
arc.absorb(turn: TurnRecord) -> list[str]  # Episode IDs
arc.consult(query: str, top_k=3) -> str    # Directive or ""
arc.get_decision_context(query: str) -> str  # Decision summary or ""
arc.get_stats() -> dict
arc.run_decay() -> None
arc.summary() -> dict
arc.reset() -> None

# TurnRecord
TurnRecord(turn_id: int, role: str, content: str, timestamp: float)
# role: "user" | "assistant"
```

### TideStone

```python
TideStone(min_turns=3, max_window=12)

# Methods
tide.observe_user(user_text: str) -> None
tide.get_state() -> TideState | None
tide.get_state_directive() -> str  # "" = normal or insufficient data
tide.summary() -> dict
tide.reset() -> None

# TideState
TideState(energy: str, pace: str, focus: str, turns: int)
# energy: "high" | "medium" | "low"
# pace:   "brisk" | "measured" | "relaxed"
# focus:  "sharp" | "normal" | "scattered"
```

### CompassStone

```python
CompassStone(path=".compass_stone.json", save_every=5)

# Methods
compass.observe(user_text: str, ai_text: str = "") -> None
compass.observe_user(user_text: str) -> None
compass.get_goal_directive() -> str
compass.get_active_goals() -> list[Goal]
compass.get_stats() -> dict
compass.summary() -> dict
compass.reset_session() -> None  # Session goals only
compass.reset() -> None         # All goals

# Goal
Goal(id: str, text: str, created_at: float, updated_at: float,
     status: str, steps: list, step_statuses: list,
     priority: float, source: str, mentions: int)
# status: "active" | "completed" | "blocked" | "abandoned"
```

### EmberStone

```python
EmberStone(path=".ember_stone.json", active_threshold=0.25,
           heat_boost=0.15, decay_rate=0.02, save_every=5, max_embers=100)

# Methods
ember.observe(user_text: str, ai_text: str = "") -> None
ember.observe_user(user_text: str) -> None
ember.get_active_context() -> str    # Hot topics or ""
ember.get_embers() -> list[Ember]  # All embers
ember.get_stats() -> dict
ember.summary() -> dict
ember.reset() -> None

# Ember
Ember(key: str, heat: float, first_seen: float, last_seen: float,
      mentions: int, resolved: bool, samples: list[str])
```

### MirrorStone

```python
MirrorStone(path=".mirror_stone.json", save_every=10)

# Methods
mirror.observe(user_text: str, ai_text: str) -> None
mirror.estimate_confidence(query: str) -> ConfidenceResult
mirror.get_mirror_directive(query: str) -> str  # "" = confident
mirror.get_stats() -> dict
mirror.summary() -> dict
mirror.reset() -> None

# ConfidenceResult (NamedTuple)
ConfidenceResult(score: float, flag: str, hedge: str)
# score: 0.0 - 1.0
# flag:  "low_data" | "confident" | "uncertain" | "low_confidence"
# hedge: Detected hedge phrase or ""
```

---

## 9. Troubleshooting

### "ModuleNotFoundError: No module named 'oracle'"

Python can't find the module. Fix:

```python
import sys
sys.path.insert(0, "/path/to/intelligence_stones")
# or
from intelligence_stones.oracle import Oracle
```

### "TideStone.get_state() always returns None"

Normal behavior. Returns `None` until `min_turns` (default: 3) observations are collected. This prevents noise when insufficient data exists. Call `observe_user()` at least 3 times before expecting state.

### "THE ARC consult() always returns empty"

THE ARC uses Jaccard similarity to match queries to episodes. At least 20% word overlap between user message and episode topic is required. Very short messages ("ok", "thanks") normalize to empty and return "" — this is normal.

### "JSON files not being written to disk"

Check file write permissions. Ensure the directory exists:

```python
import os
os.makedirs("./data", exist_ok=True)
arc = TheArc(path="./data/the_arc.json")
```

### "MirrorStone hedge detection not working"

`observe()` requires both `user_text` AND `ai_text`. Call it **immediately after** the assistant response:

```python
mirror.observe(user_msg, assistant_response)  # Both required
```

### Memory leak suspicion

All modules have a `reset()` method. Call periodically:

```python
# Every 1000 turns or at session start
oracle.reset()
spectre.reset()
archive.reset()
arc.reset()
tide.reset()
compass.reset()
ember.reset()
mirror.reset()
```

### Periodic Maintenance

Run daily or at session start:

```python
import schedule

def daily_maintenance():
    arc.run_decay()        # THE ARC temperature decay
    archive.decay_medium_term()  # ARCHIVE cleanup

schedule.every().day.do(daily_maintenance)
```

---

## File Structure (Github Folder)

```
Github/
├── oracle.py              ORACLE — Intelligent Model Router (v1.0)
├── spectre.py             SPECTRE — Proactive Context Synthesizer (v1.0)
├── archive.py             ARCHIVE — Longitudinal User Memory (v1.0)
├── the_arc.py             THE ARC — Long-Term Narrative Tracker (v1.0)
├── tide_stone.py           TideStone — Real-Time User State Reader (v1.0)
├── compass_stone.py        CompassStone — Multi-Turn Goal Tracker (v1.0)
├── ember_stone.py          EmberStone — Recurring Topic Heat Tracker (v1.0)
├── mirror_stone.py        MirrorStone — Self-Confidence Tracker (v1.0)
├── signals_vigil.py       Signal sets for all stones (EN + TR)
├── example.py              Usage examples for all modules
├── README.md              Technical documentation
└── INSTALLATION_GUIDE.md  This file
```

---

*This guide covers Intelligence Stones v1.0. All modules were extracted from AI assistant FRIDAY and made standalone with zero dependencies.*