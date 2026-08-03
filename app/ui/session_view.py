"""Training session view with solution-based move validation.

Moves are validated against the puzzle's solution (from the Lichess CSV)
instead of a chess engine: the user's move must match the next move of the
solution, and the opponent automatically replies with the following move.
"""
from __future__ import annotations

import random
import time

import chess

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (QCheckBox, QHBoxLayout, QLabel, QMessageBox,
                               QProgressBar, QPushButton, QVBoxLayout, QWidget)

from app import coach, sounds, storage
from app.exercises import difficulty_label, load_exercises
from app.ui.board_widget import BoardWidget

CURRENT_EXERCISE_KEY = "current_exercise"


class SessionView(QWidget):
    finished = Signal()
    quit_requested = Signal()
    exercise_changed = Signal(int)
    mode_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.state = None
        self.exercise = None
        self.exs = {e.number: e for e in load_exercises()}
        self.start_time = 0.0
        self.moves = []
        self._redo = []  # undone moves available for the ">" button
        self._move_idx = 0  # index into exercise.moves (next expected user move)
        self._pos_before = None  # board copy before the user's pending move
        self.start_fen = ""
        self.ex_side = "w"
        self._review_mode = False
        self._busy = False
        self.random_mode = False
        self.random_played = []
        self.sounds = sounds.init()

        self._build_ui()
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)

    # -- UI ---------------------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)

        self.info_label = QLabel("")
        self.info_label.setAlignment(Qt.AlignCenter)
        f = self.info_label.font()
        f.setPointSize(14)
        self.info_label.setFont(f)
        root.addWidget(self.info_label)

        self.turn_label = QLabel("")
        self.turn_label.setAlignment(Qt.AlignCenter)
        tf = self.turn_label.font()
        tf.setPointSize(13)
        tf.setBold(True)
        self.turn_label.setFont(tf)
        root.addWidget(self.turn_label)

        self.progress = QProgressBar()
        self.progress.setTextVisible(True)
        root.addWidget(self.progress)

        self.board = BoardWidget()
        self.board.move_made.connect(self._on_move)
        root.addWidget(self.board, stretch=1)

        self.move_label = QLabel("Mueve: -")
        self.move_label.setAlignment(Qt.AlignCenter)
        root.addWidget(self.move_label)

        self.feedback_label = QLabel("")
        self.feedback_label.setAlignment(Qt.AlignCenter)
        self.feedback_label.setWordWrap(True)
        ff = self.feedback_label.font()
        ff.setPointSize(14)
        ff.setBold(True)
        self.feedback_label.setFont(ff)
        root.addWidget(self.feedback_label)

        self.timer_label = QLabel("0:00")
        self.timer_label.setAlignment(Qt.AlignCenter)
        tlf = self.timer_label.font()
        tlf.setPointSize(22)
        tlf.setBold(True)
        self.timer_label.setFont(tlf)
        root.addWidget(self.timer_label)

        row = QHBoxLayout()
        self.review_btn = QPushButton("Continuar")
        self.review_btn.setObjectName("primary")
        self.review_btn.clicked.connect(self._load_next)
        self.review_btn.hide()
        row.addWidget(self.review_btn)
        root.addLayout(row)

        row2 = QHBoxLayout()
        self.hint_btn = QPushButton("Pista")
        self.hint_btn.clicked.connect(self._ask_hint)
        row2.addWidget(self.hint_btn)
        self.repeat_btn = QPushButton("Repetir")
        self.repeat_btn.clicked.connect(self._repeat_exercise)
        row2.addWidget(self.repeat_btn)
        row2.addStretch(1)
        self.back_btn = QPushButton("<")
        self.back_btn.clicked.connect(self._nav_back)
        row2.addWidget(self.back_btn)
        self.forward_btn = QPushButton(">")
        self.forward_btn.clicked.connect(self._nav_forward)
        row2.addWidget(self.forward_btn)
        row2.addStretch(1)
        root.addLayout(row2)

        quit_row = QHBoxLayout()
        self.sound_chk = QCheckBox("Sonido")
        self.sound_chk.setChecked(True)
        self.sound_chk.toggled.connect(self._toggle_sound)
        quit_row.addWidget(self.sound_chk)
        quit_row.addStretch(1)
        quit_btn = QPushButton("Guardar y salir")
        quit_btn.setObjectName("danger")
        quit_btn.clicked.connect(self.quit_requested)
        quit_row.addWidget(quit_btn)
        root.addLayout(quit_row)

    # -- lifecycle --------------------------------------------------------
    def start(self) -> None:
        if self.state is None:
            self.state = coach.start_or_resume_session()
        saved = storage.get_setting(CURRENT_EXERCISE_KEY)
        n = None
        if saved:
            try:
                n = int(saved)
            except (TypeError, ValueError):
                n = None
        if n is not None and n in self.state.block and n not in self.state.done:
            self._load_specific(n)
        else:
            self._load_next()

    def _load_next(self):
        if self.random_mode:
            self._load_random()
            return
        ex = coach.next_exercise(self.state)
        if ex is None:
            coach.finish(self.state)
            self.state = None
            QMessageBox.information(self, "Sesión completada",
                                    "¡Sesión completada! Tu progreso ha sido guardado.")
            self.finished.emit()
            return
        self._setup_exercise(ex)

    def _load_random(self):
        """Pick and load a random exercise (casual mode, nothing is saved)."""
        pool = [e for e in self.exs.values()]
        if self.exercise is not None:
            pool = [e for e in pool if e.number != self.exercise.number]
        if not pool:
            pool = list(self.exs.values())
        ex = random.choice(pool)
        if ex.number not in self.random_played:
            self.random_played.append(ex.number)
        self._setup_exercise(ex)

    def _on_random_toggled(self, checked: bool) -> None:
        if checked:
            self.random_mode = True
            self.random_played = []
            self._load_random()
        else:
            self.random_mode = False
            self.start()
        self.mode_changed.emit(checked)

    def load_from_sidebar(self, number: int) -> None:
        """Jump to a chosen exercise from the sidebar list."""
        if self.random_mode and number not in self.random_played:
            self.random_played.append(number)
        self._load_specific(number)

    def _load_specific(self, number: int):
        """Load a given exercise without popping it from the session queue."""
        ex = self.exs.get(number)
        if ex is None:
            self._load_next()
            return
        self._setup_exercise(ex)

    def _setup_exercise(self, ex):
        self.exercise = ex
        storage.set_setting(CURRENT_EXERCISE_KEY, str(ex.number))
        self.start_fen, self.ex_side = ex.fen, ex.side
        self._move_idx = 0
        user_color = chess.WHITE if self.ex_side != "b" else chess.BLACK
        self.board.set_fen(self.start_fen,
                           side_to_move_at_bottom=(self.ex_side != "b"),
                           user_color=user_color)
        self._highlight_prelude()
        self._pos_before = chess.Board(self.start_fen)
        self.moves = []
        self._review_mode = False
        self.move_label.setText("Mueve: -")
        self.feedback_label.setText("")
        self.review_btn.hide()
        self.hint_btn.show()
        self.repeat_btn.show()
        self.back_btn.show()
        self.forward_btn.show()
        self.board.clear_feedback()
        self.board.set_input_enabled(True)
        self._redo.clear()
        self.back_btn.setEnabled(False)
        self.forward_btn.setEnabled(False)
        self.start_time = time.monotonic()
        self._timer.start()
        self._refresh_info()
        self._set_turn()
        self.exercise_changed.emit(self.exercise.number)

    def _highlight_prelude(self):
        """Highlight the move that led to this position, if known."""
        prelude = getattr(self.exercise, "prelude", "") if self.exercise else ""
        if prelude:
            try:
                mv = chess.Move.from_uci(prelude)
                self.board.last_move = mv
            except ValueError:
                pass
        self.board.update()

    def _set_turn(self):
        white = self._pos_before.turn == chess.WHITE
        self.turn_label.setText("▲ Blancas mueven" if white else "▼ Negras mueven")
        if white:
            color, bg, border = "#ffffff", "#333333", "#ffffff"
        else:
            color, bg, border = "#111111", "#f0f0f0", "#888888"
        self.turn_label.setStyleSheet(f"color: {color};"
                                      f" border: 2px solid {border}; border-radius: 6px;"
                                      f" padding: 2px 10px; background: {bg};")

    def _refresh_info(self):
        ex = self.exercise
        c = self.state
        total = coach.TOTAL
        if c is None:
            self.info_label.setText(f"Ejercicio {ex.number}/{total} · Al azar")
            self.progress.setMaximum(0)
            self.progress.setValue(0)
            self.progress.setFormat("")
            return
        self.info_label.setText(
            f"Ciclo {c.cycle}/{coach.cycle_info()['cycles']} · Sesión {c.session_number} · "
            f"Ejercicio {ex.number}/{total} · {difficulty_label(ex.difficulty)}")
        self.progress.setMaximum(c.total)
        self.progress.setValue(c.solved_count)
        self.progress.setFormat(f"{c.solved_count}/{c.total} resueltos")

    def _tick(self):
        if self.start_time:
            s = int(time.monotonic() - self.start_time)
            self.timer_label.setText(f"{s // 60}:{s % 60:02d}")

    # -- actions ----------------------------------------------------------
    def _toggle_sound(self, checked: bool) -> None:
        self.sounds.enabled = checked

    def _ask_hint(self) -> None:
        if self._busy or self._review_mode or self._pos_before is None \
                or self.exercise is None or not self.board.input_enabled:
            return
        sol = self.exercise.moves
        if self._move_idx >= len(sol):
            return
        mv = chess.Move.from_uci(sol[self._move_idx])
        san = self._pos_before.san(mv)
        self.board.clear_feedback()
        self.board.flash_hint([mv.from_square, mv.to_square])
        self._status("Pista: " + san, None)

    def _repeat_exercise(self) -> None:
        if self.exercise is None:
            return
        self._review_mode = False
        self._move_idx = 0
        user_color = self.board.user_color
        self.board.set_fen(self.start_fen,
                           side_to_move_at_bottom=(self.ex_side != "b"),
                           user_color=user_color)
        self._highlight_prelude()
        self._pos_before = chess.Board(self.start_fen)
        self.moves = []
        self.move_label.setText("Mueve: -")
        self.feedback_label.setText("")
        self.board.clear_feedback()
        self.board.set_input_enabled(True)
        self.start_time = time.monotonic()
        self._timer.start()
        self._set_turn()
        self.review_btn.hide()
        self.hint_btn.show()
        self.repeat_btn.show()
        self.back_btn.show()
        self.forward_btn.show()
        self._redo.clear()
        self.back_btn.setEnabled(False)
        self.forward_btn.setEnabled(False)

    def _status(self, text: str, good: bool | None = None):
        self.feedback_label.setText(text)
        if good is None:
            self.feedback_label.setStyleSheet("color: #d8dee9;")
        elif good:
            self.feedback_label.setStyleSheet("color: #4caf80;")
        else:
            self.feedback_label.setStyleSheet("color: #ef5350;")

    def _on_move(self, san: str) -> None:
        if self._busy or self._review_mode \
                or (self.state is None and not self.random_mode) \
                or self.exercise is None:
            return
        self._busy = True
        before = self._pos_before
        board = self.board.board
        try:
            move = before.parse_san(san)
        except ValueError:
            self._busy = False
            return
        self.board.set_input_enabled(False)

        # a checkmate always wins, even if it is a different mate than the
        # stored solution
        if board.is_checkmate():
            self.sounds.play("move")
            self._redo.clear()
            self.moves.append(san)
            self.move_label.setText("Mueve: " + " ".join(self.moves))
            self.board.clear_feedback()
            self.board.flash_good_square(move.to_square)
            self._status("✓ Bien", True)
            self._update_nav_buttons()
            self._busy = False
            self._finish_exercise(True)
            return

        sol = self.exercise.moves
        if not self._matches(sol, move):
            # undo the wrong move and flash the destination square red
            board.pop()
            self.board.last_move = None
            self.board.clear_feedback()
            self.board.flash_bad_square(move.to_square)
            self.sounds.play("bad")
            self._status("✗ Movimiento incorrecto", False)
            self.move_label.setText("Mueve: " + " ".join(self.moves))
            self.board.set_input_enabled(True)
            self._busy = False
            return

        # correct move: green flash and record
        self.sounds.play("move")
        self._redo.clear()
        self.moves.append(san)
        self.move_label.setText("Mueve: " + " ".join(self.moves))
        self.board.clear_feedback()
        self.board.flash_good_square(move.to_square)
        self._status("✓ Bien", True)

        if self._move_idx == len(sol) - 1:
            # the user just played the solution's last move; the win is banked
            self._busy = False
            self.board.clear_feedback()
            self._status("✓ Bien — posición ganada", True)
            self._finish_exercise(True)
            return

        # opponent replies with the next solution move
        reply = chess.Move.from_uci(sol[self._move_idx + 1])
        if reply in board.legal_moves:
            reply_san = board.san(reply)
            board.push(reply)
            self.moves.append(reply_san)
            self.move_label.setText("Mueve: " + " ".join(self.moves))
            self.board.last_move = reply
            self.board.selected = None
            self.board._legal = []
            self._pos_before = board.copy()
            self.board.update()
            self.sounds.play("opponent")
        self._move_idx += 2

        if board.is_game_over():
            self._busy = False
            self.board.clear_feedback()
            self._status("✗ Te han dado mate", False)
            self._finish_exercise(False)
            return

        self.board.set_input_enabled(True)
        self._busy = False
        self._update_nav_buttons()

    def _matches(self, sol: tuple[str, ...], move: chess.Move) -> bool:
        """True when the user's move matches the next solution move.

        Only from/to squares are compared (like the reference app), so a
        promotion piece choice never blocks an otherwise correct move.
        """
        if self._move_idx >= len(sol):
            return False
        expected = chess.Move.from_uci(sol[self._move_idx])
        return expected.from_square == move.from_square \
            and expected.to_square == move.to_square

    # -- move navigation (back / forward) ---------------------------------
    def _nav_back(self):
        if self._busy or self._review_mode \
                or (self.state is None and not self.random_mode) \
                or self.exercise is None:
            return
        board = self.board.board
        if not board.move_stack:
            return
        self._redo.append(board.pop())
        self._sync_after_nav()

    def _nav_forward(self):
        if self._busy or self._review_mode \
                or (self.state is None and not self.random_mode) \
                or self.exercise is None:
            return
        if not self._redo:
            return
        board = self.board.board
        mv = self._redo.pop()
        if mv in board.legal_moves:
            board.push(mv)
        self._sync_after_nav()

    def _sync_after_nav(self):
        """Refresh board/labels/input after a back or forward navigation."""
        board = self.board.board
        n = len(board.move_stack)
        self._move_idx = n
        self._pos_before = board.copy()
        b = chess.Board(self.start_fen)
        sans = []
        for mv in board.move_stack:
            sans.append(b.san(mv))
            b.push(mv)
        self.moves = sans
        self.move_label.setText("Mueve: " + " ".join(sans) if sans else "Mueve: -")
        self.board.last_move = board.move_stack[-1] if n else None
        self.board.selected = None
        self.board._legal = []
        self.board.clear_feedback()
        self.board.update()
        self._update_nav_buttons()
        if not board.is_game_over() and board.turn == self.board.user_color:
            self.board.set_input_enabled(True)
        else:
            self.board.set_input_enabled(False)
        self._set_turn()

    def _update_nav_buttons(self):
        self.back_btn.setEnabled(bool(self.board.board.move_stack))
        self.forward_btn.setEnabled(bool(self._redo))

    def _solution_line(self) -> list[str]:
        """Full solution from the puzzle start, in SAN."""
        b = chess.Board(self.start_fen)
        parts = []
        for uci in self.exercise.moves:
            mv = chess.Move.from_uci(uci)
            if mv not in b.legal_moves:
                break
            parts.append(b.san(mv))
            b.push(mv)
        return parts

    def _finish_exercise(self, solved: bool,
                         line: list[str] | None = None) -> None:
        elapsed = int((time.monotonic() - self.start_time) * 1000)
        self._timer.stop()
        self.board.set_input_enabled(False)
        self.sounds.play("good" if solved else "bad")
        if line is None:
            line = self._solution_line()
        if not self.random_mode and self.state is not None \
                and self.exercise is not None:
            storage.record_attempt(self.exercise.number, self.state.cycle,
                                   self.state.session_id, solved, elapsed)
            coach.submit(self.state, self.exercise.number, solved)
        self._start_review(solved, line)

    def _start_review(self, solved: bool, line: list[str]) -> None:
        """Show the result keeping the board on its final position.

        The board is left exactly where it ended (the winning move stays
        visible); no moves are replayed. The solution is shown as text.
        """
        self._review_mode = True
        self.moves = list(line)
        self.move_label.setText("Mueve: " + " ".join(line))
        self.board.selected = None
        self.board._legal = []
        self.board.clear_feedback()
        self.board.update()
        if solved:
            self._status("✓ Resuelto — Solución: " + " ".join(line), True)
        elif line:
            self._status("✗ Fallaste — Solución: " + " ".join(line), False)
        else:
            self._status("✗ Fallaste", False)
        self.turn_label.setText("")
        self.back_btn.hide()
        self.forward_btn.hide()
        self.hint_btn.hide()
        self.repeat_btn.hide()
        self.review_btn.setText("Continuar")
        self.review_btn.show()
