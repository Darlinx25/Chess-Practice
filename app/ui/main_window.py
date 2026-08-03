"""Main application window."""
from __future__ import annotations

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QMainWindow,
                               QPushButton, QVBoxLayout, QWidget)

from app import coach, storage
from app.ui.session_view import SessionView
from app.ui.sidebar import ExerciseSidebar, SIDEBAR_WIDTH
from app.ui.style import build_style
from app.ui.summary_view import SummaryView
from app.ui.dialogs import confirm


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        QApplication.instance().setStyleSheet(build_style())
        self.setWindowTitle("Chess-Practice — Entrenamiento táctico")
        self.resize(900, 900)
        self._restore_geometry()

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QWidget()
        self.stack = []
        self.session_view = SessionView()
        self.summary_view = SummaryView()
        self.sidebar = ExerciseSidebar()
        self.session_view.finished.connect(self._on_session_finished)
        self.session_view.quit_requested.connect(self._quit)
        self.session_view.exercise_changed.connect(lambda _n: self._sync_sidebar())
        self.session_view.mode_changed.connect(lambda _r: self._sync_sidebar())
        self.sidebar.exercise_selected.connect(self._on_sidebar_select)
        self.sidebar.session_changed.connect(self._on_session_changed)
        self.sidebar.random_toggled.connect(self.session_view._on_random_toggled)
        self.summary_view.progress_reset.connect(self._on_progress_reset)
        self._selected_session = None
        self._active_block_start = None

        layout.addWidget(self._toolbar())
        layout.addWidget(self._pages(), stretch=1)

        storage.init_db()

        # always open directly on the exercise board (resumes the last one),
        # so the tablero is never shown empty.
        self.session_view.start()

    def _toolbar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("toolbar")
        h = QHBoxLayout(bar)
        h.setContentsMargins(8, 8, 8, 8)
        self.train_btn = QPushButton("Inicio")
        self.train_btn.clicked.connect(lambda: self._show_page(0))
        self.progress_btn = QPushButton("Progreso")
        self.progress_btn.clicked.connect(lambda: self._show_page(1))
        h.addWidget(self.train_btn)
        h.addWidget(self.progress_btn)
        h.addStretch(1)
        self._set_active_tab(0)
        return bar

    def _pages(self) -> QWidget:
        from PySide6.QtWidgets import QStackedWidget
        train_page = QWidget()
        train_layout = QHBoxLayout(train_page)
        train_layout.setContentsMargins(0, 0, 0, 0)
        train_layout.addWidget(self.sidebar, 0, Qt.AlignVCenter)
        train_layout.addWidget(self.session_view, stretch=1)
        # mirror the sidebar's width on the right so the board sits exactly
        # in the middle of the window instead of being pushed aside
        spacer = QWidget()
        spacer.setFixedWidth(SIDEBAR_WIDTH)
        train_layout.addWidget(spacer)
        self.stack = QStackedWidget()
        self.stack.addWidget(train_page)
        self.stack.addWidget(self.summary_view)
        return self.stack

    def _set_active_tab(self, idx: int) -> None:
        for btn, i in ((self.train_btn, 0), (self.progress_btn, 1)):
            btn.setProperty("active", "true" if i == idx else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _show_page(self, idx: int) -> None:
        if idx == 0:
            # "Inicio": return to the board in progress without advancing.
            # A session is only started when there is none yet (first use,
            # after finishing a session, or after a progress reset).
            if self.session_view.state is None:
                self.session_view.start()
        if idx == 1:
            self.summary_view.refresh()
        self.stack.setCurrentIndex(idx)
        self._set_active_tab(idx)

    def _on_sidebar_select(self, number: int) -> None:
        self.session_view.load_from_sidebar(number)
        self._sync_sidebar()

    def _on_session_changed(self, number: int) -> None:
        self._selected_session = number
        self._sync_sidebar()

    def _session_count(self) -> int:
        size = coach.session_size()
        return max(1, (coach.TOTAL + size - 1) // size)

    def _session_range(self, session: int) -> tuple[int, int]:
        size = coach.session_size()
        start = (session - 1) * size + 1
        end = min(start + size - 1, coach.TOTAL)
        return start, end

    def _sync_sidebar(self) -> None:
        sv = self.session_view
        current = sv.exercise.number if sv.exercise is not None else None
        if sv.random_mode:
            self.sidebar.show_session_selector(False)
            self.sidebar.set_list("Al azar", list(sv.random_played), current)
            return
        self.sidebar.show_session_selector(True)
        block_start = (sv.state.block[0]
                       if sv.state is not None and sv.state.block else None)
        if block_start is None:
            return
        size = coach.session_size()
        if self._active_block_start != block_start:
            self._active_block_start = block_start
            self._selected_session = (block_start - 1) // size + 1
        k = self._selected_session or 1
        start, end = self._session_range(k)
        self.sidebar.set_session(k, self._session_count(), start, end)
        self.sidebar.set_list("Ejercicios", list(range(start, end + 1)), current)

    def _on_session_finished(self) -> None:
        self.summary_view.refresh()
        self.stack.setCurrentIndex(1)

    def _on_progress_reset(self) -> None:
        self.session_view.state = None

    def _quit(self) -> None:
        self.close()

    def _restore_geometry(self) -> None:
        raw = storage.get_setting("win_geometry")
        if raw:
            self.restoreGeometry(QByteArray.fromBase64(raw.encode("ascii")))

    def closeEvent(self, event):
        if self.session_view.state is not None:
            if not confirm(self, "Salir",
                           "Tienes una sesión en curso. ¿Guardar y salir?"):
                event.ignore()
                return
        storage.set_setting("win_geometry",
                            bytes(self.saveGeometry().toBase64()).decode("ascii"))
        event.accept()
