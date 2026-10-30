# Met le Studio à jour depuis GitHub (Windows). Lancé tout seul à chaque ouverture de Claude Code :
# le hook passe par Git Bash (scripts/maj.sh), qui délègue ici.
#   powershell -NoProfile -ExecutionPolicy Bypass -File maj.ps1 [--silencieux]
#   ... maj.ps1 --depot      transforme seulement le dossier du studio en vrai clone git (Studio téléchargé en zip)
$Silencieux = ($args -contains "--silencieux") -or ($args -contains "-silencieux")
$DepotSeul = $args -contains "--depot"
$Racine = Split-Path -Parent $PSScriptRoot
$Depot = "https://github.com/theoprs812/editeur.git"
function Dire($t) { if (-not $Silencieux) { Write-Host $t } }
function A($c) { [bool](Get-Command $c -ErrorAction SilentlyContinue) }
Set-Location $Racine
if (-not (A git)) { foreach ($g in "$env:ProgramFiles\Git\cmd", "$env:LOCALAPPDATA\Programs\Git\cmd") { if (Test-Path "$g\git.exe") { $env:Path = "$g;$env:Path" } } }

function DepotGit {
  if (Test-Path (Join-Path $Racine ".git")) { return $true }
  if (-not (A git)) { return $false }
  git init -q 2>$null | Out-Null
  git symbolic-ref HEAD refs/heads/main 2>$null | Out-Null
  git remote add origin $Depot 2>$null | Out-Null
  git fetch -q origin main 2>$null | Out-Null
  if ($LASTEXITCODE -ne 0) { Remove-Item -Recurse -Force (Join-Path $Racine ".git"); return $false }
  git reset -q --hard origin/main 2>$null | Out-Null
  git branch -q --set-upstream-to=origin/main main 2>$null | Out-Null
  Dire "Mises à jour branchées (le dossier du studio suit maintenant GitHub)."
  return $true
}

if ($DepotSeul) {
  if (-not (DepotGit)) { Dire "Je n'ai pas pu brancher les mises à jour (git ou connexion manquants). Elles se brancheront à la prochaine ouverture de Claude." }
  exit 0
}

if (DepotGit) {
  $avant = git rev-parse HEAD
  git pull --ff-only --quiet 2>$null | Out-Null
  if ($LASTEXITCODE -ne 0) { Dire "Pas de connexion à GitHub, le studio reste dans sa version actuelle." }
  elseif ((git rev-parse HEAD) -ne $avant) {
    if (A claude) { claude plugin marketplace update editeur 2>$null | Out-Null; claude plugin update editeur@editeur --scope user 2>$null | Out-Null }
    Dire "Studio mis à jour. Ferme et rouvre Claude pour en profiter."
  } else { Dire "Le studio est déjà à jour." }
} else { Dire "Mise à jour impossible pour l'instant (git manque) : relance installer.ps1." }

# la banque de musiques : seulement les nouveaux morceaux
$Musiques = Join-Path $Racine "outils\musiques.py"
$env:PYTHONUTF8 = "1"
if ($Silencieux) {
  if (A py) { & py -3 $Musiques --sync --silencieux *> $null } elseif (A python) { & python $Musiques --sync --silencieux *> $null }
} else {
  if (A py) { & py -3 $Musiques --sync | Select-Object -Last 1 } elseif (A python) { & python $Musiques --sync | Select-Object -Last 1 }
}
exit 0
