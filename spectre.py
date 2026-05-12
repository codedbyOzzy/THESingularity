"""SPECTRE â€” Proactive Context Synthesizer for AI Assistants.

> *"FRIDAY bekleyip cevap vermesin â€” bir sonraki adimda ne sorulacaÄŸÄ±nÄ± bil sinsice."*

SPECTRE, mevcut konusma akÄ±ÅŸÄ±ndan yola Ã§Ä±karak kullanÄ±cÄ±nÄ±n bir sonraki
mesajÄ±nda ne sorabileceÄŸini tahmin eder.

Designed to be dropped into any AI assistant project without requiring FRIDAY
or any other system.

Usage:
    from spectre import Spectre, SpectrePrediction

    spectre = Spectre(the_arc=None, bond_stone=None)

    # After each conversation turn:
    predictions = spectre.predict_next(conversation_history)
    for p in predictions:
        print(f"Suggestion: {p.suggestion}")
        print(f"Confidence: {p.confidence}")
        print(f"Reason: {p.reason}")

    # Learn from completed conversations:
    spectre.learn_from_conversation(conversation_history)
"""

from __future__ import annotations

import json
import re
import time
from collections import deque
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


# â”€â”€ Data Structures â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@dataclass
class TrajectoryRule:
    trigger: str
    follows: str
    probability: float
    learned_from: str
    times_observed: int

    def as_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> TrajectoryRule:
        return TrajectoryRule(**d)


@dataclass
class InferenceLink:
    from_concept: str
    to_concept: str
    link_type: str  # "prerequisite" | "related" | "follow_up"
    strength: float

    def as_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> InferenceLink:
        return InferenceLink(**d)


@dataclass
class PersonaPrediction:
    predicted_next_question: str
    predicted_style: str  # "concise" | "detailed" | "why-focused" | "how-focused"
    confidence: float


@dataclass
class SpectrePrediction:
    suggestion: str
    reason: str
    source: str  # "trajectory" | "inference" | "persona"
    confidence: float

    def as_dict(self) -> dict:
        return asdict(self)


