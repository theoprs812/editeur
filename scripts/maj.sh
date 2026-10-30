#!/usr/bin/env bash
# Met le Studio à jour depuis GitHub. Lancé tout seul à chaque ouverture de Claude Code (--silencieux).
#
#   bash ~/.editeur/scripts/maj.sh [--silencieux]
#   bash ~/.editeur/scripts/maj.sh --depot      transforme seulement ~/.editeur en vrai clone git
#                                               (Studio téléchargé en archive zip sur un Mac sans git)
RACINE="$(cd "$(dirname "$0")/.." && pwd)"
DEPOT="https://github.com/theoprs812/editeur.git"

SILENCIEUX=0; DEPOT_SEUL=0
for a in "$@"; do
  [[ "$a" == "--silencieux" ]] && SILENCIEUX=1
  [[ "$a" == "--depot" ]] && DEPOT_SEUL=1
done
dire() { [[ $SILENCIEUX == 1 ]] || echo "$1"; }

# Les applis de bureau lancent les hooks avec un PATH minimal.
for b in /opt/homebrew/bin /usr/local/bin "$HOME/.local/bin"; do [[ -d "$b" ]] && PATH="$b:$PATH"; done
cd "$RACINE" || exit 0

git_ok() {
  # Mac sans outils Apple : /usr/bin/git ouvre une fenêtre d'installation à chaque appel, on ne le touche pas.
  if [[ "$(uname -s)" == "Darwin" ]] && ! xcode-select -p >/dev/null 2>&1; then
    [[ -x /opt/homebrew/bin/git || -x /usr/local/bin/git ]] || return 1
  fi
  git --version >/dev/null 2>&1
}

depot_git() {
  [[ -d .git ]] && return 0
  git_ok || return 1
  git init -q && git symbolic-ref HEAD refs/heads/main
  git remote add origin "$DEPOT" 2>/dev/null || git remote set-url origin "$DEPOT"
  if ! git fetch -q origin main 2>/dev/null; then rm -rf .git; return 1; fi
  git reset -q --hard origin/main && git branch -q --set-upstream-to=origin/main main 2>/dev/null
  dire "Mises à jour branchées (le dossier du studio suit maintenant GitHub)."
}

if [[ $DEPOT_SEUL == 1 ]]; then
  depot_git || dire "Je n'ai pas pu brancher les mises à jour (git ou connexion manquants). Elles se brancheront à la prochaine ouverture de Claude."
  exit 0
fi

if depot_git; then
  avant=$(git rev-parse HEAD 2>/dev/null)
  if git pull --ff-only --quiet 2>/dev/null; then
    apres=$(git rev-parse HEAD 2>/dev/null)
    if [[ "$avant" != "$apres" ]]; then
      for c in claude "$HOME/.local/bin/claude" "$HOME/.claude/local/claude"; do command -v "$c" >/dev/null 2>&1 && C="$c" && break; done
      if [[ -n "${C:-}" ]]; then
        "$C" plugin marketplace update editeur >/dev/null 2>&1
        "$C" plugin update editeur@editeur --scope user >/dev/null 2>&1
      fi
      dire "Studio mis à jour. Ferme et rouvre Claude pour en profiter."
    else
      dire "Le studio est déjà à jour."
    fi
  else
    dire "Pas de connexion à GitHub, le studio reste dans sa version actuelle."
  fi
else
  dire "Mise à jour impossible pour l'instant (git manque) : relance bash ~/.editeur/scripts/installer.sh."
fi

# la banque de musiques : seulement les nouveaux morceaux
PY="$(command -v python3 || command -v python)"
[[ "$PY" == /usr/bin/python3 ]] && ! xcode-select -p >/dev/null 2>&1 && PY=""   # même piège que git sur un Mac sans outils Apple
if [[ -n "$PY" ]]; then
  if [[ $SILENCIEUX == 1 ]]; then "$PY" "$RACINE/outils/musiques.py" --sync --silencieux >/dev/null 2>&1
  else "$PY" "$RACINE/outils/musiques.py" --sync | tail -1; fi
fi
exit 0
