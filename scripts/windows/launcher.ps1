# Opens the game's launcher (settings, mods, PLAY).
#   .\scripts\windows\launcher.ps1          the window
#   .\scripts\windows\launcher.ps1 -Play    start the game with the saved settings, no window
param([switch]$Play)
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Launcher = Join-Path $Root "launcher\ascension_launcher.py"
if ($Play) { python $Launcher --play } else { Start-Process pythonw -ArgumentList "`"$Launcher`"" }
