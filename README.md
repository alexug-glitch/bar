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
