from pathlib import Path

from src.validation.reference_loader import find_reference_csv, load_reference_marker_table


def test_find_and_load_reference_csv_from_report_folder(tmp_path: Path) -> None:
    report_dir = tmp_path / "report_v12_extracted"
    report_dir.mkdir()
    csv_path = report_dir / "formalin_marker_points.csv"
    csv_path.write_text("time_h,H\n0.0,1.0\n", encoding="utf-8")

    found = find_reference_csv("formalin", base_dir=report_dir)
    assert found == csv_path

    df = load_reference_marker_table("formalin", base_dir=report_dir)
    assert list(df.columns) == ["time_h", "H"]
    assert df.iloc[0].to_dict() == {"time_h": 0.0, "H": 1.0}
