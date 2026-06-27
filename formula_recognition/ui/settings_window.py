from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
)

from formula_recognition.config import AppConfig


class SettingsWindow(QDialog):
    def __init__(self, config_store, parent=None):
        super().__init__(parent)
        self.config_store = config_store
        self.setObjectName("settingsWindow")
        self.setWindowTitle("设置")
        self.resize(520, 360)

        config = self.config_store.load()
        self.api_key_edit = QLineEdit(config.api_key)
        self.endpoint_edit = QLineEdit(config.endpoint)
        self.model_edit = QLineEdit(config.model)
        self.hotkey_edit = QLineEdit(config.hotkey)
        self.history_dir_edit = QLineEdit(config.history_dir)
        self.auto_copy_check = QCheckBox("识别后自动复制 LaTeX")
        self.auto_copy_check.setChecked(config.auto_copy)
        self.save_screenshot_check = QCheckBox("保存截图到历史记录")
        self.save_screenshot_check.setChecked(config.save_screenshot)
        self.strip_delims_check = QCheckBox("复制到剪贴板时去除 \[ \] \( \) 等外围标记")
        self.strip_delims_check.setChecked(config.strip_latex_delimiters)
        self.close_to_tray_check = QCheckBox("关闭主窗口时保持后台运行")
        self.close_to_tray_check.setChecked(config.close_to_tray)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(12)
        form.addRow("API Key", self.api_key_edit)
        form.addRow("Endpoint", self.endpoint_edit)
        form.addRow("Model", self.model_edit)
        form.addRow("Hotkey", self.hotkey_edit)
        form.addRow("History Dir", self.history_dir_edit)
        form.addRow("", self.auto_copy_check)
        form.addRow("", self.save_screenshot_check)
        form.addRow("", self.strip_delims_check)
        form.addRow("", self.close_to_tray_check)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def save(self) -> None:
        self.config_store.save(
            AppConfig(
                api_key=self.api_key_edit.text().strip(),
                endpoint=self.endpoint_edit.text().strip(),
                model=self.model_edit.text().strip(),
                hotkey=self.hotkey_edit.text().strip(),
                history_dir=self.history_dir_edit.text().strip(),
                auto_copy=self.auto_copy_check.isChecked(),
                save_screenshot=self.save_screenshot_check.isChecked(),
                strip_latex_delimiters=self.strip_delims_check.isChecked(),
                close_to_tray=self.close_to_tray_check.isChecked(),
            )
        )
        self.accept()
