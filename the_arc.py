"""THE ARC — Long-Term Narrative Tracker for AI Assistants.

> *"An AI that knows where this conversation is going — and where it's been."*

A standalone, zero-dependency Python module that tracks the long-term narrative arc of
conversations — decisions made, topics explored, ghost threads, and growth patterns.

Designed to be dropped into any AI assistant project without requiring FRIDAY or any
other system.

Usage:
    from the_arc import TheArc, TurnRecord

    arc = TheArc()

    # After every conversation turn:
    arc.absorb(TurnRecord(turn_id=1, role="user", content="I'll use React Native", timestamp=time.time()))

    # Before every LLM call:
    context = arc.consult("React Native")
    if context:
        system_prompt += "\n\n" + context
"""

from __future__ import annotations

import json
import os
import re
import time
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


# ── Configuration ─────────────────────────────────────────────────────────────

DEFAULT_PATH = ".the_arc.json"
DECAY_PER_DAY = 0.005
ARCHIVE_AFTER_DAYS = 30
DORMANT_THRESHOLD_DAYS = 7
MAX_EPISODES = 500
MAX_TURNS_PER_EPISODE = 50
GHOST_THRESHOLD_DAYS = 30


# ── Data Structures ────────────────────────────────────────────────────────────

class EpisodeStatus(Enum):
    ACTIVE = "active"
    DORMANT = "dormant"
    ARCHIVED = "archived"


class SignalType(Enum):
    QUESTION = "question"
    DECISION = "decision"
    PROGRESS = "progress"
    FRUSTRATION = "frustration"
    REVELATION = "revelation"
    REVISION = "revision"


@dataclass
class Decision:
    content: str
    context: str
    timestamp: float
    outcome: Optional[str] = None  # "completed" | "revoked" | "blocked" | None
    outcome_at: Optional[float] = None


@dataclass
class Signal:
    role: str
    content: str
    timestamp: float
    signal_type: str
    summary: str = ""


@dataclass
class TurnRecord:
    turn_id: int
    role: str
    content: str
    timestamp: float


@dataclass
class Episode:
    id: str
    topic: str
    topic_alias: str
    status: EpisodeStatus
    temperature: float
    decisions: list
    signals: list
    turns: list
    first_seen: float
    last_seen: float
    created_at: float
    updated_at: float
    resolved: bool = False
    resolution: str = ""

    def as_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d

    @staticmethod
    def from_dict(d: dict) -> Episode:
        d["status"] = EpisodeStatus(d.get("status", "active"))
        return Episode(**d)


# ── Core Class ──────────────────────────────────────────────────────────────

