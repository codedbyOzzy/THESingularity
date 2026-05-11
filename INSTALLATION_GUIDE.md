# VIGIL Stones — Installation & Integration Guide

> This guide is intended for developers who wish to integrate the VIGIL Stones and THE ARC systems into their own AI assistant projects.
>
> **Requirements:** Python 3.9+, zero external dependencies.

---

## Contents

1. [System Overview](#1-system-overview)
2. [Installation](#2-installation)
3. [Integration Architecture](#3-integration-architecture)
4. [Step-by-Step Integration](#4-step-by-step-integration)
5. [Detailed Module Usage](#5-detailed-module-usage)
6. [Unified Implementation Example](#6-unified-implementation-example)
7. [System Integration Query Loop](#7-system-integration-query-loop)
8. [API Reference](#8-api-reference)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. System Overview

VIGIL and THE ARC form the **awareness layers** of an AI assistant:

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1 — Narrative (THE ARC)                              │
│  → Where is the user going? What decisions were made?       │
│    What topics keep recurring?                              │
├─────────────────────────────────────────────────────────────┤
│  Layer 2 — User State (TideStone)                           │
│  → How is the user feeling right now? Is energy high?       │
│    Are they focused?                                        │
├─────────────────────────────────────────────────────────────┤
│  Layer 3 — Goals (CompassStone)                             │
│  → What are the user's goals? Has progress been made?       │
├─────────────────────────────────────────────────────────────┤
│  Layer 4 — Recurrence (EmberStone)                          │
│  → What topics does the user keep revisiting?               │
│    Which are the "hot" topics?                              │
├─────────────────────────────────────────────────────────────┤
│  Layer 5 — Self-Awareness (MirrorStone)                     │
│  → How confident is the assistant in this topic?            │
│    Is it using hedging language?                            │
└─────────────────────────────────────────────────────────────┘
```

### Module Purposes

| Module | Technical Name | Purpose |
|-------|----------------|-------|
| **THE ARC** | Long-Term Narrative Tracker | Tracks long-term conversation history: decisions, ghost threads, growth trails. |
| **TideStone** | Real-Time User State Reader | Reads the user's current energy, focus, and pace. |
| **CompassStone** | Multi-Turn Goal Tracker | Tracks user goals across multiple turns. |
| **EmberStone** | Recurring Topic Heat Tracker | Tracks the "heat" of recurring topics. |
| **MirrorStone** | Self-Confidence Tracker | Monitors assistant's self-confidence and hedging usage. |

---

## 2. Installation

### 2.1 Copying Files to Your Project

All modules should be collected in a single directory. Recommended structure:

```
my_ai_project/
├── vigilstones/           # ← New directory
│   ├── the_arc.py
│   ├── tide_stone.py
│   ├── compass_stone.py
│   ├── ember_stone.py
│   ├── mirror_stone.py
│   └── signals_vigil.py   (optional)
├── your_assistant.py       # ← Your assistant file
├── system_prompt.py
└── main.py
```

### 2.2 Zero Dependencies

These modules use **only the Python standard library**. No additions to your `requirements.txt` are necessary.

```bash
# No installation required
pip install  # You can leave this empty
```

---

## 3. Integration Architecture

### 3.1 Core Concept: The Query Loop

Each module intervenes at two key points:

```
User Message
       │
       ▼
┌──────────────────┐
│  OBSERVE (Collect)│  ← Called on every message
│  (absorb/observe) │
└──────────────────┘
       │
       ▼
   ┌─────────┐
   │  LLM    │  ← Assistant generates response
   └─────────┘
       │
       ▼
┌──────────────────┐
│  OBSERVE (Collect)│  ← Called after response
│  (absorb/observe) │
└──────────────────┘
       │
       ▼
┌──────────────────┐
│  CONSULT (Consult)│  ← BEFORE the next LLM call
│  (consult/directive)│    Inject context into system prompt
└──────────────────┘
```

### 3.2 Module Execution Timing

| Module | Observe Timing | Consult Timing |
|-------|----------------|----------------|
| **THE ARC** | End of every turn (`absorb`) | BEFORE LLM call (`consult`) |
| **TideStone** | On every user message (`observe_user`) | BEFORE LLM call (`get_state_directive`) |
| **CompassStone** | End of every turn (`observe`) | BEFORE LLM call (`get_goal_directive`) |
| **EmberStone** | End of every turn (`observe`) | BEFORE LLM call (`get_active_context`) |
| **MirrorStone** | AFTER assistant response (`observe`) | BEFORE LLM call (`get_mirror_directive`) |

---

## 4. Step-by-Step Integration

### Step 1 — Importing Modules

At the top of your assistant file:

```python
from vigilstones.the_arc import TheArc, TurnRecord
from vigilstones.tide_stone import TideStone
from vigilstones.compass_stone import CompassStone
from vigilstones.ember_stone import EmberStone
from vigilstones.mirror_stone import MirrorStone

import time
```

### Step 2 — Initializing Modules

In your assistant's `__init__` or setup section:

```python
class MyAssistant:
    def __init__(self):
        # Initialize all VIGIL modules
        self.arc     = TheArc(path=".the_arc.json")
        self.tide    = TideStone()
        self.compass = CompassStone(path=".compass_stone.json")
        self.ember   = EmberStone(path=".ember_stone.json")
        self.mirror  = MirrorStone(path=".mirror_stone.json")

        self._turn_id = 0
```

### Step 3 — Observe (Collection)

Called during every conversation turn:

```python
def on_user_message(self, user_msg: str):
    self._turn_id += 1
    ts = time.time()

    # THE ARC — record every turn
    self.arc.absorb(TurnRecord(
        turn_id=self._turn_id,
        role="user",
        content=user_msg,
        timestamp=ts,
    ))

    # TideStone — user message only
    self.tide.observe_user(user_msg)

    # CompassStone — goal tracking
    self.compass.observe(user_msg, "")

    # EmberStone — hot topic tracking
    self.ember.observe(user_msg, "")
```

### Step 4 — Post-Assistant Observe

After the LLM response is generated:

```python
def on_assistant_response(self, user_msg: str, assistant_msg: str):
    self._turn_id += 1
    ts = time.time()

    # THE ARC — record assistant turn as well
    self.arc.absorb(TurnRecord(
        turn_id=self._turn_id,
        role="assistant",
        content=assistant_msg,
        timestamp=ts,
    ))

    # CompassStone — include assistant response
    self.compass.observe(user_msg, assistant_msg)

    # EmberStone — include assistant response
    self.ember.observe(user_msg, assistant_msg)

    # MirrorStone — IMMEDIATELY here
    self.mirror.observe(user_msg, assistant_msg)
```

### Step 5 — Building System Prompt (Consult)

Inject context into the system prompt BEFORE every LLM call:

```python
def build_system_prompt(self, base_prompt: str, user_msg: str) -> str:
    additions = []

    # THE ARC — narrative context
    if ctx := self.arc.consult(user_msg):
        additions.append(ctx)

    # TideStone — user state
    if directive := self.tide.get_state_directive():
        additions.append(directive)

    # CompassStone — goals
    if directive := self.compass.get_goal_directive():
        additions.append(directive)

    # EmberStone — hot topics
    if ctx := self.ember.get_active_context():
        additions.append(ctx)

    # MirrorStone — assistant confidence
    if directive := self.mirror.get_mirror_directive(user_msg):
        additions.append(directive)

    if additions:
        return base_prompt + "\n\n" + "\n\n".join(additions)
    return base_prompt
```

---

## 5. Detailed Module Usage

### 5.1 THE ARC — Long-Term Narrative Tracking

Tracks the **story dimension** of the conversation.

```python
context = arc.consult("React Native")
if context:
    print("THE ARC says:", context)

# Get decision context
decisions = arc.get_decision_context("React Native")

# Get statistics
stats = arc.get_stats()
print(f"Total episodes: {stats['total_episodes']}")
```

### 5.2 TideStone — Real-Time User State

Reads **how** the user feels (energy, pace, focus).

```python
# Get directive for system prompt
directive = tide.get_state_directive()
# Returns "" if not enough data yet (requires min_turns=3)
```

### 5.3 CompassStone — Goal Tracking

Monitors **where** the user is trying to go.

```python
# Get active goals
active_goals = compass.get_active_goals()
for goal in active_goals:
    print(f"- {goal.text} ({goal.status})")
```

### 5.4 EmberStone — Recurring Topics

Measures **what** the user keeps talking about using "heat".

```python
# Get context for active (hot) topics
context = ember.get_active_context()
```

### 5.5 MirrorStone — Self-Confidence

Monitors assistant confidence and hedging.

```python
# Get mirror directive (if uncertain)
directive = mirror.get_mirror_directive("python async")
# Returns advice to be more direct if hedging is detected.
```

---

## 6. Unified Implementation Example

```python
class VIGILAssistant:
    def chat(self, user_msg: str, llm_call_fn) -> str:
        # 1. Observe user turn
        self._observe_user(user_msg)

        # 2. Build system prompt
        system_prompt = self._consult(user_msg)

        # 3. Call LLM
        response = llm_call_fn(system_prompt, user_msg)

        # 4. Observe assistant turn
        self._observe_assistant(user_msg, response)

        return response
```

---

## 7. System Integration Query Loop

1. **User Message:** "I'm learning Python async, it's not working"
2. **Observe:** Modules absorb the frustration and the topic (async).
3. **Consult:** Prompt is enhanced with "User is focused on learning async (Goal). They seem highly engaged (Tide)."
4. **LLM:** Generates response.
5. **Observe:** MirrorStone checks if the response sounds uncertain.

---

## 8. API Reference Summary

All modules follow a similar interface:
- `observe(user, assistant)`: Collect data.
- `consult(query)`: Get directive/context.
- `reset()`: Clear all data.
- `get_stats()`: Return analytics.

---

## 9. Troubleshooting

- **ModuleNotFoundError:** Ensure your `vigilstones` directory is in the Python path.
- **TideStone returning None:** Normal behavior for the first `min_turns` (default 3).
- **THE ARC returning empty:** Requires at least 20% keyword overlap with existing episodes.
- **JSON not saving:** Check directory write permissions.

---

*Documentation v1.0 — Unified Awareness Ecosystem*