# â”€â”€ Inference Engine â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class InferenceEngine:
    """Logical X -> Y inference chains.

    Maintains a set of rules that link concepts to their common follow-ups.
    E.g., "async" -> "await" (prerequisite), "flask" -> "deployment" (follow_up)
    """

    # Default inference rules (EN + TR)
    DEFAULT_RULES: list[InferenceLink] = [
        # Python
        InferenceLink("python", "async", "prerequisite", 0.8),
        InferenceLink("python", "flask", "related", 0.7),
        InferenceLink("python", "django", "related", 0.7),
        InferenceLink("python", "pip", "related", 0.5),
        InferenceLink("async", "await", "prerequisite", 0.9),
        InferenceLink("async", "event loop", "prerequisite", 0.9),
        InferenceLink("coroutine", "await", "prerequisite", 0.9),
        InferenceLink("async", "asyncio", "related", 0.8),

        # Web Development
        InferenceLink("web app", "flask", "related", 0.8),
        InferenceLink("web app", "deployment", "follow_up", 0.7),
        InferenceLink("web app", "database", "prerequisite", 0.7),
        InferenceLink("flask", "secret key", "follow_up", 0.8),
        InferenceLink("flask", "routing", "prerequisite", 0.7),
        InferenceLink("flask", "blueprint", "related", 0.6),
        InferenceLink("deployment", "docker", "follow_up", 0.8),
        InferenceLink("docker", "docker-compose", "related", 0.8),
        InferenceLink("docker", "container", "prerequisite", 0.9),

        # Mobile
        InferenceLink("mobile app", "react native", "related", 0.7),
        InferenceLink("react native", "flutter", "follow_up", 0.6),
        InferenceLink("react native", "expo", "related", 0.5),
        InferenceLink("flutter", "dart", "prerequisite", 0.9),

        # Git
        InferenceLink("git", "github", "related", 0.7),
        InferenceLink("git", "branch", "prerequisite", 0.8),
        InferenceLink("git", "merge", "follow_up", 0.8),
        InferenceLink("branch", "pull request", "follow_up", 0.9),
        InferenceLink("merge", "conflict", "related", 0.7),

        # General
        InferenceLink("api", "rest", "prerequisite", 0.8),
        InferenceLink("rest", "http", "prerequisite", 0.7),
        InferenceLink("database", "sql", "related", 0.8),
        InferenceLink("sql", "postgresql", "related", 0.7),
        InferenceLink("postgresql", "mongodb", "follow_up", 0.4),

        # Data Science
        InferenceLink("machine learning", "python", "related", 0.8),
        InferenceLink("machine learning", "tensorflow", "related", 0.7),
        InferenceLink("data science", "pandas", "related", 0.8),
        InferenceLink("pandas", "numpy", "prerequisite", 0.8),

        # Turkish-specific
        InferenceLink("python", "asenkron", "related", 0.7),
        InferenceLink("veritabani", "sql", "related", 0.8),
        InferenceLink("web servisi", "api", "prerequisite", 0.9),
        InferenceLink("docker", "konteyner", "related", 0.9),
    ]

    def __init__(self, rules: list[InferenceLink] | None = None):
        self._rules: list[InferenceLink] = rules if rules is not None else self.DEFAULT_RULES.copy()
        self._concept_index: dict[str, list[InferenceLink]] = self._build_index()

    def _build_index(self) -> dict[str, list[InferenceLink]]:
        """Build an index for fast lookup by concept."""
        index: dict[str, list[InferenceLink]] = {}
        for rule in self._rules:
            if rule.from_concept not in index:
                index[rule.from_concept] = []
            index[rule.from_concept].append(rule)
        return index

    def get_inference_chain(self, topic: str, link_type: str | None = None) -> list[str]:
        """Get all concepts that follow from the given topic.

        Args:
            topic: The current topic (e.g., "async", "flask")
            link_type: Optional filter â€” "prerequisite" | "related" | "follow_up"

        Returns:
            List of concepts that typically follow the topic
        """
        topic_lower = topic.lower()
        results: list[tuple[float, str]] = []

        for rule in self._rules:
            if rule.from_concept == topic_lower or rule.from_concept in topic_lower:
                if link_type is None or rule.link_type == link_type:
                    results.append((rule.strength, rule.to_concept))

        # Sort by strength descending
        results.sort(key=lambda x: -x[0])
        return [concept for _, concept in results]

    def suggest_follow_up_questions(self, current_topic: str, max_suggestions: int = 3) -> list[str]:
        """Suggest follow-up questions for a given topic.

        Args:
            current_topic: The current discussion topic
            max_suggestions: Maximum number of suggestions to return

        Returns:
            List of suggested question topics
        """
        topic_lower = current_topic.lower()
        suggestions: list[tuple[float, str]] = []

        for rule in self._rules:
            if rule.from_concept in topic_lower or topic_lower in rule.from_concept:
                if rule.link_type in ("prerequisite", "follow_up"):
                    # Convert "await" -> "What is await?" or "How does await work?"
                    question_form = self._to_question_form(rule.to_concept)
                    suggestions.append((rule.strength, question_form))

        suggestions.sort(key=lambda x: -x[0])
        return [q for _, q in suggestions[:max_suggestions]]

    def _to_question_form(self, concept: str) -> str:
        """Convert a concept to a question form."""
        # Simple heuristics
        concept_lower = concept.lower()

        question_templates = [
            (("event loop", "asyncio"), "How does {concept} work?"),
            (("await", "async"), "How does {concept} work in Python?"),
            (("docker", "container"), "How do I use {concept}?"),
            (("deployment", "deploy"), "How do I {concept} my application?"),
            (("sql", "database"), "How do I query with {concept}?"),
            (("api", "rest"), "What is {concept} and how do I use it?"),
            (("github", "git"), "How do I use {concept}?"),
        ]

        for keywords, template in question_templates:
            if any(kw in concept_lower for kw in keywords):
                return template.format(concept=concept)

        # Default: "What is X?" or "How does X work?"
        if len(concept.split()) == 1:
            return f" What is {concept}?"
        else:
            return f" How does {concept} work?"

    def add_rule(self, from_concept: str, to_concept: str, link_type: str, strength: float) -> None:
        """Add a new inference rule."""
        new_rule = InferenceLink(from_concept, to_concept, link_type, strength)
        self._rules.append(new_rule)
        if from_concept not in self._concept_index:
            self._concept_index[from_concept] = []
        self._concept_index[from_concept].append(new_rule)


