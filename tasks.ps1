param(
    [Parameter(Position = 0)]
    [ValidateSet('install', 'run', 'test', 'build', 'check')]
    [string]$Task = 'run'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$LocalPython = Join-Path $Root '.venv\Scripts\python.exe'
if (Test-Path $LocalPython) {
    $PythonExecutable = $LocalPython
    $PoetryExecutable = $LocalPython
    $PoetryBaseArguments = @('-m', 'poetry')
}
else {
    $PythonExecutable = $null
    $PoetryExecutable = 'poetry'
    $PoetryBaseArguments = @()
}

function Invoke-Poetry {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    $CommandArguments = @()
    $CommandArguments += $PoetryBaseArguments
    $CommandArguments += $Arguments

    & $PoetryExecutable @CommandArguments
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

function Invoke-ProjectPython {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    if ($null -ne $PythonExecutable) {
        & $PythonExecutable @Arguments
    }
    else {
        Invoke-Poetry -Arguments (@('run', 'python') + $Arguments)
        return
    }

    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

function Get-TaskArgumentOverride {
    param(
        [Parameter(Mandatory = $true)]
        [string]$EnvironmentVariableName,

        [Parameter(Mandatory = $true)]
        [string[]]$DefaultArguments
    )

    $Override = [Environment]::GetEnvironmentVariable($EnvironmentVariableName)
    if ([string]::IsNullOrWhiteSpace($Override)) {
        return $DefaultArguments
    }

    return @($Override -split '\s+' | Where-Object { $_ })
}

switch ($Task) {
    'install' {
        Invoke-Poetry -Arguments @('install')
    }
    'run' {
        Invoke-ProjectPython -Arguments @('-m', 'CDDA_editor.main')
    }
    'test' {
        $TestArguments = Get-TaskArgumentOverride `
            -EnvironmentVariableName 'CDDA_TASKS_TEST_ARGS' `
            -DefaultArguments @('discover', '-s', 'tests', '-v')
        Invoke-ProjectPython -Arguments (@('-m', 'unittest') + $TestArguments)
    }
    'build' {
        $BuildArguments = Get-TaskArgumentOverride `
            -EnvironmentVariableName 'CDDA_TASKS_BUILD_ARGS' `
            -DefaultArguments @('.\CDDA-0G_json_editor.spec')
        Invoke-ProjectPython -Arguments (@('-m', 'PyInstaller') + $BuildArguments)
    }
    'check' {
        Invoke-Poetry -Arguments @('check')
    }
}
