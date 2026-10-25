# Copies the R36S builds to the ports folder of an R36S card (ArkOS / dArkOS: the EASYROMS partition) and gives
# each its entry and picture in the Ports list:
#   game    "Elemon"           dist\elemon      (scripts\r36s_game.py + build-r36s.ps1): the game
#   viewer  "HoLua (xem thử)"  dist\holua-r36s  (scripts\r36s_app.py + build-r36s.ps1): every room and pet, to look at
#
#   powershell -File scripts\install-to-r36s.ps1 -CardRoot G:\                    # checks the card, changes nothing
#   powershell -File scripts\install-to-r36s.ps1 -CardRoot G:\ -Install           # copies the game
#   powershell -File scripts\install-to-r36s.ps1 -CardRoot G:\ -RemoveOld -Install
#
# Per app: ports\<launcher>.sh and ports\<folder>\. A buttons.txt already on the card is kept (it may hold the
# player's own button map); the rest of the folder is replaced. ports\gamelist.xml gets (or updates) one <game>
# entry per app; the other entries are left as they are. The old launchers, buttons.txt and gamelist.xml are copied
# to <card>\elemon-backup-<time> first. The save (ports\elemon-save) is never touched.
# -RemoveOld also takes off the versions from when the game was called HoLua: "HoLua (chơi thử)" (HoLuaGame.sh,
# holua-game\) and the viewer "HoLua (xem thử)" (HoLua.sh, holua\), launchers and Ports entries too (backed up first).
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$CardRoot,
    [ValidateSet('both', 'game', 'viewer')][string]$App = 'game',
    [switch]$RemoveOld,
    [switch]$Install
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$apps = @(
    @{ key = 'game'; src = (Join-Path $root 'dist\elemon'); sh = 'Elemon.sh'; folder = 'elemon'; exe = 'elemon'
       need = 'js\load.txt'; name = 'Elemon'
       desc = 'Elemon: nuôi tinh linh Ngũ Hành từ quả trứng tới Huyền thoại. Tự lưu, chỉ số trôi theo giờ thật; nhạc và tiếng 8-bit. Giữ SELECT+START để thoát (game lưu trước khi thoát).' },
    @{ key = 'viewer'; src = (Join-Path $root 'dist\holua-r36s'); sh = 'HoLua.sh'; folder = 'holua'; exe = 'holua'
       need = 'data\list.txt'; name = 'HoLua (xem thử)'
       desc = 'HoLua: xem thử 17 phòng và 212 tinh linh Ngũ Hành, có nhạc 8-bit. L1/R1 đổi phòng, X/Y đổi pet, SELECT+START thoát.' }
) | Where-Object { $App -eq 'both' -or $_.key -eq $App }

$card = [IO.Path]::GetFullPath($CardRoot)
$ports = Join-Path $card 'ports'
if (-not (Test-Path -LiteralPath $ports -PathType Container)) {
    throw "'$card' has no ports folder: is it the EASYROMS partition of the R36S card?"
}
$size = 0
foreach ($a in $apps) {
    foreach ($need in $a.sh, "$($a.folder)\$($a.exe)", "$($a.folder)\$($a.need)", "$($a.folder)\cover.png") {
        if (-not (Test-Path -LiteralPath (Join-Path $a.src $need))) { throw "Missing $need in $($a.src): build it first (see the top of this file)." }
    }
    $size += (Get-ChildItem -Recurse -File $a.src | Measure-Object Length -Sum).Sum
}
$free = (Get-PSDrive -Name $card.Substring(0, 1)).Free
$gamelist = Join-Path $ports 'gamelist.xml'
Write-Host "Card: $ports  (free $([math]::Round($free / 1MB)) MB, needs up to $([math]::Round($size / 1MB)) MB)"
foreach ($a in $apps) { Write-Host ("$($a.name) there now: " + [bool](Test-Path (Join-Path $ports "$($a.folder)\$($a.exe)"))) }
# the HoLua-named versions (-RemoveOld): launcher, folder
$old = @(@{ sh = 'HoLuaGame.sh'; folder = 'holua-game' }, @{ sh = 'HoLua.sh'; folder = 'holua' }) |
    Where-Object { (Test-Path -LiteralPath (Join-Path $ports $_.sh)) -or (Test-Path -LiteralPath (Join-Path $ports $_.folder)) }
