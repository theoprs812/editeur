#!/usr/bin/env python3
"""Trouve le drop d'une musique : le premier moment où elle tape vraiment (pas l'intro calme).

    python3 drop.py musique.mp3 [autre.mp3 ...]

Donne le temps à mettre dans "musique.debut" de montage.json. Méthode : volume par 0,1 s (ffmpeg ebur128),
premier instant où le son reste à moins de 4 dB de son niveau fort pendant 1 seconde.
"""
import re, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from commun import ffmpeg


def drop(f, analyse=90.0):
    r = subprocess.run([ffmpeg(), "-v", "info", "-t", str(analyse), "-i", str(f), "-vn", "-af", "ebur128=peak=none",
                        "-f", "null", "-"], capture_output=True, text=True)
    pts = [(float(t), float(m)) for t, m in re.findall(r"t:\s*([0-9.]+)\s+TARGET.*?M:\s*(-?[0-9.]+)", r.stderr)]
    if not pts:
        return 0.0
    vals = sorted(m for _, m in pts if m > -70)
    fort = vals[int(len(vals) * 0.8)] if vals else -20
    for i, (t, m) in enumerate(pts):
        fenetre = [x for _, x in pts[i:i + 10]]
        if len(fenetre) == 10 and min(fenetre) > fort - 4:
            return round(max(0.0, t - 0.4), 2)   # ebur128 M = moyenne sur 0,4 s
    return 0.0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for f in sys.argv[1:]:
        print(f"{drop(f):6.2f} s  {Path(f).name}")
