# L'Éditeur Project Orange

Tu filmes, Claude monte. Un plugin Claude Code pour les élèves de Project Orange : coupe des blancs et des ratés,
meilleure prise gardée, texte du début, sous-titres animés, b-roll trié et posé tout seul, musique, dans la DA de l'élève.

- Formats : yap, talking head, vlog, one shot, 10 shots, coupe propre (règles tirées des cours Project Orange).
- Ta DA recopiée depuis un de tes reels (Template 1, 2, 3…).
- Reels Instagram, TikTok, YouTube Shorts téléchargés et intégrés (yt-dlp).
- Tout tourne sur ton ordi : transcription locale (Whisper), montage local (ffmpeg).

## Installer

Le tuto illustré : `tuto/index.html`. En bref, dans l'onglet Code de l'app Claude, colle :

> Installe l'Éditeur Project Orange. 1. Télécharge https://github.com/theoprs812/editeur dans le dossier ~/.editeur (git clone). 2. Lance : bash ~/.editeur/scripts/installer.sh 3. Suis ce qu'il affiche.

Puis rouvre Claude dans le dossier `~/Editeur` et écris « salut l'éditeur ».

## Ce qu'il y a dedans

| Dossier | Rôle |
|---|---|
| `skills/` | `editeur` (point d'entrée, guidage pas à pas), un dossier par format, `ma-da`, `instagram` |
| `outils/` | `transcrire.py`, `couper.py`, `planche.py`, `rendu.py`, `instagram.py`, `da.py`, `police.py` |
| `scripts/` | installation, vérification, mise à jour (Mac `.sh`, Windows `.ps1`) |
| `polices/` | TikTok Sans (licence SIL OFL) |

Structure et logique reprises de l'AI Video Editor de Cut30 (Colin Landforce), avec son accord.
