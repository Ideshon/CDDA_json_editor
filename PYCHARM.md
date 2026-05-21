# PyCharm

Use `tasks.cmd` as the single Windows entry point for development actions.

Project root:

`D:\Python\CDDA_Mod_Editor`

Commands:

```powershell
.\tasks.cmd install
.\tasks.cmd run
.\tasks.cmd test
.\tasks.cmd build
.\tasks.cmd check
```

Recommended PyCharm setup:

1. Create a Run/Debug configuration that runs `tasks.cmd` from the project root.
2. Pass one of `run`, `test`, `build`, or `check` as the first argument.
3. Use `run` for the GUI, `test` for `unittest`, and `build` for PyInstaller.

If you prefer direct PowerShell execution, use `tasks.ps1` with the same task names.
