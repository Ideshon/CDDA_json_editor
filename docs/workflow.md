# Workflow

Основная точка входа для Windows - `tasks.cmd`.

```powershell
.\tasks.cmd check
.\tasks.cmd test
.\tasks.cmd build
.\tasks.cmd run
```

`tasks.ps1` использует локальный `.venv\Scripts\python.exe`, если он существует. Это обходит нестабильные Windows console-script shims вроде `.venv\Scripts\poetry.exe` и `.venv\Scripts\pyinstaller.exe`.

## Проверки

- `.\tasks.cmd check` - `poetry check`.
- `.\tasks.cmd test` - полный `unittest discover`.
- `.\tasks.cmd build` - PyInstaller-сборка.
- `python -m json.tool status_worker.json` - проверка статуса.

## Быстрые Smoke-Overrides

Для тестов helper-команд используются переменные окружения:

```powershell
$env:CDDA_TASKS_TEST_ARGS = "tests.test_package_entrypoint -v"
$env:CDDA_TASKS_BUILD_ARGS = "--version"
```

Обычные пользовательские команды без этих переменных выполняют полный test/build.
