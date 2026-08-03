"""Left sidebar listing exercises (paginated) for quick selection."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QCheckBox, QHBoxLayout, QLabel, QListWidget,
                               QListWidgetItem, QPushButton, QVBoxLayout,
                               QWidget)

PAGE_SIZE = 10
SIDEBAR_WIDTH = 240


class ExerciseSidebar(QWidget):
    exercise_selected = Signal(int)
    session_changed = Signal(int)
    random_toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(SIDEBAR_WIDTH)
        self._numbers = []
        self._page = 0
        self._session = 1
        self._session_total = 1

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        # session selector
        sess = QHBoxLayout()
        self.session_prev_btn = QPushButton("◀")
        self.session_prev_btn.setObjectName("arrow")
        self.session_prev_btn.setFixedWidth(28)
        self.session_prev_btn.clicked.connect(self._prev_session)
        self.session_label = QLabel("Sesión 1")
        self.session_label.setAlignment(Qt.AlignCenter)
        slf = self.session_label.font()
        slf.setPointSize(10)
        self.session_label.setFont(slf)
        self.session_next_btn = QPushButton("▶")
        self.session_next_btn.setObjectName("arrow")
        self.session_next_btn.setFixedWidth(28)
        self.session_next_btn.clicked.connect(self._next_session)
        sess.addWidget(self.session_prev_btn)
        sess.addWidget(self.session_label, stretch=1)
        sess.addWidget(self.session_next_btn)
        root.addLayout(sess)

        self.title = QLabel("Ejercicios")
        self.title.setAlignment(Qt.AlignCenter)
        tf = self.title.font()
        tf.setPointSize(11)
        tf.setBold(True)
        self.title.setFont(tf)
        root.addWidget(self.title)

        self.listw = QListWidget()
        self.listw.itemClicked.connect(self._on_click)
        self.listw.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.listw.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        root.addWidget(self.listw)

        nav = QHBoxLayout()
        self.prev_btn = QPushButton("◀")
        self.prev_btn.setObjectName("arrow")
        self.prev_btn.setFixedWidth(28)
        self.prev_btn.clicked.connect(self._prev_page)
        self.next_btn = QPushButton("▶")
        self.next_btn.setObjectName("arrow")
        self.next_btn.setFixedWidth(28)
        self.next_btn.clicked.connect(self._next_page)
        self.page_label = QLabel("1/1")
        self.page_label.setAlignment(Qt.AlignCenter)
        nav.addWidget(self.prev_btn)
        nav.addWidget(self.page_label)
        nav.addWidget(self.next_btn)
        root.addLayout(nav)

        self.random_chk = QCheckBox("🎲 Puzles al azar")
        self.random_chk.toggled.connect(self.random_toggled)
        root.addWidget(self.random_chk)

    # -- session selector --------------------------------------------------
    def set_session(self, current: int, total: int, start: int, end: int) -> None:
        self._session = current
        self._session_total = total
        text = f"Sesión {current}"
        if start != end:
            text += f" · {start}-{end}"
        fm = self.session_label.fontMetrics()
        avail = self.session_label.width()
        if avail > 0 and fm.horizontalAdvance(text) > avail:
            text = fm.elidedText(text, Qt.ElideRight, avail)
        self.session_label.setText(text)
        self.session_prev_btn.setEnabled(current > 1)
        self.session_next_btn.setEnabled(current < total)

    def show_session_selector(self, visible: bool) -> None:
        self.session_prev_btn.setVisible(visible)
        self.session_label.setVisible(visible)
        self.session_next_btn.setVisible(visible)

    def _prev_session(self) -> None:
        if self._session > 1:
            self.session_changed.emit(self._session - 1)

    def _next_session(self) -> None:
        if self._session < self._session_total:
            self.session_changed.emit(self._session + 1)

    # -- exercise list -----------------------------------------------------
    def set_list(self, title: str, numbers: list[int],
                 current: int | None = None) -> None:
        """Show the given exercise numbers, jumping to the current one's page."""
        self.title.setText(title)
        self._numbers = list(numbers)
        if current in self._numbers:
            self._page = self._numbers.index(current) // PAGE_SIZE
        else:
            self._page = 0
        self._refresh()

    def _refresh(self) -> None:
        self.listw.clear()
        start = self._page * PAGE_SIZE
        for n in self._numbers[start:start + PAGE_SIZE]:
            it = QListWidgetItem(str(n))
            it.setData(Qt.UserRole, n)
            self.listw.addItem(it)
        pages = max(1, (len(self._numbers) + PAGE_SIZE - 1) // PAGE_SIZE)
        self.page_label.setText(f"{self._page + 1}/{pages}")
        self.prev_btn.setEnabled(self._page > 0)
        self.next_btn.setEnabled(self._page < pages - 1)
        self._fit_height()

    def _fit_height(self) -> None:
        """Cap the list at exactly PAGE_SIZE rows so the box is compact."""
        row_h = self.listw.sizeHintForRow(0) if self.listw.count() else 0
        if row_h <= 0:
            row_h = self.listw.fontMetrics().height()
        row_h = max(row_h, 22)
        self.listw.setFixedHeight(row_h * PAGE_SIZE + 2 * self.listw.frameWidth())

    def _on_click(self, item) -> None:
        self.exercise_selected.emit(int(item.data(Qt.UserRole)))

    def _prev_page(self) -> None:
        if self._page > 0:
            self._page -= 1
            self._refresh()

    def _next_page(self) -> None:
        self._page += 1
        self._refresh()
