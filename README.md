# VIGIL Stones

> *"The assistant that watches itself — and the user."*

A collection of lightweight, zero-dependency Python modules that give AI assistants
awareness of the conversation's direction, the user's state, and the assistant's
own confidence levels.

Each stone is a standalone drop-in. No framework. No configuration. No external dependencies.
Together, they build something more complete.

---

## The Collection

| Stone | Status | What it tracks |
|-------|--------|----------------|
| [**ORACLE**](#-oracle) | v1.0 | *Which* model to use — complexity, depth, urgency, repetition |
| [**SPECTRE**](#-spectre) | v1.0 | *What* the user will ask next — proactive predictions |
| [**TideStone**](#-tidestone) | v1.0 | *How* the user is feeling right now — energy, focus, pace |
| [**CompassStone**](#-compassstone) | v1.0 | *Where* the user is trying to go — goals, progress |
| [**EmberStone**](#-emberstone) | v1.0 | *What* keeps coming back — hot topics, recurring threads |
| [**ARCHIVE**](#-archive) | v1.0 | *How* FRIDAY remembers — longitudinal memory, emotional profile |

All five stones are production-tested inside [FRIDAY Synapse](https://github.com/codedbyOzzy/ProjectFRIDAY)
and available as standalone modules.

---

## How the stones fit together

```
VIGIL stones operate on a different layer than Intelligence Stones.

Intelligence Stones (Mind/Echo/Bond/Intuition):
  → How does the assistant speak to this user?

VIGIL Stones:
  → What is the user trying to achieve?
  → How is the user feeling right now?
  → What topics keep coming back?
  → Is the assistant being honest about its confidence?
```

### The full architecture — all five stones

```
  ┌──────────────────────────────────────────────────────────┐
  │  ORACLE — Model Router                                  │
  │                                                           │
  │  ORACLE      Which model to use for this query            │
  │              gpt-4.1-mini / gemini / llama routing       │
  ├──────────────────────────────────────────────────────────┤
  │  SPECTRE — Proactive Predictor                          │
  │                                                           │
  │  SPECTRE     What will the user ask next?                │
  │              Inference + Trajectory + Persona fusion     │
  ├──────────────────────────────────────────────────────────┤
  │  ARCHIVE — Longitudinal Memory                          │
  │                                                           │
  │  ARCHIVE     How FRIDAY remembers long-term             │
  │              Medium/Long-term context, emotional profile │
  ├──────────────────────────────────────────────────────────┤
  │  Layer 1 — Narrative (THE ARC)                            │
  │                                                           │
  │  THE ARC      Where this conversation has been            │
  │               Decisions made, topics explored,            │
  │               ghost threads, growth patterns             │
  ├──────────────────────────────────────────────────────────┤
  │  Layer 2 — User State (TideStone)                        │
  │                                                           │
  │  TideStone   How the user is feeling right now          │
  │               Energy, focus, pace — real-time            │
  ├──────────────────────────────────────────────────────────┤
  │  Layer 3 — Goals (CompassStone)                          │
  │                                                           │
  │  CompassStone Where the user is trying to go            │
  │               Goals tracked, progress measured           │
  ├──────────────────────────────────────────────────────────┤
  │  Layer 4 — Recurrence (EmberStone)                       │
  │                                                           │
  │  EmberStone  What the user keeps returning to          │
  │               Hot topics, unresolved threads             │
  ├──────────────────────────────────────────────────────────┤
  │  Layer 5 — Self-Awareness (MirrorStone)                   │
  │                                                           │
  │  MirrorStone Whether the assistant is confident         │
  │               Detects hedging, tracks domain trust     │
  └──────────────────────────────────────────────────────────┘
```

---

## 🏹 THE ARC

> *The user's conversation history as a story — not just logs.*

THE ARC tracks the long-term narrative arc of conversations. It learns where
conversations go, which decisions were made, which topics keep resurfacing,
and which threads were abandoned and then resurrected.

### Quick start

```python
from the_arc import TheArc, TurnRecord
import time

arc = TheArc()

# After every conversation turn:
arc.absorb(TurnRecord(
    turn_id=1,
    role="user",
    content="I'll use React Native for the mobile app",
    timestamp=time.time(),
))

# Before every LLM call:
context = arc.consult("React Native")
if context:
    system_prompt += "\n\n" + context
```

### How it works

```
User: "I'll use React Native"
       │
       ▼
  THE ARC creates episode for "react native"
       │
       ▼
User: "Actually I changed my mind — Flutter instead"
       │
       ▼
  Decision outcome = "revoked"
       │
       ▼
  30 days later: "Flutter? I thought you said React Native?"
       │
       ▼
  THE ARC detects GHOST THREAD — shows previous decision context
```

### API

```python
arc.absorb(TurnRecord(turn_id, role, content, timestamp))
arc.consult(query)                    -> str (directive or "")
arc.get_decision_context(query)       -> str (decisions summary)
arc.get_stats()                      -> dict
arc.run_decay()                       # call periodically
arc.summary()                        -> dict
arc.reset()
```

---

## 🌊 TideStone

> *Detects energy, focus, and pace from behavioral signals.*

TideStone reads the user's current cognitive/emotional state from message
patterns — message length, vocabulary complexity, inter-message gaps. No ML,
no embeddings. Just math.

### Quick start

```python
from tide_stone import TideStone

tide = TideStone()

# On every user message:
tide.observe_user("Long detailed question here...")

# Before responding:
state = tide.get_state()
if state:
    directive = tide.get_state_directive()
    if directive:
        system_prompt += "\n\n" + directive
```

### State levels

| Signal | High | Medium | Low |
|--------|------|--------|-----|
| `energy` | Long + complex message | Normal | Short + simple |
| `pace` | Fast typing (<5s gap) | Normal (5-20s) | Slow (>20s) |
| `focus` | Complex vocab + consistent length | Normal | Scattered vocab |

### API

```python
tide.observe_user(user_text)
tide.get_state()              -> TideState or None
tide.get_state_directive()     -> str (or "" if insufficient data)
tide.summary()                 -> dict
tide.reset()
```

---

## 🧭 CompassStone

> *Knows where the user is trying to get to — and tracks progress.*

CompassStone extracts goals from conversation turns and tracks their status.
Session-level and project-level goals are both supported.

### Quick start

```python
from compass_stone import CompassStone

compass = CompassStone()

# After each turn:
compass.observe("I want to learn Python", "Great, let's start!")

# Before responding:
goal_directive = compass.get_goal_directive()
if goal_directive:
    system_prompt += "\n\n" + goal_directive
```

### API

```python
compass.observe(user_text, ai_text="")
compass.observe_user(user_text)     # shorthand
compass.get_goal_directive()       -> str
compass.get_active_goals()         -> list[Goal]
compass.get_stats()                -> dict
compass.reset_session()           # clear session goals only
compass.reset()                   # clear all
```

---

## 🔥 EmberStone

> *Topics the user keeps returning to — tracked by heat.*

EmberStone assigns a heat value to each topic. Heat rises when the user
returns to a topic, decays with silence, and drops sharply when the topic
is resolved.

### Quick start

```python
from ember_stone import EmberStone

ember = EmberStone()

# After each turn:
ember.observe("I'm working on async Python", "Async is powerful...")

# Before responding:
context = ember.get_active_context()
if context:
    system_prompt += "\n\n" + context
```

### Heat lifecycle

```
Topic appears     → HEAT = 0.3
Mentions again    → HEAT += 0.15 (max 1.0)
5 days silence    → HEAT -= 0.02/day
User says "done"  → HEAT -= 0.30 (resolved)
30 days silence  → Archived (ghost)
```

### API

```python
ember.observe(user_text, ai_text="")
ember.observe_user(user_text)       # shorthand
ember.get_active_context()         -> str (hot topics or "")
ember.get_embers()                -> list[Ember] (all embers)
ember.get_stats()                  -> dict
ember.reset()
```

---

## 🪞 MirrorStone

> *Detects when the assistant is hedging — and how confident it really is.*

MirrorStone watches the assistant's responses for hedging language
("I think", "probably", "you might want to") and tracks confidence
per domain. Over time, it learns which topics the assistant
actually knows well.

### Quick start

```python
from mirror_stone import MirrorStone

mirror = MirrorStone()

# After each assistant response:
mirror.observe("How does async work?", "I think it uses an event loop...")

# Before responding:
conf = mirror.estimate_confidence("python")
if conf.flag in ("uncertain", "low_confidence"):
    directive = mirror.get_mirror_directive("python")
    system_prompt += "\n\n" + directive
```

### Confidence result

```python
ConfidenceResult:
  score: float    # 0.0 - 1.0
  flag: str       # "low_data" | "confident" | "uncertain" | "low_confidence"
  hedge: str       # detected hedging phrase, or ""
```

### API

```python
mirror.observe(user_text, ai_text)
mirror.estimate_confidence(query)  -> ConfidenceResult
mirror.get_mirror_directive(query)  -> str
mirror.get_stats()                  -> dict
mirror.reset()
```

---

## Combined Usage

```python
from the_arc import TheArc, TurnRecord
from tide_stone import TideStone
from compass_stone import CompassStone
from ember_stone import EmberStone
from mirror_stone import MirrorStone
from oracle import Oracle
from spectre import Spectre
from archive import Archive
import time

arc = TheArc()
tide = TideStone()
compass = CompassStone()
ember = EmberStone()
mirror = MirrorStone()
oracle = Oracle(the_arc=arc)
spectre = Spectre(the_arc=arc)
archive = Archive(the_arc=arc)

def after_each_turn(user_msg, assistant_msg, turn_id):
    ts = time.time()
    arc.absorb(TurnRecord(turn_id=turn_id, role="user", content=user_msg, timestamp=ts))
    arc.absorb(TurnRecord(turn_id=turn_id+1, role="assistant", content=assistant_msg, timestamp=ts))
    tide.observe_user(user_msg)
    compass.observe(user_msg, assistant_msg)
    ember.observe(user_msg, assistant_msg)
    mirror.observe(user_msg, assistant_msg)

    # ORACLE routing decision
    decision = oracle.route(user_msg)
    print(f"Model: {decision.primary_model.value}")

    # SPECTRE predictions
    history = [{"content": user_msg, "role": "user", "timestamp": ts}]
    preds = spectre.predict_next(history)

    # ARCHIVE query
    archive_context = archive.query(user_msg, depth="all")

def build_system_prompt(base, user_msg):
    additions = []
    if ctx := arc.consult(user_msg): additions.append(ctx)
    if d := tide.get_state_directive(): additions.append(d)
    if d := compass.get_goal_directive(): additions.append(d)
    if d := ember.get_active_context(): additions.append(d)
    if d := mirror.get_mirror_directive(user_msg): additions.append(d)
    if d := archive.query(user_msg, depth="all"): additions.append(d)
    if preds := spectre.predict_next([{"content": user_msg, "role": "user"}]):
        additions.append(spectre.get_proactive_prompt(preds))
    return base + ("\n\n" + "\n\n".join(additions) if additions else "")
```

---

## Files

```
oracle.py           ORACLE — Intelligent Model Router (v1.0)
spectre.py         SPECTRE — Proactive Context Synthesizer (v1.0)
archive.py         ARCHIVE — Longitudinal User Memory (v1.0)
the_arc.py         THE ARC — Long-Term Narrative Tracker (v1.0)
tide_stone.py      TideStone — Real-Time User State Reader (v1.0)
compass_stone.py   CompassStone — Multi-Turn Goal Tracker (v1.0)
ember_stone.py     EmberStone — Recurring Topic Heat Tracker (v1.0)
mirror_stone.py    MirrorStone — Self-Confidence Tracker (v1.0)
signals_vigil.py   Signal sets for all stones (English + Turkish)
example.py         Usage examples for all stones
```

---

## Requirements

Python 3.9+. No third-party packages.

---

## License

MIT — free to use, modify, and distribute.