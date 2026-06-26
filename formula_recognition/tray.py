from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon


def build_menu_actions(action_factory, on_show_window, on_capture, on_settings, on_exit):
    window_action = action_factory("主窗口")
    capture_action = action_factory("截取公式")
    settings_action = action_factory("设置")
    exit_action = action_factory("退出")
    window_action.triggered.connect(on_show_window)
    capture_action.triggered.connect(on_capture)
    settings_action.triggered.connect(on_settings)
    exit_action.triggered.connect(on_exit)
    return [window_action, capture_action, settings_action, exit_action]


def create_tray_icon() -> QIcon:
    pixmap = QPixmap(32, 32)
    pixmap.fill(QColor("#2563eb"))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(QColor("white"), 3))
    painter.drawRect(7, 8, 18, 14)
    painter.drawLine(10, 23, 22, 23)
    painter.drawLine(16, 22, 16, 27)
    painter.end()

    return QIcon(pixmap)


class TrayController:
    def __init__(self, workflow_controller, quit_callback, settings_callback=None, show_window_callback=None):
        self.workflow_controller = workflow_controller
        self.quit_callback = quit_callback
        self.settings_callback = settings_callback or (lambda: None)
        self.show_window_callback = show_window_callback or (lambda: None)
        self.tray = QSystemTrayIcon(create_tray_icon())
        self.menu = None
        self.actions = []

    def show(self):
        self.menu = QMenu()
        self.actions = build_menu_actions(
            QAction,
            self.show_window_callback,
            self.workflow_controller.run_once,
            self.settings_callback,
            self.quit_callback,
        )
        self.menu.addAction(self.actions[0])
        self.menu.addAction(self.actions[1])
        self.menu.addAction(self.actions[2])
        self.menu.addSeparator()
        self.menu.addAction(self.actions[3])
        self.tray.setContextMenu(self.menu)
        self.tray.setToolTip("Formula Recognition")
        self.tray.show()
