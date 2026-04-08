param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Label,
        [Parameter(Mandatory = $true)]
        [string]$Command,
        [switch]$DryRun
    )

    Write-Host ""
    Write-Host "==> $Label" -ForegroundColor Cyan
    Write-Host $Command -ForegroundColor DarkGray
    if (-not $DryRun) {
        Invoke-Expression $Command
    }
}

$scenarioMatrix = @(
    @{ Name = "intact"; Config = "examples/configs/scenarios/_intact.yaml"; PlotScript = "docs/plot_intact.py" },
    @{ Name = "formalin"; Config = "examples/configs/scenarios/formalin.yaml"; PlotScript = "docs/plot_formalin.py" },
    @{ Name = "capsaicin"; Config = "examples/configs/scenarios/capsaicin.yaml"; PlotScript = "docs/plot_capsaicin.py" },
    @{ Name = "compound_48_80"; Config = "examples/configs/scenarios/compound_48_80.yaml"; PlotScript = "docs/plot_compound4880.py" },
    @{ Name = "cyp_cystitis"; Config = "examples/configs/scenarios/cyp_cystitis.yaml"; PlotScript = "docs/plot_cyp_cystitis.py" }
#    @{ Name = "carrageenan"; Config = "examples/configs/scenarios/carrageenan.yaml"; PlotScript = "docs/plot_carrageenan.py" },
#    @{ Name = "hot_plate"; Config = "examples/configs/scenarios/hot_plate.yaml"; PlotScript = "docs/plot_hotplate.py" }
#    @{ Name = "acetic_writhing"; Config = "examples/configs/scenarios/acetic_writhing.yaml"; PlotScript = "docs/plot_writhing.py" },
#    @{ Name = "zymosan"; Config = "examples/configs/scenarios/zymosan.yaml"; PlotScript = "docs/plot_zymosan.py" }
)
 $ratDoses = @(9, 18, 36, 54, 72, 90, 180)
 $mouseDoses = @(15, 30, 60, 120, 150, 300)
#$ratDoses = @(90)
#$mouseDoses = @(120)
$tmpDir = "examples/configs/scenarios"
New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null
$createdTempConfigs = @()
$scenarioDoseTags = @{}

foreach ($scenario in $scenarioMatrix) {
    $scenarioName = $scenario.Name
    $scenarioConfig = $scenario.Config
    $configText = Get-Content -Path $scenarioConfig -Raw -Encoding UTF8
    $scenarioConfigLeaf = Split-Path -Path $scenarioConfig -Leaf
    $speciesMatch = [regex]::Match($configText, '(?m)^\s*species\s*:\s*(rat|mouse)\s*$')
    if (-not $speciesMatch.Success) {
        throw "Cannot resolve species in scenario config: $scenarioConfig"
    }
    $species = $speciesMatch.Groups[1].Value
    $speciesDoses = if ($species -eq "rat") { $ratDoses } else { $mouseDoses }
    $allDoseTags = if ($scenarioName -eq "intact") {
        @("0")
    } else {
        @("0") + ($speciesDoses | ForEach-Object { $_.ToString() })
    }
    $scenarioDoseTags[$scenarioName] = $allDoseTags

    foreach ($doseTag in $allDoseTags) {
        $isBaseline = $doseTag -eq "0"
        $tmpConfig = Join-Path $tmpDir "_tmp_$scenarioName`__dose_$($doseTag)mgkg.yaml"
        $tmpConfigContent = if ($isBaseline) {
@"
shared_configs:
  - $scenarioConfigLeaf

antagonist_pk:
  enabled: false
"@
        } else {
@"
shared_configs:
  - $scenarioConfigLeaf

antagonist_pk:
  enabled: true
  dose_mg_per_kg: $doseTag
"@
        }

        Set-Content -Path $tmpConfig -Value $tmpConfigContent -Encoding UTF8
        $createdTempConfigs += $tmpConfig

        $outDir = "runs/$($scenarioName)_pkpd_v1__dose_$($doseTag)mgkg"
        $simulateCommand = "python -m pkpd_xc7.cli.app simulate --config `"$tmpConfig`" --out `"$outDir`""
        Invoke-Step -Label "Simulate $scenarioName dose=$doseTag mg/kg" -Command $simulateCommand -DryRun:$DryRun
    }
}

foreach ($scenario in $scenarioMatrix) {
    $scenarioName = $scenario.Name
    $plotScript = $scenario.PlotScript
    foreach ($doseTag in $scenarioDoseTags[$scenarioName]) {
        $runDir = "runs/$($scenarioName)_pkpd_v1__dose_$($doseTag)mgkg"
        $fileStemSuffix = "dose_$($doseTag)mgkg"
        $baselineArg = ""
        $intactRefArg = ""
        if ($doseTag -ne "0") {
            $baselineRunDir = "runs/$($scenarioName)_pkpd_v1__dose_0mgkg"
            $baselineArg = "--render-xc7-concentration --render-histamine --render-internalization  --baseline-run-dir `"$baselineRunDir`""
            if ($scenarioName -ne "intact") {
                $intactRefArg = " --intact-reference-run-dir `"runs/intact_pkpd_v1__dose_0mgkg`""
            }
        }
        $plotCommand = "python $plotScript --run-dir `"$runDir`" --out-dir `"docs/figures`" --file-stem-suffix `"$fileStemSuffix`"$baselineArg$intactRefArg"
        Invoke-Step -Label "Plot $scenarioName dose=$doseTag mg/kg" -Command $plotCommand -DryRun:$DryRun
    }
}

foreach ($tmpConfig in $createdTempConfigs) {
    if (Test-Path -Path $tmpConfig) {
        Remove-Item -Path $tmpConfig -Force
    }
}

Write-Host ""
if ($DryRun) {
    Write-Host "Dry-run completed. No commands were executed." -ForegroundColor Yellow
} else {
    Write-Host "All simulations and baseline plots completed." -ForegroundColor Green
}