class TheArc:
    """Tracks the long-term narrative arc of conversations.

    Args:
        path: Persistence file path. Default: ".the_arc.json"
        decay_per_day: Temperature decay rate per idle day. Default: 0.005
        archive_after_days: Days before archiving dormant episodes. Default: 30
        dormant_threshold_days: Days before marking episode dormant. Default: 7
        max_episodes: Maximum episodes to store (LRU eviction). Default: 500
        max_turns_per_episode: Max turns per episode. Default: 50
        ghost_threshold_days: Days before treating re-emergence as ghost. Default: 30
    """

    DECAY_PER_DAY = DECAY_PER_DAY
    ARCHIVE_AFTER_DAYS = ARCHIVE_AFTER_DAYS
    DORMANT_THRESHOLD_DAYS = DORMANT_THRESHOLD_DAYS
    MAX_EPISODES = MAX_EPISODES
    MAX_TURNS_PER_EPISODE = MAX_TURNS_PER_EPISODE
    GHOST_THRESHOLD_DAYS = GHOST_THRESHOLD_DAYS

    def __init__(
        self,
        path: str | Path = DEFAULT_PATH,
        decay_per_day: float = DECAY_PER_DAY,
        archive_after_days: int = ARCHIVE_AFTER_DAYS,
        dormant_threshold_days: int = DORMANT_THRESHOLD_DAYS,
        max_episodes: int = MAX_EPISODES,
        max_turns_per_episode: int = MAX_TURNS_PER_EPISODE,
        ghost_threshold_days: int = GHOST_THRESHOLD_DAYS,
    ):
        self._path = Path(path)
        self._decay_per_day = decay_per_day
        self._archive_after_days = archive_after_days
        self._dormant_threshold_days = dormant_threshold_days
        self._max_episodes = max_episodes
        self._max_turns_per_episode = max_turns_per_episode
        self._ghost_threshold_days = ghost_threshold_days
        self._episodes: dict[str, Episode] = {}
        self._turn_count: int = 0
        self._load()

    # ── Persistence ─────────────────────────────────────────────────────────

    def _load(self) -> None:
        """Load episodes from disk."""
        if not self._path.exists():
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            self._episodes = {}
            for item in raw.get("episodes", []):
                ep = Episode.from_dict(item)
                self._episodes[ep.id] = ep
            self._turn_count = raw.get("turn_count", 0)
        except Exception:
            self._episodes = {}
            self._turn_count = 0

    def _save(self) -> None:
        """Save episodes to disk (atomic write)."""
        try:
            data = {
                "episodes": [e.as_dict() for e in self._episodes.values()],
                "turn_count": self._turn_count,
            }
            content = json.dumps(data, ensure_ascii=False, indent=2)

            if self._path.exists() and self._path.stat().st_size > 10:
                import shutil
                backup = self._path.with_suffix(".backup.json")
                shutil.copy2(self._path, backup)

            temp_path = self._path.with_suffix(".tmp")
            if temp_path.exists():
                temp_path.unlink()
            temp_path.write_text(content, encoding="utf-8")
            import os as _os
            _os.replace(str(temp_path), str(self._path))
        except Exception:
            pass

    def _normalize_topic(self, text: str) -> str:
        """Normalize text into an episode topic key."""
        text = text.lower().strip()
        stop = {
            "bir", "ve", "ile", "için", "olan", "bu", "ne", "nasıl", "neden",
            "the", "a", "an", "is", "are", "was", "were", "to", "of", "in",
        }
        words = [w for w in re.findall(r"\w+", text) if len(w) > 2 and w not in stop]
        return " ".join(words[:8])

    def _detect_signal_type(self, role: str, content: str) -> tuple[SignalType, str]:
        """Detect signal type and return (SignalType, summary)."""
        lower = content.lower()
        summary = content[:120]

        decision_patterns = [
            "yapacağım", "yapmaya karar", "seçtim", "tercih ettim",
            "use ", "i will use", "i decided", "i chose", "going with",
            "i'll go with", "i am going to", "i'm going to",
        ]
        if any(p in lower for p in decision_patterns):
            return SignalType.DECISION, summary

        progress_patterns = [
            "tamamladım", "bitirdim", "yaptım", "hallettim",
            "completed", "finished", "done", "made it",
        ]
        if any(p in lower for p in progress_patterns):
            return SignalType.PROGRESS, summary

        revision_patterns = [
            "asında değil", "fikrimi değiştirdim", "yapmayacağım",
            "instead", "actually not", "changed my mind",
        ]
        if any(p in lower for p in revision_patterns):
            return SignalType.REVISION, summary

        frustration_patterns = [
            "yapamadım", "olmadı", "hata aldım", "çalışmıyor",
            "failed", "didn't work", "error", "stuck", "blocked",
        ]
        if any(p in lower for p in frustration_patterns):
            return SignalType.FRUSTRATION, summary

        question_patterns = ["?", " mı?", " mi?", " mu?", " mü?"]
        if any(lower.strip().endswith(p) for p in question_patterns):
            return SignalType.QUESTION, summary

        return SignalType.REVELATION, summary

    # ── Public API ─────────────────────────────────────────────────────────

    def absorb(self, turn: TurnRecord) -> list[str]:
        """Absorb a conversation turn into THE ARC.

        Creates or updates an episode for the turn's topic.
        Returns list of affected episode IDs.

        Args:
            turn: TurnRecord with turn_id, role, content, timestamp

        Returns:
            List of episode IDs that were affected
        """
        self._turn_count += 1
        key = self._normalize_topic(turn.content)
        if not key:
            return []

        now = time.time()
        triggered: list[str] = []

        found_ep = None
        for ep in self._episodes.values():
            if ep.topic == key and ep.status != EpisodeStatus.ARCHIVED:
                found_ep = ep
                break

        if found_ep:
            triggered = [found_ep.id]
            found_ep.turns.append(turn)
            found_ep.last_seen = now
            found_ep.updated_at = now
            found_ep.temperature = min(1.0, found_ep.temperature + 0.05)

            if found_ep.status == EpisodeStatus.DORMANT:
                found_ep.status = EpisodeStatus.ACTIVE

            if len(found_ep.turns) > self._max_turns_per_episode:
                found_ep.turns = found_ep.turns[-self._max_turns_per_episode:]

            sig_type, sig_summary = self._detect_signal_type(turn.role, turn.content)
            found_ep.signals.append(Signal(
                role=turn.role,
                content=sig_summary,
                timestamp=turn.timestamp,
                signal_type=sig_type.value,
                summary=sig_summary,
            ))

            if sig_type == SignalType.DECISION:
                found_ep.decisions.append(Decision(
                    content=turn.content[:200],
                    context="",
                    timestamp=now,
                ))

            if sig_type == SignalType.REVISION and found_ep.decisions:
                found_ep.decisions[-1].outcome = "revoked"
                found_ep.decisions[-1].outcome_at = now

        else:
            sig_type, sig_summary = self._detect_signal_type(turn.role, turn.content)
            new_ep = Episode(
                id=str(uuid.uuid4())[:8],
                topic=key,
                topic_alias=turn.content[:80],
                status=EpisodeStatus.ACTIVE,
                temperature=0.3,
                decisions=[],
                signals=[Signal(
                    role=turn.role,
                    content=sig_summary,
                    timestamp=turn.timestamp,
                    signal_type=sig_type.value,
                    summary=sig_summary,
                )],
                turns=[turn],
                first_seen=now,
                last_seen=now,
                created_at=now,
                updated_at=now,
            )
            self._episodes[new_ep.id] = new_ep
            triggered = [new_ep.id]

            if len(self._episodes) > self._max_episodes:
                oldest = min(self._episodes.values(), key=lambda e: e.last_seen)
                del self._episodes[oldest.id]

        self._save()
        return triggered

    def consult(self, query: str, top_k: int = 3) -> str:
        """Consult THE ARC before responding.

        Returns relevant episode context as a directive string.
        Call this before every LLM response.

        Args:
            query: Current user message
            top_k: Maximum episodes to return. Default: 3

        Returns:
            Directive string with episode context, or "" if no match
        """
        key = self._normalize_topic(query)
        if not key:
            return ""

        candidates: list[tuple[float, Episode]] = []
        for ep in self._episodes.values():
            if ep.status == EpisodeStatus.ARCHIVED:
                continue
            query_words = set(key.split())
            ep_words = set(ep.topic.split())
            if not query_words or not ep_words:
                continue
            jaccard = len(query_words & ep_words) / len(query_words | ep_words)
            if jaccard > 0.2:
                candidates.append((jaccard, ep))

        candidates.sort(key=lambda x: (-x[0], -x[1].temperature))
        top = candidates[:top_k]

        if not top:
            return ""

        lines = [f"[THE ARC] {len(top)} episode(s) matched:\n"]
        for _, ep in top:
            status_icon = {"active": "ACTIVE", "dormant": "DORMANT", "archived": "GHOST"}.get(ep.status.value, "")
            lines.append(f"  [{ep.id}] '{ep.topic_alias[:40]}' — {status_icon} ({ep.temperature:.2f})")

            if ep.decisions:
                last_dec = ep.decisions[-1]
                lines.append(f"     Last decision: {last_dec.content[:80]}")
                if last_dec.outcome:
                    lines.append(f"     Outcome: {last_dec.outcome}")

            if ep.signals:
                last_sig = ep.signals[-1]
                lines.append(f"     Last signal: {last_sig.signal_type} — {last_sig.summary[:60]}")

            if ep.status == EpisodeStatus.ARCHIVED:
                days_ago = (time.time() - ep.last_seen) / 86400
                lines.append(f"     GHOST THREAD — seen {days_ago:.0f} days ago")

            lines.append("")

        return "\n".join(lines)

    def get_decision_context(self, query: str) -> str:
        """Get decisions related to a topic.

        Args:
            query: Current user message

        Returns:
            String summarizing decisions for the topic, or ""
        """
        key = self._normalize_topic(query)
        if not key:
            return ""

        for ep in self._episodes.values():
            if ep.topic == key and ep.decisions:
                lines = ["[THE ARC — Decision Context]"]
                for i, dec in enumerate(ep.decisions[-5:], 1):
                    outcome_str = f" -> {dec.outcome}" if dec.outcome else ""
                    lines.append(f"  {i}. {dec.content[:80]}{outcome_str}")
                return "\n".join(lines)
        return ""

    def get_stats(self) -> dict:
        """Get THE ARC statistics.

        Returns:
            Dict with total_episodes, active, dormant, archived,
            total_decisions, ghost_threads_detected, total_turns_tracked
        """
        active = sum(1 for e in self._episodes.values() if e.status == EpisodeStatus.ACTIVE)
        dormant = sum(1 for e in self._episodes.values() if e.status == EpisodeStatus.DORMANT)
        archived = sum(1 for e in self._episodes.values() if e.status == EpisodeStatus.ARCHIVED)
        total_decisions = sum(len(e.decisions) for e in self._episodes.values())
        ghost_threads = sum(
            1 for e in self._episodes.values()
            if e.status == EpisodeStatus.ARCHIVED and e.temperature > 0.0
        )
        return {
            "total_episodes": len(self._episodes),
            "active": active,
            "dormant": dormant,
            "archived": archived,
            "total_decisions": total_decisions,
            "ghost_threads_detected": ghost_threads,
            "total_turns_tracked": self._turn_count,
        }

    def run_decay(self) -> None:
        """Run temperature decay on all episodes.

        Call this periodically (e.g., daily or after idle).
        """
        now = time.time()
        changed = False

        for ep in self._episodes.values():
            if ep.status == EpisodeStatus.ARCHIVED:
                continue

            days_idle = (now - ep.last_seen) / 86400

            if days_idle >= self._archive_after_days:
                ep.status = EpisodeStatus.ARCHIVED
                ep.temperature = 0.0
                changed = True
            elif days_idle >= self._dormant_threshold_days:
                ep.status = EpisodeStatus.DORMANT
                ep.temperature = max(0.0, ep.temperature - self._decay_per_day * days_idle)
                changed = True
            elif ep.temperature > 0.3:
                ep.temperature = max(0.3, ep.temperature - self._decay_per_day * days_idle)
                changed = True

        if changed:
            self._save()

    def summary(self) -> dict:
        """Get a human-readable summary of THE ARC state."""
        return self.get_stats()

    def reset(self) -> None:
        """Clear all episodes and reset turn count."""
        self._episodes = {}
        self._turn_count = 0
        self._save()