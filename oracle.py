"""ORACLE — Intelligent Model Router for AI Assistants.

> *"Do the right model for the right query — automatically, intelligently, invisibly."*

A standalone, zero-dependency Python module that decides which LLM to use for each query
based on complexity, depth, urgency, and repetition signals.

Designed to be dropped into any AI assistant project without requiring FRIDAY
or any other system.

Usage:
    from oracle import Oracle, ModelChoice, ComplexityLevel

    oracle = Oracle()

    # Before each LLM call:
    decision = oracle.route("Rust lifetimes and borrowing explained")
    print(decision.primary_model)   # ModelChoice.GROQ_LLAMA
    print(decision.complexity)       # ComplexityLevel.DEEP
    print(decision.reasoning)       # "comp=deep; depth=expert; urgency=normal; ..."

    # Use the chosen model
    model_name = decision.primary_model.value.split(":")[1]
    response = call_llm(model_name, messages)

    # Record outcome for learning
    oracle.record_outcome(decision, user_satisfaction=0.9)

    # Circuit breaker integration
    if oracle.can_use_provider(decision.primary_model):
        call_llm(...)
    else:
        best = oracle.get_best_available_model(user_input)
        call_llm(best.primary_model.value.split(":")[1], ...)
"""

from __future__ import annotations

import json
import re
import time
from collections import deque
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Optional


# ── Enums ──────────────────────────────────────────────────────────────────────

class ComplexityLevel(Enum):
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    DEEP = "deep"


class DepthLevel(Enum):
    SURFACE = "surface"
    MODERATE = "moderate"
    DEEP = "deep"
    EXPERT = "expert"


class UrgencyLevel(Enum):
    NORMAL = "normal"
    BRISK = "brisk"
    RELAXED = "relaxed"


class ModelChoice(Enum):
    GPT_MINI = "openai:gpt-4.1-mini"
    GEMINI_FLASH = "gemini:gemini-2.5-flash"
    GROQ_LLAMA = "groq:llama-3.3-70b-versatile"


# ── Data Structures ────────────────────────────────────────────────────────────

@dataclass
class ComplexitySignal:
    level: ComplexityLevel
    word_count: int
    is_question: bool
    has_code: bool
    has_technical_terms: bool
    sentence_count: int
    question_count: int
    avg_word_length: float
    reasoning: str


@dataclass
class DepthSignal:
    level: DepthLevel
    topic_depth_score: float
    requires_prerequisite: bool
    requires_code: bool
    reasoning: str


@dataclass
class UrgencySignal:
    level: UrgencyLevel
    pace_score: float
    reasoning: str


@dataclass
class RepetitionSignal:
    is_repeat: bool
    times_repeated: int
    last_seen_hours_ago: float
    reasoning: str


@dataclass
class RoutingDecision:
    primary_model: ModelChoice
    fallback_model: ModelChoice
    complexity: ComplexityLevel
    reasoning: str
    confidence: float
    estimated_tokens: int

    def as_dict(self) -> dict:
        return {
            "primary_model": self.primary_model.value,
            "fallback_model": self.fallback_model.value,
            "complexity": self.complexity.value,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "estimated_tokens": self.estimated_tokens,
        }


# ── Complexity Stone ──────────────────────────────────────────────────────────

