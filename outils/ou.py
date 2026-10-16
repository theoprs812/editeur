#!/usr/bin/env python3
"""À quel moment de la vidéo finale une phrase est-elle dite ?

    python3 ou.py travail/montage.json "faire les reps" ["autre phrase" ...]
    python3 ou.py travail/montage.json --tout      le texte complet avec le temps de chaque phrase sur la vidéo finale

Sert à poser les b-roll, les textes et les zooms au bon endroit (le champ "a" de montage.json).
"""
import json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from commun import mots, dossier_projet, FPS


def norm(w):
    return re.sub(r"[^\w']", "", w.lower().replace("’", "'"))


def timeline(m_path):
    m_path = Path(m_path).resolve()
    projet = dossier_projet(m_path)
    m = json.loads(m_path.read_text(encoding="utf-8"))
    tl, off = [], 0.0
    for p in m["plans"]:
        dur = round((p["fin"] - p["debut"]) * FPS) / FPS
        if p.get("son", True) is not False:
            for w in mots(p["source"], projet) or []:
                if w["s"] >= p["debut"] - 0.02 and w["e"] <= p["fin"] + 0.05:
                    tl.append({"t": round(off + max(0, w["s"] - p["debut"]), 2), "fin": round(off + min(dur, w["e"] - p["debut"]), 2), "w": w["w"]})
        off += dur
    return tl, off


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        sys.exit(__doc__)
    tl, total = timeline(a[0])
    if a[1] == "--tout":
        ligne, t0 = [], None
        for x in tl:
            t0 = x["t"] if t0 is None else t0
            ligne.append(x["w"])
            if x["w"][-1:] in ".?!" or len(ligne) >= 12:
                print(f"[{t0:6.2f} → {x['fin']:6.2f}] {' '.join(ligne)}")
                ligne, t0 = [], None
        if ligne:
            print(f"[{t0:6.2f} → {tl[-1]['fin']:6.2f}] {' '.join(ligne)}")
        print(f"(durée totale {total:.2f} s)")
        return
    toks = [norm(x["w"]) for x in tl]
    for phrase in a[1:]:
        cible = [norm(w) for w in phrase.split()]
        trouve = [i for i in range(len(toks) - len(cible) + 1) if toks[i:i + len(cible)] == cible]
        if not trouve:
            print(f"« {phrase} » : introuvable")
        for i in trouve:
            print(f"« {phrase} » : de {tl[i]['t']:.2f} s à {tl[i + len(cible) - 1]['fin']:.2f} s")


if __name__ == "__main__":
    main()
