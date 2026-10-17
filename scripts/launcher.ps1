# Opens the game's launcher (settings, mods, PLAY).
#   .\scripts\launcher.ps1          the window
#   .\scripts\launcher.ps1 -Play    start the game with the saved settings, no window
param([switch]$Play)
$Launcher = Join-Path (Split-Path -Parent $PSScriptRoot) "launcher\ascension_launcher.py"
if ($Play) { python $Launcher --play } else { Start-Process pythonw -ArgumentList "`"$Launcher`"" }
