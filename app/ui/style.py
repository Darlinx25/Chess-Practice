"""Global QSS stylesheet (dark theme) for the app.

The checkbox check-mark is generated at runtime as a small PNG (like the
sound effects) so the checked boxes show a visible ✓ instead of a flat
blue fill.
"""
from __future__ import annotations

import os

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPen

from app.config import DATA_DIR

ASSETS_DIR = os.path.join(DATA_DIR, "assets")
CHECK_PATH = os.path.join(ASSETS_DIR, "check.png")

_QSS = r"""
* {
    font-family: "DejaVu Sans";
    font-size: 11pt;
}

QMainWindow, QStackedWidget, QDialog, QMessageBox {
    background-color: #23272e;
}
QStackedWidget > QWidget {
    background-color: #23272e;
}

QLabel {
    background: transparent;
    color: #e8e8e8;
}

QWidget#toolbar {
    background-color: #1b1f25;
}

/* -- buttons ----------------------------------------------------------- */
QPushButton {
    background-color: #3a4150;
    color: #e8e8e8;
    border: 1px solid #495163;
    border-radius: 6px;
    padding: 5px 14px;
    min-height: 22px;
}
QPushButton:hover {
    background-color: #47506a;
    border-color: #5a6380;
}
QPushButton:pressed {
    background-color: #2f3542;
}
QPushButton:disabled {
    color: #6b7280;
    background-color: #2a2f38;
    border-color: #333a44;
}
QPushButton:focus {
    border-color: #3f6fd8;
}

QPushButton[active="true"] {
    background-color: #3f6fd8;
    border-color: #3f6fd8;
    color: #ffffff;
}
QPushButton[active="true"]:hover {
    background-color: #4d7de6;
}

QPushButton#primary {
    background-color: #3f6fd8;
    border-color: #3f6fd8;
    color: #ffffff;
    padding: 8px 22px;
    font-weight: bold;
}
QPushButton#primary:hover {
    background-color: #4d7de6;
}

QPushButton#danger {
    background-color: transparent;
    border: 1px solid #ef5350;
    color: #ef5350;
}
QPushButton#danger:hover {
    background-color: #ef5350;
    color: #ffffff;
}

/* small ◀ ▶ navigation buttons: no padding so the glyph is not clipped */
QPushButton#arrow {
    padding: 0;
    min-height: 0;
    font-size: 12pt;
}
QPushButton#arrow:hover {
    background-color: #3f6fd8;
    border-color: #3f6fd8;
    color: #ffffff;
}

/* -- checkboxes -------------------------------------------------------- */
QCheckBox {
    color: #e8e8e8;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #6b7280;
    background: #2a2f38;
}
QCheckBox::indicator:hover {
    border-color: #9aa3b5;
}
QCheckBox::indicator:checked {
    border-color: #3f6fd8;
    background: #3f6fd8;
    image: url("__CHECKMARK__");
}

/* -- progress ---------------------------------------------------------- */
QProgressBar {
    background-color: #1b1f25;
    border: 1px solid #3a4150;
    border-radius: 6px;
    text-align: center;
    color: #e8e8e8;
    min-height: 18px;
}
QProgressBar::chunk {
    background-color: #4caf80;
    border-radius: 5px;
}

/* -- sidebar list ------------------------------------------------------ */
QListWidget {
    background-color: #1e2229;
    border: 1px solid #3a4150;
    border-radius: 8px;
    padding: 2px;
    outline: 0;
}
QListWidget::item {
    padding: 3px 8px;
    border-radius: 4px;
}
QListWidget::item:selected {
    background-color: #3f6fd8;
    color: #ffffff;
}
QListWidget::item:hover {
    background-color: #2c323d;
}

/* -- tables (progress view) ------------------------------------------- */
QTableWidget, QTableView {
    background-color: #1e2229;
    alternate-background-color: #232833;
    gridline-color: #333a44;
    border: 1px solid #3a4150;
    border-radius: 8px;
    color: #e8e8e8;
}
QHeaderView::section {
    background-color: #2a2f38;
    color: #e8e8e8;
    border: none;
    border-bottom: 1px solid #3a4150;
    padding: 5px;
}
QTableCornerButton::section {
    background-color: #2a2f38;
    border: none;
}

/* -- group boxes (progress cards) -------------------------------------- */
QGroupBox {
    background-color: #1e2229;
    border: 1px solid #3a4150;
    border-radius: 10px;
    margin-top: 10px;
    padding-top: 6px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #b9c2d0;
}

/* -- scroll areas ------------------------------------------------------ */
QScrollArea {
    background: transparent;
    border: none;
}
QScrollArea > QWidget > QWidget {
    background: transparent;
}

/* -- scrollbars -------------------------------------------------------- */
QScrollBar:vertical {
    background: transparent;
    width: 12px;
    margin: 2px;
    border: none;
}
QScrollBar::handle:vertical {
    background: #4a5262;
    border-radius: 5px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover {
    background: #5a6480;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}
QScrollBar:horizontal {
    background: transparent;
    height: 12px;
    margin: 2px;
    border: none;
}
QScrollBar::handle:horizontal {
    background: #4a5262;
    border-radius: 5px;
    min-width: 24px;
}
QScrollBar::handle:horizontal:hover {
    background: #5a6480;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
}
"""


def _ensure_checkmark() -> str:
    """Render a white ✓ on transparent background and cache it as PNG."""
    if not os.path.exists(CHECK_PATH):
        os.makedirs(ASSETS_DIR, exist_ok=True)
        img = QImage(16, 16, QImage.Format.Format_ARGB32_Premultiplied)
        img.fill(Qt.GlobalColor.transparent)
        p = QPainter(img)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pen = QPen(QColor("#ffffff"), 2.4)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.drawPolyline([QPoint(4, 8), QPoint(7, 11), QPoint(12, 4)])
        p.end()
        img.save(CHECK_PATH, "PNG")
    return CHECK_PATH


def build_style() -> str:
    """Return the full stylesheet, substituting the generated check image."""
    path = _ensure_checkmark()
    return _QSS.replace("__CHECKMARK__", path.replace("\\", "/"))
