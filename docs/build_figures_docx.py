from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
SRC = ROOT / "src"
DEFAULT_FIGURES_DIR = DOCS_DIR / "figures"
DEFAULT_OUTPUT_PATH = DOCS_DIR / "figures_bundle.docx"
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg"}
DOCX_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
IMAGE_KIND_LABELS = {
    "histamine": "Histamine",
    "internalization": "Internalization",
    "gsignaling": "G-signaling",
    "xc7_concentration": "Концентрация XC7 в тканях",
}
SECTION_TITLE_OVERRIDES = {
    "Formalin": "Модель болевого синдрома, индуцированная введением формалина.",
    "Compound 48 80": "Модель болевого синдрома, индуцированная введением Compound 48/80.",
    "Capsaicin": "Модель болевого синдрома, индуцированная введением капсаицина.",
    "Carrageenan": "Модель болевого синдрома, индуцированная введением карагенина.",
    "Hot Plate": "Модель болевого синдрома, индуцированная термическим воздействием в тесте «Горячая пластина».",
    "Acetic Writhing": "Модель болевого синдрома, индуцированная введением уксусной кислоты.",
    "Zymosan": "Модель болевого синдрома, индуцированная введением зимозана.",
}
FIGURE_CAPTION_OVERRIDES = {
    "fig1_1_formalin_histamine.png": (
        "Рисунок 1.1 Модель болевого синдрома, индуцированная введением формалина. "
        "Изменение концентрации гистамина после индукции паталогии."
    ),
    "fig1_2_formalin_internalization.png": (
        "Рисунок 1.2 Модель болевого синдрома, индуцированная введением формалина. "
        "Интернализация H3 рецепторов после индукции паталогии."
    ),
    "fig1_3_formalin_gsignaling.png": (
        "Рисунок 1.3 Модель болевого синдрома, индуцированная введением формалина. "
        "Уровень функциональной активности H3 рецепторов после индукции паталогии."
    ),
    "fig1_4_formalin_xc7_concentration.png": (
        "Рисунок 1.4 Модель болевого синдрома, индуцированная введением формалина. "
        "Концентрация XC7 в тканях после индукции патологии."
    ),
    "fig2_1_compound_48_80_histamine.png": (
        "Рисунок 2.1 Модель болевого синдрома, индуцированная введением Compound 48/80. "
        "Изменение концентрации гистамина после индукции паталогии."
    ),
    "fig2_2_compound_48_80_internalization.png": (
        "Рисунок 2.2 Модель болевого синдрома, индуцированная введением Compound 48/80. "
        "Интернализация H3 рецепторов после индукции паталогии."
    ),
    "fig2_3_compound_48_80_gsignaling.png": (
        "Рисунок 2.3 Модель болевого синдрома, индуцированная введением Compound 48/80. "
        "Уровень функциональной активности H3 рецепторов после индукции паталогии."
    ),
    "fig2_4_compound_48_80_xc7_concentration.png": (
        "Рисунок 2.4 Модель болевого синдрома, индуцированная введением Compound 48/80. "
        "Концентрация XC7 в тканях после индукции патологии."
    ),
    "fig3_1_capsaicin_histamine.png": (
        "Рисунок 3.1 Модель болевого синдрома, индуцированная введением капсаицина. "
        "Изменение концентрации гистамина после индукции паталогии."
    ),
    "fig3_2_capsaicin_internalization.png": (
        "Рисунок 3.2 Модель болевого синдрома, индуцированная введением капсаицина. "
        "Интернализация H3 рецепторов после индукции паталогии."
    ),
    "fig3_3_capsaicin_gsignaling.png": (
        "Рисунок 3.3 Модель болевого синдрома, индуцированная введением капсаицина. "
        "Уровень функциональной активности H3 рецепторов после индукции паталогии."
    ),
    "fig3_4_capsaicin_xc7_concentration.png": (
        "Рисунок 3.4 Модель болевого синдрома, индуцированная введением капсаицина. "
        "Концентрация XC7 в тканях после индукции патологии."
    ),
    "fig4_1_carrageenan_histamine.png": (
        "Рисунок 4.1 Модель болевого синдрома, индуцированная введением карагенина. "
        "Изменение концентрации гистамина после индукции паталогии."
    ),
    "fig4_2_carrageenan_internalization.png": (
        "Рисунок 4.2 Модель болевого синдрома, индуцированная введением карагенина. "
        "Интернализация H3 рецепторов после индукции паталогии."
    ),
    "fig4_3_carrageenan_gsignaling.png": (
        "Рисунок 4.3 Модель болевого синдрома, индуцированная введением карагенина. "
        "Уровень функциональной активности H3 рецепторов после индукции паталогии."
    ),
    "fig4_4_carrageenan_xc7_concentration.png": (
        "Рисунок 4.4 Модель болевого синдрома, индуцированная введением карагенина. "
        "Концентрация XC7 в тканях после индукции патологии."
    ),
    "fig5_1_hot_plate_histamine.png": (
        "Рисунок 5.1 Модель болевого синдрома, индуцированная термическим воздействием "
        "в тесте «Горячая пластина». Изменение концентрации гистамина после индукции паталогии."
    ),
    "fig5_2_hot_plate_internalization.png": (
        "Рисунок 5.2 Модель болевого синдрома, индуцированная термическим воздействием "
        "в тесте «Горячая пластина». Интернализация H3 рецепторов после индукции паталогии."
    ),
    "fig5_3_hot_plate_gsignaling.png": (
        "Рисунок 5.3 Модель болевого синдрома, индуцированная термическим воздействием "
        "в тесте «Горячая пластина». Уровень функциональной активности H3 рецепторов после индукции паталогии."
    ),
    "fig5_4_hot_plate_xc7_concentration.png": (
        "Рисунок 5.4 Модель болевого синдрома, индуцированная термическим воздействием "
        "в тесте «Горячая пластина». Концентрация XC7 в тканях после индукции патологии."
    ),
    "fig6_1_acetic_writhing_histamine.png": (
        "Рисунок 6.1 Модель болевого синдрома, индуцированная введением уксусной кислоты. "
        "Изменение концентрации гистамина после индукции паталогии."
    ),
    "fig6_2_acetic_writhing_internalization.png": (
        "Рисунок 6.2 Модель болевого синдрома, индуцированная введением уксусной кислоты. "
        "Интернализация H3 рецепторов после индукции паталогии."
    ),
    "fig6_3_acetic_writhing_gsignaling.png": (
        "Рисунок 6.3 Модель болевого синдрома, индуцированная введением уксусной кислоты. "
        "Уровень функциональной активности H3 рецепторов после индукции паталогии."
    ),
    "fig6_4_acetic_writhing_xc7_concentration.png": (
        "Рисунок 6.4 Модель болевого синдрома, индуцированная введением уксусной кислоты. "
        "Концентрация XC7 в тканях после индукции патологии."
    ),
    "fig7_1_zymosan_histamine.png": (
        "Рисунок 7.1 Модель болевого синдрома, индуцированная введением зимозана. "
        "Изменение концентрации гистамина после индукции паталогии."
    ),
    "fig7_2_zymosan_internalization.png": (
        "Рисунок 7.2 Модель болевого синдрома, индуцированная введением зимозана. "
        "Интернализация H3 рецепторов после индукции паталогии."
    ),
    "fig7_3_zymosan_gsignaling.png": (
        "Рисунок 7.3 Модель болевого синдрома, индуцированная введением зимозана. "
        "Уровень функциональной активности H3 рецепторов после индукции паталогии."
    ),
    "fig7_4_zymosan_xc7_concentration.png": (
        "Рисунок 7.4 Модель болевого синдрома, индуцированная введением зимозана. "
        "Концентрация XC7 в тканях после индукции патологии."
    ),
}
EMU_PER_INCH = 914400
EMU_PER_PIXEL_AT_96_DPI = 9525
MAX_IMAGE_WIDTH_EMU = int(9.0 * EMU_PER_INCH)
TABLE_KEY_COLUMN_DXA = 4200
TABLE_VALUE_COLUMN_DXA = 9600

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pkpd_xc7.config.loader import load_model_config_payload


