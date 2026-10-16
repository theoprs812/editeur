#!/usr/bin/env python3
"""La DA de l'élève : images d'un reel pour la lire, et aperçu d'un template.

    python3 da.py images <video>                 5 images pleine taille + une planche, dans ~/Editeur/ma-da/source/<nom>/
    python3 da.py apercu [--kit K] [--fond F] [--t 1.0] [--comparer IMG]
                                                 une image du template sur un fond (photo ou vidéo) → ~/Editeur/ma-da/apercu-<nom>.png
                                                 --comparer : met l'image du reel d'origine à gauche pour comparer
"""
import json, shutil, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from commun import ffmpeg, lancer, sonde, IMAGE_EXT, DOSSIER_ELEVE
import rendu

MA_DA = DOSSIER_ELEVE / "ma-da"
FOND_DEFAUT = Path(__file__).resolve().parent.parent / "skills" / "ma-da" / "fond-exemple.jpg"
INSTANTS = [0.3, 1.0, 2.0, 3.5, 6.0]


def images(video):
    video = Path(video)
    info = sonde(video)
    out = MA_DA / "source" / video.parent.name if video.name == "video.mp4" else MA_DA / "source" / video.stem
    out.mkdir(parents=True, exist_ok=True)
    faites = []
    for t in INSTANTS:
        if t >= info["duree"]:
            continue
        dst = out / f"image-{t:04.1f}s.png"
        lancer([ffmpeg(), "-y", "-v", "error", "-ss", str(t), "-i", str(video), "-frames:v", "1",
                "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2", str(dst)])
        faites.append(dst)
    entrees = sum((["-i", str(f)] for f in faites), [])
    lancer([ffmpeg(), "-y", "-v", "error", *entrees, "-filter_complex",
            "".join(f"[{i}:v]scale=432:768[v{i}];" for i in range(len(faites))) + "".join(f"[v{i}]" for i in range(len(faites))) +
            f"hstack=inputs={len(faites)}", str(out / "planche.jpg")])
    print(f"✓ {len(faites)} images dans {out}")
    for f in faites:
        print("  ", f)


def apercu(kit_p=None, fond=None, t=1.0, comparer=None):
    kit_p = Path(kit_p) if kit_p else MA_DA / "kit.json"
    if not kit_p.exists():
        sys.exit(f"Pas de DA ici : {kit_p}")
    k = json.loads(kit_p.read_text(encoding="utf-8"))
    tmp = MA_DA / ".apercu"
    shutil.rmtree(tmp, ignore_errors=True)
    (tmp / "rushes").mkdir(parents=True)
    (tmp / "travail").mkdir()
    fond = Path(fond) if fond else FOND_DEFAUT
    img = tmp / "rushes" / "fond.png"
    if fond.suffix.lower() in IMAGE_EXT:
        lancer([ffmpeg(), "-y", "-v", "error", "-i", str(fond), "-frames:v", "1", str(img)])
    else:
        lancer([ffmpeg(), "-y", "-v", "error", "-ss", str(t), "-i", str(fond), "-frames:v", "1", str(img)])
    phrase = ["Voilà", "tes", "sous-titres", "dans", "ton", "style"]
    mots = [{"s": 0.2 + i * 0.3, "e": 0.45 + i * 0.3, "w": w} for i, w in enumerate(phrase)]
    (tmp / "travail" / "fond.mots.json").write_text(json.dumps({"mots": mots}), encoding="utf-8")
    m = {"format": "apercu", "da": str(kit_p), "sortie": "export/apercu.mp4",
         "plans": [{"source": "rushes/fond.png", "debut": 0, "fin": 3.0}],
         "hook": {"texte": "Le texte du début ressemble à ça", "de": 0, "a": 3.0}, "sous_titres": True}
    (tmp / "travail" / "montage.json").write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8")
    png = rendu.rendre(tmp / "travail" / "montage.json", image=0.9)
    nom = k.get("nom", "template").lower().replace(" ", "-").replace("(", "").replace(")", "")
    dst = MA_DA / f"apercu-{nom}.png"
    if comparer:
        lancer([ffmpeg(), "-y", "-v", "error", "-i", str(comparer), "-i", str(png), "-filter_complex",
                "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1[a];"
                "[1:v]setsar=1[b];[a][b]hstack=2,scale=1080:-2", str(dst)])
    else:
        shutil.copy2(png, dst)
    print(f"✓ {dst}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == "images":
        images(a[1])
    elif a[0] == "apercu":
        opt = lambda n, d=None: a[a.index(n) + 1] if n in a else d
        apercu(opt("--kit"), opt("--fond"), float(opt("--t", 1.0)), opt("--comparer"))
    else:
        sys.exit(__doc__)
