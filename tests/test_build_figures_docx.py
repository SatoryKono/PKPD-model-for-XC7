from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from zipfile import ZipFile


def _load_module():
    path = Path(__file__).resolve().parents[1] / "docs" / "build_figures_docx.py"
    spec = importlib.util.spec_from_file_location("build_figures_docx", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_tiny_png(path: Path) -> None:
    png_bytes = (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
        b"\x1f\x15\xc4\x89"
        b"\x00\x00\x00\x0cIDATx\x9cc```\xf8\x0f\x00\x01\x01\x01\x00"
        b"\x18\xdd\x8d\xb1"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    path.write_bytes(png_bytes)


def test_collect_figure_assets_is_sorted_and_grouped(tmp_path: Path) -> None:
    module = _load_module()
    figures_dir = tmp_path / "figures"
    figures_dir.mkdir()
    _write_tiny_png(figures_dir / "fig2_3_capsaicin_gsignaling.png")
    _write_tiny_png(figures_dir / "fig1_1_formalin_histamine.png")

    assets = module.collect_figure_assets(figures_dir)

    assert [asset.relative_path.name for asset in assets] == [
        "fig1_1_formalin_histamine.png",
        "fig2_3_capsaicin_gsignaling.png",
    ]
    assert assets[0].scenario_id == "formalin"
    assert assets[0].scenario_label == "Formalin"
    assert assets[0].section_title == "Модель болевого синдрома, индуцированная введением формалина."
    assert assets[0].figure_label == "Histamine"
    assert assets[0].caption.startswith("Рисунок 1.1 Модель болевого синдрома")
    assert assets[1].scenario_id == "capsaicin"
    assert assets[1].scenario_label == "Capsaicin"
    assert assets[1].section_title == "Модель болевого синдрома, индуцированная введением капсаицина."
    assert assets[1].figure_label == "G-signaling"


def test_collect_figure_assets_recognizes_xc7_concentration_suffix(tmp_path: Path) -> None:
    module = _load_module()
    figures_dir = tmp_path / "figures"
    figures_dir.mkdir()
    _write_tiny_png(figures_dir / "fig1_4_formalin_xc7_concentration.png")

    assets = module.collect_figure_assets(figures_dir)

    assert len(assets) == 1
    assert assets[0].scenario_id == "formalin"
    assert assets[0].scenario_label == "Formalin"
    assert assets[0].figure_label == "Концентрация XC7 в тканях"
    assert assets[0].caption == (
        "Рисунок 1.4 Модель болевого синдрома, индуцированная введением формалина. "
        "Концентрация XC7 в тканях после индукции патологии."
    )


def test_build_figures_docx_writes_media_and_document_xml(tmp_path: Path) -> None:
    module = _load_module()
    figures_dir = tmp_path / "figures"
    figures_dir.mkdir()
    _write_tiny_png(figures_dir / "fig1_1_formalin_histamine.png")
    _write_tiny_png(figures_dir / "fig1_2_formalin_internalization.png")
    _write_tiny_png(figures_dir / "fig1_4_formalin_xc7_concentration.png")
    _write_tiny_png(figures_dir / "fig2_1_capsaicin_histamine.png")

    out_path = tmp_path / "bundle.docx"
    result = module.build_figures_docx(figures_dir, out_path, title="PKPD Test Figures")

    assert result == out_path
    assert out_path.exists()

    with ZipFile(out_path) as zf:
        names = set(zf.namelist())
        assert "[Content_Types].xml" in names
        assert "word/document.xml" in names
        assert "word/_rels/document.xml.rels" in names
        assert "word/media/image1.png" in names
        assert "word/media/image2.png" in names
        assert "word/media/image3.png" in names
        assert "word/media/image4.png" in names

        document_xml = zf.read("word/document.xml").decode("utf-8")
        assert "PKPD Test Figures" in document_xml
        assert "Модель болевого синдрома, индуцированная введением формалина." in document_xml
        assert "Модель болевого синдрома, индуцированная введением капсаицина." in document_xml
        assert "Рисунок 1.1 Модель болевого синдрома, индуцированная введением формалина." in document_xml
        assert "Рисунок 1.4 Модель болевого синдрома, индуцированная введением формалина." in document_xml
        assert "Концентрация XC7 в тканях после индукции патологии." in document_xml
        assert "Рисунок 2.1 Модель болевого синдрома, индуцированная введением капсаицина." not in document_xml
        assert "Параметры конфигурации" in document_xml
        assert "driver.scenario_id" in document_xml
        assert ">formalin<" in document_xml
        assert ">capsaicin<" in document_xml
        assert "time_grid" in document_xml
        assert 'w:orient="landscape"' in document_xml
        assert '<w:br w:type="page"/>' in document_xml


def test_caption_overrides_cover_formalin_and_capsaicin() -> None:
    module = _load_module()
    assert module.FIGURE_CAPTION_OVERRIDES["fig1_3_formalin_gsignaling.png"].startswith("Рисунок 1.3")
    assert module.FIGURE_CAPTION_OVERRIDES["fig1_4_formalin_xc7_concentration.png"].startswith("Рисунок 1.4")
    assert (
        module.FIGURE_CAPTION_OVERRIDES["fig3_1_capsaicin_histamine.png"]
        == "Рисунок 3.1 Модель болевого синдрома, индуцированная введением капсаицина. "
        "Изменение концентрации гистамина после индукции паталогии."
    )
