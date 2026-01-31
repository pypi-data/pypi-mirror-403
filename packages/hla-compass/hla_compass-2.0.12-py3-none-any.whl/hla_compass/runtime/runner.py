"""Entry point for containerized module execution.

This runner downloads payload/context artefacts from S3 (if applicable),
executes the module entrypoint, and writes outputs/summaries back to S3.
"""

from __future__ import annotations

import importlib
import json
import logging
import os
import sys
import traceback
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

import boto3
import requests
from botocore.exceptions import BotoCoreError, NoRegionError, ClientError

from ..module import Module
from ..types import ExecutionContext


PAYLOAD_REF = os.getenv("HLA_COMPASS_PAYLOAD", "/var/input.json")
CONTEXT_REF = os.getenv("HLA_COMPASS_CONTEXT", "/var/context.json")
OUTPUT_REF = os.getenv("HLA_COMPASS_OUTPUT", "/var/output.json")
SUMMARY_REF = os.getenv("HLA_COMPASS_SUMMARY", "/var/summary.json")
MODE = os.getenv("HLA_COMPASS_RUN_MODE", "async")
MODULE_ENTRY = os.getenv("HLA_COMPASS_MODULE", "backend.main:Module")
LOCAL_WORKDIR = Path(os.getenv("HLA_COMPASS_WORKDIR", "/tmp/hla-compass"))
LOCAL_WORKDIR.mkdir(parents=True, exist_ok=True)

_s3_client = None


def _configure_logging() -> None:
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return
    level_name = os.getenv("LOG_LEVEL") or os.getenv("HLA_COMPASS_LOG_LEVEL") or "INFO"
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stdout,
    )


def _get_s3_client():
    global _s3_client
    if _s3_client is not None:
        return _s3_client
    region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
    client_kwargs = {}
    if region:
        client_kwargs["region_name"] = region
    try:
        _s3_client = boto3.client("s3", **client_kwargs)
    except NoRegionError as exc:  # pragma: no cover - defensive
        raise RuntimeError(
            "S3 references require AWS_REGION or AWS_DEFAULT_REGION to be set."
        ) from exc
    except BotoCoreError as exc:  # pragma: no cover - defensive
        raise RuntimeError("Failed to initialize S3 client.") from exc
    return _s3_client


def _now_utc_iso() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_s3_uri(uri: str) -> Tuple[str, str]:
    parsed = urlparse(uri)
    if parsed.scheme != "s3" or not parsed.netloc or not parsed.path:
        raise ValueError(f"Invalid S3 URI: {uri}")
    bucket = parsed.netloc
    key = parsed.path.lstrip("/")
    return bucket, key


def _should_retry_http_error(exc: Exception) -> bool:
    if isinstance(exc, requests.RequestException):
        if exc.response is not None:
            return exc.response.status_code in {408, 429, 500, 502, 503, 504}
    return False


def _should_retry_s3_error(exc: Exception) -> bool:
    if isinstance(exc, ClientError):
        status = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        return status in {408, 429, 500, 502, 503, 504}
    return isinstance(exc, BotoCoreError)


def _retry_op(operation, should_retry_func, *, attempts: int = 3, base_delay: float = 1.0, max_delay: float = 10.0) -> None:
    for attempt in range(attempts):
        try:
            operation()
            return
        except Exception as exc:
            if attempt >= attempts - 1 or not should_retry_func(exc):
                raise
            delay = min(base_delay * (2 ** attempt), max_delay)
            time.sleep(delay)