class ComplexityStone:
    """Estimates how complex a given user query is.

    Signals observed:
      - Word count
      - Sentence count and structure
      - Question marks
      - Code snippets
      - Technical terminology
      - Vocabulary complexity
    """

    DEEP_TERMS: set[str] = {
        "lifetime", "borrowing", "ownership", "borrow checker",
        "coroutine", "event loop", "GIL", "bytecode", "AST",
        "descriptor", "metaclass", "garbage collection",
        "compiler", "linker", "IR", "SSA", "JIT",
        "kubernetes", "container orchestration", "cgroups",
        "network namespace", "veth",
        "monad", "functor", "applicative", " ADT", "algebraic",
        "curry", "partial application",
        "isolation level", "deadlock", "WAL", "btree",
        "transaction", "ACID", "MVCC",
        "TCP congestion", "backpressure", "mTLS", "PFS",
    }

    COMPLEX_TERMS: set[str] = {
        "architecture", "microservice", "algorithm", "optimization",
        "concurrency", "parallelism", "async", "deployment",
        "authentication", "authorization", "encryption",
        "refactoring", "design pattern", " SOLID", "Clean Code",
    }

    CODE_PATTERNS: tuple[str, ...] = (
        r"```[\s\S]*?```",
        r"`[^`]{3,}`",
        r"\bdef\b",
        r"\bclass\b",
        r"\bimport\b",
        r"\$\w+",
        r"SELECT\s+.*\s+FROM",
    )

    def estimate(self, text: str) -> ComplexitySignal:
        """Analyze text and return a ComplexitySignal."""
        if not text:
            return ComplexitySignal(
                level=ComplexityLevel.TRIVIAL,
                word_count=0,
                is_question=False,
                has_code=False,
                has_technical_terms=False,
                sentence_count=0,
                question_count=0,
                avg_word_length=0.0,
                reasoning="Bos metin",
            )

        words = text.split()
        word_count = len(words)
        question_count = text.count("?")
        is_question = question_count > 0
        sentences = [s.strip() for s in re.split(r"[.!?]", text) if s.strip()]
        sentence_count = len(sentences)
        avg_word_length = sum(len(w) for w in words) / word_count if word_count else 0.0
        has_code = any(re.search(p, text) for p in self.CODE_PATTERNS)

        lower_text = text.lower()
        technical_terms = sum(
            1 for term in self.DEEP_TERMS | self.COMPLEX_TERMS
            if term in lower_text
        )
        has_technical_terms = technical_terms >= 2
        deep_term_count = sum(1 for term in self.DEEP_TERMS if term in lower_text)

        level = self._classify(
            lower_text=lower_text,
            word_count=word_count,
            question_count=question_count,
            sentence_count=sentence_count,
            has_code=has_code,
            has_technical_terms=has_technical_terms,
            technical_terms_count=technical_terms,
            deep_term_count=deep_term_count,
            avg_word_length=avg_word_length,
            is_question=is_question,
        )

        reasoning = self._build_reasoning(level, word_count, question_count,
                                         has_code, deep_term_count, has_technical_terms)

        return ComplexitySignal(
            level=level,
            word_count=word_count,
            is_question=is_question,
            has_code=has_code,
            has_technical_terms=has_technical_terms,
            sentence_count=sentence_count,
            question_count=question_count,
            avg_word_length=avg_word_length,
            reasoning=reasoning,
        )

    def _classify(
        self,
        lower_text: str,
        word_count: int,
        question_count: int,
        sentence_count: int,
        has_code: bool,
        has_technical_terms: bool,
        technical_terms_count: int,
        deep_term_count: int,
        avg_word_length: float,
        is_question: bool,
    ) -> ComplexityLevel:
        """Classify the complexity level based on signals."""
        trivial_words = {"merhaba", "selam", "hello", "hi", "tesekkurler",
                         "sagol", "thanks", "thank", "bye", "gorusrüz"}
        if word_count <= 5:
            if any(w.lower().rstrip("!,") in trivial_words for w in words):
                return ComplexityLevel.TRIVIAL

        if deep_term_count >= 2:
            return ComplexityLevel.DEEP
        if any(term in lower_text for term in self.DEEP_TERMS):
            if word_count > 20:
                return ComplexityLevel.DEEP

        if word_count > 200:
            return ComplexityLevel.COMPLEX
        if question_count >= 3:
            return ComplexityLevel.COMPLEX
        if sentence_count > 5 and has_technical_terms:
            return ComplexityLevel.COMPLEX
        if has_code and technical_terms_count >= 3:
            return ComplexityLevel.COMPLEX

        if word_count > 20:
            if is_question or has_technical_terms:
                return ComplexityLevel.MODERATE

        if word_count <= 20:
            if not is_question and not has_code:
                return ComplexityLevel.SIMPLE
            return ComplexityLevel.MODERATE

        return ComplexityLevel.SIMPLE

    def _build_reasoning(
        self,
        level: ComplexityLevel,
        word_count: int,
        question_count: int,
        has_code: bool,
        deep_term_count: int,
        has_technical_terms: bool,
    ) -> str:
        parts = [f"Kelime: {word_count}"]
        if question_count > 0:
            parts.append(f"Soru: {question_count}")
        if has_code:
            parts.append("Kod iceriyor")
        if deep_term_count > 0:
            parts.append(f"Derin terim: {deep_term_count}")
        if has_technical_terms:
            parts.append("Teknik icerik")
        parts.append(f"Seviye: {level.value}")
        return ", ".join(parts)


