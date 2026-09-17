#!/usr/bin/env python3
"""Графическое приложение: выбрать папку с PDF-анкетами и извлечь штрихкоды.

Результат (barcodes.csv) сохраняется в ту же папку, которую выбрал
пользователь. Логика распознавания — та же, что в scripts/extract_barcodes.py.

Запуск как обычного скрипта:
    python3 scripts/gui_extract_barcodes.py

Сборка в .exe (на Windows):
    build_exe.bat
"""

from __future__ import annotations

import os
import queue
import sys
import threading
import traceback
from pathlib import Path

# PyInstaller в режиме --windowed на Windows отдаёт sys.stdout/stderr = None,
# на что падает любой print()/логирование по умолчанию.
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

sys.path.insert(0, str(Path(__file__).resolve().parent))

import csv
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

from extract_barcodes import CSV_FIELDS, extract_from_pdf, find_pdf_files

OUTPUT_FILENAME = "barcodes.csv"
DEFAULT_DPI = 300
DEFAULT_PAGE = 1


class BarcodeExtractorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Извлечение штрихкодов из PDF-анкет")
        self.root.geometry("640x420")
        self.root.minsize(520, 360)

        self.selected_folder: Path | None = None
        self.log_queue: queue.Queue[str] = queue.Queue()
        self.worker_thread: threading.Thread | None = None

        self._build_widgets()
        self.root.after(100, self._poll_log_queue)

    def _build_widgets(self) -> None:
        top = tk.Frame(self.root, padx=12, pady=12)
        top.pack(fill=tk.X)

        self.folder_var = tk.StringVar(value="Папка не выбрана")
        tk.Label(top, textvariable=self.folder_var, anchor="w", fg="#333").pack(
            fill=tk.X, pady=(0, 8)
        )

        buttons = tk.Frame(top)
        buttons.pack(fill=tk.X)

        self.choose_btn = tk.Button(
            buttons, text="Выбрать папку и начать", command=self._on_choose_folder
        )
        self.choose_btn.pack(side=tk.LEFT)

        self.open_result_btn = tk.Button(
            buttons, text="Открыть папку с результатом", command=self._open_result_folder,
            state=tk.DISABLED,
        )
        self.open_result_btn.pack(side=tk.LEFT, padx=(8, 0))

        self.log_widget = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, state=tk.DISABLED, height=18
        )
        self.log_widget.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

        self.status_var = tk.StringVar(value="Готов к работе.")
        tk.Label(self.root, textvariable=self.status_var, anchor="w", bd=1, relief=tk.SUNKEN).pack(
            fill=tk.X
        )

    def _log(self, message: str) -> None:
        self.log_queue.put(message)

    def _poll_log_queue(self) -> None:
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_widget.configure(state=tk.NORMAL)
                self.log_widget.insert(tk.END, message + "\n")
                self.log_widget.see(tk.END)
                self.log_widget.configure(state=tk.DISABLED)
        except queue.Empty:
            pass
        self.root.after(100, self._poll_log_queue)

    def _on_choose_folder(self) -> None:
        folder = filedialog.askdirectory(title="Выберите папку с PDF-анкетами")
        if not folder:
            return
        self.selected_folder = Path(folder)
        self.folder_var.set(f"Папка: {self.selected_folder}")
        self.open_result_btn.configure(state=tk.DISABLED)
        self._start_processing(self.selected_folder)

    def _start_processing(self, folder: Path) -> None:
        self.choose_btn.configure(state=tk.DISABLED)
        self.status_var.set("Обработка...")
        self.log_widget.configure(state=tk.NORMAL)
        self.log_widget.delete("1.0", tk.END)
        self.log_widget.configure(state=tk.DISABLED)

        self.worker_thread = threading.Thread(
            target=self._process_folder, args=(folder,), daemon=True
        )
        self.worker_thread.start()

    def _process_folder(self, folder: Path) -> None:
        try:
            pdf_files = find_pdf_files(folder)
        except (FileNotFoundError, ValueError) as exc:
            self._log(f"ОШИБКА: {exc}")
            self._finish(success=False)
            return

        if not pdf_files:
            self._log(f"PDF-файлы не найдены в папке: {folder}")
            self._finish(success=False)
            return

        self._log(f"Найдено PDF-файлов: {len(pdf_files)}")

        all_rows: list[dict] = []
        files_without_barcodes: list[str] = []
        for pdf_path in pdf_files:
            self._log(f"Обработка: {pdf_path.name}")
            try:
                rows = extract_from_pdf(pdf_path, DEFAULT_PAGE, DEFAULT_DPI)
            except Exception:
                self._log(f"  ОШИБКА при обработке {pdf_path.name}:\n{traceback.format_exc()}")
                files_without_barcodes.append(pdf_path.name)
                continue

            if rows:
                self._log(f"  Найдено штрихкодов: {len(rows)}")
                all_rows.extend(rows)
            else:
                self._log("  Штрихкоды не найдены")
                files_without_barcodes.append(pdf_path.name)

        output_path = folder / OUTPUT_FILENAME
        with output_path.open("w", newline="", encoding="utf-8-sig") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(all_rows)

        self._log("")
        self._log(f"Готово. Штрихкодов записано: {len(all_rows)}")
        self._log(f"Результат сохранён в: {output_path}")
        if files_without_barcodes:
            self._log(
                f"Файлы без распознанных штрихкодов ({len(files_without_barcodes)}): "
                + ", ".join(files_without_barcodes)
            )

        self.result_path = output_path
        self._finish(success=True, rows_count=len(all_rows), output_path=output_path)

    def _finish(self, success: bool, rows_count: int = 0, output_path: Path | None = None) -> None:
        def update_ui() -> None:
            self.choose_btn.configure(state=tk.NORMAL)
            if success:
                self.status_var.set(f"Готово. Штрихкодов найдено: {rows_count}.")
                self.open_result_btn.configure(state=tk.NORMAL)
                messagebox.showinfo(
                    "Готово",
                    f"Обработка завершена.\n\n"
                    f"Найдено штрихкодов: {rows_count}\n"
                    f"Результат сохранён в:\n{output_path}",
                )
            else:
                self.status_var.set("Завершено с ошибкой. Смотрите журнал выше.")
                messagebox.showwarning(
                    "Обработка завершена",
                    "Не удалось извлечь штрихкоды. Подробности - в журнале в окне приложения.",
                )

        self.root.after(0, update_ui)

    def _open_result_folder(self) -> None:
        if self.selected_folder is None:
            return
        folder = str(self.selected_folder)
        try:
            if sys.platform.startswith("win"):
                os.startfile(folder)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                os.system(f'open "{folder}"')
            else:
                os.system(f'xdg-open "{folder}"')
        except Exception as exc:
            messagebox.showerror("Ошибка", f"Не удалось открыть папку: {exc}")


def main() -> int:
    root = tk.Tk()
    BarcodeExtractorApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
