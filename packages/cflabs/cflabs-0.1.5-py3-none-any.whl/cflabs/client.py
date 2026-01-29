import base64
import mimetypes
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Union

import json

import requests


class CFLabs:
    def __init__(
        self,
        prompt_id: str,
        api_key: str | None = None,
        base_url: str = "https://octavian.chainforge.app/api/",
    ):
        """
        Initialize the CFLabs client.

        Args:
            prompt_id: The prompt ID to use for inference.
            api_key: Optional API key. If not provided, will try to get from CFLABS_API_KEY environment variable.
            base_url: Base URL for the API (default: https://octavian.chainforge.app/api/).

        Raises:
            ValueError: If api_key is not provided and CFLABS_API_KEY environment variable is not set.
        """
        self.api_key = api_key or os.environ.get("CFLABS_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key is required. Either provide it as a parameter or set the CFLABS_API_KEY environment variable."
            )
        self.base_url = base_url.rstrip("/")
        self.prompt_id = prompt_id

    def run(self, var_parameters: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """
        Trigger an inference of the Prompt using the Octavian API.

        Args:
            var_parameters: Optional dictionary of variable parameters. Defaults to empty dict if not provided.

        Returns:
            The API response as a dictionary.
        """
        url = f"{self.base_url}/run"
        headers = {"Content-Type": "application/json"}
        headers["Authorization"] = f"Bearer {self.api_key}"

        normalized_inputs: Dict[str, Any] = {}
        for k, v in (var_parameters or {}).items():
            normalized_inputs[k] = _normalize_input_value(v)

        payload = {
            "prompt_id": self.prompt_id,
            "inputs": normalized_inputs,
        }

        response = requests.post(url, json=payload, headers=headers)

        # Don't call response.raise_for_status() directly: we want to surface the
        # backend's standardized error payload (and provider error details).
        if not response.ok:
            raise CFLabsAPIError.from_response(response)

        try:
            return response.json()
        except Exception as e:
            raise CFLabsAPIError(
                status_code=response.status_code,
                url=response.url,
                message=f"Invalid JSON response from server: {e}",
                request_id=response.headers.get("X-Request-ID"),
                raw_text=_safe_response_text(response),
            ) from e


class CFLabsAPIError(RuntimeError):
    def __init__(
        self,
        *,
        status_code: int,
        url: str,
        message: str,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
        request_id: str | None = None,
        provider_error: str | None = None,
        raw_text: str | None = None,
    ):
        self.status_code = status_code
        self.url = url
        self.error_code = error_code
        self.details = details or {}
        self.request_id = request_id
        self.provider_error = provider_error
        self.raw_text = raw_text
        super().__init__(self._format_message(message))

    def _format_message(self, message: str) -> str:
        parts: list[str] = []
        parts.append(f"Octavian API error ({self.status_code})")
        if self.error_code:
            parts.append(f"code={self.error_code}")
        parts.append(f"url={self.url}")
        if self.request_id:
            parts.append(f"request_id={self.request_id}")
        header = " ".join(parts)

        body_lines: list[str] = [message]
        if self.provider_error:
            body_lines.append(self.provider_error)
        # Opt-in raw body: set CFLABS_VERBOSE_ERRORS=1
        if self.raw_text and os.environ.get("CFLABS_VERBOSE_ERRORS") in {
            "1",
            "true",
            "TRUE",
            "yes",
            "YES",
        }:
            body_lines.append("\nRaw response body:\n" + self.raw_text)

        return header + "\n" + "\n".join(body_lines)

    @staticmethod
    def from_response(response: requests.Response) -> "CFLabsAPIError":
        request_id = response.headers.get("X-Request-ID")
        raw_text = _safe_response_text(response)

        parsed: dict[str, Any] | None = None
        try:
            parsed = response.json()
        except Exception:
            parsed = None

        # Backend standardized shape is usually:
        # {"error": {"code": ..., "message": ..., "details": {...}, "request_id": ...}}
        # Some FastAPI errors may be: {"detail": {"error": {...}}} or {"detail": "..."}
        payload = parsed
        if (
            isinstance(parsed, dict)
            and "detail" in parsed
            and isinstance(parsed.get("detail"), dict)
        ):
            payload = parsed.get("detail")

        error_obj = None
        if isinstance(payload, dict) and isinstance(payload.get("error"), dict):
            error_obj = payload.get("error")

        error_code = None
        message = None
        details: dict[str, Any] = {}
        body_request_id = None

        if error_obj:
            error_code = error_obj.get("code")
            message = error_obj.get("message")
            details = error_obj.get("details") or {}
            body_request_id = error_obj.get("request_id")
        elif isinstance(payload, dict) and isinstance(payload.get("detail"), str):
            message = payload.get("detail")
        elif isinstance(parsed, dict) and isinstance(parsed.get("detail"), str):
            message = parsed.get("detail")
        else:
            message = f"HTTP {response.status_code}"

        # Prefer request_id from body if present.
        request_id = body_request_id or request_id

        provider_error = _extract_provider_error(details)

        return CFLabsAPIError(
            status_code=response.status_code,
            url=str(response.url),
            error_code=error_code,
            message=message or f"HTTP {response.status_code}",
            details=details,
            request_id=request_id,
            provider_error=provider_error,
            raw_text=_pretty_json(parsed) if parsed is not None else raw_text,
        )


def _extract_provider_error(details: dict[str, Any]) -> str | None:
    if not isinstance(details, dict):
        return None

    # Backend currently stores provider exceptions under details["original_error"].
    original_error = details.get("original_error")
    if isinstance(original_error, str) and original_error.strip():
        # If LiteLLM wraps as e.g. "litellm.BadRequestError: AnthropicException - {...}",
        # prefer the AnthropicException suffix for readability.
        marker = "AnthropicException - "
        if marker in original_error:
            return marker + original_error.split(marker, 1)[1].strip()
        return original_error.strip()

    # Fallbacks for other future shapes.
    maybe_error = details.get("error")
    if isinstance(maybe_error, str) and maybe_error.strip():
        return maybe_error.strip()

    return None


def _safe_response_text(response: requests.Response) -> str:
    try:
        return response.text
    except Exception:
        return ""


def _pretty_json(value: Any) -> str:
    try:
        return json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True)
    except Exception:
        return str(value)


