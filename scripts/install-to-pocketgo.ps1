[CmdletBinding()]
param(
    # The SD card root, e.g. E:\
    [Parameter(Mandatory = $true)]
    [string]$SdRoot,

    [string]$Source = (Join-Path $PSScriptRoot "..\dist\holua"),

    # Without -Install the card is only checked; nothing is changed.
    [switch]$Install
)

$ErrorActionPreference = 'Stop'
$utf8 = New-Object System.Text.UTF8Encoding($false)
$sd = [IO.Path]::GetFullPath($SdRoot)
$sourcePath = [IO.Path]::GetFullPath($Source)
$apps = Join-Path $sd 'apps'
$sections = Join-Path $sd 'gmenu2x\sections\applications'
$target = Join-Path $apps 'holua'
$shortcut = Join-Path $sections 'holua'

if (-not (Test-Path -LiteralPath $apps -PathType Container) -or
    -not (Test-Path -LiteralPath (Join-Path $sd 'gmenu2x\sections') -PathType Container)) {
    throw "'$sd' is not a PocketGo SD-card root (apps/ or gmenu2x/sections is missing)."
}
if (-not (Test-Path -LiteralPath (Join-Path $sourcePath 'holua') -PathType Leaf)) {
    throw "Binary not found: $(Join-Path $sourcePath 'holua'). Run 'make package' in WSL first."
}
if (-not $Install) {
    Write-Host 'Validation passed. No files were changed. Re-run with -Install to copy Ho Lua.'
    exit 0
}

if (Test-Path -LiteralPath $target) {
    $backup = Join-Path $sd ("holua-backup-" + (Get-Date -Format 'yyyyMMdd-HHmmss'))
    Copy-Item -LiteralPath $target -Destination $backup -Recurse
    Write-Host "Previous copy backed up to $backup"
}
New-Item -ItemType Directory -Force -Path $target, (Join-Path $target 'saves'), $sections | Out-Null
# saves/ on the card is kept; only the program and pictures are replaced
Copy-Item -LiteralPath (Join-Path $sourcePath 'holua') -Destination (Join-Path $target 'holua') -Force
Copy-Item -Path (Join-Path $sourcePath 'assets') -Destination $target -Recurse -Force
[IO.File]::WriteAllText($shortcut, "title=Ho Lua`ndescription=Nuoi ho lua`nexec=/mnt/apps/holua/holua`nclock=702`n", $utf8)
Write-Host "Installed to $target with the menu entry $shortcut"
