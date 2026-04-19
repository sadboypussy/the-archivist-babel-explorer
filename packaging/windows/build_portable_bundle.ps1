<#
.SYNOPSIS
    Build a portable Windows folder: embeddable Python + pip deps + app copy (no system Python required on target).

.DESCRIPTION
    Output: repo\dist\<OutputName>\ with python\, app\, Run-Archivist.bat
    See packaging\windows\README.md and DISTRIBUTION.md (repo root).
#>
[CmdletBinding()]
param(
    [string] $PythonVersion = "3.11.9",
    [string] $OutputName = "ArchivistPortable",
    [switch] $SkipPipInstall,
    [switch] $DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
    $here = $PSScriptRoot
    $packaging = Split-Path -Parent $here
    return (Split-Path -Parent $packaging)
}

$RepoRoot = Resolve-RepoRoot
$DistRoot = Join-Path $RepoRoot "dist"
$BundleRoot = Join-Path $DistRoot $OutputName
$PythonDir = Join-Path $BundleRoot "python"
$AppDir = Join-Path $BundleRoot "app"
$EmbedZipName = "python-$PythonVersion-embed-amd64.zip"
$EmbedUrl = "https://www.python.org/ftp/python/$PythonVersion/$EmbedZipName"
$GetPipUrl = "https://bootstrap.pypa.io/get-pip.py"

Write-Host "Repo:        $RepoRoot"
Write-Host "Bundle:      $BundleRoot"
if ($DryRun) { exit 0 }

New-Item -ItemType Directory -Force -Path $DistRoot | Out-Null
if (Test-Path $BundleRoot) {
    Remove-Item -Recurse -Force $BundleRoot
}
New-Item -ItemType Directory -Force -Path $BundleRoot | Out-Null
New-Item -ItemType Directory -Force -Path $AppDir | Out-Null

# --- Copy application (exclude heavy / dev-only) ---
$roboArgs = @(
    "$RepoRoot", "$AppDir",
    "/E",
    "/NFL", "/NDL", "/NJH", "/NJS", "/NC", "/NS", "/NP",
    "/XD", ".git", ".venv", "venv", "__pycache__", "tests", ".cursor", "dist", "models\.cache",
    "/XF", ".gitignore"
)
& robocopy @roboArgs | Out-Null
if ($LASTEXITCODE -ge 8) {
    throw "robocopy failed with exit code $LASTEXITCODE"
}

# Drop nested dist if robocopy recreated anything (should be excluded)
$nestedDist = Join-Path $AppDir "dist"
if (Test-Path $nestedDist) {
    Remove-Item -Recurse -Force $nestedDist
}

# --- Embeddable Python ---
New-Item -ItemType Directory -Force -Path $PythonDir | Out-Null
$zipPath = Join-Path $DistRoot $EmbedZipName
if (-not (Test-Path $zipPath)) {
    Write-Host "Downloading $EmbedUrl ..."
    Invoke-WebRequest -Uri $EmbedUrl -OutFile $zipPath -UseBasicParsing
}
Expand-Archive -Path $zipPath -DestinationPath $PythonDir -Force

# Enable site-packages / pip: uncomment or add 'import site' in python311._pth
$pthFiles = Get-ChildItem -Path $PythonDir -Filter "python*._pth" | Sort-Object Name
if (-not $pthFiles) { throw "No python*._pth found in embeddable layout." }
$pth = $pthFiles[0].FullName
$pthContent = Get-Content -Raw -Path $pth
$pthContent = $pthContent -replace "#\s*import site", "import site"
if ($pthContent -notmatch "import site") {
    $pthContent = $pthContent.TrimEnd() + "`r`nimport site`r`n"
}
Set-Content -Path $pth -Value $pthContent -NoNewline

$pyExe = Join-Path $PythonDir "python.exe"
if (-not (Test-Path $pyExe)) { throw "Missing $pyExe" }

# --- get-pip ---
$getPip = Join-Path $DistRoot "get-pip.py"
if (-not (Test-Path $getPip)) {
    Invoke-WebRequest -Uri $GetPipUrl -OutFile $getPip -UseBasicParsing
}
& $pyExe $getPip --no-warn-script-location | Write-Host

if (-not $SkipPipInstall) {
    $req1 = Join-Path $RepoRoot "requirements.txt"
    $req2 = Join-Path $RepoRoot "requirements-llm.txt"
    if (-not (Test-Path $req1)) { throw "Missing requirements.txt" }
    if (-not (Test-Path $req2)) { throw "Missing requirements-llm.txt" }
    & $pyExe -m pip install --upgrade pip | Write-Host
    & $pyExe -m pip install -r $req1 -r $req2 | Write-Host
}

# --- Launcher ---
$bat = @"
@echo off
setlocal
cd /d "%~dp0app"
set "PATH=%~dp0python;%~dp0python\Scripts;%PATH%"
if not exist "%~dp0python\python.exe" (
  echo [Archivist] python.exe introuvable dans le dossier portable.
  exit /b 1
)
"%~dp0python\python.exe" run_scanner.py %*
exit /b %ERRORLEVEL%
"@
$batPath = Join-Path $BundleRoot "Run-Archivist.bat"
Set-Content -Path $batPath -Value $bat -Encoding ASCII

$readme = @"
Archivist — bundle portable (Windows)
=====================================

0. Première fois : vérifier l'environnement (dépendances, GPU, GGUF) :

   cd app
   ..\python\python.exe scripts\first_run.py

   Option téléchargement du modèle (~5 Go) : ajoutez --download-model

1. Placez le fichier GGUF recommandé dans app\models\ (voir app\models\README.txt)
   ou utilisez --llama-server avec llama-server / LM Studio (GPU).

2. Double-cliquez sur Run-Archivist.bat ou depuis une invite :

   Run-Archivist.bat --pages 500 --mock-llm

3. GPU natif (Windows + NVIDIA) : depuis ce dossier, en ligne de commande :

   cd app
   ..\python\python.exe scripts\install_llama_cuda_windows.py

Documentation complète : voir le fichier DISTRIBUTION.md à la racine du dépôt source.
"@
Set-Content -Path (Join-Path $BundleRoot "LISEZMOI.txt") -Value $readme -Encoding UTF8

Write-Host ""
Write-Host "Done. Bundle: $BundleRoot"
Write-Host "Run: $batPath"
