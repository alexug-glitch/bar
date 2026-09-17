# Извлечение штрихкодов из PDF-анкет

Скрипт читает PDF-файлы анкет, рендерит первую страницу каждого файла,
распознаёт все штрихкоды на ней и сохраняет результат в один CSV-файл.

## Установка

```bash
sudo apt-get install -y libzbar0   # системная библиотека для pyzbar
pip install -r requirements.txt
```

## Использование

```bash
# Обработать все PDF в папке input/ и сохранить результат в barcodes.csv
python3 scripts/extract_barcodes.py input/ -o output/barcodes.csv

# Обработать один файл
python3 scripts/extract_barcodes.py anketa.pdf -o barcodes.csv

# Если штрихкоды не на первой, а, например, на второй странице
python3 scripts/extract_barcodes.py input/ -o output/barcodes.csv --page 2

# Увеличить разрешение рендеринга (полезно для мелких/плотных штрихкодов)
python3 scripts/extract_barcodes.py input/ -o output/barcodes.csv --dpi 400
```

Скрипт рекурсивно находит все `*.pdf` в указанной папке. Для файлов, где
не удалось найти ни одного штрихкода, в лог выводится предупреждение, но
обработка остальных файлов продолжается.

## Графическое приложение (Windows .exe)

Для тех, кто не хочет работать через командную строку, есть простое
GUI-приложение: кнопка "Выбрать папку" → выбираете папку с PDF-анкетами →
приложение само находит в ней все PDF, распознаёт штрихкоды и сохраняет
`barcodes.csv` **в ту же папку**.

### Собрать .exe самому (один раз, на Windows)

1. Установите Python с [python.org](https://www.python.org/downloads/)
   (галочка "Add Python to PATH" при установке).
2. Скачайте/склонируйте этот проект и откройте в нём терминал.
3. Запустите (двойным щелчком или из терминала):
   ```
   build_exe.bat
   ```
4. Готовый файл появится в `dist\ExtractBarcodes.exe`. Его можно скопировать
   на рабочий стол и запускать двойным кликом — Python на целевом компьютере
   для этого уже не нужен.

### Запуск без сборки .exe (Windows/macOS/Linux)

```bash
pip install -r requirements.txt
python3 scripts/gui_extract_barcodes.py
```

### Если .exe при запуске пишет ошибку про libiconv.dll / libzbar

Значит вы собирали через старую команду напрямую через `pyinstaller`, а не
через `build_exe.bat` / `build_exe.py`. `pyzbar` на Windows зависит от DLL
(`libzbar-64.dll`, `libiconv.dll`), которые PyInstaller в режиме `--onefile`
не всегда кладёт туда, где их ищет pyzbar. `build_exe.py` находит эти DLL
в установленном пакете `pyzbar` и подключает их вручную в нужное место —
пересоберите .exe через `build_exe.bat`, и ошибка уйдёт.

## Формат CSV

| Колонка        | Описание                                             |
|----------------|-------------------------------------------------------|
| file           | Имя PDF-файла                                          |
| page           | Номер обработанной страницы                            |
| barcode_index  | Порядковый номер штрихкода на странице                 |
| symbology      | Тип штрихкода (CODE128, EAN13, QRCODE и т.д.)           |
| data           | Распознанное содержимое штрихкода                       |

## Тесты

```bash
pip install -r requirements-dev.txt
python3 -m pytest tests/
```

Тесты генерируют тестовый PDF с несколькими штрихкодами
(`tests/generate_fixture.py`) и проверяют, что скрипт извлекает из него
верные данные.
