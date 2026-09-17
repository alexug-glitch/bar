import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.extract_barcodes import main
from tests.generate_fixture import FIXTURE_CODES, build_fixture


def test_extract_barcodes_from_fixture(tmp_path):
    pdf_path = tmp_path / "sample_anketa.pdf"
    build_fixture(pdf_path)

    output_csv = tmp_path / "barcodes.csv"
    exit_code = main([str(pdf_path), "-o", str(output_csv)])
    assert exit_code == 0
    assert output_csv.exists()

    with output_csv.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == len(FIXTURE_CODES)
    found_values = {row["data"] for row in rows}
    expected_values = {value for _, value in FIXTURE_CODES}
    assert found_values == expected_values
    assert all(row["file"] == "sample_anketa.pdf" for row in rows)
    assert all(row["page"] == "1" for row in rows)


def test_extract_barcodes_directory_with_multiple_files(tmp_path):
    pdf1 = tmp_path / "a.pdf"
    pdf2 = tmp_path / "b.pdf"
    build_fixture(pdf1)
    build_fixture(pdf2)

    output_csv = tmp_path / "out.csv"
    exit_code = main([str(tmp_path), "-o", str(output_csv)])
    assert exit_code == 0

    with output_csv.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == len(FIXTURE_CODES) * 2
    assert {row["file"] for row in rows} == {"a.pdf", "b.pdf"}
