# Build AscensionRecomp.exe (incremental ninja in build\win) and log it.
#
#   .\scripts\windows\build.ps1                 # log: build\logs\build.log
#   .\scripts\windows\build.ps1 -Name sse41     # log: build\logs\build-sse41.log
#
# Prints how long it took, the error lines if any, and the last line of the
# log; the exit code is ninja's.
param([string]$Name = "")

$Root   = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Build  = Join-Path $Root "build\win"
$Logs   = Join-Path $Root "build\logs"
$Vcvars = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
New-Item -ItemType Directory -Force $Logs | Out-Null
$Log = Join-Path $Logs ($(if ($Name) { "build-$Name.log" } else { "build.log" }))

$sw = [Diagnostics.Stopwatch]::StartNew()
cmd /c "`"$Vcvars`" >nul && ninja -C `"$Build`"" 2>&1 | Out-File -Encoding utf8 $Log
$code = $LASTEXITCODE
$sw.Stop()

$errors = Select-String -Path $Log -Pattern "error:|FAILED:|fatal error|LNK\d{4}" | Select-Object -First 15
Write-Host ("build {0} in {1:mm\:ss}  (log: {2})" -f $(if ($code -eq 0) { "OK" } else { "FAILED" }), $sw.Elapsed, $Log)
if ($errors) { $errors | ForEach-Object { Write-Host "  $($_.Line)" } }
Write-Host ("last line: " + (Get-Content $Log -Tail 1))
exit $code
