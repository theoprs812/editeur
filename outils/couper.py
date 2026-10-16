#!/usr/bin/env python3
"""Coupe fine au mot : enlève les blancs, les « euh » et les mots répétés dans les passages gardés.

    python3 couper.py travail/garde.json

garde.json : {"style": "yap" | "normal", "passages": [{"source": "rushes/x.MOV", "debut": 12.1, "fin": 31.0}, ...]}
Écrit (ou met à jour) les "plans" de travail/montage.json et affiche ce qui a été retiré.
"""
import json, re, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from commun import kit, mots, dossier_projet, ffmpeg

FILLERS = {"euh", "euhh", "euhm", "heu", "hum", "hmm", "mmh", "bah", "uh", "um", "erm"}


def norm(w):
    return re.sub(r"[^\w']", "", w.lower().replace("’", "'"))


def volume_moyen(src, debut, fin):
    r = subprocess.run([ffmpeg(), "-v", "info", "-ss", f"{debut:.3f}", "-t", f"{fin - debut:.3f}", "-i", str(src), "-vn",
                        "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True)
    m = re.search(r"mean_volume: (-?[0-9.]+) dB", r.stderr)
    return float(m.group(1)) if m else -30.0


def silences(src, debut, fin, seuil_db=None, duree=0.18):
    """Les vrais blancs du son (ffmpeg silencedetect), en temps du fichier source.
    Seuil calé sur le volume moyen de la voix : 10 dB sous la moyenne = blanc."""
    if seuil_db is None:
        seuil_db = min(-24.0, volume_moyen(src, debut, fin) - 10)
    r = subprocess.run([ffmpeg(), "-v", "info", "-ss", f"{debut:.3f}", "-t", f"{fin - debut:.3f}", "-i", str(src), "-vn",
                        "-af", f"silencedetect=noise={seuil_db}dB:d={duree}", "-f", "null", "-"], capture_output=True, text=True)
    out, cur = [], None
    for l in r.stderr.splitlines():
        if "silence_start" in l:
            cur = debut + float(l.split("silence_start:")[1].split()[0])
        elif "silence_end" in l and cur is not None:
            out.append((max(debut, cur), debut + float(l.split("silence_end:")[1].split()[0])))
            cur = None
    if cur is not None:
        out.append((cur, fin))
    return out


def retirer_silences(morceaux, sil, blanc_max, marge):
    """Enlève de chaque morceau les silences plus longs que blanc_max (on garde un peu d'air de chaque côté)."""
    res = []
    for a, b in morceaux:
        cur = a
        for s0, s1 in sil:
            if s1 - s0 <= blanc_max or s1 <= cur or s0 >= b:
                continue
            c0, c1 = max(s0, cur) + marge, min(s1, b) - marge
            if c1 - c0 > 0.05:
                if c0 - cur > 0.12:
                    res.append([round(cur, 3), round(c0, 3)])
                cur = c1
        if b - cur > 0.12:
            res.append([round(cur, 3), round(b, 3)])
    return res


def couper(ws, debut, fin, blanc_max, marge):
    ws = [m for m in ws if m["s"] >= debut - 0.05 and m["e"] <= fin + 0.05]
    garde, retire, trous = [], [], []
    for i, m in enumerate(ws):
        t = norm(m["w"])
        raison = None
        if t in FILLERS:
            raison = f"« {m['w']} » à {m['s']:.2f}"
        elif i + 1 < len(ws) and t and t == norm(ws[i + 1]["w"]) and ws[i + 1]["s"] - m["e"] < 0.6:
            raison = f"mot répété « {m['w']} » à {m['s']:.2f}"
        if raison:
            retire.append(raison)
            trous.append((m["s"], m["e"]))
            if garde:
                garde[-1] = dict(garde[-1], coupe_apres=True)
            continue
        garde.append(m)
    plans, cur = [], None
    for m in garde:
        if cur and m["s"] - cur["e"] <= blanc_max and not cur.get("coupe_apres"):
            cur["e"] = m["e"]
            cur["coupe_apres"] = m.get("coupe_apres")
        else:
            if cur:
                plans.append(cur)
            cur = {"s": m["s"], "e": m["e"], "coupe_apres": m.get("coupe_apres")}
    if cur:
        plans.append(cur)
    # marges : un peu d'air avant le premier mot et après le dernier, sans manger le mot voisin ni un mot retiré
    out = []
    for p in plans:
        a = max(debut, p["s"] - marge)
        b = min(fin, p["e"] + marge * 1.5)
        for t0, t1 in trous:
            if t1 <= p["s"] + 0.01 and t1 > a:
                a = t1
            if t0 >= p["e"] - 0.01 and t0 < b:
                b = t0
        if out and a < out[-1][1]:
            a = out[-1][1]
        if b - a > 0.12:
            out.append([round(a, 3), round(b, 3)])
    return out, retire


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    g_path = Path(sys.argv[1]).resolve()
    projet = dossier_projet(g_path)
    g = json.loads(g_path.read_text(encoding="utf-8"))
    k = kit("auto", projet)
    blanc = k["coupes"]["blanc_max_yap"] if g.get("style", "normal") == "yap" else k["coupes"]["blanc_max_normal"]
    blanc = g.get("blanc_max", blanc)
    plans, total_retire, avant, apres = [], [], 0.0, 0.0
    for p in g["passages"]:
        ws = mots(p["source"], projet)
        if ws is None:
            sys.exit(f"Pas de transcription pour {p['source']} : lance d'abord transcrire.py")
        morceaux, retire = couper(ws, p["debut"], p["fin"], blanc, k["coupes"]["marge"])
        morceaux = retirer_silences(morceaux, silences(projet / p["source"], p["debut"], p["fin"]), blanc, k["coupes"]["marge"] * 0.6)
        total_retire += retire
        avant += p["fin"] - p["debut"]
        for a, b in morceaux:
            plans.append({"source": p["source"], "debut": a, "fin": b})
            apres += b - a
    m_path = projet / "travail" / "montage.json"
    m = json.loads(m_path.read_text(encoding="utf-8")) if m_path.exists() else {}
    m["plans"] = plans
    m.setdefault("format", g.get("style", "coupe-propre"))
    m.setdefault("sortie", "export/video-v1.mp4")
    m.setdefault("da", "auto")
    m.setdefault("sous_titres", True)
    m_path.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ {len(plans)} plans, {avant:.1f} s → {apres:.1f} s ({avant - apres:.1f} s de blancs et ratés en moins)")
    for r in total_retire[:40]:
        print("  retiré :", r)


if __name__ == "__main__":
    main()
