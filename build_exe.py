#!/usr/bin/env python3
"""Сборка ExtractBarcodes.exe (Windows) через PyInstaller.

Запускать на Windows из корня проекта:
    python build_exe.py

pyzbar на Windows явно грузит рядом со своим модулем DLL-файлы
(libzbar-64.dll, libiconv.dll и т.п.) по полному пути. PyInstaller в
режиме --onefile не всегда кладёт эти DLL в ту же подпапку внутри
собранного архива, из-за чего при запуске .exe падает с ошибкой вида
"Could not find module 'libiconv.dll'". Чтобы это исправить, скрипт
находит все .dll в папке пакета pyzbar и подключает их через
--add-binary в подпапку "pyzbar" сборки - именно там их ищет pyzbar
во время выполнения.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def find_pyzbar_dlls() -> list[Path]:
    try:
        import pyzbar
    except ImportError:
        print(
            "pyzbar не установлен. Сначала выполните: pip install -r requirements.txt",
            file=sys.stderr,
        )
        sys.exit(1)

    pyzbar_dir = Path(pyzbar.__file__).resolve().parent
    return sorted(pyzbar_dir.glob("*.dll"))


def main() -> None:
    if not sys.platform.startswith("win"):
        print("Сборка .exe поддерживается только на Windows.", file=sys.stderr)
        sys.exit(1)

    import PyInstaller.__main__

    dlls = find_pyzbar_dlls()
    if not dlls:
        print(
            "ВНИМАНИЕ: в папке pyzbar не найдено .dll файлов.\n"
            "Убедитесь, что pyzbar установлен из Windows-колеса "
            "(pip install pyzbar на Windows ставит нужные DLL автоматически).",
            file=sys.stderr,
        )

    args = [
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", "ExtractBarcodes",
    ]
    for dll in dlls:
        args += ["--add-binary", f"{dll}{os.pathsep}pyzbar"]
    args.append(str(Path("scripts") / "gui_extract_barcodes.py"))

    print("Найденные DLL pyzbar, которые будут добавлены в сборку:")
    for dll in dlls:
        print(f"  - {dll.name}")
    print()

    PyInstaller.__main__.run(args)

    print()
    print("Готово! Файл ExtractBarcodes.exe находится в папке dist\\")


if __name__ == "__main__":
    main()
