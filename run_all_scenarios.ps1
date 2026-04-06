$ErrorActionPreference = "Stop"

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Label,
        [Parameter(Mandatory = $true)]
        [string]$Command
    )

    Write-Host ""
    Write-Host "==> $Label" -ForegroundColor Cyan
    Write-Host $Command -ForegroundColor DarkGray
    Invoke-Expression $Command
}

Invoke-Step -Label "Simulate formalin" -Command 'python -m pkpd_xc7.cli.app simulate --config "examples/configs/scenarios/formalin.yaml" --out "runs/formalin_pkpd_v1"'
Invoke-Step -Label "Simulate capsaicin" -Command 'python -m pkpd_xc7.cli.app simulate --config "examples/configs/scenarios/capsaicin.yaml" --out "runs/capsaicin_pkpd_v1"'
Invoke-Step -Label "Simulate compound_48_80" -Command 'python -m pkpd_xc7.cli.app simulate --config "examples/configs/scenarios/compound_48_80.yaml" --out "runs/compound_48_80_pkpd_v1"'
Invoke-Step -Label "Simulate carrageenan" -Command 'python -m pkpd_xc7.cli.app simulate --config "examples/configs/scenarios/carrageenan.yaml" --out "runs/carrageenan_pkpd_v1"'
Invoke-Step -Label "Simulate hot_plate" -Command 'python -m pkpd_xc7.cli.app simulate --config "examples/configs/scenarios/hot_plate.yaml" --out "runs/hot_plate_pkpd_v1"'
Invoke-Step -Label "Simulate acetic_writhing" -Command 'python -m pkpd_xc7.cli.app simulate --config "examples/configs/scenarios/acetic_writhing.yaml" --out "runs/acetic_writhing_pkpd_v1"'
Invoke-Step -Label "Simulate zymosan" -Command 'python -m pkpd_xc7.cli.app simulate --config "examples/configs/scenarios/zymosan.yaml" --out "runs/zymosan_pkpd_v1"'

Invoke-Step -Label "Plot formalin" -Command 'python docs/plot_formalin.py --run-dir "runs/formalin_pkpd_v1" --out-dir "docs/figures"'
Invoke-Step -Label "Plot capsaicin" -Command 'python docs/plot_capsaicin.py --run-dir "runs/capsaicin_pkpd_v1" --out-dir "docs/figures"'
Invoke-Step -Label "Plot compound_48_80" -Command 'python docs/plot_compound4880.py --run-dir "runs/compound_48_80_pkpd_v1" --out-dir "docs/figures"'
Invoke-Step -Label "Plot carrageenan" -Command 'python docs/plot_carrageenan.py --run-dir "runs/carrageenan_pkpd_v1" --out-dir "docs/figures"'
Invoke-Step -Label "Plot hot_plate" -Command 'python docs/plot_hotplate.py --run-dir "runs/hot_plate_pkpd_v1" --out-dir "docs/figures"'
Invoke-Step -Label "Plot acetic_writhing" -Command 'python docs/plot_writhing.py --run-dir "runs/acetic_writhing_pkpd_v1" --out-dir "docs/figures"'
Invoke-Step -Label "Plot zymosan" -Command 'python docs/plot_zymosan.py --run-dir "runs/zymosan_pkpd_v1" --out-dir "docs/figures"'

Write-Host ""
Write-Host "All simulations and plots completed." -ForegroundColor Green
