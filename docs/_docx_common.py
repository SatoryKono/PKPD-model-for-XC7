from __future__ import annotations

import os
import tempfile
import zipfile
from pathlib import Path
from typing import Sequence
from xml.sax.saxutils import escape

DOCX_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
EMU_PER_INCH = 914400
EMU_PER_PIXEL_AT_96_DPI = 9525
MAX_IMAGE_WIDTH_EMU_LANDSCAPE = int(9.0 * EMU_PER_INCH)
MAX_IMAGE_WIDTH_EMU_PORTRAIT = int(6.5 * EMU_PER_INCH)
TABLE_KEY_COLUMN_DXA = 4200
TABLE_VALUE_COLUMN_DXA = 9600


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


def _image_size_emu(path: Path, *, max_width_emu: int = MAX_IMAGE_WIDTH_EMU_LANDSCAPE) -> tuple[int, int]:
    width_px, height_px = _read_png_size(path)
    width_emu = width_px * EMU_PER_PIXEL_AT_96_DPI
    height_emu = height_px * EMU_PER_PIXEL_AT_96_DPI
    if width_emu > max_width_emu:
        scale = max_width_emu / float(width_emu)
        width_emu = max_width_emu
        height_emu = int(height_emu * scale)
    return width_emu, height_emu


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


def _document_relationships_xml(media_entries: Sequence[tuple[str, str, bytes]]) -> str:
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


def _content_types_xml(media_entries: Sequence[tuple[str, str, bytes]]) -> str:
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


def _landscape_section_xml() -> str:
    return """
<w:sectPr>
  <w:pgSz w:w="15840" w:h="12240" w:orient="landscape"/>
  <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/>
</w:sectPr>
""".strip()


def _portrait_a4_section_xml() -> str:
    return """
<w:sectPr>
  <w:pgSz w:w="11906" w:h="16838"/>
  <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/>
</w:sectPr>
""".strip()


def build_document_xml(body_parts: Sequence[str], *, section_xml: str | None = None) -> str:
    if section_xml is None:
        section_xml = _landscape_section_xml()
    joined_body = "".join([*body_parts, section_xml])
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
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
 xmlns:wne="http://schemas.openxmlformats.org/officeDocument/2006/wordml"
 xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape"
 mc:Ignorable="w14 wp14">
  <w:body>
    {joined_body}
  </w:body>
</w:document>
"""


def write_docx_package(
    output_path: Path | str,
    *,
    title: str,
    document_xml: str,
    media_entries: Sequence[tuple[str, str, bytes]],
) -> Path:
    resolved_output = Path(output_path)
    resolved_output.parent.mkdir(parents=True, exist_ok=True)
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
            _stable_zip_write(
                zf,
                "word/_rels/document.xml.rels",
                _document_relationships_xml(media_entries).encode("utf-8"),
            )
            _stable_zip_write(zf, "word/styles.xml", _styles_xml().encode("utf-8"))
            for _, media_name, image_bytes in media_entries:
                _stable_zip_write(zf, f"word/media/{media_name}", image_bytes)
        os.replace(temp_docx, resolved_output)
    except Exception:
        if temp_docx.exists():
            temp_docx.unlink()
        raise

    return resolved_output
