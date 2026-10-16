#!/usr/bin/env python3
"""Installe une police Google Fonts (gratuite) pour l'Éditeur.

    python3 police.py "Montserrat"            (graisses 400, 600, 700, 800, 900)
    python3 police.py --liste                 polices déjà installées

Les fichiers vont dans ~/Editeur/ma-da/polices/. Le rendu les trouve tout seul.
"""
import re, sys, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from commun import DOSSIER_ELEVE

DOSSIER = DOSSIER_ELEVE / "ma-da" / "polices"
GRAISSES = [400, 500, 600, 700, 800, 900]


def installer(famille):
    DOSSIER.mkdir(parents=True, exist_ok=True)
    q = famille.replace(" ", "+")
    ok = []
    for g in GRAISSES:
        url = f"https://fonts.googleapis.com/css2?family={q}:wght@{g}"
        req = urllib.request.Request(url, headers={"User-Agent": "Wget/1.21"})
        try:
            css = urllib.request.urlopen(req, timeout=20).read().decode()
        except Exception:
            continue
        m = re.search(r"url\((https://[^)]+\.ttf)\)", css)
        if not m:
            continue
        dst = DOSSIER / f"{famille.replace(' ', '')}-{g}.ttf"
        urllib.request.urlretrieve(m.group(1), dst)
        ok.append(g)
    if not ok:
        sys.exit(f"« {famille} » n'existe pas sur Google Fonts (vérifie l'orthographe).")
    print(f"✓ {famille} installée (graisses {', '.join(map(str, ok))}) dans {DOSSIER}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    if sys.argv[1] == "--liste":
        print("\n".join(sorted(p.name for p in DOSSIER.glob("*.ttf"))) if DOSSIER.exists() else "(aucune)")
    else:
        installer(" ".join(sys.argv[1:]))