# ── Depth Stone ────────────────────────────────────────────────────────────────

class DepthStone:
    """Estimates how deep a topic is — does it require prerequisite knowledge?"""

    EXPERT_TERMS: set[str] = {
        "lexer", "parser", "AST", "IR", "SSA", "bytecode", "JIT", "AOT",
        "consensus", "raft", "paxos", "distributed lock", "CAP theorem",
        "eventual consistency", "CRDT",
        "memory fence", "cache coherence", "NUMA", "copy-on-write",
        "futures", "promises", "channels", "actors", "software transactional memory",
        "dependent types", " GADT", "type inference", " Hindley-Milner",
    }

    DEEP_TERMS: set[str] = {
        "lifetime", "borrowing", "ownership", "borrow checker", "trait object",
        "smart pointer", "unsafe",
        "coroutine", "event loop", "GIL", "descriptor", "metaclass",
        "garbage collection", "memory model",
        "compiler", "linker", "ELF", "COFF", "stack frame", "calling convention",
        "kubernetes", "container orchestration", "cgroups", "namespace",
        "isolation level", "deadlock", "WAL", "btree", "B+tree", "LSM tree",
        "transaction", "ACID", "MVCC", "query planner",
        "TCP congestion control", "backpressure", "mTLS", "PFS", "unix domain socket",
    }

    PREREQUISITE_PHRASES: tuple[str, ...] = (
        "once you understand", "first you need", " prerequisite ",
        " before we can ", " once you know ", " once you have ",
        " after understanding ", " once you get ",
    )

    def estimate(self, text: str) -> DepthSignal:
        """Analyze text for topic depth."""
        if not text:
            return DepthSignal(
                level=DepthLevel.SURFACE,
                topic_depth_score=0.0,
                requires_prerequisite=False,
                requires_code=False,
                reasoning="Bos metin",
            )

        lower = text.lower()
        expert_count = sum(1 for t in self.EXPERT_TERMS if t in lower)
        deep_count = sum(1 for t in self.DEEP_TERMS if t in lower)
        requires_prerequisite = any(p in lower for p in self.PREREQUISITE_PHRASES)
        has_code = bool(re.search(r"\b(def|class|import|from|typedef|struct|interface)\b", text))

        total_depth_score = (expert_count * 0.4) + (deep_count * 0.2)

        if expert_count >= 2 or total_depth_score >= 0.7:
            level = DepthLevel.EXPERT
        elif expert_count >= 1 or deep_count >= 3 or total_depth_score >= 0.4:
            level = DepthLevel.DEEP
        elif deep_count >= 1 or total_depth_score >= 0.2:
            level = DepthLevel.MODERATE
        else:
            level = DepthLevel.SURFACE

        reasoning = f"expert={expert_count}, deep={deep_count}, prereq={requires_prerequisite}, code={has_code}"

        return DepthSignal(
            level=level,
            topic_depth_score=total_depth_score,
            requires_prerequisite=requires_prerequisite,
            requires_code=has_code,
            reasoning=reasoning,
        )


# ── Urgency Stone ─────────────────────────────────────────────────────────────

