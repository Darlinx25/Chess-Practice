"""Load exercises from the extracted data file."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Optional

import chess

from app.config import EXERCISES_JSON


@dataclass(frozen=True)
class Exercise:
    number: int
    fen: str
    moves: tuple[str, ...] = ()
    difficulty: str = "unknown"
    side: str = "w"
    rating: int = 0
    themes: tuple[str, ...] = ()
    puzzle_id: str = ""
    prelude: str = ""

    @property
    def label(self) -> str:
        return f"Ejercicio {self.number}"

    @property
    def side_to_move(self) -> chess.Color:
        return chess.WHITE if self.side != "b" else chess.BLACK


def _load() -> list[dict]:
    with open(EXERCISES_JSON) as fh:
        return json.load(fh)


def load_exercises() -> list[Exercise]:
    exs = []
    for r in _load():
        fen = r["fen"]
        if " " not in fen:
            fen = f"{fen} w - - 0 1"
        exs.append(Exercise(
            number=int(r["number"]),
            fen=fen,
            moves=tuple(r.get("moves", ())),
            difficulty=r.get("difficulty", "unknown"),
            side=fen.split()[1],
            rating=int(r.get("rating", 0)),
            themes=tuple(r.get("themes", ())),
            puzzle_id=r.get("puzzle_id", ""),
            prelude=r.get("prelude", ""),
        ))
    return exs


def total() -> int:
    return len(_load())


def difficulty_label(d: str) -> str:
    return {"easy": "Fáciles", "intermediate": "Intermedios",
            "advanced": "Avanzados"}.get(d, d)
