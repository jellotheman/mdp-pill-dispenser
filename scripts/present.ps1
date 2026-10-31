param([Parameter(ValueFromRemainingArguments = $true)][string[]]$PresentationArgs)
$ErrorActionPreference = 'Stop'
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    & python (Join-Path $PSScriptRoot 'present.py') @PresentationArgs
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
