#!/usr/bin/env python3
"""Coupe fine au mot : enlève les blancs, les « euh » et les mots répétés dans les passages gardés.

    python3 couper.py travail/garde.json [--montage travail/montage-v2.json]

garde.json : {"style": "normal" | "yap" | "garder-blancs", "passages": [{"source": "rushes/x.MOV", "debut": 12.1, "fin": 31.0}, ...]}
Écrit (ou met à jour) les "plans" de travail/montage.json et affiche ce qui a été retiré.

La règle (celle des shorts de Théo) :
- tout blanc de plus de 0,35 s est coupé, en gardant 0,12 s d'air de chaque côté ("yap" : dès 0,25 s) ;
- une coupe ne mord jamais sur un mot : les bornes sont recalées sur le vrai silence (silencedetect),
  les temps de Whisper débordent souvent de 0,2 à 0,3 s sur les blancs ;
- la vidéo commence pile sur le premier mot utile (ni blanc ni « euh » avant) et finit 0,4 s après le dernier ;
- "garder-blancs" : on n'enlève que les « euh » et les ratés, les silences voulus restent.
garde.json peut forcer "blanc_max" et "marge" (en secondes).
"""
import json, re, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from commun import kit, mots, dossier_projet, ffmpeg, sonde

FILLERS = {"euh", "euhh", "euhm", "heu", "hum", "hmm", "mmh", "bah", "uh", "um", "erm"}
REGLE = {"blanc_max": 0.35, "blanc_max_yap": 0.25, "marge": 0.12, "attaque": 0.03, "fin": 0.4}
ANCIENS = {"blanc_max_yap": 0.25, "blanc_max_normal": 0.5, "marge": 0.08}   # défauts d'avant la 1.0.1, recopiés dans les kits


def norm(w):
    return re.sub(r"[^\w']", "", w.lower().replace("’", "'"))


