# Re-lift the SPU job modules or the position-independent code fragments.
#
#   .\scripts\windows\relift.ps1 jobmods                       # all 15 modules (all of them recompile)
#   .\scripts\windows\relift.ps1 jobmods -Only e9f3f00d551e    # one module: only it recompiles
#   .\scripts\windows\relift.ps1 fragments                     # tools\job_fragments.json -> src\spu\pic_*
#
# Extra entries per module: tools\jobmods_extra_funcs.json. Run .\scripts\windows\build.ps1 after.
param(
    [Parameter(Mandatory)][ValidateSet("jobmods", "fragments")][string]$What,
    [string]$Only = ""
)

$Root  = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Top   = Split-Path -Parent $Root
$Tools = Join-Path $Top "ps3recomp\tools"
$Spu   = Join-Path $Root "src\spu"
$Log   = Join-Path $Root "build\logs\relift-$What.log"

if ($What -eq "jobmods") {
    $mods = Join-Path $Top "work\jobmods"
    if ($Only) {
        # Lift one module in a scratch folder and copy only its sources over:
        # rewriting all of them would make every module recompile.
        $tmp = Join-Path $env:TEMP "ascension-relift"
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $tmp
        New-Item -ItemType Directory -Force "$tmp\in", "$tmp\out" | Out-Null
        $bin = Get-ChildItem $mods -Filter "jobmod_$Only*.bin" | Select-Object -First 1
        if (-not $bin) { Write-Error "no work\jobmods\jobmod_$Only*.bin"; exit 1 }
        Copy-Item $bin.FullName "$tmp\in"
        python (Join-Path $Tools "lift_jobmods.py") --jobmods "$tmp\in" --out "$tmp\out" --register "$tmp\out\reg.c" `
            --symbol-prefix ascension --extra-funcs-json (Join-Path $Root "tools\jobmods_extra_funcs.json") 2>&1 | Tee-Object $Log
        $name = $bin.BaseName
        Copy-Item "$tmp\out\$name\spu_recomp.c", "$tmp\out\$name\spu_recomp.h" (Join-Path $Spu $name)
        Write-Host "copied $name into src\spu"
    } else {
        python (Join-Path $Tools "lift_jobmods.py") --jobmods $mods --out $Spu --register (Join-Path $Spu "jobmods_register.c") `
            --symbol-prefix ascension --extra-funcs-json (Join-Path $Root "tools\jobmods_extra_funcs.json") 2>&1 | Tee-Object $Log
    }
} else {
    python (Join-Path $Tools "lift_spu_pic.py") --elf (Join-Path $Top "work\disc\PS3_GAME\USRDIR\EBOOT.ELF") `
        --fragments (Join-Path $Root "tools\job_fragments.json") --out $Spu --register (Join-Path $Spu "pic_register.c") `
        --symbol-prefix ascension 2>&1 | Tee-Object $Log
}
