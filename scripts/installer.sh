#!/usr/bin/env bash
# Installe l'Éditeur de Project Orange sur Mac. Chaque étape se saute si c'est déjà fait : on peut le relancer sans risque.
#
#   bash ~/.editeur/scripts/installer.sh
#
# 1. Homebrew (le seul moment où il faut le mot de passe du Mac)
# 2. ffmpeg (lire et fabriquer les vidéos), whisper (transcrire), yt-dlp (télécharger les reels)
# 3. Le modèle de transcription (~550 Mo, en dernier)
# 4. Le dossier ~/Editeur
# 5. L'Éditeur dans Claude Code

set -euo pipefail

RACINE="$(cd "$(dirname "$0")/.." && pwd)"
ELEVE="${EDITEUR_DOSSIER:-$HOME/Editeur}"
MODELES="$HOME/Library/Application Support/whisper.cpp/models"
MODELE="ggml-large-v3-turbo-q5_0.bin"
ETAT="$HOME/.config/editeur"

ok()    { printf '  \033[32m✓\033[0m %s\n' "$1"; }
etape() { printf '\n\033[1m%s\033[0m\n' "$1"; }
a()     { command -v "$1" >/dev/null 2>&1; }

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Ce script est pour Mac. Sur Windows : scripts/installer.ps1"; exit 1
fi

# 1. Homebrew --------------------------------------------------------------
etape "1/5 Homebrew (le magasin d'outils du Mac)"
brew_env() { for b in /opt/homebrew/bin/brew /usr/local/bin/brew; do [[ -x "$b" ]] && { eval "$("$b" shellenv)"; return 0; }; done; return 1; }
a brew || brew_env || true
if ! a brew; then
  INSTALL_BREW='/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
  if [[ -t 0 ]]; then
    eval "$INSTALL_BREW"
  else
    # Dans Claude Code il n'y a pas de clavier : on ouvre une fenêtre Terminal pour le mot de passe.
    mkdir -p "$ETAT" && rm -f "$ETAT/.brew-ok"
    osascript -e 'tell application "Terminal" to activate' \
      -e "tell application \"Terminal\" to do script \"$(printf '%s' "$INSTALL_BREW" | sed 's/\\/\\\\/g; s/"/\\"/g'); touch '$ETAT/.brew-ok'; echo; echo 'C est fini. Tu peux fermer cette fenetre et revenir dans Claude.'\"" >/dev/null
    echo "  Une fenêtre Terminal vient de s'ouvrir."
    echo "  Tape le mot de passe de ton Mac dedans (rien ne s'affiche quand tu tapes, c'est normal), puis Entrée."
    echo "  S'il demande d'appuyer sur Entrée encore une fois, fais-le. J'attends que ce soit fini..."
    for _ in $(seq 1 180); do [[ -f "$ETAT/.brew-ok" ]] && break; sleep 10; done
  fi
  brew_env || { echo "Homebrew n'a pas fini de s'installer. Relance l'installation quand la fenêtre a terminé."; exit 1; }
fi
ok "Homebrew"

# 2. Les outils ---------------------------------------------------------------
etape "2/5 Les outils vidéo"
a python3 || brew install python
a git || brew install git
if a ffmpeg && ffmpeg -hide_banner -filters 2>/dev/null | grep -q " subtitles "; then ok "ffmpeg"; else brew install ffmpeg; ok "ffmpeg"; fi
if a whisper-cli; then ok "whisper"; else brew install whisper-cpp; ok "whisper"; fi
if a yt-dlp; then ok "yt-dlp"; brew upgrade yt-dlp >/dev/null 2>&1 || true; else brew install yt-dlp; ok "yt-dlp"; fi

# 3. Le dossier de l'élève -------------------------------------------------------
etape "3/5 Ton dossier Editeur"
mkdir -p "$ELEVE"/{ma-da/polices,references,musiques,videos}
ok "$ELEVE"

# 4. L'Éditeur dans Claude Code ----------------------------------------------------
etape "4/5 L'Éditeur dans Claude Code"
# Les applis de bureau embarquent leur propre claude, souvent hors du PATH.
sur_path() { [[ -x "$1" ]] && PATH="$(dirname "$1"):$PATH"; }
a claude || for c in "$HOME/.local/bin/claude" "$HOME/.claude/local/claude" \
  "$(ls -t "$HOME/Library/Application Support/Claude/claude-code"/*/*/claude.app/Contents/MacOS/claude 2>/dev/null | head -1)"; do
  sur_path "$c" && break
done
if a claude; then
  if claude plugin marketplace list 2>/dev/null | grep -q "editeur"; then
    claude plugin marketplace update editeur >/dev/null 2>&1 || true
  else
    claude plugin marketplace add "$RACINE" >/dev/null
  fi
  if claude plugin list 2>/dev/null | grep -q "editeur@editeur"; then
    claude plugin update editeur@editeur --scope user >/dev/null 2>&1 || true
  else
    claude plugin install editeur@editeur --scope user >/dev/null
  fi
  ok "Éditeur branché dans Claude Code"
else
  echo "  Je ne trouve pas Claude Code sur ce Mac. Installe l'app Claude (claude.ai/download), puis relance."
fi

# 5. Le modèle de transcription (le plus gros, en dernier) -------------------------------------
etape "5/5 Le modèle de transcription (~550 Mo, quelques minutes)"
if [[ -f "$MODELES/$MODELE" || -f "$MODELES/ggml-large-v3-turbo.bin" ]]; then
  ok "modèle"
else
  mkdir -p "$MODELES"
  curl -fL --progress-bar -o "$MODELES/$MODELE.part" "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/$MODELE"
  mv "$MODELES/$MODELE.part" "$MODELES/$MODELE"
  ok "modèle"
fi

echo
echo "C'EST INSTALLÉ."
echo "Ferme complètement l'app Claude (Cmd+Q), rouvre-la, ouvre le dossier Editeur dans l'onglet Code, et écris : salut l'éditeur"
