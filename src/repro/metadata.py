from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import platform
import sys
from typing import Any
import uuid


@dataclass(frozen=True)
class ArtifactHash:
    algorithm: str
    path: str
    sha256: str
    size_bytes: int


def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _stable_json_dumps(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def hash_file(path: str | Path, chunk_size: int = 1 << 20) -> ArtifactHash:
    file_path = Path(path)
    digest = sha256()
    with file_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)

    return ArtifactHash(
        algorithm="sha256",
        path=file_path.name,
        sha256=digest.hexdigest(),
        size_bytes=file_path.stat().st_size,
    )


def collect_environment() -> dict[str, Any]:
    return {
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "executable": sys.executable,
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
    }


def create_run_metadata(
    *,
    run_dir: str | Path,
    deterministic_mode: bool,
    config_payload: dict[str, Any],
    artifacts: list[str | Path],
    command: list[str] | None = None,
) -> dict[str, Any]:
    run_root = Path(run_dir)
    artifact_hashes = [asdict(hash_file(path)) for path in artifacts]

    metadata = {
        "schema_version": "1.0",
        "run_id": str(uuid.uuid4()),
        "created_at_utc": _iso_utc_now(),
        "run_dir": str(run_root),
        "deterministic_mode": deterministic_mode,
        "command": command or sys.argv,
        "environment": collect_environment(),
        "config_sha256": sha256(_stable_json_dumps(config_payload).encode("utf-8")).hexdigest(),
        "artifacts": artifact_hashes,
    }
    return metadata


def write_metadata(metadata: dict[str, Any], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output
