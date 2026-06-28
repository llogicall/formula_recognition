from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QMainWindow,
    QPlainTextEdit,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from formula_recognition.ui.latex_preview import LatexPreviewWidget


class MainWindow(QMainWindow):
    def __init__(
        self,
        history_store,
        capture_callback,
        settings_callback,
        exit_callback,
        close_to_tray_getter=lambda: True,
    ):
        super().__init__()
        self.history_store = history_store
        self.capture_callback = capture_callback
        self.settings_callback = settings_callback
        self.exit_callback = exit_callback
        self.close_to_tray_getter = close_to_tray_getter
        self.records = []

        self.setObjectName("mainWindow")
        self.setWindowTitle("Formula Recognition")
        self.resize(980, 620)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["时间", "状态", "置信度", "文件"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.currentCellChanged.connect(self._show_selected_record)

        self.metadata_detail = QPlainTextEdit()
        self.metadata_detail.setReadOnly(True)
        self.metadata_detail.setMinimumHeight(120)
        self.detail = self.metadata_detail

        self.latex_editor_title = QLabel("LaTeX")
        self.latex_editor_title.setProperty("class", "sectionTitle")
        self.latex_editor = QPlainTextEdit()
        self.latex_editor.setReadOnly(False)
        self.latex_editor.setMinimumHeight(120)
        self.latex_editor.setPlaceholderText("编辑 LaTeX 后会实时更新上方预览")
        self.latex_editor.textChanged.connect(self._render_preview_from_editor)

        self.formula_preview_title = QLabel("公式预览")
        self.formula_preview_title.setProperty("class", "sectionTitle")
        self.formula_preview = LatexPreviewWidget()

        detail_panel = QWidget()
        detail_layout = QVBoxLayout()
        detail_layout.setContentsMargins(16, 12, 16, 12)
        detail_layout.setSpacing(10)
        detail_layout.addWidget(self.formula_preview_title)
        detail_layout.addWidget(self.formula_preview, 1)
        detail_layout.addWidget(self.latex_editor_title)
        detail_layout.addWidget(self.latex_editor, 1)
        detail_layout.addWidget(self.metadata_detail, 1)
        detail_panel.setLayout(detail_layout)

        splitter = QSplitter()
        splitter.addWidget(self.table)
        splitter.addWidget(detail_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        self.setCentralWidget(splitter)

        self._build_menu()
        self.refresh_history()

    def _build_menu(self):
        self.capture_action = self.menuBar().addAction("截图")
        self.settings_action = self.menuBar().addAction("设置")
        self.exit_action = self.menuBar().addAction("退出")
        self.capture_action.triggered.connect(self.capture_callback)
        self.settings_action.triggered.connect(self.settings_callback)
        self.exit_action.triggered.connect(self.exit_callback)

    def refresh_history(self):
        self.records = self.history_store.list_records()
        self.table.setRowCount(len(self.records))
        for row, record in enumerate(self.records):
            self.table.setItem(row, 0, QTableWidgetItem(record.timestamp))
            self.table.setItem(row, 1, QTableWidgetItem(record.status))
            self.table.setItem(row, 2, QTableWidgetItem(record.confidence))
            self.table.setItem(row, 3, QTableWidgetItem(str(record.path)))

        if self.records:
            self.table.selectRow(0)
            self._render_detail(self.records[0])
        else:
            self.formula_preview.set_latex("")
            self.latex_editor.setPlainText("")
            self.metadata_detail.setPlainText("暂无历史记录")

    def _show_selected_record(self, current_row, current_column, previous_row, previous_column):
        if 0 <= current_row < len(self.records):
            self._render_detail(self.records[current_row])

    def _render_detail(self, record):
        self.latex_editor.blockSignals(True)
        self.latex_editor.setPlainText(record.latex)
        self.latex_editor.blockSignals(False)
        self.formula_preview.set_latex(record.latex)
        self.metadata_detail.setPlainText(
            "时间: {}\n状态: {}\n图片: {}\n错误: {}\n文件: {}".format(
                record.timestamp,
                record.status,
                record.image,
                record.error,
                record.path,
            )
        )

    def _render_preview_from_editor(self):
        self.formula_preview.set_latex(self.latex_editor.toPlainText())

    def closeEvent(self, event):
        if self.close_to_tray_getter():
            event.ignore()
            self.hide()
            return

        self.exit_callback()
        super().closeEvent(event)
