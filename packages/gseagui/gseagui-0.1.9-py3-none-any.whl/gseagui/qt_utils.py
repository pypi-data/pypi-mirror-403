from __future__ import annotations

import os
from typing import Optional

from PyQt5.QtWidgets import QApplication

try:
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QFontMetrics
    from PyQt5.QtWidgets import QLabel, QSizePolicy
except Exception:  # pragma: no cover
    Qt = None
    QFontMetrics = None
    QLabel = object  # type: ignore
    QSizePolicy = None


class ElidingLabel(QLabel):
    """A QLabel that elides (adds …) long text to avoid forcing parent layouts wider.

    - Stores the full text internally.
    - Updates displayed text on resize.
    - Sets tooltip to the full text for easy inspection.
    """

    def __init__(self, *args, elide_mode=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._full_text = ""
        if elide_mode is None and Qt is not None:
            elide_mode = Qt.ElideMiddle
        self._elide_mode = elide_mode

        try:
            if QSizePolicy is not None:
                self.setSizePolicy(QSizePolicy.Ignored, self.sizePolicy().verticalPolicy())
            self.setMinimumWidth(0)
        except Exception:
            pass

    def fullText(self) -> str:
        return self._full_text

    def setText(self, text):  # type: ignore[override]
        self._full_text = "" if text is None else str(text)
        try:
            self.setToolTip(self._full_text)
        except Exception:
            pass
        self._update_elided_text()

    def resizeEvent(self, event):  # type: ignore[override]
        super().resizeEvent(event)
        self._update_elided_text()

    def _update_elided_text(self) -> None:
        if Qt is None or QFontMetrics is None:
            # Fallback: show full text.
            try:
                QLabel.setText(self, self._full_text)
            except Exception:
                pass
            return

        available = 0
        try:
            available = self.contentsRect().width()
        except Exception:
            available = self.width()

        available = max(10, int(available))
        fm = QFontMetrics(self.font())
        elided = fm.elidedText(self._full_text, self._elide_mode, available)
        QLabel.setText(self, elided)


def fit_window_to_available_screen(
    window,
    desired_width: int,
    desired_height: int,
    *,
    max_ratio: float = 0.95,
) -> None:
    """Resize + center a top-level window so it never exceeds the available screen area.

    This is especially useful on HiDPI displays where hard-coded sizes can end up
    larger than the physical screen.
    """

    screen = None
    try:
        screen = window.screen()
    except Exception:
        screen = None

    if screen is None:
        screen = QApplication.primaryScreen()

    if screen is None:
        window.resize(desired_width, desired_height)
        return

    avail = screen.availableGeometry()
    max_width = max(200, int(avail.width() * max_ratio))
    max_height = max(200, int(avail.height() * max_ratio))

    target_width = min(int(desired_width), max_width)
    target_height = min(int(desired_height), max_height)

    try:
        window.setMinimumSize(
            min(window.minimumWidth(), target_width),
            min(window.minimumHeight(), target_height),
        )
    except Exception:
        pass

    window.resize(target_width, target_height)

    x = avail.x() + max(0, (avail.width() - target_width) // 2)
    y = avail.y() + max(0, (avail.height() - target_height) // 2)
    window.move(x, y)


def set_qt_highdpi_attributes() -> None:
    """Configure Qt HiDPI behavior.

    Must be called *before* the first QApplication is created to take effect.
    """

    try:
        from PyQt5.QtCore import Qt
    except Exception:
        return

    if hasattr(QApplication, "setAttribute") and hasattr(Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(QApplication, "setAttribute") and hasattr(Qt, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # Prefer PassThrough to keep OS scale factors (125%, 150%, ...) exact.
    # Users who feel it is too large can override via `GSEAGUI_UI_SCALE`.
    if hasattr(QApplication, "setHighDpiScaleFactorRoundingPolicy") and hasattr(
        Qt, "HighDpiScaleFactorRoundingPolicy"
    ):
        try:
            QApplication.setHighDpiScaleFactorRoundingPolicy(
                Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
            )
        except Exception:
            pass


def apply_application_ui_scale(
    app: QApplication,
    *,
    scale: Optional[float] = None,
    env_var: str = "GSEAGUI_UI_SCALE",
    min_point_size: float = 8.0,
) -> float:
    """Apply a global UI scale by scaling the application's default font.

    - If `scale` is provided, it wins.
    - Else if env var `env_var` is set, use that.
    - Else auto-scale down slightly on HiDPI screens.

    Returns the scale actually applied.
    """

    if app is None:
        return 1.0

    resolved_scale = scale
    if resolved_scale is None:
        raw = os.getenv(env_var, "").strip()
        if raw:
            try:
                resolved_scale = float(raw)
            except ValueError:
                resolved_scale = 1.0
        else:
            resolved_scale = _auto_ui_scale(app)

    if resolved_scale is None:
        resolved_scale = 1.0

    # Avoid weird values.
    if resolved_scale <= 0:
        resolved_scale = 1.0

    if abs(resolved_scale - 1.0) < 1e-6:
        return 1.0

    font = app.font()

    point_size = float(font.pointSizeF() or 0)
    if point_size > 0:
        font.setPointSizeF(max(min_point_size, point_size * resolved_scale))
        app.setFont(font)
        return float(resolved_scale)

    pixel_size = int(font.pixelSize() or 0)
    if pixel_size > 0:
        font.setPixelSize(max(1, int(round(pixel_size * resolved_scale))))
        app.setFont(font)
        return float(resolved_scale)

    return 1.0


def _auto_ui_scale(app: QApplication) -> float:
    """Heuristic: scale down a bit when logical DPI indicates HiDPI."""

    try:
        screen = app.primaryScreen()
        if screen is None:
            return 1.0

        dpi = float(screen.logicalDotsPerInch() or 0)
        if dpi <= 0:
            return 1.0

        ratio = dpi / 96.0
        if ratio >= 1.6:
            return 0.85
        if ratio >= 1.25:
            return 0.9
        return 1.0
    except Exception:
        return 1.0