class UrgencyStone:
    """Estimates how urgent/pressing the user's query is."""

    URGENT_PHRASES: set[str] = {
        "acil", "hemen", "quickly", "urgent", "asap", "emergency",
        "immediately", "right now", " right away", "sans onekritik",
    }

    def estimate(self, text: str, tide_state=None) -> UrgencySignal:
        """Analyze text for urgency signals."""
        if not text:
            return UrgencySignal(level=UrgencyLevel.NORMAL, pace_score=0.5, reasoning="Bos metin")

        lower = text.lower()

        if any(p in lower for p in self.URGENT_PHRASES):
            return UrgencySignal(level=UrgencyLevel.BRISK, pace_score=1.0, reasoning="Directly urgent")

        word_count = len(text.split())
        if word_count <= 5 and not text.endswith("?"):
            return UrgencySignal(level=UrgencyLevel.BRISK, pace_score=0.8, reasoning=f"Very short query ({word_count} words)")

        if tide_state is not None and hasattr(tide_state, "pace"):
            if tide_state.pace == "brisk":
                return UrgencySignal(level=UrgencyLevel.BRISK, pace_score=0.9, reasoning="TideStone: brisk pace")
            elif tide_state.pace == "relaxed":
                return UrgencySignal(level=UrgencyLevel.RELAXED, pace_score=0.3, reasoning="TideStone: relaxed pace")

        return UrgencySignal(level=UrgencyLevel.NORMAL, pace_score=0.5, reasoning="Normal urgency")


# ── Oracle Core ───────────────────────────────────────────────────────────────

