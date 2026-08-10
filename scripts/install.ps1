$ErrorActionPreference = "Stop"
$Target = ""
$DryRun = $false
for ($index = 0; $index -lt $args.Count; $index++) {
    switch ($args[$index]) {
        { $_ -in @("--target", "-Target") } {
            if ($index + 1 -ge $args.Count) {
                throw "--target requires codex, claude-code, both, or repo-local."
            }
            $index++
            $Target = $args[$index]
        }
        { $_ -in @("--dry-run", "-DryRun") } { $DryRun = $true }
        { $_ -in @("--help", "-h", "-Help") } {
            Write-Output "Usage: install.ps1 --target codex|claude-code|both|repo-local [--dry-run]"
            exit 0
        }
        default { throw "Unknown argument: $($args[$index])" }
    }
}
if ($Target -notin @("codex", "claude-code", "both", "repo-local")) {
    throw "--target must be codex, claude-code, both, or repo-local."
}

$sourceDir = Split-Path -Parent $PSScriptRoot
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$userBase = [Environment]::GetFolderPath("UserProfile")

function Get-PythonCommand {
    foreach ($name in @("python", "python3")) {
        $command = Get-Command $name -ErrorAction SilentlyContinue
        if ($command) {
            return $command.Source
        }
    }
    throw "Python 3 is required."
}

function Remove-InstallTree([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) {
        return
    }
    Get-ChildItem -LiteralPath $Path -Recurse -File -Force -ErrorAction SilentlyContinue |
        ForEach-Object { if ($_.IsReadOnly) { $_.IsReadOnly = $false } }
    Remove-Item -LiteralPath $Path -Recurse -Force
}

function Install-One([string]$Destination) {
    $backup = "$Destination.bak.$timestamp"
    Write-Output "target: $Destination"
    if (Test-Path -LiteralPath $Destination) {
        Write-Output "backup: $backup"
    }
    if ($DryRun) {
        Write-Output "dry-run: copy $sourceDir -> $Destination"
        return
    }

    $python = Get-PythonCommand
    $parent = Split-Path -Parent $Destination
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
    $hadBackup = $false
    if (Test-Path -LiteralPath $Destination) {
        Move-Item -LiteralPath $Destination -Destination $backup
        $hadBackup = $true
    }

    try {
        New-Item -ItemType Directory -Path $Destination | Out-Null
        Get-ChildItem -LiteralPath $sourceDir -Force |
            Where-Object { $_.Name -notin @(".git", ".agents") } |
            Copy-Item -Destination $Destination -Recurse -Force
        & $python -B (Join-Path $Destination "scripts\check_skill_integrity.py") $Destination
        if ($LASTEXITCODE -ne 0) {
            throw "Installed skill failed integrity validation."
        }
    }
    catch {
        Remove-InstallTree $Destination
        if ($hadBackup) {
            Move-Item -LiteralPath $backup -Destination $Destination
        }
        throw
    }
    Write-Output "installed: $Destination"
}

$destinations = switch ($Target) {
    "codex" { Join-Path $userBase ".agents\skills\HElicon" }
    "claude-code" { Join-Path $userBase ".claude\skills\HElicon" }
    "both" {
        Join-Path $userBase ".agents\skills\HElicon"
        Join-Path $userBase ".claude\skills\HElicon"
    }
    "repo-local" { Join-Path (Get-Location).Path ".agents\skills\HElicon" }
}

foreach ($destination in $destinations) {
    Install-One $destination
}
