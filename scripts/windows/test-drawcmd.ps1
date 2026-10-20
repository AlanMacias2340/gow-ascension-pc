# Differential tests for module 218: accumulator, or -Stage for the blend loop
# and fused stage (including actual entry/exit captures when available).
# Uses the local lift and captures; no game data enters either repository.
param([switch]$NoFma, [switch]$Stage, [switch]$Field)
if ($Stage -and $Field) { throw "Choose -Stage or -Field" }
. (Join-Path $PSScriptRoot "env.ps1")
$nativeDir = Join-Path $Cfg.PS3KIT_DIR "libs\spu_hle\gowa_drawcmd"
$testBuild = Join-Path $Cfg.WORK_DIR "drawcmd-native"
New-Item -ItemType Directory -Force $testBuild | Out-Null
$reference = Join-Path $testBuild "vertex_reference.inc"
$lift = Join-Path $Root "src\spu\jobmod_7868e9b847d1_e6D98\spu_recomp.c"
python (Join-Path $nativeDir "prepare_reference.py") $lift $reference
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$testName = if ($Field) { "test_field" } elseif ($Stage) { "test_stage" } else { "test_vertex" }
if ($NoFma) { $testName += "_nofma" }
$testExe = Join-Path $testBuild "$testName.exe"
$testObj = [IO.Path]::ChangeExtension($testExe, ".obj")
$source = Join-Path $nativeDir $(if ($Field) { "tests\test_field.c" } elseif ($Stage) { "tests\test_stage.c" } else { "tests\test_vertex.c" })
if ($Field) {
    python (Join-Path $nativeDir "prepare_field.py") $lift $testBuild
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
if ($Stage) {
    python (Join-Path $nativeDir "prepare_stage.py") $lift $testBuild
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
$fmaFlag = if ($NoFma) { "" } else { "/clang:-mfma" }
cmd /c "`"$($Cfg.VCVARS)`" >nul && clang-cl /nologo /O2 /D_CRT_SECURE_NO_WARNINGS /clang:-msse4.1 $fmaFlag /clang:-ffp-contract=off /clang:-frounding-math /DSPU_ASSUME_SPU_FP /I`"$testBuild`" `"$source`" /Fe`"$testExe`" /Fo`"$testObj`""
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$captureGlob = if ($Field) { "edge_cases\field_stage\*.sjc" } elseif ($Stage) { "edge_cases\vertex_stage\*.sjc" } else { "edge_cases\level2\*.sjc" }
$captures = @(Get-ChildItem (Join-Path $Cfg.WORK_DIR $captureGlob) -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName })
& $testExe @captures
exit $LASTEXITCODE
