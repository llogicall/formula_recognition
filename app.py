import sys
from pathlib import Path

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import QApplication

from formula_recognition.capture import QtCaptureService
from formula_recognition.config import AppConfigStore
from formula_recognition.history import HistoryStore
from formula_recognition.hotkey import GlobalHotkeyService
from formula_recognition.ocr import OCRClient
from formula_recognition.paths import get_default_config_path, get_default_history_dir
from formula_recognition.tray import TrayController
from formula_recognition.ui import MainWindow, ResultPresenter, SettingsWindow
from formula_recognition.ui.theme import apply_app_theme
from formula_recognition.workflow import WorkflowController


class MainThreadInvoker(QObject):
    requested = Signal(object)

    def __init__(self):
        super().__init__()
        self.requested.connect(self._invoke, Qt.ConnectionType.QueuedConnection)

    def invoke(self, callback) -> None:
        self.requested.emit(callback)

    def _invoke(self, callback) -> None:
        callback()


def build_controller(
    app: QApplication,
    capture_service_cls=QtCaptureService,
    history_store_cls=HistoryStore,
    hotkey_service_cls=GlobalHotkeyService,
    ocr_client_cls=OCRClient,
    presenter_cls=ResultPresenter,
    main_thread_invoker_cls=MainThreadInvoker,
):
    config_path = get_default_config_path(Path.cwd())
    config_store = AppConfigStore(config_path)
    config = config_store.load()

    def build_history_store(cfg):
        history_dir = Path(cfg.history_dir) if cfg.history_dir else get_default_history_dir(Path.cwd())
        return history_store_cls(history_dir)

    controller = WorkflowController(
        config_store=config_store,
        capture_service=capture_service_cls(app),
        ocr_client_factory=lambda cfg: ocr_client_cls(
            api_key=cfg.api_key,
            endpoint=cfg.endpoint or "https://example.com/ocr",
            model=cfg.model,
        ),
        history_store=build_history_store(config),
        presenter=presenter_cls(app),
        history_store_factory=build_history_store,
    )

    hotkey_service = hotkey_service_cls()
    main_thread_invoker = main_thread_invoker_cls()
    controller.main_thread_invoker = main_thread_invoker
    controller.history_updated_callback = lambda: None
    hotkey_service.register(config.hotkey, lambda: main_thread_invoker.invoke(controller.run_once))
    return controller, hotkey_service


def build_settings_callback(config_store, settings_window_cls=SettingsWindow):
    state = {"window": None}

    def show_settings() -> None:
        if state["window"] is None:
            state["window"] = settings_window_cls(config_store)
        state["window"].show()
        state["window"].raise_()
        state["window"].activateWindow()

    return show_settings


def configure_app_lifecycle(app: QApplication) -> None:
    app.setQuitOnLastWindowClosed(False)
    apply_app_theme(app)


def build_main_window_callback(
    controller,
    settings_callback,
    exit_callback,
    main_window_cls=MainWindow,
    history_store_cls=HistoryStore,
):
    state = {"window": None}

    def build_history_store():
        config = controller.config_store.load()
        history_dir = Path(config.history_dir) if config.history_dir else get_default_history_dir(Path.cwd())
        return history_store_cls(history_dir)

    def show_main_window() -> None:
        if state["window"] is None:
            state["window"] = main_window_cls(
                history_store=build_history_store(),
                capture_callback=controller.run_once,
                settings_callback=settings_callback,
                exit_callback=exit_callback,
                close_to_tray_getter=lambda: controller.config_store.load().close_to_tray,
            )
        elif hasattr(state["window"], "refresh_history"):
            state["window"].refresh_history()
        state["window"].show()
        state["window"].raise_()
        state["window"].activateWindow()

    def refresh_main_window() -> None:
        window = state["window"]
        if window is not None and hasattr(window, "refresh_history"):
            window.refresh_history()

    controller.history_updated_callback = refresh_main_window

    return show_main_window


def main() -> int:
    app = QApplication(sys.argv)
    configure_app_lifecycle(app)
    controller, hotkey_service = build_controller(app)
    settings_callback = build_settings_callback(controller.config_store)
    show_main_window = build_main_window_callback(controller, settings_callback, app.quit)
    tray = TrayController(
        controller,
        app.quit,
        settings_callback=settings_callback,
        show_window_callback=show_main_window,
    )
    tray.show()
    show_main_window()
    exit_code = app.exec()
    hotkey_service.unregister_all()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
