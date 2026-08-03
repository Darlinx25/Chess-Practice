"""Entry point for the Chess-Practice training app."""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from PySide6.QtWidgets import QApplication

from app import storage
from app.ui.main_window import MainWindow


def main() -> int:
    storage.init_db()
    if "--sndtest" in sys.argv:
        # hidden flag: play the "good" tone and exit, to verify audio output
        from PySide6.QtCore import QTimer
        from app import sounds
        app = QApplication(sys.argv)
        sp = sounds.init()

        def _play() -> None:
            sp.play("good")
            QTimer.singleShot(1500, app.quit)

        QTimer.singleShot(100, _play)
        return app.exec()
    app = QApplication(sys.argv)
    app.setApplicationName("ChessPractice")
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
