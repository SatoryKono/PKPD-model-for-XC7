from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from pathlib import Path


class JsonlFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        run_id = getattr(record, "run_id", None)
        if run_id is not None:
            payload["run_id"] = run_id
        return json.dumps(payload, ensure_ascii=False)


def configure_run_logger(run_dir: str | Path, *, logger_name: str = "pkpd.run") -> logging.Logger:
    output_dir = Path(run_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    text_handler = logging.FileHandler(output_dir / "run.log", encoding="utf-8")
    text_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))

    jsonl_handler = logging.FileHandler(output_dir / "run.jsonl", encoding="utf-8")
    jsonl_handler.setFormatter(JsonlFormatter())

    logger.addHandler(text_handler)
    logger.addHandler(jsonl_handler)
    return logger


def close_run_logger(logger: logging.Logger) -> None:
    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)