def volume_moyen(src, debut, fin):
    r = subprocess.run([ffmpeg(), "-v", "info", "-ss", f"{debut:.3f}", "-t", f"{fin - debut:.3f}", "-i", str(src), "-vn",
                        "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True)
    m = re.search(r"mean_volume: (-?[0-9.]+) dB", r.stderr)
    return float(m.group(1)) if m else -30.0


def silences(src, debut, fin, seuil_db=None, duree=0.08):
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


def trier_mots(ws):
    """Sépare les mots gardés des « euh » et des mots répétés. Renvoie les groupes de mots gardés
    (un groupe = une suite sans mot retiré au milieu), les mots retirés et ce qu'on affiche."""
    groupes, cur, trous, retire = [], [], [], []
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
            if cur:
                groupes.append(cur)
            cur = []
            continue
        cur.append(m)
    if cur:
        groupes.append(cur)
    return groupes, trous, retire


class Son:
    """Le son d'un passage : où sont les blancs, où commence et finit vraiment la voix."""

    def __init__(self, sil, debut, fin):
        self.sil, self.debut, self.fin = sorted(sil), debut, fin

    def blanc_a(self, t):
        return next(((a, b) for a, b in self.sil if a <= t < b), None)

    def blanc_avant(self, t):
        """Le blanc qui finit juste avant t (ou qui contient t)."""
        return next(((a, b) for a, b in reversed(self.sil) if a < t), None)

    def blanc_apres(self, t):
        return next(((a, b) for a, b in self.sil if b > t), None)

    def debut_voix(self, s, e, limite):
        """Le vrai début de la voix d'un mot que Whisper place à s (souvent trop tôt, parfois trop tard)."""
        b = self.blanc_a(s)
        if b:   # Whisper commence dans le blanc : la voix part à sa fin (mot trop faible pour être entendu : temps de Whisper)
            return max(b[1] if b[1] < e else s, limite)
        av = self.blanc_avant(s)
        v0 = av[1] if av else self.debut
        return max(v0, s - 0.3, limite)       # Whisper en retard : on remonte au début de la voix

    def fin_voix(self, e, s, limite):
        b = self.blanc_a(e - 1e-6)
        if b:   # Whisper déborde sur le blanc : la voix s'arrête à son début
            return min(b[0] if b[0] > s else e, limite)
        ap = self.blanc_apres(e)
        v1 = ap[0] if ap else self.fin
        return min(v1, e + 0.3, limite)

    def voix_avant(self, t):
        """Fin de la voix qui précède t : une marge ne remonte jamais au-delà."""
        av = self.blanc_avant(t)
        return av[0] if av and av[1] >= t - 1e-6 else t

    def voix_apres(self, t):
        ap = self.blanc_apres(t)
        return ap[1] if ap and ap[0] <= t + 1e-6 else t


def couper(ws, debut, fin, sil, blanc_max, marge, premier=False, dernier=False, duree_source=None):
    """Les morceaux à garder d'un passage, en temps du fichier source, et ce qui a été retiré."""
    ws = [m for m in ws if debut - 0.05 <= (m["s"] + m["e"]) / 2 <= fin + 0.05]
    groupes, trous, retire = trier_mots(ws)
    son = Son(sil, max(0.0, debut - 0.5), (duree_source or fin + 1) if dernier else fin + 0.6)
    # Son bruité (aucun blanc trouvé) : les trous entre les mots de Whisper servent de blancs
    if not sil:
        son.sil = [(a["e"], b["s"]) for g in groupes for a, b in zip(g, g[1:]) if b["s"] - a["e"] > blanc_max]
    out = []
    for gi, g in enumerate(groupes):
        s, e = g[0]["s"], g[-1]["e"]
        lim_av = max([t1 for t0, t1 in trous if t1 <= s + 0.01] + [son.debut])
        lim_ap = min([t0 for t0, t1 in trous if t0 >= e - 0.01] + [son.fin])
        v0 = son.debut_voix(s, e, lim_av)
        v1 = son.fin_voix(e, s, lim_ap)
        if v1 - v0 < 0.05:
            continue
        avant = REGLE["attaque"] if premier and gi == 0 else marge
        apres = REGLE["fin"] if dernier and gi == len(groupes) - 1 else marge
        a = max(v0 - avant, son.voix_avant(v0), 0.0)
        b = min(v1 + apres, son.voix_apres(v1) - (0.05 if apres > marge else 0.0))
        if duree_source:
            b = min(b, duree_source)
        if out and a < out[-1][1]:
            a = out[-1][1]
        # les blancs à l'intérieur du groupe (entre deux mots qu'on garde)
        cur = a
        for t0, t1 in son.sil:
            if t1 - t0 <= blanc_max or t0 < v0 or t1 > v1:
                continue
            c0, c1 = t0 + marge, t1 - marge
            if c1 - c0 > 0.05:
                if c0 - cur > 0.05:
                    out.append([round(cur, 3), round(c0, 3)])
                cur = c1
        if b - cur > 0.05:
            out.append([round(cur, 3), round(b, 3)])
    return out, retire


def reglage_kit(k):
    """Les réglages de coupe de la DA, s'ils ont été changés exprès (les anciens défauts ne comptent pas)."""
    c = {x: y for x, y in (k.get("coupes") or {}).items() if ANCIENS.get(x) != y}
    return {"blanc_max": c.get("blanc_max_normal", REGLE["blanc_max"]), "blanc_max_yap": c.get("blanc_max_yap", REGLE["blanc_max_yap"]),
            "marge": c.get("marge", REGLE["marge"])}


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    g_path = Path(sys.argv[1]).resolve()
    projet = dossier_projet(g_path)
    g = json.loads(g_path.read_text(encoding="utf-8"))
    r = reglage_kit(kit("auto", projet))
    style = g.get("style", "normal")
    blanc = {"yap": r["blanc_max_yap"], "garder-blancs": float("inf")}.get(style, r["blanc_max"])
    blanc = float(g.get("blanc_max", blanc))
    marge = float(g.get("marge", r["marge"]))
    plans, total_retire, avant, apres = [], [], 0.0, 0.0
    n = len(g["passages"])
    for i, p in enumerate(g["passages"]):
        ws = mots(p["source"], projet)
        if ws is None:
            sys.exit(f"Pas de transcription pour {p['source']} : lance d'abord transcrire.py")
        src = projet / p["source"]
        duree = sonde(src)["duree"]
        dernier = i == n - 1
        z0, z1 = max(0.0, p["debut"] - 0.5), min(duree, p["fin"] + (1.0 if dernier else 0.6))
        sil = silences(src, z0, z1, seuil_db=min(-24.0, volume_moyen(src, p["debut"], p["fin"]) - 10))
        morceaux, retire = couper(ws, p["debut"], p["fin"], sil, blanc, marge, premier=i == 0, dernier=dernier, duree_source=duree)
        total_retire += retire
        avant += p["fin"] - p["debut"]
        for a, b in morceaux:
            plans.append({"source": p["source"], "debut": a, "fin": b})
            apres += b - a
    m_path = projet / "travail" / "montage.json"
    if "--montage" in sys.argv:   # une version à part : travail/montage-v2.json
        m_path = Path(sys.argv[sys.argv.index("--montage") + 1]).resolve()
    m = json.loads(m_path.read_text(encoding="utf-8")) if m_path.exists() else {}
    m["plans"] = plans
    m.setdefault("format", "coupe-propre" if style == "garder-blancs" else style)
    m.setdefault("sortie", "export/video-v1.mp4")
    m.setdefault("da", "auto")
    m.setdefault("sous_titres", True)
    m_path.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ {len(plans)} plans, {avant:.1f} s → {apres:.1f} s ({avant - apres:.1f} s de blancs et ratés en moins)")
    for r_ in total_retire[:40]:
        print("  retiré :", r_)


if __name__ == "__main__":
    main()
