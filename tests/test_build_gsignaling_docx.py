from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from zipfile import ZipFile


def _load_module():
    path = Path(__file__).resolve().parents[1] / "docs" / "build_gsignaling_docx.py"
    spec = importlib.util.spec_from_file_location("build_gsignaling_docx", path)
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


def test_collect_gsignaling_assets_filters_and_sorts(tmp_path: Path) -> None:
    module = _load_module()
    figures_dir = tmp_path / "figures"
    figures_dir.mkdir()
    _write_tiny_png(figures_dir / "fig3_3_capsaicin_dose_180mgkg_gsignaling.png")
    _write_tiny_png(figures_dir / "fig3_3_capsaicin_dose_0mgkg_gsignaling.png")
    _write_tiny_png(figures_dir / "fig3_3_capsaicin_dose_18mgkg_gsignaling.png")
    _write_tiny_png(figures_dir / "fig3_3_capsaicin_gsignaling.png")
    _write_tiny_png(figures_dir / "fig1_3_formalin_dose_18mgkg_gsignaling.png")
    _write_tiny_png(figures_dir / "fig1_3_formalin_dose_0mgkg_gsignaling.png")
    _write_tiny_png(figures_dir / "fig8_3_intact_dose_0mgkg_gsignaling.png")

    assets = module.collect_gsignaling_assets(figures_dir)

    assert [asset.relative_path.name for asset in assets] == [
        "fig1_3_formalin_dose_0mgkg_gsignaling.png",
        "fig1_3_formalin_dose_18mgkg_gsignaling.png",
        "fig3_3_capsaicin_dose_0mgkg_gsignaling.png",
        "fig3_3_capsaicin_dose_18mgkg_gsignaling.png",
        "fig3_3_capsaicin_dose_180mgkg_gsignaling.png",
    ]
    assert all(asset.scenario_id != "intact" for asset in assets)
    assert all("_dose_" in asset.relative_path.name for asset in assets)


def test_build_gsignaling_docx_writes_grouped_sections_and_baseline_tables(tmp_path: Path) -> None:
    module = _load_module()
    figures_dir = tmp_path / "figures"
    figures_dir.mkdir()
    _write_tiny_png(figures_dir / "fig1_3_formalin_dose_0mgkg_gsignaling.png")
    _write_tiny_png(figures_dir / "fig1_3_formalin_dose_18mgkg_gsignaling.png")
    _write_tiny_png(figures_dir / "fig3_3_capsaicin_dose_0mgkg_gsignaling.png")
    _write_tiny_png(figures_dir / "fig3_3_capsaicin_dose_180mgkg_gsignaling.png")
    _write_tiny_png(figures_dir / "fig3_3_capsaicin_gsignaling.png")
    _write_tiny_png(figures_dir / "fig8_3_intact_dose_0mgkg_gsignaling.png")

    out_path = tmp_path / "gsignaling.docx"
    result = module.build_gsignaling_docx(figures_dir, out_path, title="Dose-specific G-signaling")

    assert result == out_path
    assert out_path.exists()

    with ZipFile(out_path) as zf:
        names = set(zf.namelist())
        assert "word/document.xml" in names
        assert "word/media/image1.png" in names
        assert "word/media/image2.png" in names
        assert "word/media/image3.png" in names
        assert "word/media/image4.png" in names

        document_xml = zf.read("word/document.xml").decode("utf-8")
        assert "Dose-specific G-signaling" in document_xml
        assert "Модель болевого синдрома, индуцированная введением формалина." in document_xml
        assert "Модель болевого синдрома, индуцированная введением капсаицина." in document_xml
        assert (
            "Рисунок 1.1 Модель болевого синдрома, индуцированная введением формалина. "
            "Уровень функциональной активности H3 рецепторов после индукции патологии. "
            "A - контроль патологии, B - XC7DCH в дозе 18 мг/кг."
        ) in document_xml
        assert (
            "Рисунок 3.1 Модель болевого синдрома, индуцированная введением капсаицина. "
            "Уровень функциональной активности H3 рецепторов после индукции патологии. "
            "A - контроль патологии, B - XC7DCH в дозе 180 мг/кг."
        ) in document_xml
        assert document_xml.count("Параметры конфигурации") == 2
        assert "fig3_3_capsaicin_gsignaling.png" not in document_xml
        assert "intact" not in document_xml
        assert "driver.scenario_id" in document_xml
        assert ">formalin<" in document_xml
        assert ">capsaicin<" in document_xml
        assert '<w:br w:type="page"/>' in document_xml
