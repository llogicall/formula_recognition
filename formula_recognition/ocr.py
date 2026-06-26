import base64
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests


class OCRClientError(RuntimeError):
    pass


@dataclass
class OCRResult:
    latex: str
    confidence: Optional[float]
    raw_response: Dict[str, Any]


class OCRClient:
    def __init__(
        self,
        api_key: str,
        endpoint: str = "https://example.com/ocr",
        model: str = "glm-4.1v-thinking-flashx",
        session=None,
    ):
        self.api_key = api_key
        self.endpoint = endpoint
        self.model = model
        self.session = session or requests.Session()

    def recognize(self, image_bytes: bytes) -> OCRResult:
        if not self.api_key:
            raise OCRClientError("Missing API key")

        if self._use_chat_completions():
            response = self.session.post(
                self._normalize_endpoint(),
                headers={
                    "Authorization": "Bearer {}".format(self.api_key),
                    "Content-Type": "application/json",
                },
                json=self._build_chat_payload(image_bytes),
                timeout=30,
            )
        else:
            response = self.session.post(
                self.endpoint,
                headers={"Authorization": "Bearer {}".format(self.api_key)},
                files={"file": ("capture.png", image_bytes, "image/png")},
                data={"model": self.model},
                timeout=30,
            )

        if response.status_code >= 400:
            raise OCRClientError("HTTP {}: {}".format(response.status_code, response.text))

        payload = response.json()
        latex = self._extract_latex(payload)
        if not latex:
            raise OCRClientError("Empty LaTeX result")

        confidence = self._extract_confidence(payload)
        return OCRResult(latex=latex, confidence=confidence, raw_response=payload)

    def _use_chat_completions(self) -> bool:
        return "open.bigmodel.cn" in self.endpoint or self.endpoint.rstrip("/").endswith("/chat/completions")

    def _normalize_endpoint(self) -> str:
        base = self.endpoint.rstrip("/")
        if base.endswith("/chat/completions"):
            return base
        return base + "/chat/completions"

    def _build_chat_payload(self, image_bytes: bytes) -> Dict[str, Any]:
        image_b64 = base64.b64encode(image_bytes).decode("ascii")
        return {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "请识别图片中的数学公式，只输出纯 LaTeX，不要添加解释、前后缀或 Markdown 代码块。",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": "data:image/png;base64,{}".format(image_b64)
                            },
                        },
                    ],
                }
            ],
            "temperature": 0.1,
        }

    def _extract_latex(self, payload: Dict[str, Any]) -> str:
        if isinstance(payload.get("latex"), str):
            return payload["latex"].strip()

        result = payload.get("result", {})
        if isinstance(result.get("latex"), str):
            return result["latex"].strip()

        data = payload.get("data", {})
        if isinstance(data.get("latex"), str):
            return data["latex"].strip()

        choices = payload.get("choices", [])
        if choices:
            message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
            content = message.get("content")
            if isinstance(content, str):
                return self._clean_latex_text(content)
            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if isinstance(item, dict):
                        if isinstance(item.get("text"), str):
                            text_parts.append(item["text"])
                        elif item.get("type") == "text" and isinstance(item.get("content"), str):
                            text_parts.append(item["content"])
                if text_parts:
                    return self._clean_latex_text("\n".join(text_parts))

        return ""

    def _extract_confidence(self, payload: Dict[str, Any]) -> Optional[float]:
        if isinstance(payload.get("confidence"), (int, float)):
            return float(payload["confidence"])

        result = payload.get("result", {})
        if isinstance(result.get("confidence"), (int, float)):
            return float(result["confidence"])

        data = payload.get("data", {})
        if isinstance(data.get("confidence"), (int, float)):
            return float(data["confidence"])

        return None

    def _clean_latex_text(self, text: str) -> str:
        cleaned = text.strip()
        if cleaned.startswith("```") and cleaned.endswith("```"):
            lines = cleaned.splitlines()
            if len(lines) >= 3:
                cleaned = "\n".join(lines[1:-1]).strip()
        if cleaned.lower().startswith("latex"):
            cleaned = cleaned[5:].lstrip(":：\n ").strip()
        return cleaned
