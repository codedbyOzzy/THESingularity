"""ARCHIVE â€” Longitudinal User Memory System for AI Assistants.

> *"FRIDAY seni gunler/haftalar sonra da hatirlasin â€” sadece bilgileri deÄŸil, DUYGULARI da."*

ARCHIVE, FRIDAY'in kisa vadeli episode bellgini (THE ARC) uzun vadeli,
hiyerarsik ve duygusal bir bellek sistemine donusturur.

Designed to be dropped into any AI assistant project without requiring FRIDAY
or any other system.

Usage:
    from archive import Archive, MemoryTier, MemoryEntry

    archive = Archive(the_arc=None)

    # Absorb a THE ARC episode into ARCHIVE
    archive.absorb_episode(episode)

    # Query for context
    context = archive.query("3 hafta once ne yapmistim?", depth="medium")

    # Record emotional signal
    archive.record_emotional_signal("frustration", 0.8)
"""

from __future__ import annotations

import json
import re
import time
from collections import deque
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


# â”€â”€ Enums â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class MemoryTier(Enum):
    SHORT_TERM = "short"    # THE ARC ile ayni (episode bazli)
    MEDIUM_TERM = "medium"  # 2-8 hafta
    LONG_TERM = "long"      # Aylar
    EMOTIONAL = "emotional" # Kalici parmak izi


# â”€â”€ Data Structures â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@dataclass
class MemoryEntry:
    id: str
    content: str
    tier: MemoryTier
    created_at: float
    last_accessed: float
    access_count: int
    source_episode: str
    tags: list[str]
    emotional_weight: float
    summary: str

    def as_dict(self) -> dict:
        d = asdict(self)
        d["tier"] = self.tier.value
        return d

    @staticmethod
    def from_dict(d: dict) -> MemoryEntry:
        d["tier"] = MemoryTier(d.get("tier", "short"))
        return MemoryEntry(**d)


@dataclass
class EmotionalSignature:
    language_preference: str = "tr"
    communication_style: str = "detailed"
    patience_level: str = "medium"
    frustration_triggers: list[str] = field(default_factory=list)
    satisfaction_signals: list[str] = field(default_factory=list)
    peak_productivity_hours: list[int] = field(default_factory=list)
    last_updated: float = field(default_factory=time.time)

    def as_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> EmotionalSignature:
        return EmotionalSignature(**d)

    def update_trigger(self, trigger: str, signal_type: str = "frustration") -> None:
        """Add or update a trigger signal."""
        if signal_type == "frustration":
            if trigger not in self.frustration_triggers:
                self.frustration_triggers.append(trigger)
        else:
            if trigger not in self.satisfaction_signals:
                self.satisfaction_signals.append(trigger)
        self.last_updated = time.time()


@dataclass
class LongTermProfile:
    occupation: str = ""
    tools_stack: list[str] = field(default_factory=list)
    learning_history: list[str] = field(default_factory=list)
    goals_completed: list[str] = field(default_factory=list)
    preferences: dict[str, str] = field(default_factory=dict)
    last_updated: float = field(default_factory=time.time)

    def as_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> LongTermProfile:
        return LongTermProfile(**d)


@dataclass
class MediumTermContext:
    topic: str
    status: str  # "in_progress" | "paused" | "completed"
    started_at: float
    last_mentioned: float
    progress_notes: list[str]
    blockers: list[str]
    confidence_level: float

    def as_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> MediumTermContext:
        return MediumTermContext(**d)