class Oracle:
    """Intelligently routes queries to the best-fit LLM model.

    Uses weighted voting across four stones:
      - ComplexityStone (40%): How textually complex is this?
      - DepthStone (30%): How deep is the topic?
      - UrgencyStone (10%): Is the user in a hurry?
      - RepetitionStone (20%): Has this been asked before?

    Args:
        the_arc: Optional THE ARC instance for repetition detection
        tide_stone: Optional TideStone instance for urgency signals
        persistence_path: Path for route history persistence
    """

    ROUTING_TABLE: dict[ComplexityLevel, tuple[ModelChoice, ModelChoice]] = {
        ComplexityLevel.TRIVIAL:   (ModelChoice.GPT_MINI,      ModelChoice.GPT_MINI),
        ComplexityLevel.SIMPLE:   (ModelChoice.GPT_MINI,      ModelChoice.GEMINI_FLASH),
        ComplexityLevel.MODERATE: (ModelChoice.GEMINI_FLASH,  ModelChoice.GPT_MINI),
        ComplexityLevel.COMPLEX:   (ModelChoice.GEMINI_FLASH,  ModelChoice.GROQ_LLAMA),
        ComplexityLevel.DEEP:     (ModelChoice.GROQ_LLAMA,   ModelChoice.GEMINI_FLASH),
    }

    TOKEN_ESTIMATES: dict[ComplexityLevel, tuple[int, int]] = {
        ComplexityLevel.TRIVIAL:   (5, 30),
        ComplexityLevel.SIMPLE:   (20, 100),
        ComplexityLevel.MODERATE: (50, 250),
        ComplexityLevel.COMPLEX:   (100, 500),
        ComplexityLevel.DEEP:     (200, 1000),
    }

    def __init__(
        self,
        the_arc=None,
        tide_stone=None,
        persistence_path: str | Path = ".oracle.json",
    ):
        self._complexity = ComplexityStone()
        self._depth = DepthStone()
        self._urgency = UrgencyStone()
        self._the_arc = the_arc
        self._tide = tide_stone
        self._persistence_path = Path(persistence_path)

        self._recent_routes: deque[RoutingDecision] = deque(maxlen=50)
        self._model_token_counts: dict[str, int] = {
            "openai:gpt-4.1-mini": 0,
            "gemini:gemini-2.5-flash": 0,
            "groq:llama-3.3-70b-versatile": 0,
        }

        self._load_history()

    def _load_history(self) -> None:
        if not self._persistence_path.exists():
            return
        try:
            data = json.loads(self._persistence_path.read_text(encoding="utf-8"))
            self._model_token_counts = data.get("token_counts", self._model_token_counts)
        except Exception:
            pass

    def _save_history(self) -> None:
        try:
            recent = [d.as_dict() for d in list(self._recent_routes)]
            data = {
                "recent_routes": recent[-20:],
                "token_counts": self._model_token_counts,
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

    def route(self, user_input: str) -> RoutingDecision:
        """Route a user query to the best-fit model."""
        complexity_signal = self._complexity.estimate(user_input)
        depth_signal = self._depth.estimate(user_input)
        tide_state = self._tide.get_state() if self._tide else None
        urgency_signal = self._urgency.estimate(user_input, tide_state)

        # Repetition detection via THE ARC
        is_repeat = False
        if self._the_arc:
            context = self._the_arc.consult(user_input)
            is_repeat = bool(context)

        level_points: dict[ComplexityLevel, float] = {
            ComplexityLevel.TRIVIAL: 0.0,
            ComplexityLevel.SIMPLE: 0.0,
            ComplexityLevel.MODERATE: 0.0,
            ComplexityLevel.COMPLEX: 0.0,
            ComplexityLevel.DEEP: 0.0,
        }

        # Complexity (40%)
        comp_weight = 0.4
        for level, target in [
            (complexity_signal.level, ComplexityLevel.TRIVIAL),
        ]:
            if complexity_signal.level == ComplexityLevel.TRIVIAL:
                level_points[ComplexityLevel.TRIVIAL] += comp_weight
            elif complexity_signal.level == ComplexityLevel.SIMPLE:
                level_points[ComplexityLevel.SIMPLE] += comp_weight
            elif complexity_signal.level == ComplexityLevel.MODERATE:
                level_points[ComplexityLevel.MODERATE] += comp_weight
            elif complexity_signal.level == ComplexityLevel.COMPLEX:
                level_points[ComplexityLevel.COMPLEX] += comp_weight
            elif complexity_signal.level == ComplexityLevel.DEEP:
                level_points[ComplexityLevel.DEEP] += comp_weight
            break

        # Simpler mapping
        comp_level_map = {
            ComplexityLevel.TRIVIAL: ComplexityLevel.TRIVIAL,
            ComplexityLevel.SIMPLE: ComplexityLevel.SIMPLE,
            ComplexityLevel.MODERATE: ComplexityLevel.MODERATE,
            ComplexityLevel.COMPLEX: ComplexityLevel.COMPLEX,
            ComplexityLevel.DEEP: ComplexityLevel.DEEP,
        }
        level_points[comp_level_map[complexity_signal.level]] += comp_weight

        # Depth (30%)
        depth_weight = 0.3
        if depth_signal.level == DepthLevel.SURFACE:
            level_points[ComplexityLevel.SIMPLE] += depth_weight
        elif depth_signal.level == DepthLevel.MODERATE:
            level_points[ComplexityLevel.MODERATE] += depth_weight
        elif depth_signal.level == DepthLevel.DEEP:
            level_points[ComplexityLevel.COMPLEX] += depth_weight
        elif depth_signal.level == DepthLevel.EXPERT:
            level_points[ComplexityLevel.DEEP] += depth_weight

        # Urgency (10%)
        urgency_weight = 0.1
        if urgency_signal.level == UrgencyLevel.BRISK:
            level_points[ComplexityLevel.MODERATE] += urgency_weight
        elif urgency_signal.level == UrgencyLevel.RELAXED:
            level_points[ComplexityLevel.SIMPLE] += urgency_weight

        # Repetition (20%)
        rep_weight = 0.2
        if is_repeat:
            level_points[ComplexityLevel.SIMPLE] += rep_weight
        else:
            level_points[ComplexityLevel.MODERATE] += rep_weight

        final_level = max(level_points, key=lambda k: level_points[k])
        primary, fallback = self.ROUTING_TABLE[final_level]

        min_tokens, max_tokens = self.TOKEN_ESTIMATES[final_level]
        estimated_tokens = (min_tokens + max_tokens) // 2

        reasoning_parts = [
            f"comp={complexity_signal.level.value}",
            f"depth={depth_signal.level.value}",
            f"urgency={urgency_signal.level.value}",
            f"repeat={is_repeat}",
        ]
        reasoning = "; ".join(reasoning_parts)

        decision = RoutingDecision(
            primary_model=primary,
            fallback_model=fallback,
            complexity=final_level,
            reasoning=reasoning,
            confidence=self._calculate_confidence(complexity_signal),
            estimated_tokens=estimated_tokens,
        )

        self._recent_routes.append(decision)
        self._save_history()
        return decision

    def _calculate_confidence(self, signal: ComplexitySignal) -> float:
        base = 0.7
        if signal.word_count > 20 and signal.is_question:
            base += 0.15
        if signal.has_code:
            base += 0.1
        if signal.level == ComplexityLevel.DEEP:
            base += 0.1
        return min(1.0, base)

    def should_upgrade(self, current: ModelChoice, failure_count: int) -> bool:
        if failure_count == 0:
            return False
        if failure_count >= 2:
            return current != ModelChoice.GROQ_LLAMA
        return False

    def upgrade_decision(self, decision: RoutingDecision) -> RoutingDecision:
        if decision.primary_model == ModelChoice.GPT_MINI:
            upgraded = ModelChoice.GEMINI_FLASH
        elif decision.primary_model == ModelChoice.GEMINI_FLASH:
            upgraded = ModelChoice.GROQ_LLAMA
        else:
            upgraded = decision.primary_model

        return RoutingDecision(
            primary_model=upgraded,
            fallback_model=decision.primary_model,
            complexity=decision.complexity,
            reasoning=f"{decision.reasoning} [UPGRADED after failure]",
            confidence=max(0.0, decision.confidence - 0.2),
            estimated_tokens=decision.estimated_tokens,
        )

    def record_tokens(self, model: str, input_tokens: int, output_tokens: int) -> None:
        if model in self._model_token_counts:
            self._model_token_counts[model] += input_tokens + output_tokens
        self._save_history()

    def record_outcome(self, decision: RoutingDecision, user_satisfaction: float) -> None:
        decision.confidence = user_satisfaction
        model_key = decision.primary_model.value
        if model_key in self._model_token_counts:
            self._model_token_counts[model_key] += decision.estimated_tokens
        self._save_history()

    def get_cost_report(self) -> dict:
        total = sum(self._model_token_counts.values())
        return {
            "total_tokens": total,
            "by_model": dict(self._model_token_counts),
            "percentages": {
                m: round((count / total * 100) if total > 0 else 0, 1)
                for m, count in self._model_token_counts.items()
            },
            "total_routes": len(self._recent_routes),
        }

    def suggest_model_for_budget(self, max_cost_factor: float = 1.0) -> ModelChoice:
        if max_cost_factor >= 1.0:
            return ModelChoice.GEMINI_FLASH
        return ModelChoice.GPT_MINI

    def get_adaptive_model(self, user_input: str, budget_factor: float = 1.0) -> ModelChoice:
        decision = self.route(user_input)
        if budget_factor < 1.0:
            if decision.primary_model == ModelChoice.GROQ_LLAMA and budget_factor >= 0.5:
                return decision.primary_model
            elif decision.primary_model == ModelChoice.GEMINI_FLASH and budget_factor >= 0.3:
                return decision.primary_model
            else:
                return ModelChoice.GPT_MINI
        return decision.primary_model

    def get_stats(self) -> dict:
        by_model: dict[str, int] = {}
        by_complexity: dict[str, int] = {}
        confidence_sum = 0.0

        for d in self._recent_routes:
            model_name = d.primary_model.value
            by_model[model_name] = by_model.get(model_name, 0) + 1
            by_complexity[d.complexity.value] = by_complexity.get(d.complexity.value, 0) + 1
            confidence_sum += d.confidence

        return {
            "total_routes": len(self._recent_routes),
            "by_model": by_model,
            "by_complexity": by_complexity,
            "avg_confidence": round(confidence_sum / len(self._recent_routes), 2)
                if self._recent_routes else 0.0,
            "cost_report": self.get_cost_report(),
        }

    def summary(self) -> dict:
        return self.get_stats()

    def reset(self) -> None:
        self._recent_routes.clear()
        self._model_token_counts = {
            "openai:gpt-4.1-mini": 0,
            "gemini:gemini-2.5-flash": 0,
            "groq:llama-3.3-70b-versatile": 0,
        }
        self._save_history()


# ── Global Singleton ──────────────────────────────────────────────────────────

_oracle_instance: Optional[Oracle] = None


def get_oracle() -> Oracle:
    """Get or create the global ORACLE instance."""
    global _oracle_instance
    if _oracle_instance is None:
        _oracle_instance = Oracle()
    return _oracle_instance
