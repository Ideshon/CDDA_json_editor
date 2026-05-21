# CDDA JSON Mod Editor

Графический редактор модов для Cataclysm: Dark Days Ahead (0.G+).

- Редактирование объектов по схемам: mutations, items, monsters и другие типы.
- Схемы можно менять в файлах `CDDA_editor/schemas/`.
- Поддержка вариантов, флагов и ссылок через `ref_list`.
- Удаление и добавление полей.
- Ручное редактирование сырых JSON-структур
- Поддержка открытия одной папки мода или отдельного JSON-файла.
- Темная тема

## Структура рабочей папки

- `CDDA_editor/` - исходный код программы.
- `CDDA_editor/schemas/` - описания поддерживаемых типов CDDA JSON.
- `CDDA_editor/ui_widgets.py` - малые переиспользуемые PyQt5-виджеты редактора.
- `Slaanesh/` - эталонный мод для проверки загрузки, редактирования и сравнения файлов после сохранения программой.
- `dist/` - готовая сборка приложения.
- `build/` - рабочие файлы PyInstaller.
- `CDDA-0G_json_editor.spec` - конфигурация сборки PyInstaller.
- `tests/` - автоматические проверки базовой логики.

`Slaanesh/`, `dist/` и `build/` могут лежать рядом с исходниками в этой рабочей папке. Они не являются мусором и не удаляются при реорганизации проекта.

## Сохранение и эталонный мод

Логика записи JSON-файлов находится в `ModProject`, а интерфейс только вызывает методы сохранения. Это позволяет проверять сохранение без запуска PyQt5.

Автоматические тесты не изменяют `Slaanesh/` напрямую. Для проверок создаётся временная копия эталонного мода, над ней выполняются создание, удаление и сохранение объектов, после чего неизменённые файлы сравниваются с исходным эталоном.

## Запуск из исходников

Основной способ для Windows 10 после установки Poetry:

```powershell
poetry install
poetry run cdda-mod-editor
```

Если Poetry установлен только в локальное окружение проекта:

```powershell
.\.venv\Scripts\poetry.exe install
.\.venv\Scripts\poetry.exe run cdda-mod-editor
```

Запуск через существующее виртуальное окружение без Poetry:

```powershell
.\.venv\Scripts\python.exe .\CDDA_editor\main.py
```

## Проверки

Тесты используют стандартный `unittest`, поэтому не требуют установки `pytest`.

Через Poetry:

```powershell
poetry run python -m unittest discover -s tests -v
```

Через локальный Poetry из `.venv`:

```powershell
.\.venv\Scripts\poetry.exe run python -m unittest discover -s tests -v
```

Через системный Python:

```powershell
python -m unittest discover -s tests -v
```

Через существующее виртуальное окружение:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Сборка exe

```powershell
poetry run pyinstaller .\CDDA-0G_json_editor.spec
```

Через локальный Poetry из `.venv`:

```powershell
.\.venv\Scripts\poetry.exe run pyinstaller .\CDDA-0G_json_editor.spec
```

`CDDA-0G_json_editor.spec` добавляет `CDDA_editor` в `pathex`, чтобы PyInstaller видел script-style fallback-импорты при сборке.

Если Poetry не установлен, текущую сборку можно запускать из `dist/`, а разработку продолжать через `.venv`.