@dataclass(frozen=True, slots=True)
class FigureAsset:
    path: Path
    relative_path: Path
    scenario_id: str
    scenario_label: str
    section_title: str
    figure_label: str
    caption: str


def _stable_zip_write(zf: zipfile.ZipFile, arcname: str, payload: bytes) -> None:
    info = zipfile.ZipInfo(filename=arcname, date_time=DOCX_TIMESTAMP)
    info.compress_type = zipfile.ZIP_DEFLATED
    zf.writestr(info, payload)


def _read_png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as f:
        header = f.read(24)
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"Only PNG figures are supported for DOCX export: {path}")
    width = int.from_bytes(header[16:20], "big")
    height = int.from_bytes(header[20:24], "big")
    if width <= 0 or height <= 0:
        raise ValueError(f"Invalid PNG dimensions for figure: {path}")
    return width, height


def _to_title_case(value: str) -> str:
    return value.replace("_", " ").strip().title()


def _parse_figure_id(relative_path: Path) -> tuple[str, str, str]:
    stem = relative_path.stem
    for kind, kind_label in IMAGE_KIND_LABELS.items():
        suffix = f"_{kind}"
        if stem.endswith(suffix):
            scenario_token = stem[: -len(suffix)]
            scenario_token = re.sub(r"^fig\d+_\d+_", "", scenario_token)
            scenario_id = scenario_token if scenario_token else "figures"
            scenario_label = _to_title_case(scenario_token) if scenario_token else "Figures"
            return scenario_id, scenario_label, kind_label
    if relative_path.parent != Path("."):
        scenario_id = relative_path.parent.name
        scenario_label = _to_title_case(relative_path.parent.as_posix().replace("/", " "))
        return scenario_id, scenario_label, _to_title_case(stem)
    return "figures", "Figures", _to_title_case(stem)


