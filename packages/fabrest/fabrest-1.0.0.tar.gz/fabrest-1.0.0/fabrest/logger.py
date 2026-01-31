import json
import logging
from string import Formatter
from typing import Any, Dict, Optional, Tuple

from .logging_catalog import LOG_EVENTS


BASE_LOGGER_NAME = "fabrest"


def _configure_logger(base_logger: logging.Logger) -> None:
    base_logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    if not base_logger.hasHandlers():
        base_logger.addHandler(console_handler)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    if name and name.startswith(BASE_LOGGER_NAME):
        logger = logging.getLogger(name)
    elif name:
        logger = logging.getLogger(f"{BASE_LOGGER_NAME}.{name}")
    else:
        logger = logging.getLogger(BASE_LOGGER_NAME)
    _configure_logger(logging.getLogger(BASE_LOGGER_NAME))
    return logger


def _format_fields(fields: Dict[str, Any]) -> str:
    parts = []
    for key, value in fields.items():
        if value is None:
            continue
        if isinstance(value, (dict, list)):
            rendered = json.dumps(value, ensure_ascii=True, separators=(",", ":"))
        else:
            rendered = str(value)
        parts.append(f"{key}={rendered}")
    return " ".join(parts)


def render_message(template: str, fields: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    formatter = Formatter()
    used_keys = set()
    for _, field_name, _, _ in formatter.parse(template):
        if field_name:
            used_keys.add(field_name)

    class _SafeDict(dict):
        def __missing__(self, key: str) -> str:
            return ""

    message = template.format_map(_SafeDict(fields))
    remaining = {k: v for k, v in fields.items() if k not in used_keys}
    return message.strip(), remaining


def log_event(logger: logging.Logger, event: str, **fields: Any) -> None:
    meta = LOG_EVENTS.get(event, {})
    level = meta.get("level", "info")
    template = meta.get("template", event)
    message, remaining = render_message(template, fields)
    payload = _format_fields(remaining)
    full_message = f"{message} {payload}".strip()
    log_fn = getattr(logger, level, logger.info)
    log_fn(full_message)
