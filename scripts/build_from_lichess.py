"""Build data/exercises.json from the Lichess puzzle CSV.

The export FEN is the position one ply before the puzzle starts: the first
move in `Moves` is the game's last move (prelude), and the solver is the side
that plays from `Moves[1]` onwards (the winning side). We apply the prelude so
`fen` in the output is the position the user actually faces, with the user
to move. `moves` then alternates user / opponent starting with the user and
always ends on the user's winning move.

Every row is validated with python-chess; rows that fail to replay are skipped
(with a warning) so a malformed export cannot poison the data file.
"""
from __future__ import annotations

import csv
import json
import os
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import (EXERCISES_JSON, EASY_RATING_MAX,  # noqa: E402
                        INTERMEDIATE_RATING_MAX, PUZZLES_CSV)

CSV_HEADER = [
    "PuzzleId", "FEN", "Moves", "Rating", "RatingDeviation", "Popularity",
    "NbPlays", "Themes", "GameUrl", "OpeningTags", "DailyDate",
]


def difficulty(rating: int) -> str:
    if rating < EASY_RATING_MAX:
        return "easy"
    if rating < INTERMEDIATE_RATING_MAX:
        return "intermediate"
    return "advanced"


def main() -> int:
    with open(PUZZLES_CSV, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    skipped = 0
    exercises = []
    for row in rows:
        try:
            moves = [chess.Move.from_uci(m) for m in row["Moves"].split()]
            board = chess.Board(row["FEN"])
            if not moves or moves[0] not in board.legal_moves:
                raise ValueError("illegal prelude")
            board.push(moves[0])  # apply the game's last move -> puzzle start

            sol = moves[1:]
            if not sol or len(sol) % 2 == 0:
                raise ValueError("solution must end on the user's move")
            probe = board.copy()
            for m in sol:
                if m not in probe.legal_moves:
                    raise ValueError("illegal solution move")
                probe.push(m)
        except (ValueError, KeyError) as exc:
            skipped += 1
            print(f"  skip {row.get('PuzzleId')}: {exc}", file=sys.stderr)
            continue

        rating = int(row["Rating"])
        exercises.append({
            "number": len(exercises) + 1,
            "puzzle_id": row["PuzzleId"],
            "fen": board.fen(),
            "prelude": moves[0].uci(),
            "moves": [m.uci() for m in sol],
            "side": "w" if board.turn == chess.WHITE else "b",
            "difficulty": difficulty(rating),
            "rating": rating,
            "themes": row["Themes"].split(),
        })

    if not exercises:
        print("no exercises produced", file=sys.stderr)
        return 1

    os.makedirs(os.path.dirname(EXERCISES_JSON), exist_ok=True)
    with open(EXERCISES_JSON, "w", encoding="utf-8") as fh:
        json.dump(exercises, fh, indent=1)

    from collections import Counter
    sides = Counter(e["side"] for e in exercises)
    diff = Counter(e["difficulty"] for e in exercises)
    print(f"wrote {len(exercises)} exercises to {EXERCISES_JSON}")
    print(f"  side: {dict(sides)}")
    print(f"  difficulty: {dict(diff)}")
    print(f"  skipped {skipped} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
