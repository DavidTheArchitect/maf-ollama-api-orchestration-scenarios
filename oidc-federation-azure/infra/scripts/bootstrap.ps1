<#
.SYNOPSIS
    In-deployment Keycloak bootstrap, run by an AzurePowerShell
    deploymentScripts resource as part of the Bicep deployment.

.DESCRIPTION
    Deploying infra/main.bicep - from the CLI or the Bicep extension GUI -
    performs the entire post-provisioning flow with no local scripts:
      1. Wait for Keycloak's OIDC discovery endpoint.
      2. Bootstrap realm / confidential client / audience mapper (idempotent).
      3. Provision a test user (idempotent) for the password-grant flow.
      4. Upload the demo blob used by the data-plane verification.
      5. Re-enable the Caddy admin lockdown.
      6. Emit the service-account and test-user UUIDs; Bicep feeds them into
         the two federated identity credentials as their subjects.

    Inputs arrive as environment variables set by infra/modules/bootstrap.bicep:
      KEYCLOAK_URL, REALM, CLIENT_ID, KC_ADMIN_PASSWORD, KC_CLIENT_SECRET,
      TEST_USERNAME, TEST_USER_PASSWORD, STORAGE_ACCOUNT, STORAGE_KEY,
      CONTAINER_APP, RESOURCE_GROUP.

    The AzurePowerShell container auto-connects Az to the deployer managed
    identity, so Az.Storage and Invoke-AzRestMethod need no explicit login.
#>
$ErrorActionPreference = 'Stop'

$keycloakUrl      = ($env:KEYCLOAK_URL).TrimEnd('/')
$realm            = $env:REALM
$clientId         = $env:CLIENT_ID
$adminPassword    = $env:KC_ADMIN_PASSWORD
$clientSecret     = $env:KC_CLIENT_SECRET
$testUsername     = $env:TEST_USERNAME
$testUserPassword = $env:TEST_USER_PASSWORD
$storageAccount   = $env:STORAGE_ACCOUNT
$storageKey       = $env:STORAGE_KEY
$containerApp     = $env:CONTAINER_APP
$resourceGroup    = $env:RESOURCE_GROUP
$audience         = 'api://AzureADTokenExchange'

