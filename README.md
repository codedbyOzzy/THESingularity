# THE SINGULARITY — The Awareness Ecosystem

> *"The assistant that doesn't just process data — it understands the human behind it."*

The Singularity is a comprehensive awareness layer for AI assistants. It moves beyond simple "stateless" chat by providing a hierarchical ecosystem of intelligence modules that track narrative arcs, predict user trajectories, and build longitudinal emotional memory.

It is the convergence of **Soul (Intelligence Stones)**, **Mind (Model Routing)**, and **Body (Proactive Awareness)**.

---

## 💠 The Ecosystem v1.0

The Singularity consists of 8 interconnected modules designed to run alongside any LLM pipeline with **zero external dependencies**.

| Layer | Module | Status | What it does |
|-------|--------|--------|--------------|
| **ORACLE** | Intelligent Router | ✅ Released | Dynamically selects the best LLM based on query complexity. |
| **SPECTRE** | Proactive Predictor | ✅ Released | Anticipates the user's next logical step using narrative synthesis. |
| **ARCHIVE** | Longitudinal Memory | ✅ Released | Builds a persistent, emotional user profile across months and years. |
| **THE ARC** | Narrative Architecture| ✅ Released | Tracks the long-term story of conversations and definitive decisions. |
| **TideStone** | Behavioral State | ✅ Released | Reads real-time user energy, focus, and cognitive pace. |
| **CompassStone** | Goal Engine | ✅ Released | Extracts and tracks multi-turn goals and project intent. |
| **EmberStone** | Recurrence Tracker | ✅ Released | Measures "heat" of recurring topics and unresolved threads. |
| **MirrorStone** | Self-Awareness | ✅ Released | Detects assistant hedging and tracks domain-specific confidence. |

---

## 🏛️ Convergence Architecture

The system operates on a hierarchical awareness loop that injects context into your AI's reasoning before it ever generates a word.

```
   ┌──────────────────────────────────────────────────────────┐
   │  LAYER 1: STRATEGIC (ORACLE)                             │
   │  → Which brain should I use for this specific turn?      │
   ├──────────────────────────────────────────────────────────┤
   │  LAYER 2: PREDICTIVE (SPECTRE)                           │
   │  → What is the user going to ask before they ask it?     │
   ├──────────────────────────────────────────────────────────┤
   │  LAYER 3: HISTORICAL (ARCHIVE / THE ARC)                 │
   │  → What is the long-term story? What did we decide?      │
   ├──────────────────────────────────────────────────────────┤
   │  LAYER 4: COGNITIVE (STONES)                             │
   │  → How is the user feeling? What are their goals?        │
   └──────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

Every module in The Singularity is a standalone Python file. To initialize the full ecosystem:

```python
from the_singularity import Oracle, Spectre, Archive, TheArc, TideStone

# Initialize the Convergence Loop
arc = TheArc()
oracle = Oracle(the_arc=arc)
spectre = Spectre(the_arc=arc)
archive = Archive(the_arc=arc)
tide = TideStone()

# On every turn:
decision = oracle.route(user_msg)
preds = spectre.predict_next(arc.get_history())
context = build_awareness_context(user_msg)

# Final prompt generation
system_prompt += "\n\n" + context
```

---

## 📜 Principles

1.  **Awareness is a Layer:** Not a feature, not a tool. It lives beneath the words.
2.  **Zero Dependencies:** Only Python standard library. No frameworks, no DB lock-in.
3.  **Proactive, not Reactive:** The assistant should notice things without being asked.
4.  **Longitudinal Narrative:** Conversations are arcs, not isolated snips.

---

## 📂 Files

- `oracle.py`: Intelligent Model Router
- `spectre.py`: Proactive Context Synthesizer
- `archive.py`: Longitudinal User Memory
- `the_arc.py`: Long-Term Narrative Tracker
- `tide_stone.py`: Real-Time User State Reader
- `compass_stone.py`: Multi-Turn Goal Tracker
- `ember_stone.py`: Recurring Topic Heat Tracker
- `mirror_stone.py`: Self-Confidence Tracker
- `signals_vigil.py`: Signal sets for awareness detection
- `example.py`: Unified implementation examples

---

## ⚖️ License

Apache 2.0 — Open for all. Free to use, modify, and distribute.

<div align="center">

*"The Singularity: Where data becomes awareness."*

</div>