if ($RemoveOld) { foreach ($o in $old) { Write-Host "Old version to take off: $($o.sh), $($o.folder)\" } }
if ($free -lt $size * 1.1) { throw 'Not enough free space on the card.' }
if (-not $Install) { Write-Host 'Re-run with -Install to copy.'; return }

$backup = Join-Path $card ('elemon-backup-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Force -Path $backup | Out-Null
if (Test-Path -LiteralPath $gamelist) { Copy-Item -LiteralPath $gamelist -Destination $backup }
$doc = New-Object System.Xml.XmlDocument
if (Test-Path -LiteralPath $gamelist) { $doc.Load($gamelist) } else { $doc.AppendChild($doc.CreateXmlDeclaration('1.0', $null, $null)) | Out-Null; $doc.AppendChild($doc.CreateElement('gameList')) | Out-Null }
$list = $doc.DocumentElement

if ($RemoveOld) {
    foreach ($o in $old) {
        foreach ($f in $o.sh, "$($o.folder)\buttons.txt") {
            $p = Join-Path $ports $f
            if (Test-Path -LiteralPath $p) { Copy-Item -LiteralPath $p -Destination (Join-Path $backup ($f -replace '[\\/]', '_')) }
        }
        foreach ($f in $o.sh, $o.folder) {
            $p = Join-Path $ports $f
            if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Recurse -Force }
        }
        foreach ($g in @($list.SelectNodes('game') | Where-Object { $_.path -eq "./$($o.sh)" })) { $list.RemoveChild($g) | Out-Null }
        Write-Host "Took off $($o.sh) and $($o.folder)\"
    }
}

foreach ($a in $apps) {
    $dst = Join-Path $ports $a.folder
    foreach ($old in $a.sh, "$($a.folder)\buttons.txt") {
        $p = Join-Path $ports $old
        if (Test-Path -LiteralPath $p) { Copy-Item -LiteralPath $p -Destination (Join-Path $backup ($old -replace '[\\/]', '_')) }
    }
    $buttons = Join-Path $dst 'buttons.txt'
    $keep = if (Test-Path -LiteralPath $buttons) { [IO.File]::ReadAllBytes($buttons) } else { $null }
    # replaced as a whole (pictures or pets may have been removed since the last copy); saves of later versions
    # will live outside these folders
    if (Test-Path -LiteralPath $dst) { Remove-Item -LiteralPath $dst -Recurse -Force }
    Copy-Item -LiteralPath (Join-Path $a.src $a.folder) -Destination $dst -Recurse -Force
    if ($keep) { [IO.File]::WriteAllBytes($buttons, $keep) }
    # the launcher must keep Unix line ends
    $sh = [IO.File]::ReadAllText((Join-Path $a.src $a.sh)).Replace("`r`n", "`n")
    [IO.File]::WriteAllText((Join-Path $ports $a.sh), $sh, (New-Object System.Text.UTF8Encoding($false)))

    $game = $list.SelectNodes('game') | Where-Object { $_.path -eq "./$($a.sh)" } | Select-Object -First 1
    if (-not $game) { $game = $doc.CreateElement('game'); $list.AppendChild($game) | Out-Null }
    $fields = [ordered]@{ path = "./$($a.sh)"; name = $a.name; image = "./$($a.folder)/cover.png"; desc = $a.desc
                          developer = 'Elemon'; genre = 'Virtual pet'; players = '1' }
    foreach ($k in $fields.Keys) {
        $node = $game.SelectSingleNode($k)
        if (-not $node) { $node = $doc.CreateElement($k); $game.AppendChild($node) | Out-Null }
        $node.InnerText = $fields[$k]
    }
    Write-Host "Installed $($a.name) in $dst"
}
$settings = New-Object System.Xml.XmlWriterSettings
$settings.Indent = $true
$settings.Encoding = New-Object System.Text.UTF8Encoding($false)
$writer = [System.Xml.XmlWriter]::Create($gamelist, $settings)
$doc.Save($writer)
$writer.Close()
Write-Host "Backup: $backup. Restart EmulationStation (or the handheld) to see the new entries in Ports."
