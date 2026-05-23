from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = ROOT_DIR / "logs"
WORKFLOW_LOG = LOGS_DIR / "workflow.log"


def get_workflow_logger() -> logging.Logger:
    logger = logging.getLogger("mywiki.workflow")
    if logger.handlers:
        return logger

    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    handler = logging.FileHandler(WORKFLOW_LOG, encoding="utf-8")
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    )

    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def log_workflow(stage: str, message: str, **context: Any) -> None:
    logger = get_workflow_logger()
    payload = json.dumps(context, sort_keys=True, default=str) if context else "{}"
    logger.info("%s | %s | %s", stage, message, payload)
