param(
    [string]$BaseUrl = "http://localhost:8089",
    [string]$Pattern = "concurrent"
)

$file = if ($Pattern -eq "handoff") { "handoff_request.json" } else { "concurrent_request.json" }
$body = Get-Content "$PSScriptRoot\$file" -Raw
(Invoke-WebRequest -Uri "$BaseUrl/invocations" -Method POST -ContentType "application/json" -Body $body).Content
