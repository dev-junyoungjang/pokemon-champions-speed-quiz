from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from app.core.settings import Settings

logger = logging.getLogger(__name__)


class AiQuestionError(RuntimeError):
    pass


@dataclass(frozen=True)
class OpenAiResponsesClient:
    """Small OpenAI Responses API adapter.

    The quiz service can use this later for two model-backed steps:
    1. candidate JSON generation
    2. validated-question text rendering

    The adapter is intentionally isolated so tests and local development can use
    deterministic template generation when no API key is configured.
    """

    settings: Settings

    def enabled_for_candidates(self) -> bool:
        return self.settings.openai_configured and self.settings.ai_question_generation_enabled

    def enabled_for_rendering(self) -> bool:
        return self.settings.openai_configured and self.settings.ai_question_rendering_enabled

    def create_json(self, *, model: str, instructions: str, input_payload: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.openai_api_key:
            raise AiQuestionError("OPENAI_API_KEY is not configured")

        body = {
            "model": model,
            "instructions": instructions,
            # Responses API requires the literal word "json" in the input when
            # text.format is json_object; instructions alone don't satisfy it.
            "input": "Respond in JSON.\n" + json.dumps(input_payload, ensure_ascii=False),
            "text": {"format": {"type": "json_object"}},
        }
        request = urllib.request.Request(
            f"{self.settings.openai_base_url}/responses",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.settings.ai_timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            logger.warning("OpenAI request failed (model=%s, status=%s): %s", model, exc.code, detail[:500])
            raise AiQuestionError(f"OpenAI request failed with {exc.code}: {detail[:500]}") from exc
        except urllib.error.URLError as exc:
            logger.warning("OpenAI request failed (model=%s): %s", model, exc)
            raise AiQuestionError(f"OpenAI request failed: {exc}") from exc

        text = self._extract_output_text(payload)
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            logger.warning("OpenAI response was not valid JSON (model=%s): %s", model, text[:500])
            raise AiQuestionError(f"OpenAI response was not valid JSON: {text[:500]}") from exc
        if not isinstance(parsed, dict):
            logger.warning("OpenAI response JSON was not an object (model=%s): %s", model, text[:500])
            raise AiQuestionError("OpenAI response JSON must be an object")
        logger.info("OpenAI request ok (model=%s): %s", model, json.dumps(parsed, ensure_ascii=False)[:1000])
        return parsed

    def _extract_output_text(self, payload: dict[str, Any]) -> str:
        if isinstance(payload.get("output_text"), str):
            return payload["output_text"]
        chunks: list[str] = []
        for item in payload.get("output", []):
            for content in item.get("content", []):
                if content.get("type") in {"output_text", "text"} and isinstance(content.get("text"), str):
                    chunks.append(content["text"])
        if chunks:
            return "".join(chunks)
        raise AiQuestionError("OpenAI response did not include output text")
