"""Chess-Practice session/cycle coach logic.

Sessions partition the exercises into contiguous blocks of a configured
size. Within a session, exercises are served in order; missed ones are
re-queued (repeated up to MAX_REPEAT_ROUNDS). A cycle is a full pass over all
exercises; the method prescribes up to 7 cycles.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from app import storage
from app.config import (CYCLES, DEFAULT_SESSION_SIZE, MAX_REPEAT_ROUNDS,
                        PROBLEM_THRESHOLD)
from app.exercises import Exercise, load_exercises, total

STATE_KEY = "session_state"
CYCLE_KEY = "cycle"
SESSION_KEY = "session_number"

TOTAL = total()


@dataclass
class SessionState:
    session_id: int
    cycle: int
    session_number: int
    block: list[int] = field(default_factory=list)
    queue: list[int] = field(default_factory=list)
    repeats: list[int] = field(default_factory=list)
    done: list[int] = field(default_factory=list)
    round_counts: dict[int, int] = field(default_factory=dict)

    @property
    def total(self) -> int:
        return len(self.block)

    @property
    def solved_count(self) -> int:
        return len(self.done)

    def to_json(self) -> str:
        return json.dumps({
            "session_id": self.session_id,
            "cycle": self.cycle,
            "session_number": self.session_number,
            "block": self.block,
            "queue": self.queue,
            "repeats": self.repeats,
            "done": self.done,
            "round_counts": self.round_counts,
        })

    @classmethod
    def from_json(cls, s: str) -> "SessionState":
        d = json.loads(s)
        return cls(
            session_id=int(d["session_id"]),
            cycle=int(d["cycle"]),
            session_number=int(d["session_number"]),
            block=[int(x) for x in d["block"]],
            queue=[int(x) for x in d["queue"]],
            repeats=[int(x) for x in d["repeats"]],
            done=[int(x) for x in d["done"]],
            round_counts={int(k): int(v) for k, v in d["round_counts"].items()},
        )


def session_size() -> int:
    try:
        return int(storage.get_setting("session_size", str(DEFAULT_SESSION_SIZE)))
    except (TypeError, ValueError):
        return DEFAULT_SESSION_SIZE


def load_state() -> SessionState | None:
    raw = storage.get_setting(STATE_KEY)
    if raw:
        try:
            return SessionState.from_json(raw)
        except (ValueError, KeyError):
            return None
    return None


def save_state(state: SessionState) -> None:
    storage.set_setting(STATE_KEY, state.to_json())


def _exercise_map(exs: list[Exercise]) -> dict[int, Exercise]:
    return {e.number: e for e in exs}


def _next_block(cycle: int, size: int) -> tuple[int, int]:
    """Compute (start, end) of the next incomplete session block in a cycle."""
    done = set(storage.solved_numbers_in_cycle(cycle))
    first_undone = 1
    while first_undone <= TOTAL and first_undone in done:
        first_undone += 1
    if first_undone > TOTAL:
        return TOTAL + 1, TOTAL + 1
    start = ((first_undone - 1) // size) * size + 1
    end = min(start + size - 1, TOTAL)
    return start, end


def _current_cycle() -> int:
    raw = storage.get_setting(CYCLE_KEY, "1")
    try:
        return min(max(int(raw), 1), CYCLES)
    except (TypeError, ValueError):
        return 1


def _problem_numbers() -> set[int]:
    """Exercises flagged as problems (repeated lifetime misses)."""
    bad = set()
    for e in load_exercises():
        st = storage.exercise_stats(e.number)
        if st["misses"] >= PROBLEM_THRESHOLD:
            bad.add(e.number)
    return bad


def start_or_resume_session() -> SessionState:
    existing = load_state()
    if existing:
        return existing

    cycle = _current_cycle()
    size = session_size()
    start, end = _next_block(cycle, size)
    if start > TOTAL:
        # cycle complete
        cycle = cycle + 1 if cycle < CYCLES else 1
        storage.set_setting(CYCLE_KEY, str(cycle))
        start, end = _next_block(cycle, size)

    block = list(range(start, end + 1))
    session_id = storage.create_session(cycle, start // size + 1, len(block))
    state = SessionState(
        session_id=session_id,
        cycle=cycle,
        session_number=start // size + 1,
        block=block,
        queue=list(block),
    )
    save_state(state)
    return state


def next_exercise(state: SessionState) -> Exercise | None:
    exs = _exercise_map(load_exercises())
    while state.queue:
        n = state.queue.pop(0)
        if n not in state.done:
            return exs.get(n)
    return None


def _repeat_priority(state: SessionState, n: int) -> int:
    st = storage.exercise_stats(n)
    return st["misses"]


def submit(state: SessionState, number: int, solved: bool) -> None:
    """Record the result and re-queue the exercise if it was missed."""
    if number in state.done:
        # already solved: replaying from the sidebar must not re-count it
        return
    if solved:
        state.done.append(number)
    else:
        rnd = state.round_counts.get(number, 0) + 1
        state.round_counts[number] = rnd
        if rnd < MAX_REPEAT_ROUNDS:
            # re-queue at the end of the repeat list
            state.repeats.append(number)
    # refill repeats once the main queue is exhausted
    if not state.queue and state.repeats:
        # priority: problem exercises first
        state.repeats.sort(key=lambda n: -_repeat_priority(state, n))
        state.queue, state.repeats = state.repeats, []
    save_state(state)


def is_complete(state: SessionState) -> bool:
    return len(state.done) >= state.total


def finish(state: SessionState) -> None:
    storage.finish_session(state.session_id)
    storage.set_setting(STATE_KEY, "")
    # advance cycle if the whole cycle is now done
    done = storage.cycle_summary(state.cycle)["done"]
    if done >= TOTAL and state.cycle < CYCLES:
        storage.set_setting(CYCLE_KEY, str(state.cycle + 1))


def cycle_info() -> dict:
    return {"cycle": _current_cycle(), "cycles": CYCLES,
            "size": session_size()}
