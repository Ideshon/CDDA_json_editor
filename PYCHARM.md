# PyCharm

Используй `tasks.cmd` как единый Windows entry point для действий разработки.

Корень проекта:

`E:\python\cdda_mod_editor`

Команды:

```powershell
.\tasks.cmd install
.\tasks.cmd run
.\tasks.cmd test
.\tasks.cmd build
.\tasks.cmd check
```

Рекомендуемая настройка PyCharm:

1. Создай Run/Debug configuration, которая запускает `tasks.cmd` из корня проекта.
2. Передай первым аргументом `run`, `test`, `build` или `check`.
3. Используй `run` для GUI, `test` для `unittest`, `build` для PyInstaller, `check` для `poetry check`.

Если нужен прямой запуск через PowerShell, используй `tasks.ps1` с теми же именами задач и `-ExecutionPolicy Bypass`.
