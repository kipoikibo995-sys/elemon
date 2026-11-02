# Builds Elemon for the Miyoo Mini Plus (SigmaStar SSD202D: two Cortex-A7, 32-bit ARMv7 hard float, glibc 2.28,
# 128 MB) the same way as scripts\build-r36s.ps1 builds it for the ARM64 handhelds, with zig cc:
#   game    r36s/jsrt.c (-DJSRT_LAZY) + js_miyoo.c + r36s/quickjs/   -> build\miyoo-armv7\elemon
# No SDL: js_miyoo.c draws on /dev/fb0, reads /dev/input/event0 and plays through /dev/dsp. The game's data is the
# one in dist\elemon\elemon (game/build_game.py + scripts/r36s_game.py); scripts\pack_miyoo.py puts the two together.
#
#   powershell -File scripts\build-miyoo.ps1
#   powershell -File scripts\build-miyoo.ps1 -Test    # also the PC test runner (r36s/js_test.c) for ARMv7 and ARM64,
#                                                     # to run under qemu-arm / qemu-aarch64 (packaging/miyoo/README.md)
# The ARM64 build (Brick, R36S) is not touched: JSRT_LAZY is off there, and its binary stays byte for byte the same.
param([switch]$Test)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$out = Join-Path $root 'build\miyoo-armv7'
$arm = 'arm-linux-gnueabihf.2.17'      # the Miyoo has glibc 2.28 (its toolchain: gcc 8.3); asking for 2.17 keeps fcntl off the 2.28 symbol, so an older one works too
$cpu = @('-mcpu=cortex_a7', '-mfpu=neon-vfpv4')
[IO.Directory]::CreateDirectory($out) | Out-Null
# a Python that has the ziglang package (python on the PATH may be another one)
$py = @('python', 'py -3.13', 'py -3') | Where-Object { cmd /c "$_ -c `"import ziglang`" >nul 2>nul"; $LASTEXITCODE -eq 0 } | Select-Object -First 1
if (-not $py) { throw 'no Python with ziglang (pip install ziglang)' }
$py = $py -split ' '
function zig { & $py[0] @($py[1..9] + @('-m', 'ziglang', 'cc') + $args) }

function Objects($tag, $target, $cpuFlags, $sources, $flags) {
    $objects = @()
    foreach ($source in $sources) {
        $object = Join-Path $out ($tag + '-' + [IO.Path]::GetFileNameWithoutExtension($source) + '.o')
        $warn = @(if ($source -like 'r36s/quickjs/*') { '-w' } else { '-Wall'; '-Wextra' })
        $opt = @(if ($source -like 'r36s/quickjs/*') { '-O2' } else { '-O3' })
        zig -target $target @cpuFlags -std=gnu99 @opt -D_GNU_SOURCE @flags @warn -c $source -o $object
        if ($LASTEXITCODE -ne 0) { throw "compile failed: $source" }
        $objects += $object
    }
    return $objects
}

Push-Location $root
try {
    $qjs = @('quickjs', 'dtoa', 'libregexp', 'libunicode', 'cutils') | ForEach-Object { "r36s/quickjs/$_.c" }
    # PowerShell 5.1 drops bare inner quotes of native arguments: \" reaches the compiler as "
    $common = @('-DCONFIG_VERSION=\"2026-06-04\"', '-DJSRT_LAZY')
    $q = Objects 'arm' $arm $cpu $qjs $common
    $objects = (Objects 'arm' $arm $cpu @('r36s/jsrt.c', 'r36s/js_miyoo.c') $common) + $q
    $binary = Join-Path $out 'elemon'
    zig -target $arm @cpu -s -o $binary @objects -lm -lpthread
    if ($LASTEXITCODE -ne 0) { throw 'link failed' }
    Write-Host "Built $binary ($([math]::Round((Get-Item $binary).Length / 1KB)) KB)"
    if ($Test) {
        # the test runner, ARMv7 and (for the other side of a wifi match) ARM64 as the Brick's build is
        $t = (Objects 'arm-test' $arm $cpu @('r36s/jsrt.c', 'r36s/js_test.c') $common) + $q
        zig -target $arm @cpu -o (Join-Path $out 'holua-game-test-armv7') @t -lm -lpthread
        if ($LASTEXITCODE -ne 0) { throw 'link failed (test, ARMv7)' }
        $a64 = 'aarch64-linux-gnu.2.28'
        $t = Objects 'a64-test' $a64 @('-mcpu=cortex_a35') (@('r36s/jsrt.c', 'r36s/js_test.c') + $qjs) @('-DCONFIG_VERSION=\"2026-06-04\"')
        zig -target $a64 -mcpu=cortex_a35 -o (Join-Path $out 'holua-game-test-arm64') @t -lm -lpthread
        if ($LASTEXITCODE -ne 0) { throw 'link failed (test, ARM64)' }
        Write-Host "Built the test runners in $out"
    }
} finally { Pop-Location }
