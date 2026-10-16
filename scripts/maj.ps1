# Met l'Éditeur à jour depuis GitHub (Windows).
$Racine = Split-Path -Parent $PSScriptRoot
Set-Location $Racine
$avant = git rev-parse HEAD
git pull --ff-only --quiet
if ((git rev-parse HEAD) -ne $avant) {
  if (Get-Command claude -ErrorAction SilentlyContinue) { claude plugin marketplace update editeur | Out-Null; claude plugin update editeur@editeur --scope user | Out-Null }
  Write-Host "Éditeur mis à jour. Ferme et rouvre Claude pour en profiter."
} else { Write-Host "L'éditeur est déjà à jour." }