def _looks_like_url(value: str) -> bool:
    s = value.lstrip()
    lower = s.lower()
    if lower.startswith(("http://", "https://", "data:", "s3://", "gs://")):
        return True
    # Generic scheme detection (e.g. "ftp://", "file://") but only near the front
    # to avoid treating arbitrary text as a URL.
    return "://" in lower[:64]


def _normalize_input_value(value: Any) -> Any:
    """Normalize SDK input values to the Octavian API format.

    Supports:
    - Passing ImageInput/PdfInput directly
    - Passing an existing local file path as a plain string (auto-encodes)
    """
    if isinstance(value, (ImageInput, PdfInput)):
        return value.to_dict()

    if isinstance(value, str):
        # IMPORTANT: treat URL strings and large / multi-line text as pure text.
        # Attempting Path(...).is_file() on these can raise (e.g. Errno 36 on Linux).
        if _looks_like_url(value):
            return value
        if "\n" in value or "\r" in value:
            return value
        # Avoid filesystem stats for large text blobs (JSON, prompts, etc.).
        if len(value) > 1024:
            return value
        if value[:1] in ("{", "[", "<"):
            return value

        try:
            p = Path(value)
            if p.is_file():
                guessed, _ = mimetypes.guess_type(str(p))
                if guessed and guessed.startswith("image/"):
                    return ImageInput.from_file(p).to_dict()
                if guessed == "application/pdf" or p.suffix.lower() == ".pdf":
                    return PdfInput.from_file(p).to_dict()
                raise ValueError(
                    f"Local file path provided ('{p}'), but mime type '{guessed}' is not supported. "
                    "Use ImageInput/PdfInput explicitly or pass a URL/data URL."
                )
        except (OSError, ValueError):
            # If the string isn't a valid local path (or is too long), keep it as text.
            return value

    return value


@dataclass(frozen=True)
class ImageInput:
    """Represents an image variable input for Octavian.

    Use either a URL or a local file.
    """

    source: str
    url: Optional[str] = None
    data: Optional[str] = None
    mime_type: Optional[str] = None
    abs_path_local_file: Optional[str] = None
    size_bytes: Optional[int] = None

    @classmethod
    def from_url(cls, url: str, mime_type: Optional[str] = None) -> "ImageInput":
        return cls(source="url", url=url, mime_type=mime_type)

    @classmethod
    def from_file(
        cls, path: Union[str, Path], mime_type: Optional[str] = None
    ) -> "ImageInput":
        p = Path(path)
        raw = p.read_bytes()
        b64 = base64.b64encode(raw).decode("utf-8")

        mt = mime_type
        if not mt:
            guessed, _ = mimetypes.guess_type(str(p))
            mt = guessed

        if not mt or not mt.startswith("image/"):
            raise ValueError(
                f"Could not infer image mime type for '{p}'. Pass mime_type='image/png' (or similar)."
            )

        return cls(
            source="base64",
            data=b64,
            mime_type=mt,
            abs_path_local_file=str(p.resolve()),
            size_bytes=len(raw),
        )

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"source": self.source}
        if self.url is not None:
            payload["url"] = self.url
        if self.data is not None:
            payload["data"] = self.data
        if self.mime_type is not None:
            payload["mime_type"] = self.mime_type
        if self.abs_path_local_file is not None:
            payload["abs_path_local_file"] = self.abs_path_local_file
        if self.size_bytes is not None:
            payload["size_bytes"] = self.size_bytes
        return payload


@dataclass(frozen=True)
class PdfInput:
    """Represents a PDF variable input for Octavian."""

    source: str
    url: Optional[str] = None
    data: Optional[str] = None
    mime_type: str = "application/pdf"
    abs_path_local_file: Optional[str] = None
    size_bytes: Optional[int] = None

    @classmethod
    def from_url(cls, url: str) -> "PdfInput":
        return cls(source="url", url=url)

    @classmethod
    def from_file(cls, path: Union[str, Path]) -> "PdfInput":
        p = Path(path)
        raw = p.read_bytes()
        b64 = base64.b64encode(raw).decode("utf-8")
        return cls(
            source="base64",
            data=b64,
            abs_path_local_file=str(p.resolve()),
            size_bytes=len(raw),
        )

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"source": self.source, "mime_type": self.mime_type}
        if self.url is not None:
            payload["url"] = self.url
        if self.data is not None:
            payload["data"] = self.data
        if self.abs_path_local_file is not None:
            payload["abs_path_local_file"] = self.abs_path_local_file
        if self.size_bytes is not None:
            payload["size_bytes"] = self.size_bytes
        return payload
