# Third-party notices

Chess-Practice uses the following third-party components. Their licenses
and attributions are listed below.

## python-chess

- Author: Niklas Fiekas and contributors
- License: GNU GPL v3.0 or later
- Used for: chess rules/move validation and SVG chess piece rendering
  (`chess.svg.piece`).
- Source: <https://github.com/niklasf/python-chess>

## Chess piece set (Cburnett)

- Author: Colin M. L. Burnett
- License: CC-BY-SA 3.0 / GPL v2 or later
- The piece SVGs embedded in python-chess and rendered at runtime by the
  board widget.
- Source: <https://github.com/cburnett/chess-pieces>

## Lichess puzzle database

- License: CC0 1.0 Universal
- `lichess_db_puzzle.csv` and the generated `data/exercises.json` derive
  from the Lichess open puzzle database.
- Source: <https://database.lichess.org/>

## Qt / PySide6

- License: GNU LGPL v3.0
- GUI framework (QtWidgets, QtMultimedia, QtSvg) via PySide6.
- Source: <https://doc.qt.io/>

## PyInstaller

- License: GPL v2.0 or later, with a special exception for the built
  executables.
- Used at build time only.
- Source: <https://www.pyinstaller.org/>
