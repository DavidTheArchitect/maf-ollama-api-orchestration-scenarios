param(
    [string]$BaseUrl = "http://localhost:8088"
)

$body = Get-Content "$PSScriptRoot\request_non_streaming.json" -Raw
(Invoke-WebRequest -Uri "$BaseUrl/responses" -Method POST -ContentType "application/json" -Body $body).Content