# â”€â”€ Archive Core â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class Archive:
    """Longitudinal memory system with tiered storage.

    Memory tiers:
      - SHORT_TERM: THE ARC episodes (1-14 days)
      - MEDIUM_TERM: Active projects/learning (14-60 days)
      - LONG_TERM: General profile/occupation (60+ days)
      - EMOTIONAL: User's communication fingerprint (persistent)

    Args:
        the_arc: Optional THE ARC instance for episode absorption
        persistence_path: Path for JSON persistence
    """

    # Configuration
    MEDIUM_THRESHOLD_DAYS = 14    # Days before upgrading to medium-term
    LONG_THRESHOLD_DAYS = 60     # Days before upgrading to long-term
    DECAY_PER_DAY = 0.005        # Temperature decay rate
    MAX_MEDIUM_ENTRIES = 50      # Max medium-term entries
    MAX_LONG_ENTRIES = 20        # Max long-term entries

    def __init__(
        self,
        the_arc=None,
        persistence_path: str | Path = ".archive.json",
    ):
        self._the_arc = the_arc
        self._persistence_path = Path(persistence_path)

        self._medium_term: dict[str, MediumTermContext] = {}
        self._long_term: LongTermProfile = LongTermProfile()
        self._emotional: EmotionalSignature = EmotionalSignature()

        self._load()

    # â”€â”€ Persistence â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _load(self) -> None:
        if not self._persistence_path.exists():
            return
        try:
            data = json.loads(self._persistence_path.read_text(encoding="utf-8"))
            self._medium_term = {
                k: MediumTermContext.from_dict(v)
                for k, v in data.get("medium_term", {}).items()
            }
            self._long_term = LongTermProfile.from_dict(data.get("long_term", {}))
            self._emotional = EmotionalSignature.from_dict(data.get("emotional", {}))
        except Exception:
            pass

    def _save(self) -> None:
        try:
            data = {
                "medium_term": {k: v.as_dict() for k, v in self._medium_term.items()},
                "long_term": self._long_term.as_dict(),
                "emotional": self._emotional.as_dict(),
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

    # â”€â”€ Episode Absorption â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def absorb_episode(self, episode) -> None:
        """Absorb a THE ARC episode into ARCHIVE.

        Args:
            episode: A THE ARC Episode object with id, topic, topic_alias,
                     temperature, status, decisions, signals, turns, etc.
        """
        if not episode:
            return

        # Check episode age
        last_seen = getattr(episode, "last_seen", time.time())
        days_idle = (time.time() - last_seen) / 86400

        topic_key = getattr(episode, "topic", "").lower().replace(" ", "_")
        if not topic_key:
            return

        # Determine tier based on idle time
        if days_idle >= self.LONG_THRESHOLD_DAYS:
            self._upgrade_to_long_term(episode)
        elif days_idle >= self.MEDIUM_THRESHOLD_DAYS:
            self._upgrade_to_medium_term(episode)
        else:
            # Still short-term, just record in emotional if significant
            temp = getattr(episode, "temperature", 0.0)
            if temp > 0.7:
                self._extract_emotional_from_episode(episode)

    def _upgrade_to_medium_term(self, episode) -> None:
        """Upgrade a dormant episode to medium-term."""
        topic_key = getattr(episode, "topic", "").lower().replace(" ", "_")

        # Extract signals for emotional data
        self._extract_emotional_from_episode(episode)

        # Create medium-term context
        decisions = getattr(episode, "decisions", [])
        latest_decision = decisions[-1] if decisions else None

        ctx = MediumTermContext(
            topic=topic_key,
            status="in_progress" if latest_decision else "paused",
            started_at=getattr(episode, "first_seen", time.time()),
            last_mentioned=getattr(episode, "last_seen", time.time()),
            progress_notes=[],
            blockers=[],
            confidence_level=getattr(episode, "temperature", 0.5),
        )
        self._medium_term[topic_key] = ctx

        # Limit size
        if len(self._medium_term) > self.MAX_MEDIUM_ENTRIES:
            oldest = min(self._medium_term.items(), key=lambda x: x[1].last_mentioned)
            del self._medium_term[oldest[0]]

        self._save()

    def _upgrade_to_long_term(self, episode) -> None:
        """Upgrade a very old episode to long-term profile."""
        # Update long-term profile based on episode content
        topic = getattr(episode, "topic", "")

        # Detect occupation/tools from episode
        if any(kw in topic.lower() for kw in ["python", "flask", "django", "api"]):
            if "python" not in self._long_term.tools_stack:
                self._long_term.tools_stack.append("python")
        if any(kw in topic.lower() for kw in ["rust", "lifetime", "borrowing"]):
            if "rust" not in self._long_term.tools_stack:
                self._long_term.tools_stack.append("rust")
        if any(kw in topic.lower() for kw in ["docker", "container", "kubernetes"]):
            if "docker" not in self._long_term.tools_stack:
                self._long_term.tools_stack.append("docker")

        self._long_term.last_updated = time.time()
        self._save()

    def _extract_emotional_from_episode(self, episode) -> None:
        """Extract emotional signals from an episode."""
        if not episode:
            return

        # Count frustration/progress signals
        signals = getattr(episode, "signals", [])
        frustration_count = sum(1 for s in signals if getattr(s, "signal_type", "") == "frustration")
        progress_count = sum(1 for s in signals if getattr(s, "signal_type", "") == "progress")

        if frustration_count >= 3:
            topic = getattr(episode, "topic", "unknown")
            trigger = f"frustrated_by_{topic[:20]}"
            self._emotional.update_trigger(trigger, "frustration")

        if progress_count >= 2:
            topic = getattr(episode, "topic", "unknown")
            signal = f"progress_in_{topic[:20]}"
            self._emotional.update_trigger(signal, "satisfaction")

    # â”€â”€ Emotional Signal Processing â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def record_emotional_signal(self, signal_type: str, value: float) -> None:
        """Record an emotional signal from TideStone or user behavior.

        Args:
            signal_type: "frustration" | "satisfaction" | "patience" | "energy"
            value: Signal intensity 0.0-1.0
        """
        now = time.time()
        hour = datetime.fromtimestamp(now).hour

        if signal_type == "frustration" and value > 0.7:
            # High frustration â€” record time context
            if hour >= 22 or hour <= 5:
                self._emotional.update_trigger("late_night_frustration", "frustration")
            self._emotional.patience_level = "low"

        if signal_type == "satisfaction" and value > 0.7:
            self._emotional.update_trigger("genuine_satisfaction", "satisfaction")

        if signal_type == "patience":
            if value < 0.3:
                self._emotional.patience_level = "low"
            elif value > 0.7:
                self._emotional.patience_level = "high"
            else:
                self._emotional.patience_level = "medium"

        if signal_type == "energy" and value > 0.7:
            if hour not in self._emotional.peak_productivity_hours:
                if len(self._emotional.peak_productivity_hours) < 6:
                    self._emotional.peak_productivity_hours.append(hour)
                    self._emotional.peak_productivity_hours.sort()

        self._emotional.last_updated = now
        self._save()

    def get_emotional_prompt(self) -> str:
        """Get emotional signature as a system prompt addition.

        Returns:
            String describing the user's emotional profile
        """
        parts = []

        if self._emotional.communication_style != "unknown":
            if self._emotional.communication_style == "detailed":
                parts.append("Bu kullanici detay ister, kisa cevaplari sevmez.")
            elif self._emotional.communication_style == "concise":
                parts.append("Bu kullanici Ã¶zet bilgi tercih eder, gereksiz detay istemez.")

        if self._emotional.patience_level == "low":
            parts.append("Kullanici sabirsiz olabilir â€” kisa ve Ã¶z yanitlar uygun.")
        elif self._emotional.patience_level == "high":
            parts.append("Kullanici sabirli â€” detayli aÃ§iklamalar uygun.")

        if self._emotional.frustration_triggers:
            triggers_str = ", ".join(self._emotional.frustration_triggers[:3])
            parts.append(f"Frustraston tetikleyicileri: {triggers_str}")

        if self._emotional.peak_productivity_hours:
            hours_str = ", ".join(str(h) for h in self._emotional.peak_productivity_hours[:4])
            parts.append(f"En verimli oldugu saatler: {hours_str}")

        if self._emotional.satisfaction_signals:
            signals_str = ", ".join(self._emotional.satisfaction_signals[:2])
            parts.append(f"Memnuniyet belirtileri: {signals_str}")

        if not parts:
            return ""

        return "[ARCHIVE - Kullanici Profili]\n" + "\n".join(parts)

    # â”€â”€ Query System â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def query(self, query: str, depth: str = "all") -> str:
        """Query ARCHIVE for relevant context.

        Args:
            query: User's query string
            depth: "short" | "medium" | "long" | "emotional" | "all"

        Returns:
            System prompt-compatible context string
        """
        results = []

        if depth in ("short", "all"):
            if self._the_arc:
                ctx = self._the_arc.consult(query)
                if ctx:
                    results.append(f"[ARCHIVE - Kisa Vadeli]\n{ctx}")

        if depth in ("medium", "all"):
            medium_results = self._query_medium_term(query)
            if medium_results:
                results.append(f"[ARCHIVE - Orta Vadeli]\n{medium_results}")

        if depth in ("long", "all"):
            long_results = self._query_long_term(query)
            if long_results:
                results.append(f"[ARCHIVE - Uzun Vadeli]\n{long_results}")

        if depth in ("emotional", "all"):
            emotional = self.get_emotional_prompt()
            if emotional:
                results.append(f"[ARCHIVE - Duygusal]\n{emotional}")

        return "\n\n".join(results) if results else ""

    def _query_medium_term(self, query: str) -> str:
        """Query medium-term context."""
        query_lower = query.lower()
        matches = []

        for topic, ctx in self._medium_term.items():
            if query_lower in topic or topic in query_lower:
                if ctx.status == "in_progress":
                    days_ago = (time.time() - ctx.last_mentioned) / 86400
                    matches.append(
                        f"- {topic}: {ctx.status} ({days_ago:.0f} gun once, {ctx.confidence_level:.1f} guven)"
                    )
                    if ctx.blockers:
                        matches.append(f"  Blocker: {', '.join(ctx.blockers[:2])}")

        if not matches:
            return ""

        return "Aktif projeler:\n" + "\n".join(matches)

    def _query_long_term(self, query: str) -> str:
        """Query long-term profile."""
        parts = []

        if self._long_term.occupation:
            parts.append(f"Is: {self._long_term.occupation}")

        if self._long_term.tools_stack:
            tools_str = ", ".join(self._long_term.tools_stack[:5])
            parts.append(f"Araclari: {tools_str}")

        if self._long_term.learning_history:
            recent = self._long_term.learning_history[-3:]
            parts.append(f"Ogrenme gecmisi: {', '.join(recent)}")

        if self._long_term.goals_completed:
            recent_goals = self._long_term.goals_completed[-3:]
            parts.append(f"Tamamlanan hedefler: {', '.join(recent_goals)}")

        return "\n".join(parts) if parts else ""

    # â”€â”€ Upgrade Cycle â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def run_upgrade_cycle(self) -> None:
        """Run the periodic upgrade cycle â€” check THE ARC for old episodes."""
        if not self._the_arc:
            return

        # Check all episodes for dormancy
        stats = self._the_arc.get_stats()
        total = stats.get("total_episodes", 0)

        if total == 0:
            return

        # Request all episode IDs from THE ARC
        # THE ARC consult can find matching episodes
        # We iterate over possible topics to find dormant ones
        pass  # THE ARC doesn't expose episode iteration, so we rely on absorb_episode being called

    def decay_medium_term(self) -> None:
        """Apply time-based decay to medium-term entries."""
        now = time.time()
        to_remove = []

        for topic, ctx in self._medium_term.items():
            days_idle = (now - ctx.last_mentioned) / 86400
            if days_idle > 90:  # 90+ days idle = remove
                to_remove.append(topic)
            elif days_idle > 30:
                # Reduce confidence
                ctx.confidence_level = max(0.0, ctx.confidence_level - 0.01)

        for topic in to_remove:
            del self._medium_term[topic]

        if to_remove:
            self._save()

    # â”€â”€ Stats â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def get_stats(self) -> dict:
        """Get ARCHIVE statistics."""
        return {
            "medium_term_entries": len(self._medium_term),
            "long_term_profile": bool(self._long_term.occupation),
            "emotional_triggers": len(self._emotional.frustration_triggers),
            "satisfaction_signals": len(self._emotional.satisfaction_signals),
            "peak_hours": self._emotional.peak_productivity_hours,
            "patience_level": self._emotional.patience_level,
            "tools_count": len(self._long_term.tools_stack),
        }

    def summary(self) -> str:
        """Human-readable ARCHIVE summary."""
        parts = [
            f"Medium-term: {len(self._medium_term)} entries",
            f"Long-term: {self._long_term.occupation or 'not set'}",
            f"Emotional: patience={self._emotional.patience_level}",
            f"Peak hours: {self._emotional.peak_productivity_hours}",
        ]
        return " | ".join(parts)

    def reset_tier(self, tier: MemoryTier) -> None:
        """Clear a specific memory tier."""
        if tier == MemoryTier.MEDIUM_TERM:
            self._medium_term.clear()
        elif tier == MemoryTier.LONG_TERM:
            self._long_term = LongTermProfile()
        elif tier == MemoryTier.EMOTIONAL:
            self._emotional = EmotionalSignature()
        self._save()

    def reset(self) -> None:
        """Clear all memory tiers."""
        self._medium_term.clear()
        self._long_term = LongTermProfile()
        self._emotional = EmotionalSignature()
        self._save()


# â”€â”€ Global Singleton â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_archive_instance: Optional[Archive] = None


def get_archive() -> Archive:
    """Get or create the global ARCHIVE instance."""
    global _archive_instance
    if _archive_instance is None:
        _archive_instance = Archive()
    return _archive_instance
