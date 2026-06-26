from typing import Optional

from PySide6.QtCore import QBuffer, QEventLoop, QRect, Qt, Signal
from PySide6.QtGui import QColor, QGuiApplication, QMouseEvent, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QRubberBand, QWidget

from formula_recognition.capture.geometry import normalize_drag, translate_rect_to_origin, union_rects


class CaptureOverlay(QWidget):
    captured = Signal(bytes)
    canceled = Signal()

    def __init__(self, desktop_pixmap: QPixmap, virtual_geometry: QRect):
        super().__init__()
        self.desktop_pixmap = desktop_pixmap
        self.virtual_geometry = virtual_geometry
        self._start_point = None
        self._rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setGeometry(self.virtual_geometry)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.desktop_pixmap)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 80))
        painter.setPen(QPen(QColor(0, 180, 255), 2))

    def show(self):
        super().show()
        self.activateWindow()
        self.raise_()
        self.setFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            self.canceled.emit()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        self._start_point = event.globalPosition().toPoint()
        local_start = self._start_point - self.virtual_geometry.topLeft()
        self._rubber_band.setGeometry(QRect(local_start, local_start))
        self._rubber_band.show()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._start_point is None:
            return
        local_start = self._start_point - self.virtual_geometry.topLeft()
        local_current = event.globalPosition().toPoint() - self.virtual_geometry.topLeft()
        self._rubber_band.setGeometry(QRect(local_start, local_current).normalized())

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._start_point is None:
            return

        end_point = event.globalPosition().toPoint()
        self._rubber_band.hide()
        rect = normalize_drag(
            (self._start_point.x(), self._start_point.y()),
            (end_point.x(), end_point.y()),
        )
        self.hide()

        if rect is None:
            self.canceled.emit()
            return

        left, top, width, height = translate_rect_to_origin(
            rect,
            (
                self.virtual_geometry.x(),
                self.virtual_geometry.y(),
                self.virtual_geometry.width(),
                self.virtual_geometry.height(),
            ),
        )
        pixmap = self.desktop_pixmap.copy(left, top, width, height)
        if pixmap.isNull():
            self.canceled.emit()
            return

        image = pixmap.toImage()
        buffer = QBuffer()
        buffer.open(QBuffer.OpenModeFlag.ReadWrite)
        image.save(buffer, "PNG")
        self.captured.emit(bytes(buffer.data()))


class QtCaptureService:
    def __init__(self, app: QApplication):
        self.app = app

    def capture(self) -> Optional[bytes]:
        overlay = self._create_overlay()
        if overlay is None:
            return None
        loop = QEventLoop()
        result = {"image": None}

        def on_captured(image_bytes: bytes) -> None:
            result["image"] = image_bytes
            loop.quit()

        overlay.captured.connect(on_captured)
        overlay.canceled.connect(loop.quit)
        overlay.show()
        loop.exec()
        overlay.deleteLater()
        return result["image"]

    def _create_overlay(self) -> Optional[CaptureOverlay]:
        desktop_pixmap, virtual_geometry = self._capture_virtual_desktop()
        if desktop_pixmap.isNull():
            return None
        return CaptureOverlay(desktop_pixmap, virtual_geometry)

    def _capture_virtual_desktop(self):
        screens = QGuiApplication.screens()
        rect = union_rects(
            (
                screen.geometry().x(),
                screen.geometry().y(),
                screen.geometry().width(),
                screen.geometry().height(),
            )
            for screen in screens
        )
        if rect is None:
            return QPixmap(), QRect()

        virtual_geometry = QRect(*rect)
        desktop_pixmap = QPixmap(virtual_geometry.size())
        desktop_pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(desktop_pixmap)
        for screen in screens:
            geometry = screen.geometry()
            screen_pixmap = screen.grabWindow(0)
            target = geometry.topLeft() - virtual_geometry.topLeft()
            painter.drawPixmap(target, screen_pixmap)
        painter.end()
        return desktop_pixmap, virtual_geometry