# â”€â”€ Trajectory Engine â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class TrajectoryEngine:
    """Learns conversation flow patterns from THE ARC episodes.

    Tracks which topics tend to follow which other topics based on observed
    conversation sequences.
    """

    def __init__(self, the_arc=None):
        self._the_arc = the_arc
        self._trajectories: list[TrajectoryRule] = []
        self._global_patterns: list[TrajectoryRule] = []  # High-frequency patterns

    def learn_from_the_arc(self) -> None:
        """Extract trajectory patterns from THE ARC episodes."""
        if not self._the_arc:
            return

        stats = self._the_arc.get_stats()
        total_episodes = stats.get("total_episodes", 0)
        if total_episodes == 0:
            return

        # Get all episodes
        for ep_id in range(total_episodes):
            # We don't have direct episode access, so we use consult
            pass  # THE ARC doesn't expose episode iteration directly

    def learn_from_conversation(self, conversation: list[dict]) -> list[TrajectoryRule]:
        """Learn trajectory patterns from a conversation.

        Args:
            conversation: List of TurnRecord-like dicts with "content" and "role"

        Returns:
            List of newly learned trajectory rules
        """
        if not conversation or len(conversation) < 2:
            return []

        new_rules: list[TrajectoryRule] = []

        for i in range(len(conversation) - 1):
            current = self._normalize_topic(conversation[i].get("content", ""))
            next_topic = self._normalize_topic(conversation[i + 1].get("content", ""))

            if not current or not next_topic or current == next_topic:
                continue

            # Check if this trajectory already exists
            existing = self._find_trajectory(current, next_topic)
            if existing:
                existing.times_observed += 1
                existing.probability = min(1.0, existing.probability + 0.05)
            else:
                new_rule = TrajectoryRule(
                    trigger=current,
                    follows=next_topic,
                    probability=0.5,
                    learned_from="conversation",
                    times_observed=1,
                )
                self._trajectories.append(new_rule)
                new_rules.append(new_rule)

        self._update_global_patterns()
        return new_rules

    def predict_next_topics(self, current_topic: str, max_predictions: int = 3) -> list[tuple[str, float]]:
        """Predict what topics are likely to follow the current topic.

        Returns:
            List of (predicted_topic, probability) tuples
        """
        current = self._normalize_topic(current_topic)
        if not current:
            return []

        candidates: list[tuple[float, str]] = []

        for rule in self._trajectories:
            if rule.trigger == current:
                # Factor in how many times observed
                score = rule.probability * min(rule.times_observed / 5.0, 1.0)
                candidates.append((score, rule.follows))

        # Also check global patterns
        for rule in self._global_patterns:
            if rule.trigger == current:
                score = rule.probability * 0.7  # Global patterns are less specific
                candidates.append((score, rule.follows))

        candidates.sort(key=lambda x: -x[0])
        return [(topic, prob) for prob, topic in candidates[:max_predictions]]

    def _find_trajectory(self, trigger: str, follows: str) -> TrajectoryRule | None:
        for rule in self._trajectories:
            if rule.trigger == trigger and rule.follows == follows:
                return rule
        return None

    def _normalize_topic(self, text: str) -> str:
        text = text.lower().strip()
        stop = {
            "bir", "ve", "ile", "icin", "olan", "bu", "ne", "nasil", "neden",
            "the", "a", "an", "is", "are", "was", "were", "to", "of", "in",
            "what", "how", "why", "when", "where", "who", "which",
        }
        words = [w for w in re.findall(r"\w+", text) if len(w) > 2 and w not in stop]
        return " ".join(words[:5])

    def _update_global_patterns(self) -> None:
        """Update global patterns â€” high-frequency trajectories across all users."""
        from collections import Counter

        # Count how many times each trigger has been observed across all trajectories
        trigger_observed_count: dict[str, int] = {}
        for rule in self._trajectories:
            trigger_observed_count[rule.trigger] = trigger_observed_count.get(rule.trigger, 0) + rule.times_observed

        # A trigger becomes a "global pattern" when observed 5+ times total
        for trigger, total_obs in trigger_observed_count.items():
            if total_obs >= 5:
                matching = [t for t in self._trajectories if t.trigger == trigger]
                if not matching:
                    continue

                # Find the most common "follows" for this trigger
                from collections import Counter as C
                follows_counter = C(t.follows for t in matching)
                most_common_follows, _ = follows_counter.most_common(1)[0] if follows_counter else (matching[0].follows, 1)

                avg_prob = sum(t.probability for t in matching) / len(matching)

                existing = next((g for g in self._global_patterns if g.trigger == trigger), None)
                if existing:
                    existing.probability = avg_prob
                    existing.times_observed = total_obs
                    existing.follows = most_common_follows
                else:
                    self._global_patterns.append(TrajectoryRule(
                        trigger=trigger,
                        follows=most_common_follows,
                        probability=avg_prob,
                        learned_from="global",
                        times_observed=total_obs,
                    ))


