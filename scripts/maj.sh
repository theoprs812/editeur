#!/usr/bin/env bash
# Met l'Éditeur à jour depuis GitHub. Lancé tout seul à chaque ouverture de Claude Code (--silencieux).
RACINE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$RACINE" || exit 0
[[ -d .git ]] || exit 0
avant=$(git rev-parse HEAD 2>/dev/null)
git pull --ff-only --quiet 2>/dev/null || { [[ "$1" == "--silencieux" ]] || echo "Pas de connexion à GitHub, l'éditeur reste dans sa version actuelle."; exit 0; }
apres=$(git rev-parse HEAD 2>/dev/null)
if [[ "$avant" != "$apres" ]]; then
  for c in claude "$HOME/.local/bin/claude" "$HOME/.claude/local/claude"; do command -v "$c" >/dev/null 2>&1 && C="$c" && break; done
  if [[ -n "${C:-}" ]]; then
    "$C" plugin marketplace update editeur >/dev/null 2>&1
    "$C" plugin update editeur@editeur --scope user >/dev/null 2>&1
  fi
  [[ "$1" == "--silencieux" ]] || echo "Éditeur mis à jour. Ferme et rouvre Claude pour en profiter."
else
  [[ "$1" == "--silencieux" ]] || echo "L'éditeur est déjà à jour."
fi
