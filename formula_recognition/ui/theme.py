from PySide6.QtGui import QFont


def build_app_stylesheet() -> str:
    return """
    QWidget {
        background: #f6f7fb;
        color: #1f2937;
        font-size: 13px;
    }
    QMainWindow#mainWindow,
    QDialog#settingsWindow {
        background: #f6f7fb;
    }
    QMenuBar {
        background: #ffffff;
        border-bottom: 1px solid #e5e7eb;
        padding: 4px;
    }
    QMenuBar::item {
        background: transparent;
        border-radius: 6px;
        padding: 6px 10px;
    }
    QMenuBar::item:selected,
    QMenu::item:selected {
        background: #e0f2fe;
        color: #0f172a;
    }
    QMenu {
        background: #ffffff;
        border: 1px solid #dbe3ef;
        border-radius: 8px;
        padding: 6px;
    }
    QMenu::item {
        padding: 7px 18px;
        border-radius: 6px;
    }
    QTableWidget {
        background: #ffffff;
        alternate-background-color: #f8fafc;
        border: 1px solid #dbe3ef;
        border-radius: 8px;
        gridline-color: #eef2f7;
        selection-background-color: #dbeafe;
        selection-color: #0f172a;
    }
    QHeaderView::section {
        background: #eef5fb;
        color: #334155;
        border: none;
        border-bottom: 1px solid #dbe3ef;
        padding: 8px;
        font-weight: 600;
    }
    QPlainTextEdit,
    QLineEdit {
        background: #ffffff;
        border: 1px solid #d5dde8;
        border-radius: 8px;
        padding: 8px;
        selection-background-color: #bfdbfe;
    }
    QLineEdit:focus,
    QPlainTextEdit:focus {
        border: 1px solid #7dd3fc;
    }
    QCheckBox {
        spacing: 8px;
        background: transparent;
    }
    QCheckBox::indicator {
        width: 16px;
        height: 16px;
        border-radius: 5px;
        border: 1px solid #94a3b8;
        background: #ffffff;
    }
    QCheckBox::indicator:checked {
        background: #38bdf8;
        border: 1px solid #0284c7;
    }
    QPushButton {
        background: #e0f2fe;
        border: 1px solid #bae6fd;
        border-radius: 8px;
        color: #075985;
        padding: 7px 14px;
        font-weight: 600;
    }
    QPushButton:hover {
        background: #bae6fd;
    }
    QPushButton:pressed {
        background: #7dd3fc;
    }
    QLabel[class="sectionTitle"] {
        color: #334155;
        font-weight: 600;
        background: transparent;
    }
    QWidget[class="previewCard"] {
        background: #ffffff;
        border: 1px solid #dbe3ef;
        border-radius: 8px;
    }
    QSplitter::handle {
        background: #e5edf6;
        width: 6px;
    }
    """


def apply_app_theme(app) -> None:
    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet(build_app_stylesheet())
