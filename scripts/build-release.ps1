[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$builder = Join-Path $PSScriptRoot 'build_release.py'

python $builder
if ($LASTEXITCODE -ne 0) {
    throw "FileModifiedTime release build failed with exit code $LASTEXITCODE."
}