def _ensure_local_input(reference: str, fallback_name: str) -> Tuple[Path, Optional[str]]:
    local_path = LOCAL_WORKDIR / fallback_name
    local_path.parent.mkdir(parents=True, exist_ok=True)

    if reference.startswith("https://") or reference.startswith("http://"):
        def _download():
            with requests.get(reference, stream=True, timeout=30) as r:
                r.raise_for_status()
                with local_path.open("wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
        
        _retry_op(_download, _should_retry_http_error)
        return local_path, reference

    if reference.startswith("s3://"):
        bucket, key = _parse_s3_uri(reference)
        client = _get_s3_client()
        _retry_op(lambda: client.download_file(bucket, key, str(local_path)), _should_retry_s3_error)
        return local_path, reference
        
    return Path(reference), None


def _prepare_output(reference: str, fallback_name: str) -> Tuple[Path, Optional[str]]:
    local_path = LOCAL_WORKDIR / fallback_name
    local_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Return path and reference; reference might be an HTTPS URL or S3 URI
    if reference.startswith("https://") or reference.startswith("http://") or reference.startswith("s3://"):
        return local_path, reference
        
    return Path(reference), None


def _upload_json_if_needed(path: Path, reference: Optional[str]) -> None:
    if not reference:
        return
        
    with path.open("rb") as fh:
        body = fh.read()

    if reference.startswith("https://") or reference.startswith("http://"):
        def _upload():
            with requests.put(reference, data=body, headers={"Content-Type": "application/json"}, timeout=30) as r:
                r.raise_for_status()
        _retry_op(_upload, _should_retry_http_error)
        return

    if reference.startswith("s3://"):
        bucket, key = _parse_s3_uri(reference)
        client = _get_s3_client()
        _retry_op(
            lambda: client.put_object(
                Bucket=bucket,
                Key=key,
                Body=body,
                ContentType="application/json",
            ),
            _should_retry_s3_error
        )


def _load_payload(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("Payload must be a JSON object.")
    return data


def _load_context(path: Path) -> ExecutionContext:
    if not path.exists():
        return ExecutionContext(  # type: ignore[arg-type]
            run_id="local",
            job_id="local",
            module_id="local-module",
            module_version="0.0.0",
            user_id="local",
            organization_id="local",
            roles=["developer"],
            environment=os.getenv("HLA_COMPASS_ENV") or os.getenv("HLA_ENV", "local"),
            correlation_id="local-run",
            requested_at=_now_utc_iso(),
            api=None,
            storage=None,
            tier="foundational",
            execution_time=None,
            mode=MODE,
        )
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("Context payload must be a JSON object.")
    data.setdefault("run_id", data.get("job_id") or "local")
    data.setdefault("job_id", data["run_id"])
    data.setdefault("module_id", data.get("moduleId") or "local-module")
    data.setdefault("module_version", data.get("moduleVersion") or "0.0.0")
    data.setdefault("roles", data.get("roles") or ["developer"])
    data.setdefault("environment", data.get("environment") or os.getenv("HLA_COMPASS_ENV") or os.getenv("HLA_ENV", "local"))
    data.setdefault("correlation_id", data.get("correlation_id") or data["run_id"])
    data.setdefault("requested_at", data.get("requested_at") or _now_utc_iso())
    data.setdefault("mode", MODE)
    if not (
        data.get("state_machine_execution_arn")
        or data.get("stateMachineExecutionArn")
    ):
        env_execution_arn = os.environ.get("HLA_COMPASS_STATE_MACHINE_EXECUTION_ARN")
        if env_execution_arn:
            data["state_machine_execution_arn"] = env_execution_arn
    return data  # type: ignore[return-value]


def _resolve_module(entry: str) -> Module:
    if ":" not in entry:
        raise RuntimeError("HLA_COMPASS_MODULE must be in format '<module_path>:<class_name>'")
    module_path, class_name = entry.split(":", 1)
    module = importlib.import_module(module_path)
    clazz = getattr(module, class_name, None)
    if clazz is None:
        raise RuntimeError(f"Module class '{class_name}' not found in '{module_path}'")
    if not issubclass(clazz, Module):
        raise RuntimeError("Configured class does not inherit from Module")
    return clazz()


def _write_output(result: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, default=str)


def _write_summary(summary: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, default=str)


def main() -> None:
    _configure_logging()
    # Execute once per container invocation.

    payload_path, payload_s3 = _ensure_local_input(PAYLOAD_REF, "payload.json")
    context_path, context_s3 = _ensure_local_input(CONTEXT_REF, "context.json")
    output_path, output_s3 = _prepare_output(OUTPUT_REF, "output.json")
    summary_path, summary_s3 = _prepare_output(SUMMARY_REF, "summary.json")

    try:
        module_instance = _resolve_module(MODULE_ENTRY)
        payload = _load_payload(payload_path)
        context = _load_context(context_path)
        result = module_instance.run(payload, context)
        _write_output(result, output_path)
        summary = result.get("summary", {}) if isinstance(result, dict) else {}
        _write_summary(summary if isinstance(summary, dict) else {"summary": summary}, summary_path)
        _upload_json_if_needed(output_path, output_s3)
        _upload_json_if_needed(summary_path, summary_s3)
    except Exception as exc:  # pragma: no cover - container level failure
        s3_refs = {
            "payload": payload_s3,
            "context": context_s3,
            "output": output_s3,
            "summary": summary_s3,
        }
        error_payload = {
            "status": "error",
            "error": {
                "type": "runtime_error",
                "message": str(exc),
                "traceback": traceback.format_exc(),
                "s3_refs": {key: value for key, value in s3_refs.items() if value},
            },
        }
        _write_output(error_payload, output_path)
        _upload_json_if_needed(output_path, output_s3)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
