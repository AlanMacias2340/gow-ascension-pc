# Run the game for a while, with the window visible, and summarise the log.
#
#   .\scripts\windows\run.ps1                          # 120 s, no save (first-use menus)
#   .\scripts\windows\run.ps1 -Save backup -Seconds 90 # work\save-backup in place: straight to the cinematic
#   .\scripts\windows\run.ps1 -Name cin -Env @{ VDEC_TIMELOG = "1"; PS3_HLE_HIST = "5" }
#   .\scripts\windows\run.ps1 -Profile -ProfileAt 45   # sample the busiest threads at 45 s
#   .\scripts\windows\run.ps1 -Seconds 0 -Save keep    # play: runs until you close the window
#   .\scripts\windows\run.ps1 -Menu -Seconds 60        # straight to the main menu (~15 s)
#
# -Save fresh  : move the current save aside (work\save-moved\<time>) so the
#                first-use config menus show up (the default)
# -Save backup : as fresh, then copy work\save-backup in (skips those menus)
# -Save keep   : leave the save alone
# -CaptureAt N : presses F12 in the game window at N s: one frame's draws,
#                shaders and surfaces land in captures\cap_<frame>\.
# -Menu        : save-backup, the launcher's composed mods (skip intro) and
#                one X press (14 s) that skips the opening cinematic; the menu is up in
#                ~15 s. More presses enter the second menu (Single Player).
# The log is build\logs\<Name>.log; tools\log_summary.py prints the summary,
# and with -Profile the resolved profile is build\logs\<Name>-prof.txt.
param(
    [int]$Seconds = 120,
    [ValidateSet("fresh", "backup", "keep")][string]$Save = "fresh",
    [string]$Name = "run",
    $Env = @{},                         # hashtable, or "NAME=value;NAME2=value2"
    [switch]$Profile,
    [int]$ProfileAt = 45,
    [int]$ProfileThreads = 4,
    [ValidateSet("prof", "profip")][string]$ProfileVerb = "prof",   # profip: exclusive time per instruction
    [switch]$Menu,
    [int]$CaptureAt = 0                 # press F12 (frame capture into captures\) at this second
)

. (Join-Path $PSScriptRoot "env.ps1")
$Work    = $Cfg.WORK_DIR
$Exe     = Join-Path $Root "build\win\AscensionRecomp.exe"
$Elf     = Join-Path $Work "disc\PS3_GAME\USRDIR\EBOOT.ELF"
$Logs    = Join-Path $Root "build\logs"
$SaveDir = Join-Path $Root "gamedata\dev_hdd0\home\00000001\savedata"
$Slot    = Join-Path $SaveDir "BCES01741-SYSDATA"
New-Item -ItemType Directory -Force $Logs, $SaveDir | Out-Null
$Log = Join-Path $Logs "$Name.log"

if ($Menu) {
    if (-not $PSBoundParameters.ContainsKey("Save")) { $Save = "backup" }
    if ($Env -is [string]) { $Env = $Env + ";" } else { $Env = $Env.Clone() }
    $menuEnv = @{ PAD_SCRIPT = "14:0x4000,15:0x0000" }
    $gen = Join-Path $env:APPDATA "ascension-launcher\generated"
    if (Test-Path $gen) { $menuEnv["PS3_MODS"] = $gen } else { Write-Host "no launcher mods at $($gen): the intro screens will play" }
    if ($Env -is [string]) { foreach ($k in $menuEnv.Keys) { $Env += "$k=$($menuEnv[$k]);" } }
    else { foreach ($k in $menuEnv.Keys) { if (-not $Env.ContainsKey($k)) { $Env[$k] = $menuEnv[$k] } } }
}
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
Write-Host $(if ($Seconds -le 0) { "running until closed (log: $Log)" } else { "running for $Seconds s (log: $Log)" })

Start-Sleep -Seconds 2
$game = Get-Process AscensionRecomp -ErrorAction SilentlyContinue | Sort-Object StartTime -Descending | Select-Object -First 1
if ($Profile -and $game) {
    $wait = $ProfileAt - ((Get-Date) - $t0).TotalSeconds
    if ($wait -gt 0) { Start-Sleep -Seconds $wait }
    python -I (Join-Path $Root "tools\profile_threads.py") --pid $game.Id --dbg $dbg --threads $ProfileThreads `
        --verb $ProfileVerb --map (Join-Path $Root "build\win\AscensionRecomp.map") --out (Join-Path $Logs "$Name-prof.txt")
}
if ($CaptureAt -gt 0 -and $game) {
    $wait = $CaptureAt - ((Get-Date) - $t0).TotalSeconds
    if ($wait -gt 0) { Start-Sleep -Seconds $wait }
    Add-Type -Namespace RunPs1 -Name Keys -MemberDefinition @"
[DllImport("user32.dll")] public static extern void keybd_event(byte k, byte s, uint f, System.UIntPtr e);
[DllImport("user32.dll")] public static extern bool SetForegroundWindow(System.IntPtr h);
"@
    $game.Refresh()
    [RunPs1.Keys]::SetForegroundWindow($game.MainWindowHandle) | Out-Null
    Start-Sleep -Milliseconds 300
    [RunPs1.Keys]::keybd_event(0x7B, 0, 0, [System.UIntPtr]::Zero)
    Start-Sleep -Milliseconds 150
    [RunPs1.Keys]::keybd_event(0x7B, 0, 2, [System.UIntPtr]::Zero)
    Write-Host "F12 sent at $([int]((Get-Date) - $t0).TotalSeconds) s"
}
if ($Seconds -le 0) {
    # -Seconds 0: play; wait until the game is closed, never kill it.
    if ($game) { Write-Host "playing: close the game window when done"; Wait-Process -Id $game.Id }
} else {
    $left = $Seconds - ((Get-Date) - $t0).TotalSeconds
    if ($left -gt 0 -and $game) { Wait-Process -Id $game.Id -Timeout $left -ErrorAction SilentlyContinue }
    Get-Process AscensionRecomp -ErrorAction SilentlyContinue | Stop-Process -Force
}
Start-Sleep -Milliseconds 500

python -I (Join-Path $Root "tools\log_summary.py") $Log
