import base64
import json
import re
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
                loose_latex = self._extract_loose_latex(content)
                parsed = self._try_parse_json(content)
                if parsed and isinstance(parsed.get("latex"), str):
                    parsed_latex = parsed["latex"].strip()
                    if self._is_usable_latex_text(parsed_latex) and not self._lost_tex_escape(parsed_latex, loose_latex):
                        return parsed_latex
                    if loose_latex:
                        return loose_latex
                if loose_latex:
                    return loose_latex
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
                    loose_latex = self._extract_loose_latex(joined)
                    parsed = self._try_parse_json(joined)
                    if parsed and isinstance(parsed.get("latex"), str):
                        parsed_latex = parsed["latex"].strip()
                        if self._is_usable_latex_text(parsed_latex) and not self._lost_tex_escape(parsed_latex, loose_latex):
                            return parsed_latex
                        if loose_latex:
                            return loose_latex
                    if loose_latex:
                        return loose_latex
                    return self._clean_latex_text(joined)

        return ""

    def _extract_confidence(self, payload: Dict[str, Any]) -> Optional[float]:
        confidence = self._extract_confidence_from_mapping(payload)
        if confidence is not None:
            return confidence

        result = payload.get("result", {})
        confidence = self._extract_confidence_from_mapping(result)
        if confidence is not None:
            return confidence

        data = payload.get("data", {})
        confidence = self._extract_confidence_from_mapping(data)
        if confidence is not None:
            return confidence

        choices = payload.get("choices", [])
        if choices:
            message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
            content = message.get("content")
            if isinstance(content, str):
                parsed = self._try_parse_json(content)
                if parsed:
                    confidence = self._extract_confidence_from_mapping(parsed)
                    if confidence is not None:
                        return confidence
                loose_confidence = self._extract_loose_confidence(content)
                if loose_confidence is not None:
                    return loose_confidence
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
                    if parsed:
                        confidence = self._extract_confidence_from_mapping(parsed)
                        if confidence is not None:
                            return confidence
                    loose_confidence = self._extract_loose_confidence(joined)
                    if loose_confidence is not None:
                        return loose_confidence

        return None

    def _extract_confidence_from_mapping(self, value: Any) -> Optional[float]:
        if not isinstance(value, dict):
            return None
        for key in ("confidence", "置信度"):
            confidence = self._coerce_confidence(value.get(key))
            if confidence is not None:
                return confidence
        return None

    def _coerce_confidence(self, value: Any) -> Optional[float]:
        if isinstance(value, bool) or value is None:
            return None
        if isinstance(value, (int, float)):
            number = float(value)
        elif isinstance(value, str):
            match = re.fullmatch(r"\s*(\d+(?:\.\d+)?|\.\d+)\s*(%)?\s*", value)
            if not match:
                return None
            number = float(match.group(1))
            if match.group(2):
                number = number / 100
        else:
            return None

        if number > 1:
            if number > 100:
                return None
            number = number / 100
        if number < 0:
            return None
        return number

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
            cleaned = re.sub(r"^\s*latex\s*[:：]?\s*", "", cleaned, flags=re.IGNORECASE).strip()
        return self._remove_confidence_text(cleaned)

    def _extract_loose_latex(self, text: str) -> str:
        cleaned = text.strip()
        if cleaned.startswith("```") and cleaned.endswith("```"):
            lines = cleaned.splitlines()
            if len(lines) >= 3:
                cleaned = "\n".join(lines[1:-1]).strip()

        quoted = re.search(
            r"(?:^|[\{,\n])\s*[\"']?latex[\"']?\s*[:：]\s*[\"'](?P<latex>.*?)(?<!\\)[\"']",
            cleaned,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if quoted:
            return self._remove_confidence_text(quoted.group("latex")).strip()

        unquoted = re.search(
            r"(?:^|[\{,\n])\s*[\"']?latex[\"']?\s*[:：]\s*(?P<latex>.+)",
            cleaned,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if not unquoted:
            return ""

        latex = unquoted.group("latex")
        latex = re.split(
            r"(?:\n|,)\s*[\"']?(?:confidence|置信度)[\"']?\s*[:：]",
            latex,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]
        latex = latex.strip().strip(",").strip()
        latex = latex.strip().strip("\"'")
        return self._remove_confidence_text(latex)

    def _is_usable_latex_text(self, text: str) -> bool:
        return not any(ord(char) < 32 and char not in "\n\t" for char in text)

    def _lost_tex_escape(self, parsed_latex: str, loose_latex: str) -> bool:
        return bool(loose_latex and "\\" in loose_latex and "\\" not in parsed_latex)

    def _remove_confidence_text(self, text: str) -> str:
        kept_lines = []
        for line in text.splitlines():
            if self._is_confidence_only_line(line):
                continue
            kept_lines.append(self._strip_confidence_suffix(line))
        return "\n".join(kept_lines).strip()

    def _strip_confidence_suffix(self, text: str) -> str:
        return re.sub(
            r"\s*[,;，；]?\s*(?:confidence|置信度)\s*[:：]\s*(?:\d+(?:\.\d+)?|\.\d+)\s*%?\s*$",
            "",
            text,
            flags=re.IGNORECASE,
        ).rstrip()

    def _is_confidence_only_line(self, text: str) -> bool:
        return (
            re.fullmatch(
                r"\s*(?:confidence|置信度)\s*[:：]\s*(?:\d+(?:\.\d+)?|\.\d+)\s*%?\s*",
                text,
                flags=re.IGNORECASE,
            )
            is not None
        )

    def _extract_loose_confidence(self, text: str) -> Optional[float]:
        match = re.search(
            r"(?:confidence|置信度)\s*[:：]\s*(\d+(?:\.\d+)?|\.\d+)\s*(%)?",
            text,
            flags=re.IGNORECASE,
        )
        if not match:
            return None

        value = float(match.group(1))
        if match.group(2) or value > 1:
            if value > 100:
                return None
            value = value / 100
        return value
