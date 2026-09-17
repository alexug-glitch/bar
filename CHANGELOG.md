# Журнал изменений

## v1.0-working — 2026-09-17 (подтверждено пользователем как рабочая версия)

Базовая рабочая версия. Дальнейшая разработка ведётся поверх неё.

Коммит: `a0d2717` — "Fix Windows .exe build: bundle pyzbar's DLL dependencies"

Состав:
- `scripts/extract_barcodes.py` — CLI: PDF-файл или папка с PDF → CSV со
  штрихкодами, найденными на первой странице каждого файла (`pymupdf` для
  рендеринга страницы + `pyzbar` для распознавания).
- `scripts/gui_extract_barcodes.py` — desktop-приложение (Tkinter): кнопка
  выбора папки, результат `barcodes.csv` сохраняется в ту же папку.
- `build_exe.py` / `build_exe.bat` — сборка `ExtractBarcodes.exe` под
  Windows через PyInstaller; вручную подключает DLL-зависимости `pyzbar`
  (`libzbar-64.dll`, `libiconv.dll`) в нужную подпапку сборки — без этого
  собранный .exe падал при запуске с ошибкой `Could not find module
  'libiconv.dll'`.
- `tests/` — фикстура с тестовым PDF (несколько штрихкодов, генерируется
  `tests/generate_fixture.py`) и pytest-тесты, проверяющие корректность
  извлечения.

Проверено пользователем: сборка `.exe` через `build_exe.bat` запускается
и корректно обрабатывает реальные PDF-анкеты.