def _default_caption(relative_path: Path, scenario_label: str, figure_label: str) -> str:
    match = re.match(r"^fig(\d+)_(\d+)_", relative_path.name)
    if match:
        number = f"{match.group(1)}.{match.group(2)}"
        return f"Рисунок {number} {scenario_label}. {figure_label}."
    return relative_path.as_posix()


def collect_figure_assets(figures_dir: Path | str) -> list[FigureAsset]:
    resolved_dir = Path(figures_dir)
    if not resolved_dir.exists():
        raise FileNotFoundError(f"Figures directory does not exist: {resolved_dir}")
    if not resolved_dir.is_dir():
        raise NotADirectoryError(f"Expected a directory with figures: {resolved_dir}")

    figure_paths = sorted(
        (
            path
            for path in resolved_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
        ),
        key=lambda path: path.relative_to(resolved_dir).as_posix(),
    )
    if not figure_paths:
        raise ValueError(f"No supported figure files were found in: {resolved_dir}")

    assets: list[FigureAsset] = []
    for path in figure_paths:
        relative_path = path.relative_to(resolved_dir)
        scenario_id, scenario_label, figure_label = _parse_figure_id(relative_path)
        section_title = SECTION_TITLE_OVERRIDES.get(scenario_label, scenario_label)
        caption = FIGURE_CAPTION_OVERRIDES.get(
            relative_path.name,
            _default_caption(relative_path, scenario_label, figure_label),
        )
        assets.append(
            FigureAsset(
                path=path,
                relative_path=relative_path,
                scenario_id=scenario_id,
                scenario_label=scenario_label,
                section_title=section_title,
                figure_label=figure_label,
                caption=caption,
            )
        )
    return assets


def _paragraph_xml(text: str, *, style: str | None = None) -> str:
    style_xml = f'<w:pPr><w:pStyle w:val="{escape(style)}"/></w:pPr>' if style else ""
    return (
        "<w:p>"
        f"{style_xml}"
        f"<w:r><w:t xml:space=\"preserve\">{escape(text)}</w:t></w:r>"
        "</w:p>"
    )


