# ReveniQ AI - Start dashboard
# Run from ReveniQ-AI folder: .\run_dashboard.ps1
# Digital COE Gen AI Team

Set-Location $PSScriptRoot

# Check if virtual environment exists
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Green
    .\.venv\Scripts\Activate.ps1
}

# Check if dependencies are installed
try {
    python -c "import streamlit, pandas, plotly" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installing dependencies..." -ForegroundColor Yellow
        pip install -r requirements.txt
    }
} catch {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

Write-Host "Starting ReveniQ AI Dashboard..." -ForegroundColor Cyan
Write-Host "Dashboard will open in your default browser." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server." -ForegroundColor Yellow
Write-Host ""

# Use venv's Streamlit so all dependencies (plotly, etc.) are found
if (Test-Path ".venv\Scripts\streamlit.exe") {
    .\.venv\Scripts\streamlit.exe run dashboard.py
} else {
    .\.venv\Scripts\python.exe -m streamlit run dashboard.py
}
