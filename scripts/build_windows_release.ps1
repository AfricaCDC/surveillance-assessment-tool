$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $projectRoot
try {
    python -m PyInstaller --noconfirm --clean --onefile --name AfricaCDCWebAssessment `
        --distpath package_dist --workpath package_build/runtime --specpath package_build `
        --add-data "$projectRoot\static;static" `
        --add-data "$projectRoot\standard_assessment_template.xlsx;." server.py
    if ($LASTEXITCODE -ne 0) { throw 'Executable build failed' }
    $builtExecutable = Join-Path $projectRoot 'package_dist\AfricaCDCWebAssessment.exe'
    foreach ($relativeTarget in @('AfricaCDCWebAssessment.exe', 'package_dist_i18n\AfricaCDCWebAssessment.exe', 'package_dist_ollama\AfricaCDCWebAssessment.exe')) {
        Copy-Item -LiteralPath $builtExecutable -Destination (Join-Path $projectRoot $relativeTarget) -Force
    }
} finally {
    Pop-Location
}