def _page_break_paragraph_xml() -> str:
    return "<w:p><w:r><w:br w:type=\"page\"/></w:r></w:p>"


def _table_cell_xml(text: str, *, width_dxa: int, bold: bool = False) -> str:
    bold_xml = "<w:b/>" if bold else ""
    return (
        "<w:tc>"
        f"<w:tcPr><w:tcW w:w=\"{width_dxa}\" w:type=\"dxa\"/></w:tcPr>"
        "<w:p>"
        f"<w:r><w:rPr>{bold_xml}</w:rPr><w:t xml:space=\"preserve\">{escape(text)}</w:t></w:r>"
        "</w:p>"
        "</w:tc>"
    )


def _table_xml(rows: list[tuple[str, str]]) -> str:
    body = [
        "<w:tbl>",
        "<w:tblPr>",
        "<w:tblW w:w=\"0\" w:type=\"auto\"/>",
        (
            "<w:tblBorders>"
            + "<w:top w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"auto\"/>"
            + "<w:left w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"auto\"/>"
            + "<w:bottom w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"auto\"/>"
            + "<w:right w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"auto\"/>"
            + "<w:insideH w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"auto\"/>"
            + "<w:insideV w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"auto\"/>"
            + "</w:tblBorders>"
        ),
        "</w:tblPr>",
        f"<w:tblGrid><w:gridCol w:w=\"{TABLE_KEY_COLUMN_DXA}\"/><w:gridCol w:w=\"{TABLE_VALUE_COLUMN_DXA}\"/></w:tblGrid>",
        "<w:tr>"
        f"{_table_cell_xml('Параметр', width_dxa=TABLE_KEY_COLUMN_DXA, bold=True)}"
        f"{_table_cell_xml('Значение', width_dxa=TABLE_VALUE_COLUMN_DXA, bold=True)}"
        "</w:tr>",
    ]
    for key, value in rows:
        body.append(
            "<w:tr>"
            f"{_table_cell_xml(key, width_dxa=TABLE_KEY_COLUMN_DXA)}"
            f"{_table_cell_xml(value, width_dxa=TABLE_VALUE_COLUMN_DXA)}"
            "</w:tr>"
        )
    body.append("</w:tbl>")
    return "".join(body)


def _serialize_config_value(value: Any) -> str:
    if isinstance(value, (str, int, float, bool)) or value is None:
        if isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        if len(value) > 16:
            head = ", ".join(_serialize_config_value(item) for item in value[:6])
            tail = ", ".join(_serialize_config_value(item) for item in value[-3:])
            return f"[{head}, ..., {tail}] (len={len(value)})"
        return json.dumps(value, ensure_ascii=False)
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _flatten_config_payload(payload: Any, *, prefix: str = "") -> list[tuple[str, str]]:
    if isinstance(payload, dict):
        rows: list[tuple[str, str]] = []
        for key, value in payload.items():
            next_prefix = f"{prefix}.{key}" if prefix else str(key)
            rows.extend(_flatten_config_payload(value, prefix=next_prefix))
        return rows
    return [(prefix, _serialize_config_value(payload))]


def _config_rows_for_scenario(scenario_id: str) -> list[tuple[str, str]]:
    config_path = ROOT / "examples" / "configs" / "scenarios" / f"{scenario_id}.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Scenario config was not found for DOCX export: {config_path}")
    payload = load_model_config_payload(config_path)
    return _flatten_config_payload(payload)


