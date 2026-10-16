#!/usr/bin/env bash
# Vérifie que tout est là, sans rien changer. Code de sortie 0 = tout est prêt.
for b in /opt/homebrew/bin /usr/local/bin "$HOME/.local/bin"; do [[ -d "$b" ]] && PATH="$b:$PATH"; done
manque=0
ok()   { printf '  \033[32m✓\033[0m %s\n' "$1"; }
non()  { printf '  \033[33m•\033[0m %s manque\n' "$1"; manque=1; }
a()    { command -v "$1" >/dev/null 2>&1; }
a python3 && ok "python3" || non "python3"
if a ffmpeg && ffmpeg -hide_banner -filters 2>/dev/null | grep -q " subtitles "; then ok "ffmpeg"; else non "ffmpeg"; fi
a whisper-cli && ok "whisper" || non "whisper"
M="$HOME/Library/Application Support/whisper.cpp/models"
[[ -f "$M/ggml-large-v3-turbo-q5_0.bin" || -f "$M/ggml-large-v3-turbo.bin" ]] && ok "modèle de transcription" || non "modèle de transcription"
a yt-dlp && ok "yt-dlp" || non "yt-dlp"
[[ -d "${EDITEUR_DOSSIER:-$HOME/Editeur}" ]] && ok "dossier Editeur" || non "dossier Editeur"
exit $manque
