#!/usr/bin/env bash
# Vérifie que tout est là, sans rien changer. Code de sortie 0 = tout est prêt.
for b in /opt/homebrew/bin /usr/local/bin "$HOME/.local/bin"; do [[ -d "$b" ]] && PATH="$b:$PATH"; done
manque=0
ok()   { printf '  \033[32m✓\033[0m %s\n' "$1"; }
non()  { printf '  \033[33m•\033[0m %s manque\n' "$1"; manque=1; }
a()    { command -v "$1" >/dev/null 2>&1; }
a python3 && ok "python3" || non "python3"
ff_ok() { for f in /opt/homebrew/opt/ffmpeg-full/bin/ffmpeg /usr/local/opt/ffmpeg-full/bin/ffmpeg "$(command -v ffmpeg)" "$HOME/.local/bin/ffmpeg"; do
  [[ -x "$f" ]] && "$f" -hide_banner -filters 2>/dev/null | grep -q " subtitles " && "$f" -hide_banner -filters 2>/dev/null | grep -q " zscale " && return 0; done; return 1; }
ff_ok && ok "ffmpeg" || non "ffmpeg (complet)"
a whisper-cli && ok "whisper" || non "whisper"
M="$HOME/Library/Application Support/whisper.cpp/models"
[[ -f "$M/ggml-large-v3-turbo-q5_0.bin" || -f "$M/ggml-large-v3-turbo.bin" ]] && ok "modèle de transcription" || non "modèle de transcription"
a yt-dlp && ok "yt-dlp" || non "yt-dlp"
python3 -c "import PIL" 2>/dev/null && ok "Pillow" || non "Pillow"
ls "${EDITEUR_DOSSIER:-$HOME/Editeur}/ma-da/polices/"Instagram_Sans-* >/dev/null 2>&1 && ok "polices" || non "polices"
[[ -d "${EDITEUR_DOSSIER:-$HOME/Editeur}" ]] && ok "dossier Editeur" || non "dossier Editeur"
exit $manque
