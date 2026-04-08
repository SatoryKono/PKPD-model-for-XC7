from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
DEFAULT_FIGURES_DIR = DOCS_DIR / "figures"
DEFAULT_OUTPUT_PATH = DOCS_DIR / "gsignaling_bundle.docx"
G_SIGNALING_PATTERN = re.compile(
    r"^fig(?P<chapter>\d+)_3_(?P<scenario>[a-z0-9_]+)_dose_(?P<dose>\d+)mgkg_gsignaling\.png$"
)
SCENARIO_ORDER = (
    "formalin",
    "compound_48_80",
    "capsaicin",
    "carrageenan",
    "hot_plate",
    "acetic_writhing",
    "zymosan",
)
SCENARIO_ORDER_INDEX = {scenario_id: index for index, scenario_id in enumerate(SCENARIO_ORDER)}

if str(DOCS_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_DIR))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from _docx_common import (
    _portrait_a4_section_xml,
    _image_paragraph_xml,
    _image_size_emu,
    _page_break_paragraph_xml,
    _paragraph_xml,
    _table_xml,
    MAX_IMAGE_WIDTH_EMU_PORTRAIT,
    build_document_xml,
    write_docx_package,
)
from build_figures_docx import SECTION_TITLE_OVERRIDES, _config_rows_for_scenario, _to_title_case


@dataclass(frozen=True, slots=True)
class GSignalingAsset:
    path: Path
    relative_path: Path
    chapter_num: int
    scenario_id: str
    scenario_label: str
    section_title: str
    dose_mgkg: int


def _scenario_sort_key(asset: GSignalingAsset) -> tuple[int, int, str]:
    return (
        SCENARIO_ORDER_INDEX.get(asset.scenario_id, len(SCENARIO_ORDER)),
        asset.chapter_num,
        asset.scenario_id,
    )


def _asset_sort_key(asset: GSignalingAsset) -> tuple[int, int]:
    return (_scenario_sort_key(asset)[0], asset.dose_mgkg)


def _panel_label(dose_mgkg: int, *, letter: str) -> str:
    if dose_mgkg == 0:
        return f"{letter} - контроль патологии"
    return f"{letter} - XC7DCH в дозе {dose_mgkg} мг/кг"


def _caption_for_group(chapter_num: int, section_title: str, doses_mgkg: list[int]) -> str:
    panel_labels = [_panel_label(dose, letter=chr(65 + index)) for index, dose in enumerate(doses_mgkg)]
    labels_text = ", ".join(panel_labels)
    return (
        f"Рисунок {chapter_num}.1 {section_title} "
        f"Уровень функциональной активности H3 рецепторов после индукции патологии. "
        f"{labels_text}."
    )


def collect_gsignaling_assets(figures_dir: Path | str) -> list[GSignalingAsset]:
    resolved_dir = Path(figures_dir)
    if not resolved_dir.exists():
        raise FileNotFoundError(f"Figures directory does not exist: {resolved_dir}")
    if not resolved_dir.is_dir():
        raise NotADirectoryError(f"Expected a directory with figures: {resolved_dir}")

    assets: list[GSignalingAsset] = []
    for path in resolved_dir.rglob("*.png"):
        relative_path = path.relative_to(resolved_dir)
        match = G_SIGNALING_PATTERN.fullmatch(relative_path.name)
        if match is None:
            continue

        scenario_id = match.group("scenario")
        if scenario_id == "intact":
            continue

        scenario_label = _to_title_case(scenario_id)
        section_title = SECTION_TITLE_OVERRIDES.get(scenario_label, scenario_label)
        assets.append(
            GSignalingAsset(
                path=path,
                relative_path=relative_path,
                chapter_num=int(match.group("chapter")),
                scenario_id=scenario_id,
                scenario_label=scenario_label,
                section_title=section_title,
                dose_mgkg=int(match.group("dose")),
            )
        )

    if not assets:
        raise ValueError(f"No dose-specific G-signaling PNG files were found in: {resolved_dir}")

    return sorted(assets, key=lambda asset: (_scenario_sort_key(asset), asset.dose_mgkg))


def _document_xml(title: str, assets: list[GSignalingAsset]) -> tuple[str, list[tuple[str, str, bytes]]]:
    body_parts = [_paragraph_xml(title, style="Title")]
    media_entries: list[tuple[str, str, bytes]] = []

    grouped_assets: dict[str, list[GSignalingAsset]] = {}
    for asset in assets:
        grouped_assets.setdefault(asset.scenario_id, []).append(asset)

    ordered_groups = sorted(
        grouped_assets.values(),
        key=lambda group: _scenario_sort_key(group[0]),
    )

    image_index = 1
    for group_index, group in enumerate(ordered_groups):
        if group_index > 0:
            body_parts.append(_page_break_paragraph_xml())

        group = sorted(group, key=lambda asset: asset.dose_mgkg)
        group_head = group[0]
        body_parts.append(_paragraph_xml(group_head.section_title, style="Heading1"))

        doses_mgkg: list[int] = []
        for asset in group:
            image_bytes = asset.path.read_bytes()
            rel_id = f"rId{image_index}"
            media_name = f"image{image_index}{asset.path.suffix.lower()}"
            width_emu, height_emu = _image_size_emu(asset.path, max_width_emu=MAX_IMAGE_WIDTH_EMU_PORTRAIT)
            body_parts.append(
                _image_paragraph_xml(
                    rel_id=rel_id,
                    image_name=media_name,
                    width_emu=width_emu,
                    height_emu=height_emu,
                    drawing_id=image_index,
                )
            )
            media_entries.append((rel_id, media_name, image_bytes))
            doses_mgkg.append(asset.dose_mgkg)
            image_index += 1

        body_parts.append(_paragraph_xml(_caption_for_group(group_head.chapter_num, group_head.section_title, doses_mgkg)))
        config_rows = _config_rows_for_scenario(group_head.scenario_id)
        if config_rows:
            body_parts.append(_paragraph_xml("Параметры конфигурации", style="Heading2"))
            body_parts.append(_table_xml(config_rows))

    return build_document_xml(body_parts, section_xml=_portrait_a4_section_xml()), media_entries


def build_gsignaling_docx(
    figures_dir: Path | str,
    output_path: Path | str,
    *,
    title: str = "Dose-specific G-signaling Figures",
) -> Path:
    assets = collect_gsignaling_assets(figures_dir)
    document_xml, media_entries = _document_xml(title, assets)
    return write_docx_package(output_path, title=title, document_xml=document_xml, media_entries=media_entries)


def main() -> int:
    parser = argparse.ArgumentParser(description="Bundle dose-specific G-signaling PNG files into a DOCX document.")
    parser.add_argument(
        "--figures-dir",
        type=Path,
        default=DEFAULT_FIGURES_DIR,
        help="Directory with dose-specific G-signaling PNG files.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Output DOCX path.",
    )
    parser.add_argument(
        "--title",
        default="Dose-specific G-signaling Figures",
        help="Document title written into the DOCX.",
    )
    args = parser.parse_args()

    output = build_gsignaling_docx(args.figures_dir, args.out, title=args.title)
    print(f"Saved DOCX report: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
