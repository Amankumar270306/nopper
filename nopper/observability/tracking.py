"""Usage tracking and logging module."""

import csv
import json
import time
from pathlib import Path
from typing import Any


def log_usage(
    prompt: Any,
    response: Any,
    enabled: bool = False,
    file_path: str = "usage.csv",
    fmt: str = "csv",
) -> None:
    """Log usage statistics to a file (CSV or JSON)."""
    if not enabled:
        return

    path = Path(file_path)
    prompt_str = str(prompt)
    response_str = getattr(response.message, "content", "") if hasattr(response, "message") else str(response)

    tokens = getattr(response, "total_tokens", 0)
    cost = getattr(response, "cost", 0.0)
    model = getattr(response, "model", "unknown")
    provider = getattr(response, "provider", "unknown")
    latency = getattr(response, "latency", 0.0)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    data = {
        "timestamp": timestamp,
        "provider": provider,
        "model": model,
        "prompt": prompt_str,
        "response": response_str,
        "total_tokens": tokens,
        "cost": cost,
        "latency": latency,
    }

    if fmt.lower() == "json":
        records = []
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    records = json.load(f)
            except json.JSONDecodeError:
                records = []
        records.append(data)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)
    else:
        file_exists = path.exists()
        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "timestamp",
                    "provider",
                    "model",
                    "prompt",
                    "response",
                    "total_tokens",
                    "cost",
                    "latency",
                ],
            )
            if not file_exists:
                writer.writeheader()
            writer.writerow(data)