# â”€â”€ Persona Engine â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class PersonaEngine:
    """Infers how the user prefers to ask questions.

    Analyzes conversation style to predict whether the user prefers:
    - concise vs detailed explanations
    - why-focused vs how-focused questions
    - technical depth vs simple explanations
    """

    def __init__(self, bond_stone=None):
        self._bond = bond_stone
        self._style_counts = {
            "detailed": 0,
            "concise": 0,
            "why_focused": 0,
            "how_focused": 0,
        }
        self._total_observations = 0

    def learn_from_turn(self, user_message: str) -> None:
        """Analyze a user message to update style profile."""
        if not user_message:
            return

        words = user_message.split()
        word_count = len(words)

        # Detailed vs Concise
        if word_count > 50:
            self._style_counts["detailed"] += 1
        elif word_count < 15:
            self._style_counts["concise"] += 1

        # Why vs How focused
        lower = user_message.lower()
        why_patterns = ["neden", "niye", "why", "reason", "amaci", "mantigi"]
        how_patterns = ["nasil", "how", "yapmak", "yapilir", "calisiyor", "use"]

        if any(p in lower for p in why_patterns):
            self._style_counts["why_focused"] += 1
        if any(p in lower for p in how_patterns):
            self._style_counts["how_focused"] += 1

        self._total_observations += 1

    def predict_style(self) -> str:
        """Predict the user's preferred question style."""
        if self._total_observations == 0:
            return "detailed"  # Default assumption

        # Determine most common style
        max_style = max(self._style_counts, key=self._style_counts.get)
        return max_style

    def get_persona_prediction(self, predicted_topic: str) -> PersonaPrediction:
        """Get a prediction of how the user will ask about a topic."""
        style = self.predict_style()

        if style == "concise":
            question = f" What is {predicted_topic}?"
        elif style == "why_focused":
            question = f" Why is {predicted_topic} important?"
        elif style == "how_focused":
            question = f" How do I use {predicted_topic}?"
        else:  # detailed
            question = f" Can you explain {predicted_topic} in detail?"

        confidence = min(self._style_counts[style] / max(self._total_observations, 1), 1.0)

        return PersonaPrediction(
            predicted_next_question=question,
            predicted_style=style,
            confidence=confidence,
        )

    def get_stats(self) -> dict:
        return {
            "style_counts": dict(self._style_counts),
            "total_observations": self._total_observations,
            "dominant_style": self.predict_style(),
        }


# â”€â”€ Fusion Brain â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class FusionBrain:
    """Combines predictions from all three engines into unified predictions."""

    def __init__(self, inference: InferenceEngine, trajectory: TrajectoryEngine, persona: PersonaEngine):
        self._inference = inference
        self._trajectory = trajectory
        self._persona = persona

    def fuse(
        self,
        current_topic: str,
        max_predictions: int = 3,
    ) -> list[SpectrePrediction]:
        """Combine all signals to produce final predictions.

        Args:
            current_topic: The current discussion topic
            max_predictions: Maximum number of predictions to return

        Returns:
            List of SpectrePrediction objects sorted by confidence
        """
        all_predictions: list[tuple[float, SpectrePrediction]] = []

        # 1. Inference-based predictions
        inf_suggestions = self._inference.suggest_follow_up_questions(current_topic, max_predictions)
        for suggestion in inf_suggestions:
            all_predictions.append((0.7, SpectrePrediction(
                suggestion=suggestion,
                reason=f"Inference: {current_topic} often leads to {suggestion}",
                source="inference",
                confidence=0.7,
            )))

        # 2. Trajectory-based predictions
        traj_predictions = self._trajectory.predict_next_topics(current_topic, max_predictions)
        for predicted_topic, prob in traj_predictions:
            # Convert to question form using persona style
            persona_pred = self._persona.get_persona_prediction(predicted_topic)
            all_predictions.append((prob * 0.8, SpectrePrediction(
                suggestion=persona_pred.predicted_next_question,
                reason=f"Trajectory: after '{current_topic}', '{predicted_topic}' was observed",
                source="trajectory",
                confidence=prob * 0.8,
            )))

        # Sort by confidence
        all_predictions.sort(key=lambda x: -x[0])

        # Deduplicate and limit
        seen_topics = set()
        final_predictions: list[SpectrePrediction] = []
        for score, pred in all_predictions:
            topic_key = pred.suggestion.lower()[:30]
            if topic_key not in seen_topics:
                seen_topics.add(topic_key)
                final_predictions.append(pred)
            if len(final_predictions) >= max_predictions:
                break

        return final_predictions


