"""Small helpers for modal dialogs with Spanish button labels."""
from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QWidget


def confirm(parent: QWidget | None, title: str, text: str) -> bool:
    """Ask a yes/no question using Spanish buttons. Returns True for "Sí"."""
    box = QMessageBox(QMessageBox.Question, title, text, parent=parent)
    yes = box.addButton("Sí", QMessageBox.AcceptRole)
    no = box.addButton("No", QMessageBox.RejectRole)
    box.setDefaultButton(no)
    box.exec()
    return box.clickedButton() is yes
