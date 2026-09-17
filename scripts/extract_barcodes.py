#!/usr/bin/env python3
"""Извлечение штрихкодов с первой страницы PDF-анкет в CSV.

Использование:
    python3 scripts/extract_barcodes.py <input_dir_or_file> -o barcodes.csv

Для каждого PDF-файла рендерится указанная страница (по умолчанию первая),
на ней ищутся все штрихкоды (pyzbar), и результат построчно пишется в CSV:
    file, page, barcode_index, symbology, data
"""

from __future__ import annotations

import argparse
import csv
import logging
import sys
from pathlib import Path

import pymupdf
from PIL import Image
from pyzbar.pyzbar import decode as decode_barcodes

logger = logging.getLogger("extract_barcodes")

CSV_FIELDS = ["file", "page", "barcode_index", "symbology", "data"]


def find_pdf_files(input_path: Path) -> list[Path]:
    if input_path.is_file():
        if input_path.suffix.lower() != ".pdf":
            raise ValueError(f"Не PDF-файл: {input_path}")
        return [input_path]
    if input_path.is_dir():
        files = sorted(p for p in input_path.rglob("*.pdf"))
        return files
    raise FileNotFoundError(f"Путь не найден: {input_path}")


def render_page_to_image(doc: pymupdf.Document, page_number: int, dpi: int) -> Image.Image:
    if page_number < 1 or page_number > doc.page_count:
        raise IndexError(
            f"В файле {doc.name} нет страницы {page_number} (всего страниц: {doc.page_count})"
        )
    page = doc.load_page(page_number - 1)
    zoom = dpi / 72
    matrix = pymupdf.Matrix(zoom, zoom)
    pixmap = page.get_pixmap(matrix=matrix)
    mode = "RGB" if pixmap.n < 4 else "RGBA"
    image = Image.frombytes(mode, (pixmap.width, pixmap.height), pixmap.samples)
    if mode == "RGBA":
        image = image.convert("RGB")
    return image


def extract_from_pdf(pdf_path: Path, page_number: int, dpi: int) -> list[dict]:
    rows: list[dict] = []
    try:
        doc = pymupdf.open(pdf_path)
    except Exception as exc:
        logger.error("Не удалось открыть %s: %s", pdf_path, exc)
        return rows

    try:
        image = render_page_to_image(doc, page_number, dpi)
    except Exception as exc:
        logger.error("Не удалось отрендерить страницу %s из %s: %s", page_number, pdf_path, exc)
        return rows
    finally:
        doc.close()

    barcodes = decode_barcodes(image)
    if not barcodes:
        logger.warning("Штрихкоды не найдены: %s (страница %s)", pdf_path.name, page_number)
        return rows

    for idx, barcode in enumerate(barcodes, start=1):
        rows.append(
            {
                "file": pdf_path.name,
                "page": page_number,
                "barcode_index": idx,
                "symbology": barcode.type,
                "data": barcode.data.decode("utf-8", errors="replace"),
            }
        )
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input",
        type=Path,
        help="PDF-файл или папка с PDF-файлами анкет",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("barcodes.csv"),
        help="Путь к выходному CSV-файлу (по умолчанию: barcodes.csv)",
    )
    parser.add_argument(
        "-p",
        "--page",
        type=int,
        default=1,
        help="Номер страницы для поиска штрихкодов, начиная с 1 (по умолчанию: 1)",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Разрешение рендеринга страницы в точках на дюйм (по умолчанию: 300)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Подробный вывод (уровень логирования DEBUG)",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    try:
        pdf_files = find_pdf_files(args.input)
    except (FileNotFoundError, ValueError) as exc:
        logger.error(str(exc))
        return 1

    if not pdf_files:
        logger.error("PDF-файлы не найдены в %s", args.input)
        return 1

    logger.info("Найдено PDF-файлов: %d", len(pdf_files))

    all_rows: list[dict] = []
    files_without_barcodes: list[str] = []
    for pdf_path in pdf_files:
        rows = extract_from_pdf(pdf_path, args.page, args.dpi)
        if rows:
            all_rows.extend(rows)
        else:
            files_without_barcodes.append(pdf_path.name)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(all_rows)

    logger.info("Записано штрихкодов: %d -> %s", len(all_rows), args.output)
    if files_without_barcodes:
        logger.warning(
            "Файлы без распознанных штрихкодов (%d): %s",
            len(files_without_barcodes),
            ", ".join(files_without_barcodes),
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
