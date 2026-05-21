param(
    [Parameter(Position = 0)]
    [ValidateSet('install', 'run', 'test', 'build', 'check')]
    [string]$Task = 'run'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$LocalPoetry = Join-Path $Root '.venv\Scripts\poetry.exe'
if (Test-Path $LocalPoetry) {
    $Poetry = $LocalPoetry
}
else {
    $Poetry = 'poetry'
}

function Invoke-Poetry {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    & $Poetry @Arguments
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

switch ($Task) {
    'install' {
        Invoke-Poetry -Arguments @('install')
    }
    'run' {
        Invoke-Poetry -Arguments @('run', 'cdda-mod-editor')
    }
    'test' {
        Invoke-Poetry -Arguments @('run', 'python', '-m', 'unittest', 'discover', '-s', 'tests', '-v')
    }
    'build' {
        Invoke-Poetry -Arguments @('run', 'pyinstaller', '.\CDDA-0G_json_editor.spec')
    }
    'check' {
        Invoke-Poetry -Arguments @('check')
    }
}
