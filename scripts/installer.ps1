# Installe le Studio de Project Orange sur Windows 10/11. On peut le relancer sans risque.
#   powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.editeur\scripts\installer.ps1"
$ErrorActionPreference = "Continue"
$Racine = Split-Path -Parent $PSScriptRoot
$Eleve = if ($env:EDITEUR_DOSSIER) { $env:EDITEUR_DOSSIER } else { Join-Path $env:USERPROFILE "Editeur" }
function Ok($t) { Write-Host "  OK  $t" -ForegroundColor Green }
function Etape($t) { Write-Host "`n$t" -ForegroundColor White }
function A($c) { [bool](Get-Command $c -ErrorAction SilentlyContinue) }
function Rafraichir { $env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User") }
function Winget($id) { winget install --id $id -e --silent --accept-package-agreements --accept-source-agreements | Out-Null; Rafraichir }

if (-not (A winget)) { Write-Host "winget manque : mets Windows à jour (Microsoft Store > App Installer), puis relance."; exit 1 }

Etape "1/4 Les outils"
if (-not (A git)) { Winget "Git.Git" }; Ok "git"
if (-not ((A py) -or (A python))) { Winget "Python.Python.3.12" }; Ok "python"
if (-not (A ffmpeg)) { Winget "Gyan.FFmpeg" }; Ok "ffmpeg"
if (-not (A yt-dlp)) { Winget "yt-dlp.yt-dlp" }; Ok "yt-dlp"
$Py = if (A py) { "py" } else { "python" }
Etape "2/4 La transcription (faster-whisper, le modèle se télécharge à la première vidéo)"
& $Py -m pip install --quiet --upgrade faster-whisper pillow pycapcut gdown | Out-Null; Ok "faster-whisper + Pillow + pycapcut + gdown"

Etape "3/4 Ton dossier Editeur"
foreach ($d in "ma-da\polices","references","musiques","videos","b-roll\entrainement","b-roll\lifestyle","b-roll\podcast","b-roll\bureau") { New-Item -ItemType Directory -Force -Path (Join-Path $Eleve $d) | Out-Null }
Ok $Eleve
& $Py (Join-Path $Racine "outils\police.py") --pack | Select-Object -Last 1

Etape "4/4 Le Studio dans Claude Code"
if (A claude) {
  if (-not ((claude plugin marketplace list 2>$null) -match "editeur")) { claude plugin marketplace add $Racine | Out-Null } else { claude plugin marketplace update editeur | Out-Null }
  if (-not ((claude plugin list 2>$null) -match "editeur@editeur")) { claude plugin install editeur@editeur --scope user | Out-Null } else { claude plugin update editeur@editeur --scope user | Out-Null }
  Ok "Studio branché dans Claude Code"
} else { Write-Host "  Claude Code introuvable : installe l'app Claude (claude.ai/download), puis relance." }

Write-Host "`nC'EST INSTALLÉ. Ferme complètement l'app Claude, rouvre-la, ouvre le dossier Editeur dans l'onglet Code, et écris : salut le studio"
