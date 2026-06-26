from datetime import datetime

from formula_recognition.history import HistoryRecord


class WorkflowController:
    def __init__(
        self,
        config_store,
        capture_service,
        ocr_client_factory,
        history_store,
        presenter,
        history_store_factory=None,
        history_updated_callback=None,
    ):
        self.config_store = config_store
        self.capture_service = capture_service
        self.ocr_client_factory = ocr_client_factory
        self.history_store = history_store
        self.presenter = presenter
        self.history_store_factory = history_store_factory
        self.history_updated_callback = history_updated_callback or (lambda: None)

    def run_once(self) -> None:
        config = self.config_store.load()
        history_store = (
            self.history_store_factory(config)
            if self.history_store_factory is not None
            else self.history_store
        )
        if not config.api_key:
            self.presenter.show_error("请先在 data/config.json 中填写 api_key")
            return

        image_bytes = self.capture_service.capture()
        if image_bytes is None:
            return

        client = self.ocr_client_factory(config)
        try:
            result = client.recognize(image_bytes)
        except Exception as exc:
            history_store.write(
                HistoryRecord(
                    timestamp=datetime.now(),
                    latex="",
                    confidence=None,
                    status="failure",
                    error=str(exc),
                ),
                image_bytes,
                save_image=config.save_screenshot,
            )
            self.history_updated_callback()
            self.presenter.show_error(str(exc))
            return

        history_store.write(
            HistoryRecord(
                timestamp=datetime.now(),
                latex=result.latex,
                confidence=result.confidence,
                status="success",
                error=None,
            ),
            image_bytes,
            save_image=config.save_screenshot,
        )
        self.history_updated_callback()
        self.presenter.show_result(result, auto_copy=config.auto_copy)
