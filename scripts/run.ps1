# Run the game for a while, with the window visible, and summarise the log.
#
#   .\scripts\run.ps1                          # 120 s, no save (first-use menus)
#   .\scripts\run.ps1 -Save backup -Seconds 90 # work\save-backup in place: straight to the cinematic
#   .\scripts\run.ps1 -Name cin -Env @{ VDEC_TIMELOG = "1"; PS3_HLE_HIST = "5" }
#   .\scripts\run.ps1 -Profile -ProfileAt 45   # sample the busiest threads at 45 s
#
# -Save fresh  : move the current save aside (work\save-moved\<time>) so the
#                first-use config menus show up (the default)
# -Save backup : as fresh, then copy work\save-backup in (skips those menus)
# -Save keep   : leave the save alone
# The log is build\logs\<Name>.log; tools\log_summary.py prints the summary,
# and with -Profile the resolved profile is build\logs\<Name>-prof.txt.
param(
    [int]$Seconds = 120,
    [ValidateSet("fresh", "backup", "keep")][string]$Save = "fresh",
    [string]$Name = "run",
    $Env = @{},                         # hashtable, or "NAME=value;NAME2=value2"
    [switch]$Profile,
    [int]$ProfileAt = 45,
    [int]$ProfileThreads = 4
)

$Root    = Split-Path -Parent $PSScriptRoot
$Work    = Join-Path (Split-Path -Parent $Root) "work"
$Exe     = Join-Path $Root "build\win\AscensionRecomp.exe"
$Elf     = Join-Path $Work "disc\PS3_GAME\USRDIR\EBOOT.ELF"
$Logs    = Join-Path $Root "build\logs"
$SaveDir = Join-Path $Root "gamedata\dev_hdd0\home\00000001\savedata"
$Slot    = Join-Path $SaveDir "BCES01741-SYSDATA"
New-Item -ItemType Directory -Force $Logs, $SaveDir | Out-Null
$Log = Join-Path $Logs "$Name.log"

if ($Save -ne "keep" -and (Test-Path $Slot)) {
    $dest = Join-Path $Work ("save-moved\" + (Get-Date -Format "yyyyMMdd-HHmmss"))
    New-Item -ItemType Directory -Force $dest | Out-Null
    Move-Item $Slot $dest
    Write-Host "save moved to $dest"
}
if ($Save -eq "backup") {
    Copy-Item -Recurse (Join-Path $Work "save-backup\BCES01741-SYSDATA") $SaveDir
    Write-Host "save-backup copied in"
}

if ($Env -is [string]) {
    $h = @{}
    foreach ($kv in ($Env -split ";")) { if ($kv -match "^\s*([^=]+)=(.*)$") { $h[$Matches[1].Trim()] = $Matches[2] } }
    $Env = $h
}
# The game inherits this process's environment; restore it afterwards.
$saved = @{}
foreach ($k in $Env.Keys) { $saved[$k] = [Environment]::GetEnvironmentVariable($k); [Environment]::SetEnvironmentVariable($k, [string]$Env[$k]) }
$dbg = Join-Path $Logs "$Name-dbg.txt"
if ($Profile) {
    Remove-Item -ErrorAction SilentlyContinue $dbg, "$dbg.out"
    $saved["PS3_DEBUG"] = $env:PS3_DEBUG; $env:PS3_DEBUG = $dbg
}

$t0 = Get-Date
$p = Start-Process cmd.exe -ArgumentList "/c `"`"$Exe`" `"$Elf`" > `"$Log`" 2>&1`"" -WorkingDirectory $Root -PassThru -WindowStyle Hidden
foreach ($k in $saved.Keys) { [Environment]::SetEnvironmentVariable($k, $saved[$k]) }
Write-Host "running for $Seconds s (log: $Log)"

Start-Sleep -Seconds 2
$game = Get-Process AscensionRecomp -ErrorAction SilentlyContinue | Sort-Object StartTime -Descending | Select-Object -First 1
if ($Profile -and $game) {
    $wait = $ProfileAt - ((Get-Date) - $t0).TotalSeconds
    if ($wait -gt 0) { Start-Sleep -Seconds $wait }
    python -I (Join-Path $Root "tools\profile_threads.py") --pid $game.Id --dbg $dbg --threads $ProfileThreads `
        --map (Join-Path $Root "build\win\AscensionRecomp.map") --out (Join-Path $Logs "$Name-prof.txt")
}
$left = $Seconds - ((Get-Date) - $t0).TotalSeconds
if ($left -gt 0 -and $game) { Wait-Process -Id $game.Id -Timeout $left -ErrorAction SilentlyContinue }
Get-Process AscensionRecomp -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Milliseconds 500

python -I (Join-Path $Root "tools\log_summary.py") $Log
