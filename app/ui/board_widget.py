"""Interactive chess board widget."""
from __future__ import annotations

import chess
import chess.svg
from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QSizePolicy, QWidget

LIGHT = QColor("#f0d9b5")
DARK = QColor("#b58863")
HIGHLIGHT = QColor(76, 175, 80, 120)      # legal move targets (green dots)
LAST_MOVE = QColor(255, 213, 79, 110)     # amber: from/to of the last move
CHECK = QColor(224, 82, 82, 150)
SELECT = QColor(61, 126, 255, 150)        # blue: piece being dragged/clicked
BAD = QColor(224, 82, 82, 160)
GOOD = QColor(76, 175, 122, 160)
HINT = QColor(160, 108, 255, 165)         # purple: hint squares
MARGIN = 24  # px reserved for board coordinates


class BoardWidget(QWidget):
    """Displays a python-chess position and supports click-move input."""

    move_made = Signal(str)  # emits SAN of a played move
    move_rejected = Signal()  # a move was attempted but not accepted

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(280, 280)
        self.board = chess.Board()
        self.selected = None
        self.last_move = None
        self.side_to_move = True  # True = white at bottom
        self.highlight_moves = True
        self.user_color = chess.WHITE  # only this side is controllable
        self.input_enabled = True
        self._legal = []
        self._bad_square = None  # square flashed red after a rejected move
        self._good_square = None  # square flashed green after an accepted move
        self._hint = []  # squares highlighted amber after asking for a hint
        self._drag_started = False
        self._flash_timer = QTimer(self)
        self._flash_timer.setSingleShot(True)
        self._flash_timer.setInterval(1000)
        self._flash_timer.timeout.connect(self.clear_feedback)
        self._piece_cache: dict[tuple[str, int], QPixmap] = {}

    # -- position handling -------------------------------------------------
    def set_fen(self, fen: str, side_to_move_at_bottom: bool = True,
                user_color: int = chess.WHITE) -> None:
        self.board = chess.Board(fen)
        self.side_to_move = side_to_move_at_bottom
        self.user_color = user_color
        self.selected = None
        self.last_move = None
        self._legal = []
        self._bad_square = None
        self._good_square = None
        self._hint = []
        self._drag_started = False
        self.update()

    def set_input_enabled(self, enabled: bool) -> None:
        self.input_enabled = enabled
        if not enabled:
            self.selected = None
            self._legal = []
        self.update()

    def reset(self) -> None:
        self.board.reset()
        self.selected = None
        self.last_move = None
        self._legal = []
        self.update()

    def flash_bad_square(self, square: int) -> None:
        self._bad_square = square
        self._flash_timer.start()
        self.update()

    def flash_good_square(self, square: int) -> None:
        self._good_square = square
        self._flash_timer.start()
        self.update()

    def flash_hint(self, squares: list[int]) -> None:
        self._hint = squares
        self.update()

    def clear_feedback(self) -> None:
        self._flash_timer.stop()
        self._bad_square = None
        self._good_square = None
        self._hint = []
        self.update()

    def san_to_move(self, san: str) -> str | None:
        try:
            move = self.board.parse_san(san)
            s = self.board.san(move)
            self.board.push(move)
            self.last_move = move
            self.selected = None
            self._legal = []
            self.update()
            self.move_made.emit(s)
            return s
        except ValueError:
            return None

    # -- painting ----------------------------------------------------------
    def _geom(self):
        w, h = self.width(), self.height()
        s = max(0, min(w, h) - 2 * MARGIN)
        ox, oy = (w - s) // 2, (h - s) // 2
        return s, ox, oy

    def _coord_squares(self):
        """(file, rank) of the top-left widget cell."""
        return (0, 7) if self.side_to_move else (7, 0)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        s, ox, oy = self._geom()
        if s == 0:
            return
        sq = s / 8
        board = self.board
        for r in range(8):
            for c in range(8):
                rect = (ox + c * sq, oy + r * sq, sq, sq)
                file_i, rank_i = c, r
                if self.side_to_move:
                    rank = 7 - rank_i
                    file = file_i
                else:
                    rank = rank_i
                    file = 7 - file_i
                sq_index = chess.square(file, rank)
                color = LIGHT if (r + c) % 2 == 1 else DARK
                p.fillRect(*rect, color)

                piece = board.piece_at(sq_index)
                if piece is not None:
                    self._draw_piece(p, rect, sq, piece)

                # highlights
                if self._bad_square == sq_index:
                    p.fillRect(*rect, BAD)
                if self._good_square == sq_index:
                    p.fillRect(*rect, GOOD)
                if self.last_move is not None and sq_index in (
                        self.last_move.from_square, self.last_move.to_square):
                    p.fillRect(*rect, LAST_MOVE)
                if self.selected == sq_index:
                    p.fillRect(*rect, SELECT)
                if sq_index in self._legal:
                    p.setBrush(HIGHLIGHT)
                    p.setPen(Qt.NoPen)
                    if board.piece_at(sq_index) is None:
                        p.drawEllipse(ox + (c + 0.35) * sq, oy + (r + 0.35) * sq,
                                      sq * 0.3, sq * 0.3)
                    else:
                        p.drawRoundedRect(*rect, sq * 0.12, sq * 0.12)
                king_sq = board.king(board.turn)
                if king_sq == sq_index and board.is_check():
                    p.fillRect(*rect, CHECK)
                if sq_index in self._hint:
                    p.fillRect(*rect, HINT)

        self._draw_coordinates(p, sq, ox, oy)

    def _draw_coordinates(self, p: QPainter, sq: float, ox: float, oy: float) -> None:
        p.save()
        font = QFont("DejaVu Sans", 1)
        font.setPixelSize(int(MARGIN * 0.55))
        p.setFont(font)
        # draw the glyph twice: dark outline + light fill so the coordinates
        # stay readable on any background
        dark = QPen(QColor("#202020"), 1)
        light = QPen(QColor("#f5f5f5"), 1)
        cells = []
        # file letters (a-h) along the bottom edge
        for c in range(8):
            file = c if self.side_to_move else 7 - c
            cells.append((ox + c * sq, oy + 8 * sq, sq, MARGIN,
                          chr(ord("a") + file)))
        # rank numbers (1-8) along the left edge
        for r in range(8):
            rank = 7 - r if self.side_to_move else r
            cells.append((ox - MARGIN, oy + r * sq, MARGIN, sq, str(rank + 1)))
        for x, y, w, h, ch in cells:
            p.setPen(dark)
            for dx, dy in ((-1, -1), (1, 1), (-1, 1), (1, -1)):
                p.drawText(int(x) + dx, int(y) + dy, int(w), int(h),
                           Qt.AlignCenter, ch)
            p.setPen(light)
            p.drawText(int(x), int(y), int(w), int(h), Qt.AlignCenter, ch)
        p.restore()

    def _piece_pixmap(self, piece: chess.Piece, size: int) -> QPixmap:
        """Render a piece to a transparent pixmap (cached per symbol+size)."""
        key = (piece.symbol(), size)
        pm = self._piece_cache.get(key)
        if pm is not None:
            return pm
        svg = chess.svg.piece(piece, size=size)
        renderer = QSvgRenderer(svg.encode("utf-8"))
        pm = QPixmap(size, size)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        renderer.render(p, QRectF(0, 0, size, size))
        p.end()
        self._piece_cache[key] = pm
        return pm

    def _draw_piece(self, p: QPainter, rect, sq: float, piece: chess.Piece) -> None:
        s = max(8, int(sq * 0.92))
        pm = self._piece_pixmap(piece, s)
        x, y, w, h = rect
        px = int(x + (w - s) / 2)
        py = int(y + (h - s) / 2)
        p.drawPixmap(px, py, pm)

    # -- interaction -------------------------------------------------------
    def _cell_to_square(self, c: int, r: int) -> int:
        if self.side_to_move:
            return chess.square(c, 7 - r)
        return chess.square(7 - c, r)

    def _try_move(self, to_sq: int) -> None:
        board = self.board
        self._hint = []
        move = chess.Move(self.selected, to_sq)
        if board.piece_at(self.selected).piece_type == chess.PAWN and \
                chess.square_rank(to_sq) in (0, 7):
            move = chess.Move(self.selected, to_sq, promotion=chess.QUEEN)
        if move in board.legal_moves:
            san = board.san(move)
            board.push(move)
            self.last_move = move
            self.move_made.emit(san)
        self.selected = None
        self._legal = []
        self.update()

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton or not self.input_enabled:
            return
        self._drag_started = False
        s, ox, oy = self._geom()
        if s == 0:
            return
        sq = s / 8
        c = int((event.position().x() - ox) // sq)
        r = int((event.position().y() - oy) // sq)
        if not (0 <= c < 8 and 0 <= r < 8):
            return
        sq_index = self._cell_to_square(c, r)
        board = self.board
        piece = board.piece_at(sq_index)
        if piece is not None and piece.color == self.user_color:
            if self.selected == sq_index:
                self.selected = None
                self._legal = []
            else:
                self.selected = sq_index
                self._legal = [m.to_square for m in board.legal_moves
                               if m.from_square == sq_index]
            self._drag_started = True
        elif self.selected is not None:
            # click on a destination: try to move the selected piece there
            self._try_move(sq_index)
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton or not self.input_enabled:
            return
        if not self._drag_started or self.selected is None:
            return
        s, ox, oy = self._geom()
        if s == 0:
            return
        sq = s / 8
        c = int((event.position().x() - ox) // sq)
        r = int((event.position().y() - oy) // sq)
        if 0 <= c < 8 and 0 <= r < 8:
            to_sq = self._cell_to_square(c, r)
            if to_sq != self.selected:
                self._try_move(to_sq)
        self._drag_started = False
        self.update()
