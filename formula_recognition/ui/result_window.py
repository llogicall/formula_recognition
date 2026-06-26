from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QTimer, Qt
from PySide6.QtWidgets import QApplication, QLabel, QMessageBox, QVBoxLayout, QWidget


class FloatingResultToast(QWidget):
    def __init__(self, latex: str, confidence, parent=None, display_ms: int = 5000, fade_ms: int = 800):
        super().__init__(parent)
        self.setObjectName("floatingToast")
        self.display_ms = display_ms
        self.fade_ms = fade_ms
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        confidence_text = "未知" if confidence is None else "{:.2f}".format(confidence)
        title = QLabel("公式识别结果")
        title.setObjectName("toastTitle")
        latex_label = QLabel(latex)
        latex_label.setObjectName("toastLatex")
        latex_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        latex_label.setWordWrap(True)
        info = QLabel("Confidence: {}".format(confidence_text))
        info.setObjectName("toastInfo")

        layout = QVBoxLayout()
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(8)
        layout.addWidget(title)
        layout.addWidget(latex_label)
        layout.addWidget(info)
        self.setLayout(layout)
        self.setStyleSheet(
            """
            QWidget {
                background: rgba(255, 255, 255, 245);
                border: 1px solid rgba(203, 213, 225, 210);
                border-radius: 12px;
            }
            QLabel {
                color: #1f2937;
                border: none;
                background: transparent;
            }
            QLabel#toastTitle {
                font-weight: 600;
                font-size: 13px;
                color: #0f172a;
            }
            QLabel#toastLatex {
                font-family: Consolas, monospace;
                font-size: 14px;
                color: #334155;
            }
            QLabel#toastInfo {
                color: #64748b;
                font-size: 11px;
            }
            """
        )
        self.setMinimumWidth(320)
        self.setMaximumWidth(520)
        self.animation = None
        self.fade_in_animation = None
        self.fade_out_animation = None

    def show(self):
        self.adjustSize()
        self._move_to_bottom_right()
        self.setWindowOpacity(0.0)
        super().show()
        self.start_fade_in()
        QTimer.singleShot(self.display_ms, self.fade_out)

    def start_fade_in(self):
        self.fade_in_animation = QPropertyAnimation(self, b"windowOpacity", self)
        self.fade_in_animation.setDuration(220)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation = self.fade_in_animation
        self.fade_in_animation.start()

    def fade_out(self):
        self.fade_out_animation = QPropertyAnimation(self, b"windowOpacity", self)
        self.fade_out_animation.setDuration(self.fade_ms)
        self.fade_out_animation.setStartValue(1.0)
        self.fade_out_animation.setEndValue(0.0)
        self.fade_out_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.fade_out_animation.finished.connect(self.close)
        self.animation = self.fade_out_animation
        self.fade_out_animation.start()

    def _move_to_bottom_right(self):
        screen = QApplication.screenAt(QApplication.primaryScreen().availableGeometry().center())
        if screen is None:
            screen = QApplication.primaryScreen()
        if screen is None:
            return
        available = screen.availableGeometry()
        margin = 24
        self.move(
            available.right() - self.width() - margin,
            available.bottom() - self.height() - margin,
        )


class ResultPresenter:
    def __init__(self, app: QApplication, toast_cls=FloatingResultToast):
        self.app = app
        self.toast_cls = toast_cls
        self.active_toasts = []

    def show_result(self, result, auto_copy: bool = True):
        if auto_copy:
            self.app.clipboard().setText(result.latex)

        toast = self.toast_cls(result.latex, result.confidence, display_ms=5000)
        self.active_toasts.append(toast)
        toast.show()

    def show_error(self, message: str):
        box = QMessageBox()
        box.setWindowTitle("公式识别错误")
        box.setText(message)
        box.exec()
