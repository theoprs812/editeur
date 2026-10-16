#!/usr/bin/env python3
"""Planche d'images : 6 images par vidéo sur une seule image, pour que Claude voie ce qu'il y a dedans.

    python3 planche.py b-roll/            (toutes les vidéos et images du dossier, sous-dossiers compris)
    python3 planche.py rushes/IMG_1.MOV
    python3 planche.py --bibliotheque     toute la bibliothèque ~/Editeur/b-roll/<thème>/ (seuls les nouveaux fichiers)

Écrit travail/planches/<nom>.jpg et travail/planches/index.json (durée, taille, son, HDR de chaque fichier).
Pour la bibliothèque : ~/Editeur/b-roll/.planches/<thème>--<nom>.jpg et index.json, réutilisés par toutes les vidéos.
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from commun import ffmpeg, lancer, sonde, dossier_projet, POLICES, VIDEO_EXT, IMAGE_EXT, DOSSIER_ELEVE

N = 6


def planche(src, dst):
    info = sonde(src)
    d = max(info["duree"], 0.1)
    vf = []
    if info.get("image_fixe") or d < 0.2:
        lancer([ffmpeg(), "-y", "-v", "error", "-i", str(src), "-vf", "scale=360:-2", "-frames:v", "1", str(dst)])
        return info
    entrees = []
    for i in range(N):
        entrees += ["-ss", f"{d * (i + 0.5) / N:.2f}", "-i", str(src)]
    police = str(POLICES / "TikTokSans-Bold.ttf").replace("\\", "/").replace(":", "\\:")
    filt = "".join(f"[{i}:v]scale=240:426:force_original_aspect_ratio=decrease,pad=240:426:(ow-iw)/2:(oh-ih)/2,"
                   f"drawtext=fontfile='{police}':text='{d * (i + 0.5) / N:.1f}s':x=6:y=6:fontsize=20:fontcolor=white:box=1:boxcolor=black@0.6[v{i}];" for i in range(N))
    filt += "".join(f"[v{i}]" for i in range(N)) + f"hstack=inputs={N}"
    lancer([ffmpeg(), "-y", "-v", "error", *entrees, "-filter_complex", filt, "-frames:v", "1", "-q:v", "4", str(dst)])
    return info


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    biblio = DOSSIER_ELEVE / "b-roll"
    if args == ["--bibliotheque"]:
        args = [str(biblio)]
    cibles = []
    for a in args:
        p = Path(a).expanduser()
        if p.is_dir():
            cibles += sorted(x for x in p.rglob("*") if x.suffix.lower() in VIDEO_EXT | IMAGE_EXT and ".planches" not in x.parts)
        else:
            cibles.append(p)
    if not cibles:
        sys.exit("Aucune vidéo ni image trouvée.")
    for c in cibles:
        dans_biblio = biblio.exists() and str(c.resolve()).startswith(str(biblio.resolve()))
        out = biblio / ".planches" if dans_biblio else dossier_projet(c) / "travail" / "planches"
        out.mkdir(parents=True, exist_ok=True)
        nom = f"{c.parent.name}--{c.stem}" if dans_biblio else c.stem
        dst = out / f"{nom}.jpg"
        idx_p = out / "index.json"
        idx = json.loads(idx_p.read_text(encoding="utf-8")) if idx_p.exists() else {}
        if dst.exists() and dst.stat().st_mtime >= c.stat().st_mtime and str(c) in idx:
            print(f"= {c.name} (déjà vue) → {dst}")
            continue
        try:
            info = planche(c, dst)
        except RuntimeError as e:
            print(f"✗ {c.name} : illisible ({str(e).splitlines()[-1][:120]})")
            continue
        idx[str(c)] = {**info, "planche": str(dst), "theme": c.parent.name if dans_biblio else None}
        idx_p.write_text(json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✓ {c.name} ({info['duree']:.1f} s) → {dst}")


if __name__ == "__main__":
    main()
