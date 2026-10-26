# Builds the two R36S programs for ARM64 Linux handhelds (R36S, RG351MP ... running ArkOS / dArkOS) with SDL2,
# the same way as the Mimo build (Mimo-0.1\scripts\build-arm64.ps1):
#   viewer  r36s/core.c + sdl2_main.c                 -> dist\holua-r36s\holua\holua        (data: scripts\r36s_app.py)
#   game    r36s/jsrt.c + js_sdl2.c + r36s/quickjs/   -> dist\elemon\elemon\elemon        (data: scripts\r36s_game.py)
#
#   powershell -File scripts\build-r36s.ps1            # both
#   powershell -File scripts\build-r36s.ps1 -Only game
#
# Needs Python with the "ziglang" package as the cross compiler and the SDL2 headers (-Sdl, default: the ones
# unpacked for Mimo). SDL2 itself is NOT linked: the handheld already has libSDL2-2.0.so.0.
param(
    [string]$Sdl = 'C:\Users\DLA\Documents\Codex\2026-10-20\tao\outputs\Mimo-0.1\build\sdl2\SDL2-2.30.9\include',
    [ValidateSet('both', 'viewer', 'game')][string]$Only = 'both'
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$out = Join-Path $root 'build\r36s-arm64'
$inc = (Resolve-Path $Sdl).Path.Replace('\', '/')
$target = 'aarch64-linux-gnu.2.28'    # glibc 2.28 runs on everything from ArkOS (Ubuntu 19.10) on
[IO.Directory]::CreateDirectory($out) | Out-Null

function Build($name, $sources, $flags, $dist, $need) {
    if (-not (Test-Path (Join-Path $dist $need))) { throw "$dist\$need is missing: make the data first (see the top of this file)." }
    $objects = @()
    foreach ($source in $sources) {
        $object = Join-Path $out ($name + '-' + [IO.Path]::GetFileNameWithoutExtension($source) + '.o')
        # our own files with every warning, QuickJS as it comes
        $warn = @(if ($source -like 'r36s/quickjs/*') { '-w' } else { '-Wall'; '-Wextra' })
        # made for the R36S's Cortex-A35 (RK3326; the RG351 family has the same core); the pixel loops at -O3,
        # where the compiler turns them into SIMD
        $opt = @(if ($source -like 'r36s/quickjs/*') { '-O2' } else { '-O3' })
        & python -m ziglang cc -target $target -mcpu=cortex_a35 -std=gnu99 @opt -D_GNU_SOURCE "-I$inc" @flags @warn -c $source -o $object
        if ($LASTEXITCODE -ne 0) { throw "compile failed: $source" }
        $objects += $object
    }
    # a stand-in libSDL2 with just the names the program uses: the link works and the binary records
    # libSDL2-2.0.so.0 as a dependency (the real library on the handheld takes its place when it starts)
    $symbols = & python (Join-Path $PSScriptRoot 'sdl-symbols.py') @objects
    $stubC = Join-Path $out "$name-sdl2stub.c"
    Set-Content -Path $stubC -Encoding ascii -Value (($symbols | ForEach-Object { "int $_(void) { return 0; }" }) -join "`n")
    $stub = Join-Path $out "$name-stub\libSDL2-2.0.so.0"
    [IO.Directory]::CreateDirectory((Split-Path $stub)) | Out-Null
    & python -m ziglang cc -target $target -shared '-Wl,-soname,libSDL2-2.0.so.0' $stubC -o $stub
    if ($LASTEXITCODE -ne 0) { throw 'stub failed' }
    $binary = Join-Path $out $name
    & python -m ziglang cc -target $target -s -o $binary @objects $stub -lm
    if ($LASTEXITCODE -ne 0) { throw 'link failed' }
    Copy-Item $binary (Join-Path $dist $name) -Force
    Write-Host "Built $(Join-Path $dist $name) ($([math]::Round((Get-Item $binary).Length / 1KB)) KB)"
}

Push-Location $root
try {
    if ($Only -ne 'game') {
        Build 'holua' @('r36s/core.c', 'r36s/sdl2_main.c') @() (Join-Path $root 'dist\holua-r36s\holua') 'data\list.txt'
    }
    if ($Only -ne 'viewer') {
        $qjs = @('quickjs', 'dtoa', 'libregexp', 'libunicode', 'cutils') | ForEach-Object { "r36s/quickjs/$_.c" }
        # PowerShell 5.1 drops bare inner quotes of native arguments: \" reaches the compiler as "
        Build 'elemon' (@('r36s/jsrt.c', 'r36s/js_sdl2.c') + $qjs) @('-DCONFIG_VERSION=\"2026-06-04\"') `
            (Join-Path $root 'dist\elemon\elemon') 'js\load.txt'
    }
} finally { Pop-Location }
