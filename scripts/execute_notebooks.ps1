param(
    [string]$Project = "all"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot

$projects = @(
    @{
        Name = "responses"
        Dir = Join-Path $repoRoot "responses-api-scenarios"
    },
    @{
        Name = "invocations"
        Dir = Join-Path $repoRoot "invocations-api-scenarios"
    }
)

foreach ($entry in $projects) {
    if ($Project -ne "all" -and $Project -ne $entry.Name) {
        continue
    }

    Push-Location $entry.Dir
    try {
        $python = Join-Path $entry.Dir ".venv\Scripts\python.exe"
        $notebooks = Get-ChildItem -Path "notebooks" -Filter "*.ipynb" | Sort-Object Name
        foreach ($notebook in $notebooks) {
            $relative = Join-Path $entry.Name $notebook.Name
            Write-Output "$(Get-Date -Format o) START $relative"
            & $python -m nbconvert `
                --to notebook `
                --execute `
                --ExecutePreprocessor.timeout=1200 `
                --inplace `
                $notebook.FullName
            if ($LASTEXITCODE -ne 0) {
                throw "Notebook execution failed for $relative"
            }
            Write-Output "$(Get-Date -Format o) DONE  $relative"
        }
    }
    finally {
        Pop-Location
    }
}