# â”€â”€ Spectre Core â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class Spectre:
    """Proactive Context Synthesizer â€” predicts what the user will ask next.

    Args:
        the_arc: Optional THE ARC instance for trajectory learning
        bond_stone: Optional BondStone instance for persona inference
        persistence_path: Path for persistence
    """

    def __init__(self, the_arc=None, bond_stone=None, persistence_path: str | Path = ".spectre.json"):
        self._the_arc = the_arc
        self._bond = bond_stone
        self._persistence_path = Path(persistence_path)

        self._inference = InferenceEngine()
        self._trajectory = TrajectoryEngine(the_arc)
        self._persona = PersonaEngine(bond_stone)
        self._fusion = FusionBrain(self._inference, self._trajectory, self._persona)
        self._prediction_history: list[dict] = []  # For accuracy tracking

        self._load()

    # â”€â”€ Persistence â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _load(self) -> None:
        if not self._persistence_path.exists():
            return
        try:
            data = json.loads(self._persistence_path.read_text(encoding="utf-8"))
            # Load trajectory rules
            self._trajectory._trajectories = [
                TrajectoryRule.from_dict(r) for r in data.get("trajectories", [])
            ]
            # Load style counts
            style_counts = data.get("style_counts", {})
            for key, value in style_counts.items():
                if key in self._persona._style_counts:
                    self._persona._style_counts[key] = value
            self._persona._total_observations = data.get("total_observations", 0)
            self._prediction_history = data.get("prediction_history", [])
        except Exception:
            pass

    def _save(self) -> None:
        try:
            data = {
                "trajectories": [r.as_dict() for r in self._trajectory._trajectories],
                "style_counts": self._persona._style_counts,
                "total_observations": self._persona._total_observations,
                "prediction_history": self._prediction_history[-50:],  # Keep last 50
            }
            content = json.dumps(data, ensure_ascii=False, indent=2)
            temp = self._persistence_path.with_suffix(".tmp")
            if temp.exists():
                temp.unlink()
            temp.write_text(content, encoding="utf-8")
            import os as _os
            _os.replace(str(temp), str(self._persistence_path))
        except Exception:
            pass

    # â”€â”€ Core API â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def predict_next(self, conversation_history: list[dict], max_predictions: int = 3) -> list[SpectrePrediction]:
        """Predict likely next questions based on conversation history.

        Args:
            conversation_history: List of TurnRecord-like dicts with "content", "role", "timestamp"
            max_predictions: Maximum number of predictions to return

        Returns:
            List of SpectrePrediction objects sorted by confidence
        """
        if not conversation_history:
            return []

        # Use the last message as the current topic
        last_message = conversation_history[-1].get("content", "")
        if not last_message:
            return []

        # Learn from conversation (trajectory patterns)
        self.learn_from_conversation(conversation_history)

        # Learn user style from all user messages in the conversation
        for msg in conversation_history:
            if msg.get("role") == "user":
                self._persona.learn_from_turn(msg.get("content", ""))

        # Fuse all predictions
        predictions = self._fusion.fuse(last_message, max_predictions)
        self._save()
        return predictions

    def learn_from_conversation(self, conversation: list[dict]) -> None:
        """Learn trajectory patterns from a conversation."""
        self._trajectory.learn_from_conversation(conversation)
        self._save()

    def get_proactive_prompt(self, predictions: list[SpectrePrediction]) -> str:
        """Convert predictions to a system prompt addition.

        Args:
            predictions: List of SpectrePrediction objects

        Returns:
            String to add to system prompt, or "" if no predictions
        """
        if not predictions:
            return ""

        lines = ["[SPECTRE] User may ask about:"]
        for p in predictions:
            lines.append(f"  - {p.suggestion} (source: {p.source})")
        return "\n".join(lines)

    def should_suggest(self, prediction: SpectrePrediction, answered_topics: list[str]) -> bool:
        """Check if a prediction should be suggested.

        Args:
            prediction: The prediction to check
            answered_topics: List of topics already addressed

        Returns:
            True if the prediction should be shown to the user
        """
        if prediction.confidence < 0.3:
            return False

        prediction_lower = prediction.suggestion.lower()
        # Split answered topics into words for more robust matching
        for topic in answered_topics:
            topic_words = topic.lower().split()
            for word in topic_words:
                if len(word) > 2 and word in prediction_lower:
                    return False
        return True

    def get_inference_chain(self, topic: str) -> list[str]:
        """Get the full inference chain for a topic."""
        return self._inference.get_inference_chain(topic)

    def suggest_follow_up_questions(self, current_topic: str, max_suggestions: int = 3) -> list[str]:
        """Get follow-up questions for the current topic."""
        return self._inference.suggest_follow_up_questions(current_topic, max_suggestions)

    def get_stats(self) -> dict:
        """Get Spectre statistics."""
        return {
            "trajectories_learned": len(self._trajectory._trajectories),
            "global_patterns": len(self._trajectory._global_patterns),
            "inference_rules": len(self._inference._rules),
            "persona_stats": self._persona.get_stats(),
        }

    def summary(self) -> dict:
        return self.get_stats()

    def reset(self) -> None:
        """Clear all learned patterns."""
        self._trajectory._trajectories.clear()
        self._trajectory._global_patterns.clear()
        self._persona._style_counts = {"detailed": 0, "concise": 0, "why_focused": 0, "how_focused": 0}
        self._persona._total_observations = 0
        self._prediction_history.clear()
        self._save()

    # â”€â”€ Learning Loop + Accuracy Tracking â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def record_prediction_outcome(
        self,
        predicted_topic: str,
        was_asked: bool,
        actual_question: str | None = None,
    ) -> None:
        """Record whether a predicted question was actually asked.

        This builds the learning loop â€” predictions that are frequently
        confirmed get higher confidence, those that miss get lowered.

        Args:
            predicted_topic: The topic/question that was predicted
            was_asked: True if the user actually asked this
            actual_question: If not asked, what did the user actually ask?
        """
        entry = {
            "predicted": predicted_topic.lower()[:50],
            "was_asked": was_asked,
            "actual": actual_question.lower()[:100] if actual_question else None,
            "timestamp": time.time(),
        }
        self._prediction_history.append(entry)

        # Keep history bounded
        if len(self._prediction_history) > 100:
            self._prediction_history = self._prediction_history[-100:]

        # Adjust trajectory probabilities based on outcome
        if not was_asked:
            # Find matching trajectory and reduce its probability
            for rule in self._trajectory._trajectories:
                if predicted_topic.lower()[:20] in rule.follows.lower():
                    rule.probability = max(0.1, rule.probability - 0.05)

        self._save()

    def get_accuracy_report(self) -> dict:
        """Get prediction accuracy metrics.

        Returns:
            Dict with accuracy_rate, total_predictions, hit_rate_by_source
        """
        if not self._prediction_history:
            return {
                "accuracy_rate": 0.0,
                "total_predictions": 0,
                "hit_rate_by_source": {},
                "most_missed_topics": [],
            }

        total = len(self._prediction_history)
        hits = sum(1 for e in self._prediction_history if e["was_asked"])
        accuracy = hits / total if total > 0 else 0.0

        # Missed topics
        missed = [e["predicted"] for e in self._prediction_history if not e["was_asked"]]
        from collections import Counter
        missed_counts = Counter(missed)
        most_missed = [topic for topic, _ in missed_counts.most_common(5)]

        return {
            "accuracy_rate": round(accuracy, 3),
            "total_predictions": total,
            "hit_rate_by_source": {},  # Can be enhanced with source tracking
            "most_missed_topics": most_missed,
        }

    def get_stats(self) -> dict:
        """Get Spectre statistics."""
        accuracy_report = self.get_accuracy_report()
        return {
            "trajectories_learned": len(self._trajectory._trajectories),
            "global_patterns": len(self._trajectory._global_patterns),
            "inference_rules": len(self._inference._rules),
            "persona_stats": self._persona.get_stats(),
            "prediction_accuracy": accuracy_report["accuracy_rate"],
            "total_predictions_tracked": accuracy_report["total_predictions"],
        }


# â”€â”€ Global Singleton â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_spectre_instance: Optional[Spectre] = None


def get_spectre() -> Spectre:
    """Get or create the global SPECTRE instance."""
    global _spectre_instance
    if _spectre_instance is None:
        _spectre_instance = Spectre()
    return _spectre_instance
