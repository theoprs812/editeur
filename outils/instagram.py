#!/usr/bin/env python3
"""Télécharge un reel Instagram (ou TikTok, YouTube Shorts…) avec yt-dlp.

    python3 instagram.py <lien> [<lien> ...] [--dossier ~/Editeur/references] [--audio]

Chaque reel arrive dans <dossier>/<auteur>-<id>/ : video.mp4 + legende.txt (la légende et les chiffres publics).
--audio : garde aussi le son seul en .m4a (pour une musique).
Si Instagram demande d'être connecté, on réessaie avec la session du navigateur (Chrome, puis Safari, Firefox, Edge).
"""
import json, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from commun import outil, DOSSIER_ELEVE

NAVIGATEURS = ["chrome", "safari", "firefox", "edge", "brave"]


def telecharger(lien, dossier, audio=False):
    ytdlp = outil("yt-dlp")
    if not ytdlp:
        sys.exit("yt-dlp manque. Dis à Claude : « installe mon studio ».")
    dossier.mkdir(parents=True, exist_ok=True)
    modele = str(dossier / "%(channel,uploader_id,uploader)s-%(id)s" / "video.%(ext)s")
    base = [ytdlp, "--no-playlist", "--no-warnings", "-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b",
            "--merge-output-format", "mp4", "--write-info-json", "-o", modele, "--print", "after_move:filepath"]
    essais = [[]] + [["--cookies-from-browser", n] for n in NAVIGATEURS]
    derniere = ""
    for extra in essais:
        r = subprocess.run(base + extra + [lien], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            video = Path(r.stdout.strip().splitlines()[-1])
            break
        derniere = (r.stderr or "").strip().splitlines()[-1:] or [""]
        derniere = derniere[0]
    else:
        print(f"✗ {lien} : impossible de le télécharger ({derniere[:160]})")
        return None
    info_p = next(video.parent.glob("*.info.json"), None)
    info = json.loads(info_p.read_text(encoding="utf-8")) if info_p else {}
    legende = [f"Lien : {lien}", f"Compte : {info.get('uploader') or info.get('channel') or '?'}",
               f"Date : {info.get('upload_date', '?')}", f"Durée : {info.get('duration', '?')} s",
               f"Vues : {info.get('view_count', '?')} · J'aime : {info.get('like_count', '?')} · Commentaires : {info.get('comment_count', '?')}",
               "", info.get("description") or ""]
    (video.parent / "legende.txt").write_text("\n".join(map(str, legende)) + "\n", encoding="utf-8")
    if info_p:
        info_p.unlink()
    if audio:
        ff = outil("ffmpeg")
        subprocess.run([ff, "-y", "-v", "error", "-i", str(video), "-vn", "-c:a", "aac", "-b:a", "192k", str(video.with_suffix(".m4a"))])
    print(f"✓ {video}")
    return video


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    dossier = DOSSIER_ELEVE / "references"
    if "--dossier" in args:
        i = args.index("--dossier")
        dossier = Path(args[i + 1]).expanduser()
        del args[i:i + 2]
    audio = "--audio" in args
    for lien in [a for a in args if not a.startswith("--")]:
        telecharger(lien, dossier, audio)


if __name__ == "__main__":
    main()
