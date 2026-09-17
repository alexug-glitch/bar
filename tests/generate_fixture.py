#!/usr/bin/env python3
"""Генерация тестового PDF с несколькими штрихкодами на первой странице.

Используется только для тестирования scripts/extract_barcodes.py.
Требует дополнительную зависимость python-barcode (см. requirements-dev.txt).
"""

from __future__ import annotations

import io
from pathlib import Path

import barcode
import pymupdf
from barcode.writer import ImageWriter
from PIL import Image

FIXTURE_CODES = [
    ("code128", "ANKETA-0001"),
    ("code128", "PATIENT-42"),
    ("ean13", "5901234123457"),
]


def make_barcode_png(symbology: str, value: str) -> bytes:
    writer_class = barcode.get_barcode_class(symbology)
    instance = writer_class(value, writer=ImageWriter())
    buf = io.BytesIO()
    instance.write(buf, options={"write_text": False, "module_height": 12})
    return buf.getvalue()


def build_fixture(output_path: Path, codes: list[tuple[str, str]] = FIXTURE_CODES) -> None:
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)  # A4

    page.insert_text((50, 60), "Анкета участника", fontsize=18)
    page.insert_text((50, 90), "Тестовая форма для проверки распознавания штрихкодов", fontsize=10)

    y = 130
    target_width = 260
    for symbology, value in codes:
        png_bytes = make_barcode_png(symbology, value)
        img_w, img_h = Image.open(io.BytesIO(png_bytes)).size
        height = target_width * img_h / img_w
        rect = pymupdf.Rect(50, y, 50 + target_width, y + height)
        page.insert_image(rect, stream=png_bytes)
        y += height + 20

    # Вторая страница без штрихкодов - убедиться, что скрипт смотрит только на нужную.
    doc.new_page(width=595, height=842)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)
    doc.close()


if __name__ == "__main__":
    target = Path(__file__).parent / "fixtures" / "sample_anketa.pdf"
    build_fixture(target)
    print(f"Fixture written to {target}")
