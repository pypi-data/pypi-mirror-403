# CVE Sentinel - Claude Code SessionStart Hook (Windows PowerShell)
# This script is triggered when Claude Code starts a new session.
# It initializes CVE scanning in the background to avoid blocking the session.

$ErrorActionPreference = "Stop"

# Configuration
$OutputDir = ".cve-sentinel"
$StatusFile = "$OutputDir\status.json"
$LogFile = "$OutputDir\scanner.log"
$ConfigFile = ".cve-sentinel.yaml"
$AltConfigFile = ".cve-sentinel.yml"

function Test-AutoScanEnabled {
    $configPath = $null

    if (Test-Path $ConfigFile) {
        $configPath = $ConfigFile
    } elseif (Test-Path $AltConfigFile) {
        $configPath = $AltConfigFile
    } else {
        # No config file, use default (enabled)
        return $true
    }

    # Check if auto_scan_on_startup is explicitly set to false
    $content = Get-Content $configPath -Raw -ErrorAction SilentlyContinue
    if ($content -match "auto_scan_on_startup:\s*false") {
        return $false
    }

    return $true
}

function Get-ISOTimestamp {
    return (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
}

function Write-StatusJson {
    param(
        [string]$Status,
        [string]$ErrorMessage = ""
    )

    $timestamp = Get-ISOTimestamp

    if ($ErrorMessage) {
        $json = @{
            status = $Status
            started_at = $timestamp
            error = $ErrorMessage
        } | ConvertTo-Json
    } else {
        $json = @{
            status = $Status
            started_at = $timestamp
        } | ConvertTo-Json
    }

    Set-Content -Path $StatusFile -Value $json -Encoding UTF8
}

function Main {
    try {
        # Check if auto scan is enabled
        if (-not (Test-AutoScanEnabled)) {
            Write-Host "CVE Sentinel: Auto-scan disabled in configuration"
            exit 0
        }

        # Create output directory
        if (-not (Test-Path $OutputDir)) {
            New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
        }

        # Initialize status.json with "scanning" state
        Write-StatusJson -Status "scanning"

        # Check if Python is available
        $pythonCmd = $null

        if (Get-Command "python" -ErrorAction SilentlyContinue) {
            $pythonCmd = "python"
        } elseif (Get-Command "python3" -ErrorAction SilentlyContinue) {
            $pythonCmd = "python3"
        } elseif (Get-Command "py" -ErrorAction SilentlyContinue) {
            $pythonCmd = "py"
        } else {
            Write-StatusJson -Status "error" -ErrorMessage "Python not found"
            exit 0  # Exit 0 to not block Claude Code
        }

        # Check if cve_sentinel module is installed
        $moduleCheck = & $pythonCmd -c "import cve_sentinel" 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-StatusJson -Status "error" -ErrorMessage "cve_sentinel module not installed"
            exit 0  # Exit 0 to not block Claude Code
        }

        # Start the scanner in background
        $scriptBlock = {
            param($pythonCmd, $logFile)
            & $pythonCmd -m cve_sentinel --path . *> $logFile
        }

        $job = Start-Job -ScriptBlock $scriptBlock -ArgumentList $pythonCmd, $LogFile

        # Store the job ID
        Set-Content -Path "$OutputDir\scanner.jobid" -Value $job.Id -Encoding UTF8

        # Exit immediately (Hook timeout avoidance)
        # The background job will update status.json when complete
        exit 0

    } catch {
        # Handle any unexpected errors
        try {
            Write-StatusJson -Status "error" -ErrorMessage $_.Exception.Message
        } catch {
            # Ignore errors writing status
        }
        exit 0  # Exit 0 to not block Claude Code
    }
}

Main
