# Run the llama3.2 model for ReveniQ AI (Ollama must already be installed)
# Run in PowerShell: .\scripts\install_ollama_and_run_model.ps1
# Digital COE Gen AI Team

$ollamaPath = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
if (-not (Test-Path $ollamaPath)) {
    Write-Host "Ollama not found. Install from https://ollama.com first (run in PowerShell: irm https://ollama.com/install.ps1 | iex)"
    exit 1
}
$env:Path += ";$env:LOCALAPPDATA\Programs\Ollama"

Write-Host "Pulling and running model: llama3.2 (first time downloads ~2GB)..."
ollama run llama3.2