def _image_paragraph_xml(
    *,
    rel_id: str,
    image_name: str,
    width_emu: int,
    height_emu: int,
    drawing_id: int,
) -> str:
    name_xml = escape(image_name)
    return f"""
<w:p>
  <w:r>
    <w:drawing>
      <wp:inline distT="0" distB="0" distL="0" distR="0"
        xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
        xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
        xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">
        <wp:extent cx="{width_emu}" cy="{height_emu}"/>
        <wp:docPr id="{drawing_id}" name="{name_xml}"/>
        <wp:cNvGraphicFramePr>
          <a:graphicFrameLocks noChangeAspect="1"/>
        </wp:cNvGraphicFramePr>
        <a:graphic>
          <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
            <pic:pic>
              <pic:nvPicPr>
                <pic:cNvPr id="{drawing_id}" name="{name_xml}"/>
                <pic:cNvPicPr/>
              </pic:nvPicPr>
              <pic:blipFill>
                <a:blip r:embed="{rel_id}"/>
                <a:stretch><a:fillRect/></a:stretch>
              </pic:blipFill>
              <pic:spPr>
                <a:xfrm>
                  <a:off x="0" y="0"/>
                  <a:ext cx="{width_emu}" cy="{height_emu}"/>
                </a:xfrm>
                <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
              </pic:spPr>
            </pic:pic>
          </a:graphicData>
        </a:graphic>
      </wp:inline>
    </w:drawing>
  </w:r>
</w:p>
""".strip()


def _image_size_emu(path: Path) -> tuple[int, int]:
    width_px, height_px = _read_png_size(path)
    width_emu = width_px * EMU_PER_PIXEL_AT_96_DPI
    height_emu = height_px * EMU_PER_PIXEL_AT_96_DPI
    if width_emu > MAX_IMAGE_WIDTH_EMU:
        scale = MAX_IMAGE_WIDTH_EMU / float(width_emu)
        width_emu = MAX_IMAGE_WIDTH_EMU
        height_emu = int(height_emu * scale)
    return width_emu, height_emu


def _document_xml(title: str, assets: list[FigureAsset]) -> tuple[str, list[tuple[str, str, bytes]]]:
    body_parts = [_paragraph_xml(title, style="Title")]
    media_entries: list[tuple[str, str, bytes]] = []
    current_scenario: str | None = None
    config_rows_by_scenario = {
        scenario_id: _config_rows_for_scenario(scenario_id)
        for scenario_id in dict.fromkeys(asset.scenario_id for asset in assets)
        if scenario_id != "figures"
    }

    for index, asset in enumerate(assets, start=1):
        if asset.scenario_label != current_scenario:
            if current_scenario is not None:
                body_parts.append(_page_break_paragraph_xml())
            body_parts.append(_paragraph_xml(asset.section_title, style="Heading1"))
            current_scenario = asset.scenario_label
        image_bytes = asset.path.read_bytes()
        rel_id = f"rId{index}"
        media_name = f"image{index}{asset.path.suffix.lower()}"
        width_emu, height_emu = _image_size_emu(asset.path)
        body_parts.append(
            _image_paragraph_xml(
                rel_id=rel_id,
                image_name=media_name,
                width_emu=width_emu,
                height_emu=height_emu,
                drawing_id=index,
            )
        )
        body_parts.append(_paragraph_xml(asset.caption))
        media_entries.append((rel_id, media_name, image_bytes))

        next_asset = assets[index] if index < len(assets) else None
        if next_asset is None or next_asset.scenario_id != asset.scenario_id:
            config_rows = config_rows_by_scenario.get(asset.scenario_id)
            if config_rows:
                body_parts.append(_paragraph_xml("Параметры конфигурации", style="Heading2"))
                body_parts.append(_table_xml(config_rows))

    body_parts.append(
        """
<w:sectPr>
  <w:pgSz w:w="15840" w:h="12240" w:orient="landscape"/>
  <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/>
</w:sectPr>
""".strip()
    )
    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document
 xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas"
 xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"
 xmlns:o="urn:schemas-microsoft-com:office:office"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"
 xmlns:v="urn:schemas-microsoft-com:vml"
 xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing"
 xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
 xmlns:w10="urn:schemas-microsoft-com:office:word"
 xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
 xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"
 xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup"
 xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk"
 xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml"
 xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape"
 mc:Ignorable="w14 wp14">
  <w:body>
    {"".join(body_parts)}
  </w:body>
</w:document>
"""
    return document_xml, media_entries


def _document_relationships_xml(media_entries: list[tuple[str, str, bytes]]) -> str:
    image_rels = "".join(
        f'<Relationship Id="{rel_id}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{media_name}"/>'
        for rel_id, media_name, _ in media_entries
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  {image_rels}
</Relationships>
"""