# --- 1. Wait for Keycloak discovery endpoint ---------------------------------
Write-Host "Waiting for Keycloak discovery endpoint at $keycloakUrl ..."
$ready = $false
foreach ($attempt in 1..90) {
    try {
        Invoke-RestMethod -Method Get -TimeoutSec 10 `
            -Uri "$keycloakUrl/realms/master/.well-known/openid-configuration" | Out-Null
        $ready = $true
        break
    } catch {
        Start-Sleep -Seconds 10
    }
}
if (-not $ready) { throw 'Keycloak did not become ready within 15 minutes.' }
Write-Host 'Keycloak is up.'

# --- Admin token + REST helpers ----------------------------------------------
$token = (Invoke-RestMethod -Method Post `
    -Uri "$keycloakUrl/realms/master/protocol/openid-connect/token" `
    -ContentType 'application/x-www-form-urlencoded' `
    -Body @{
        grant_type = 'password'
        client_id  = 'admin-cli'
        username   = 'admin'
        password   = $adminPassword
    }).access_token
$headers = @{ Authorization = "Bearer $token" }
$adminBase = "$keycloakUrl/admin/realms"

function Test-KcExists {
    param([string]$Uri)
    try {
        Invoke-RestMethod -Method Get -Uri $Uri -Headers $headers | Out-Null
        return $true
    } catch {
        if ($_.Exception.Response -and [int]$_.Exception.Response.StatusCode -eq 404) { return $false }
        throw
    }
}

# Invoke-RestMethod can surface an empty JSON array as a single empty item;
# piping through Write-Output normalizes it to a real (possibly empty) array.
function Get-KcList {
    param([string]$Uri)
    ,@(Invoke-RestMethod -Method Get -Uri $Uri -Headers $headers | Write-Output)
}

function Invoke-KcJson {
    param([string]$Method, [string]$Uri, $Body)
    Invoke-RestMethod -Method $Method -Uri $Uri -Headers $headers `
        -ContentType 'application/json' -Body ($Body | ConvertTo-Json -Depth 10) | Out-Null
}

# --- 2. Realm (short-lived tokens keep the Entra assertions short-lived) ------
if (Test-KcExists "$adminBase/$realm") {
    Write-Host "Realm '$realm' already exists."
} else {
    Write-Host "Creating realm '$realm' ..."
    Invoke-KcJson -Method Post -Uri $adminBase -Body @{
        realm = $realm; enabled = $true; accessTokenLifespan = 300
    }
}

# --- 3. Confidential client --------------------------------------------------
# Two flows are enabled on one client so both federation subjects work:
#   - serviceAccounts (client_credentials): sub = the service-account UUID.
#   - directAccessGrants (password/ROPC):   sub = the test user's UUID, so a
#     token minted for the test user also carries the audience mapper below.
# The client secret is a deployment parameter (not Keycloak-generated) so it
# never has to appear in deployment outputs.
$clients = Get-KcList "$adminBase/$realm/clients?clientId=$clientId"
if ($clients.Count -eq 0) {
    Write-Host "Creating client '$clientId' ..."
    Invoke-KcJson -Method Post -Uri "$adminBase/$realm/clients" -Body @{
        clientId                  = $clientId
        protocol                  = 'openid-connect'
        publicClient              = $false
        serviceAccountsEnabled    = $true
        standardFlowEnabled       = $false
        implicitFlowEnabled       = $false
        directAccessGrantsEnabled = $true
        secret                    = $clientSecret
    }
    $clients = Get-KcList "$adminBase/$realm/clients?clientId=$clientId"
} else {
    Write-Host "Client '$clientId' already exists; ensuring secret and enabled flows match."
    Invoke-KcJson -Method Put -Uri "$adminBase/$realm/clients/$($clients[0].id)" -Body @{
        secret                    = $clientSecret
        serviceAccountsEnabled    = $true
        directAccessGrantsEnabled = $true
    }
}
$clientUuid = $clients[0].id

# --- Hardcoded audience mapper -> aud: api://AzureADTokenExchange -------------
$mapperName = 'azure-token-exchange-audience'
$mappers = Get-KcList "$adminBase/$realm/clients/$clientUuid/protocol-mappers/models"
if ($mappers | Where-Object { $_.name -eq $mapperName }) {
    Write-Host 'Audience mapper already present.'
} else {
    Write-Host "Adding audience mapper ($audience) ..."
    Invoke-KcJson -Method Post -Uri "$adminBase/$realm/clients/$clientUuid/protocol-mappers/models" -Body @{
        name           = $mapperName
        protocol       = 'openid-connect'
        protocolMapper = 'oidc-audience-mapper'
        config         = @{
            'included.custom.audience' = $audience
            'access.token.claim'       = 'true'
            'id.token.claim'           = 'false'
        }
    }
}

# The service-account user's UUID is the `sub` claim of client_credentials
# tokens; it becomes one federated identity credential's subject.
$subject = (Invoke-RestMethod -Method Get -Headers $headers `
    -Uri "$adminBase/$realm/clients/$clientUuid/service-account-user").id
Write-Host "Service-account subject: $subject"

# --- 4. Test user (idempotent) -----------------------------------------------
# A regular Keycloak user whose UUID is the `sub` of password-grant tokens;
# it becomes the second federated identity credential's subject.
$users = Get-KcList "$adminBase/$realm/users?username=$testUsername&exact=true"
if ($users.Count -eq 0) {
    Write-Host "Creating test user '$testUsername' ..."
    Invoke-KcJson -Method Post -Uri "$adminBase/$realm/users" -Body @{
        username      = $testUsername
        enabled       = $true
        emailVerified = $true
        email         = "$testUsername@example.invalid"
        firstName     = 'Test'
        lastName      = 'User'
    }
    $users = Get-KcList "$adminBase/$realm/users?username=$testUsername&exact=true"
} else {
    Write-Host "Test user '$testUsername' already exists."
}
$userSubject = $users[0].id
# Set (or reset) the password; this call is idempotent.
Invoke-KcJson -Method Put -Uri "$adminBase/$realm/users/$userSubject/reset-password" -Body @{
    type = 'password'; value = $testUserPassword; temporary = $false
}
Write-Host "Test user subject: $userSubject"

# --- 5a. Demo blob for the data-plane verification ---------------------------
Write-Host 'Uploading demo blob ...'
$blobFile = New-TemporaryFile
Set-Content -Path $blobFile -Value 'Hello from the Azure data plane, via your own OIDC provider!' -NoNewline
$storageContext = New-AzStorageContext -StorageAccountName $storageAccount -StorageAccountKey $storageKey
Set-AzStorageBlobContent -Container 'demo' -File $blobFile -Blob 'hello.txt' `
    -Context $storageContext -Force | Out-Null
Remove-Item $blobFile -Force
Write-Host 'Demo blob uploaded.'

# --- 5b. Re-enable the public admin lockdown (Caddy sidecar) ------------------
# The template deploys with CADDY_ADMIN_LOCKDOWN=false so this script can reach
# the admin REST API; flipping it back is the last step. The retry loop covers
# RBAC propagation on the deployer identity's fresh Contributor assignment.
# ARM has no "set one env var" verb, so this reads the container app, updates
# the caddy container's env in place, and writes the whole template back.
$apiVersion = '2024-03-01'
$appPath = "/subscriptions/$($env:SUBSCRIPTION_ID)/resourceGroups/$resourceGroup/providers/Microsoft.App/containerApps/$containerApp"
$locked = $false
foreach ($attempt in 1..10) {
    try {
        $getResponse = Invoke-AzRestMethod -Method GET -Path "$($appPath)?api-version=$apiVersion"
        if ($getResponse.StatusCode -ge 400) { throw "GET returned HTTP $($getResponse.StatusCode)" }
        $app = $getResponse.Content | ConvertFrom-Json

        $caddy = $app.properties.template.containers | Where-Object { $_.name -eq 'caddy' } | Select-Object -First 1
        if (-not $caddy) { throw "caddy container not found on '$containerApp'." }
        $lockVar = @($caddy.env | Write-Output) | Where-Object { $_.name -eq 'CADDY_ADMIN_LOCKDOWN' } | Select-Object -First 1
        if ($lockVar) {
            $lockVar.value = 'true'
        } else {
            $caddy.env = @($caddy.env | Write-Output) + @([pscustomobject]@{ name = 'CADDY_ADMIN_LOCKDOWN'; value = 'true' })
        }

        $payload = @{ properties = @{ template = $app.properties.template } } | ConvertTo-Json -Depth 100
        $patchResponse = Invoke-AzRestMethod -Method PATCH -Path "$($appPath)?api-version=$apiVersion" -Payload $payload
        if ($patchResponse.StatusCode -ge 400) { throw "PATCH returned HTTP $($patchResponse.StatusCode): $($patchResponse.Content)" }

        $locked = $true
        break
    } catch {
        Write-Host "containerapp update failed (RBAC propagation?): $($_.Exception.Message)"
        Write-Host 'Retrying in 30s ...'
        Start-Sleep -Seconds 30
    }
}
if (-not $locked) { throw 'Failed to enable the admin lockdown.' }
Write-Host 'Admin lockdown enabled.'

# --- 6. Outputs consumed by modules/federation.bicep -------------------------
$DeploymentScriptOutputs = @{
    subject     = $subject
    userSubject = $userSubject
}
