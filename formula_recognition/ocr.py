import base64
import json
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
                            "text": "请识别图片中的数学公式，输出 JSON 格式：{\"latex\": \"公式的 LaTeX 代码\", \"confidence\": 0.0-1.0 之间的浮点数表示置信度}。只输出纯 JSON，不要添加任何其他内容。",
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
                parsed = self._try_parse_json(content)
                if parsed and isinstance(parsed.get("latex"), str):
                    return parsed["latex"].strip()
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
                    joined = "\n".join(text_parts)
                    parsed = self._try_parse_json(joined)
                    if parsed and isinstance(parsed.get("latex"), str):
                        return parsed["latex"].strip()
                    return self._clean_latex_text(joined)

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

        choices = payload.get("choices", [])
        if choices:
            message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
            content = message.get("content")
            if isinstance(content, str):
                parsed = self._try_parse_json(content)
                if parsed and isinstance(parsed.get("confidence"), (int, float)):
                    return float(parsed["confidence"])
            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if isinstance(item, dict):
                        if isinstance(item.get("text"), str):
                            text_parts.append(item["text"])
                        elif item.get("type") == "text" and isinstance(item.get("content"), str):
                            text_parts.append(item["content"])
                if text_parts:
                    parsed = self._try_parse_json("\n".join(text_parts))
                    if parsed and isinstance(parsed.get("confidence"), (int, float)):
                        return float(parsed["confidence"])

        return None

    def _try_parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        cleaned = text.strip()
        if cleaned.startswith("```") and cleaned.endswith("```"):
            lines = cleaned.splitlines()
            if len(lines) >= 3:
                cleaned = "\n".join(lines[1:-1]).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
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
