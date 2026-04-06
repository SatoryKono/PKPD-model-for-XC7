from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC_DIR = ROOT / "src"
CONFIG_DIR = ROOT / "examples" / "configs"
DOC_DIR = ROOT / "docs"
SRC_OUTPUT = ROOT / "src_all.md"
CONFIG_OUTPUT = ROOT / "config_all.md"
DOC_OUTPUT = ROOT / "doc_all.md"
SKIP_DIR_NAMES = {"__pycache__"}
SKIP_SUFFIXES = {".pyc", ".pyo"}

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def _iter_text_files(base_dir: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(base_dir.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        files.append(path)
    return files


def _language_for_suffix(path: Path) -> str:
    suffix = path.suffix.lower()
    return {
        ".py": "python",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".json": "json",
        ".md": "markdown",
        ".txt": "text",
        ".cfg": "ini",
        ".ini": "ini",
    }.get(suffix, "")


def _render_bundle(paths: list[Path]) -> str:
    sections: list[str] = []
    for path in paths:
        resolved = path.resolve()
        language = _language_for_suffix(path)
        try:
            content = path.read_text(encoding="utf-8")
            binary_notice = None
        except UnicodeDecodeError:
            content = "[binary or non-UTF-8 file skipped]"
            binary_notice = "text"
        fence = f"```{language}" if language else "```"
        if binary_notice is not None:
            fence = f"```{binary_notice}"
        sections.append(
            "\n".join(
                [
                    f"# {resolved}  {path.name}",
                    "",
                    fence,
                    content.rstrip("\n"),
                    "```",
                    "",
                ]
            )
        )
    return "\n".join(sections).rstrip() + "\n"


def _atomic_write_text(dest_path: Path, payload: str) -> None:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(dir=dest_path.parent, suffix=".tmp", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
        os.replace(temp_path, dest_path)
    except Exception:
        try:
            os.remove(temp_path)
        except OSError:
            pass
        raise


def build_bundle(base_dir: Path, output_path: Path) -> None:
    paths = _iter_text_files(base_dir)
    payload = _render_bundle(paths)
    _atomic_write_text(output_path, payload)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Собирает все файлы из src, examples/configs и docs в единые Markdown-файлы."
    )
    parser.add_argument(
        "--src-output",
        type=Path,
        default=SRC_OUTPUT,
        help="Путь для итогового Markdown по директории src.",
    )
    parser.add_argument(
        "--config-output",
        type=Path,
        default=CONFIG_OUTPUT,
        help="Путь для итогового Markdown по директории examples/configs.",
    )
    parser.add_argument(
        "--doc-output",
        type=Path,
        default=DOC_OUTPUT,
        help="Путь для итогового Markdown по директории docs.",
    )
    args = parser.parse_args()

    build_bundle(SRC_DIR, args.src_output.resolve())
    build_bundle(CONFIG_DIR, args.config_output.resolve())
    build_bundle(DOC_DIR, args.doc_output.resolve())

    print(f"Saved source bundle: {args.src_output.resolve()}")
    print(f"Saved config bundle: {args.config_output.resolve()}")
    print(f"Saved docs bundle: {args.doc_output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
