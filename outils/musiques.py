#!/usr/bin/env python3
"""La banque de musiques du Studio : celle de Théo, synchronisée depuis un dossier Google Drive partagé par lien.

    python3 musiques.py --lien <lien du dossier Drive>   enregistre le lien (donné sur Slack) puis synchronise
    python3 musiques.py --sync [--silencieux]             récupère seulement les nouveaux morceaux
    python3 musiques.py --liste                           les musiques disponibles, par style

Les morceaux arrivent dans ~/Editeur/musiques/<style>/ (chill, hard, reflexion, emotion, suspense, inspirant,
sigma, phonk, youtube-libre). Le lien n'est jamais écrit dans le dépôt public : il reste sur l'ordinateur de l'élève.
Les morceaux libres de droits fournis avec le Studio (musiques-libres/) sont copiés aussi.
"""
import json, shutil, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from commun import DOSSIER_ELEVE, EDITEUR, AUDIO_EXT

MUSIQUES = DOSSIER_ELEVE / "musiques"
CONFIG = DOSSIER_ELEVE / ".config" / "musiques.json"
LIBRES = EDITEUR / "musiques-libres"


def dire(txt, silencieux):
    if not silencieux:
        print(txt, flush=True)


def copier_libres():
    for f in LIBRES.rglob("*") if LIBRES.exists() else []:
        if f.suffix.lower() in AUDIO_EXT:
            dst = MUSIQUES / f.relative_to(LIBRES)
            if not dst.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dst)


def synchroniser(silencieux=False):
    MUSIQUES.mkdir(parents=True, exist_ok=True)
    copier_libres()
    if not CONFIG.exists():
        dire("Pas encore de lien vers la banque de musiques : demande-le sur Slack (#general-p90).", silencieux)
        return 0
    lien = json.loads(CONFIG.read_text(encoding="utf-8"))["lien"]
    try:
        import gdown
    except ImportError:
        dire("gdown manque. Dis à Claude : « installe mon studio ».", silencieux)
        return 0
    with tempfile.TemporaryDirectory() as tmp:
        try:
            fichiers = gdown.download_folder(url=lien, output=tmp, quiet=True, use_cookies=False,
                                             remaining_ok=True, skip_download=True)
        except Exception as e:
            dire(f"Banque de musiques injoignable pour l'instant ({str(e)[:120]}).", silencieux)
            return 0
        nouveaux = 0
        for f in fichiers or []:
            rel = Path(f.local_path).relative_to(tmp)
            if len(rel.parts) > 1 and rel.parts[0].lower().startswith("studio"):
                rel = Path(*rel.parts[1:])   # on enlève le dossier racine « Studio - Musiques »
            if rel.suffix.lower() not in AUDIO_EXT:
                continue
            dst = MUSIQUES / rel
            if dst.exists():
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            try:
                gdown.download(id=f.id, output=str(dst), quiet=True, use_cookies=False)
                nouveaux += 1
                dire(f"  + {rel}", silencieux)
            except Exception:
                if dst.exists():
                    dst.unlink()
    dire(f"✓ Banque de musiques à jour ({nouveaux} nouveau{'x' if nouveaux > 1 else ''} morceau{'x' if nouveaux > 1 else ''}).", silencieux)
    return nouveaux


def liste():
    if not MUSIQUES.exists():
        print("(aucune musique)")
        return
    for d in sorted(p for p in MUSIQUES.iterdir() if p.is_dir()):
        morceaux = sorted(f.stem for f in d.iterdir() if f.suffix.lower() in AUDIO_EXT)
        if morceaux:
            print(f"{d.name} ({len(morceaux)}) : " + " · ".join(morceaux))


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == "--lien" and len(a) > 1:
        CONFIG.parent.mkdir(parents=True, exist_ok=True)
        CONFIG.write_text(json.dumps({"lien": a[1]}), encoding="utf-8")
        synchroniser()
    elif a[0] == "--sync":
        synchroniser(silencieux="--silencieux" in a)
    elif a[0] == "--liste":
        liste()
    else:
        sys.exit(__doc__)