def _styles_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:qFormat/>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Title">
    <w:name w:val="Title"/>
    <w:basedOn w:val="Normal"/>
    <w:qFormat/>
    <w:rPr><w:b/><w:sz w:val="32"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/>
    <w:basedOn w:val="Normal"/>
    <w:qFormat/>
    <w:rPr><w:b/><w:sz w:val="28"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="heading 2"/>
    <w:basedOn w:val="Normal"/>
    <w:qFormat/>
    <w:rPr><w:b/><w:sz w:val="24"/></w:rPr>
  </w:style>
</w:styles>
"""


def _content_types_xml(media_entries: list[tuple[str, str, bytes]]) -> str:
    has_jpeg = any(media_name.endswith((".jpg", ".jpeg")) for _, media_name, _ in media_entries)
    jpeg_default = (
        '<Default Extension="jpg" ContentType="image/jpeg"/>'
        '<Default Extension="jpeg" ContentType="image/jpeg"/>'
        if has_jpeg
        else ""
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="png" ContentType="image/png"/>
  {jpeg_default}
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>
"""


def _root_relationships_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>
"""


def _core_properties_xml(title: str) -> str:
    safe_title = escape(title)
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
 xmlns:dc="http://purl.org/dc/elements/1.1/"
 xmlns:dcterms="http://purl.org/dc/terms/"
 xmlns:dcmitype="http://purl.org/dc/dcmitype/"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>{safe_title}</dc:title>
  <dc:creator>pkpd-model-xc7</dc:creator>
  <cp:lastModifiedBy>pkpd-model-xc7</cp:lastModifiedBy>
</cp:coreProperties>
"""


def _app_properties_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
 xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>pkpd-model-xc7</Application>
</Properties>
"""


def build_figures_docx(
    figures_dir: Path | str,
    output_path: Path | str,
    *,
    title: str = "PKPD Figures",
) -> Path:
    assets = collect_figure_assets(figures_dir)
    resolved_output = Path(output_path)
    resolved_output.parent.mkdir(parents=True, exist_ok=True)

    document_xml, media_entries = _document_xml(title, assets)
    fd, temp_path = tempfile.mkstemp(dir=resolved_output.parent, suffix=".docx")
    os.close(fd)
    temp_docx = Path(temp_path)

    try:
        with zipfile.ZipFile(temp_docx, "w") as zf:
            _stable_zip_write(zf, "[Content_Types].xml", _content_types_xml(media_entries).encode("utf-8"))
            _stable_zip_write(zf, "_rels/.rels", _root_relationships_xml().encode("utf-8"))
            _stable_zip_write(zf, "docProps/core.xml", _core_properties_xml(title).encode("utf-8"))
            _stable_zip_write(zf, "docProps/app.xml", _app_properties_xml().encode("utf-8"))
            _stable_zip_write(zf, "word/document.xml", document_xml.encode("utf-8"))
            _stable_zip_write(zf, "word/_rels/document.xml.rels", _document_relationships_xml(media_entries).encode("utf-8"))
            _stable_zip_write(zf, "word/styles.xml", _styles_xml().encode("utf-8"))
            for _, media_name, image_bytes in media_entries:
                _stable_zip_write(zf, f"word/media/{media_name}", image_bytes)
        os.replace(temp_docx, resolved_output)
    except Exception:
        if temp_docx.exists():
            temp_docx.unlink()
        raise

    return resolved_output


def main() -> int:
    parser = argparse.ArgumentParser(description="Bundle docs/figures PNG files into a single DOCX document.")
    parser.add_argument(
        "--figures-dir",
        type=Path,
        default=DEFAULT_FIGURES_DIR,
        help="Directory with PNG/JPEG figures to include.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Output DOCX path.",
    )
    parser.add_argument(
        "--title",
        default="PKPD Figures",
        help="Document title written into the DOCX.",
    )
    args = parser.parse_args()

    output = build_figures_docx(args.figures_dir, args.out, title=args.title)
    print(f"Saved DOCX report: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
