"""Progress and analytics view."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QGridLayout, QGroupBox, QHBoxLayout, QLabel,
                               QPushButton, QScrollArea,
                               QTableWidget, QTableWidgetItem, QVBoxLayout,
                               QWidget)

from app import coach, storage
from app.ui.dialogs import confirm
from app.config import CYCLES
from app.exercises import difficulty_label, load_exercises
from PySide6.QtCore import Signal


class SummaryView(QWidget):
    progress_reset = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        root.addWidget(scroll)

        body = QWidget()
        inner = QVBoxLayout(body)
        inner.setContentsMargins(24, 16, 24, 16)

        self.cards = QGridLayout()
        inner.addLayout(self.cards)

        inner.addWidget(QLabel("Ciclos"))
        self.cycle_table = QTableWidget()
        self.cycle_table.setColumnCount(2)
        self.cycle_table.setHorizontalHeaderLabels(["Ciclo", "Ejercicios resueltos"])
        self.cycle_table.horizontalHeader().setStretchLastSection(True)
        inner.addWidget(self.cycle_table)

        inner.addWidget(QLabel("Sesiones recientes"))
        self.session_table = QTableWidget()
        self.session_table.setColumnCount(5)
        self.session_table.setHorizontalHeaderLabels(
            ["Fecha", "Ciclo", "Sesión", "Resueltos", "Precisión"])
        self.session_table.horizontalHeader().setStretchLastSection(True)
        inner.addWidget(self.session_table)

        inner.addWidget(QLabel("Ejercicios problemáticos (≥2 fallos)"))
        self.problem_table = QTableWidget()
        self.problem_table.setColumnCount(4)
        self.problem_table.setHorizontalHeaderLabels(
            ["Ejercicio", "Dificultad", "Intentos", "Precisión"])
        self.problem_table.horizontalHeader().setStretchLastSection(True)
        inner.addWidget(self.problem_table)

        self.reset_btn = QPushButton("Reiniciar todo el progreso")
        self.reset_btn.setObjectName("danger")
        self.reset_btn.clicked.connect(self._reset_all)
        inner.addWidget(self.reset_btn)
        scroll.setWidget(body)

    def _reset_all(self):
        if not confirm(self, "Reiniciar progreso",
                       "Esto borrará todo el progreso, intentos y sesiones. ¿Seguro?"):
            return
        storage.reset_all()
        self.progress_reset.emit()
        self.refresh()

    def refresh(self) -> None:
        self._refresh_cards()
        self._refresh_cycles()
        self._refresh_sessions()
        self._refresh_problems()

    def _card(self, grid, row, col, title, value):
        box = QGroupBox(title)
        lab = QLabel(str(value))
        lab.setAlignment(Qt.AlignCenter)
        f = lab.font()
        f.setPointSize(20)
        f.setBold(True)
        lab.setFont(f)
        v = QVBoxLayout(box)
        v.addWidget(lab)
        grid.addWidget(box, row, col)

    def _refresh_cards(self):
        while self.cards.count():
            it = self.cards.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        prog = storage.overall_progress()
        info = coach.cycle_info()
        acc = f"{100 * prog['solved'] / prog['total_attempts']:.0f}%" \
            if prog["total_attempts"] else "-"
        self._card(self.cards, 0, 0, "Ciclo actual", f"{info['cycle']}/{info['cycles']}")
        self._card(self.cards, 0, 1, "Ejercicios resueltos (único)", prog["unique_solved"])
        self._card(self.cards, 0, 2, "Sesiones completadas", prog["sessions"])
        self._card(self.cards, 0, 3, "Precisión general", acc)

    def _refresh_cycles(self):
        total = coach.TOTAL
        rows = []
        for cyc in range(1, CYCLES + 1):
            rows.append((cyc, storage.cycle_summary(cyc)["done"]))
        self.cycle_table.setRowCount(len(rows))
        for i, (cyc, done) in enumerate(rows):
            self.cycle_table.setItem(i, 0, QTableWidgetItem(str(cyc)))
            it = QTableWidgetItem(f"{done}/{total}")
            it.setData(Qt.UserRole, done)
            self.cycle_table.setItem(i, 1, it)

    def _refresh_sessions(self):
        import sqlite3
        conn = sqlite3.connect(storage.DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM sessions WHERE finished_at IS NOT NULL "
            "ORDER BY id DESC LIMIT 15").fetchall()
        conn.close()
        self.session_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.session_table.setItem(i, 0, QTableWidgetItem(r["started_at"][:16].replace("T", " ")))
            self.session_table.setItem(i, 1, QTableWidgetItem(str(r["cycle"])))
            self.session_table.setItem(i, 2, QTableWidgetItem(str(r["session_number"])))
            self.session_table.setItem(i, 3, QTableWidgetItem(f"{r['solved']}/{r['total']}"))
            acc = f"{100 * r['solved'] / r['total']:.0f}%" if r["total"] else "-"
            self.session_table.setItem(i, 4, QTableWidgetItem(acc))
        self.session_table.resizeColumnsToContents()

    def _refresh_problems(self):
        problems = []
        for e in load_exercises():
            st = storage.exercise_stats(e.number)
            if st["misses"] >= 2:
                problems.append((e, st))
        self.problem_table.setRowCount(len(problems))
        for i, (e, st) in enumerate(problems):
            self.problem_table.setItem(i, 0, QTableWidgetItem(str(e.number)))
            self.problem_table.setItem(i, 1, QTableWidgetItem(difficulty_label(e.difficulty)))
            self.problem_table.setItem(i, 2, QTableWidgetItem(str(st["attempts"])))
            self.problem_table.setItem(i, 3, QTableWidgetItem(f"{100 * st['accuracy']:.0f}%"))
        self.problem_table.resizeColumnsToContents()
