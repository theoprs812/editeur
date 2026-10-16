#!/usr/bin/env python3
"""La page de réglages du Studio, ouverte dans le navigateur de l'élève.

    python3 studio.py <dossier de la vidéo>        (ou travail/montage.json)

L'élève voit sa vidéo avec le texte du début et les sous-titres par-dessus, change le texte, les tailles, les couleurs,
le mot surligné, les positions (en glissant), puis clique sur « Fabriquer la vidéo ».
Il enregistre pour cette vidéo seulement (montage.json) ou dans sa DA pour toutes ses vidéos (ma-da/kit.json).
Tout reste sur l'ordinateur : le serveur n'écoute que sur 127.0.0.1.
"""
import copy, hashlib, json, re, socket, sys, threading, time, traceback, webbrowser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, str(Path(__file__).parent))
import rendu
from commun import dossier_projet, DOSSIER_ELEVE, DA_DEFAUT, police_de

ICI = Path(__file__).parent

ETAT = {"fond": "absent", "fabrication": None, "erreur": None, "fichier": None}
VERROU = threading.Lock()


class Session:
    def __init__(self, cible):
        p = Path(cible).expanduser().resolve()
        self.montage = p if p.suffix == ".json" else p / "travail" / "montage.json"
        if not self.montage.exists():
            sys.exit(f"Pas de montage ici : {self.montage}")
        self.projet = dossier_projet(self.montage)
        self.travail = self.projet / "travail"
        self.fond = self.travail / "studio-fond.mp4"

    def lire(self):
        return json.loads(self.montage.read_text(encoding="utf-8"))

    def cle_fond(self, m):
        utile = {k: m.get(k) for k in ("plans", "incrustations", "musique", "format_image")}
        return hashlib.md5(json.dumps(utile, sort_keys=True).encode()).hexdigest()

    def preparer_fond(self):
        """La vidéo sans aucun texte (demi-taille), sur laquelle le studio dessine les textes en direct."""
        m = self.lire()
        cle = self.cle_fond(m)
        marque = self.travail / "studio-fond.cle"
        if self.fond.exists() and marque.exists() and marque.read_text() == cle:
            self.affiche()
            ETAT["fond"] = "pret"
            return
        ETAT["fond"] = "preparation"
        try:
            rendu.rendre(self.montage, apercu=True, sans_textes=True, sortie=self.fond)
            marque.write_text(cle)
            self.affiche()
            ETAT["fond"] = "pret"
        except Exception as e:
            ETAT["fond"], ETAT["erreur"] = "erreur", str(e)[-800:]

    def affiche(self):
        """Une image de la vidéo, montrée avant que la lecture démarre."""
        img = self.travail / "studio-fond.jpg"
        if not img.exists() or img.stat().st_mtime < self.fond.stat().st_mtime:
            from commun import ffmpeg, lancer
            lancer([ffmpeg(), "-y", "-v", "error", "-ss", "0.5", "-i", str(self.fond), "-frames:v", "1", "-q:v", "3", str(img)])

    def etat(self):
        _, projet, m, k = rendu.preparer(self.montage)
        plans_t, total = rendu.plans_temps(m)
        blocs = rendu.blocs_sous_titres(projet, plans_t, int(k["sous_titres"].get("mots_par_bloc", 3))) if m.get("sous_titres", True) else []
        polices = {}
        for f in sorted(rendu.dossier_polices(self.travail, k).glob("*.[ot]tf")):
            fam, poids = police_de(f.name)
            polices.setdefault(fam, []).append({"fichier": f.name, "poids": poids})
        sortie = projet / m.get("sortie", "export/video-v1.mp4")
        return {
            "nom": projet.name, "largeur": rendu.W, "hauteur": rendu.H, "total": total,
            "format": m.get("format", ""), "format_image": m.get("format_image", "9:16"),
            "hook": m.get("hook") or {"texte": "", "de": 0, "a": 3},
            "sous_titres_actifs": m.get("sous_titres", True), "textes": m.get("textes", []),
            "kit": {s: k.get(s) for s in ("police", "hook", "sous_titres", "textes")},
            "da_nom": k.get("nom", "Template"), "da_fichier": k.get("_fichier"),
            "blocs": [[{"s": round(w["s"], 3), "e": round(w["e"], 3), "w": w["w"]} for w in b] for b in blocs],
            "polices": polices, "fond": ETAT["fond"], "erreur": ETAT["erreur"],
            "sortie": str(sortie), "sortie_existe": sortie.exists(),
            "fabrication": ETAT["fabrication"], "fichier": ETAT["fichier"],
        }

    def enregistrer(self, data):
        """portee = "video" : montage.json (texte du début + ajustements) ; "da" : ma-da/kit.json, pour toutes les vidéos."""
        m = self.lire()
        if "hook" in data:
            m["hook"] = {**(m.get("hook") or {}), **data["hook"]}
        if "sous_titres_actifs" in data:
            m["sous_titres"] = bool(data["sous_titres_actifs"])
        styles = {s: data[s] for s in ("police", "hook_style", "sous_titres") if s in data}
        if "hook_style" in styles:
            styles["hook"] = styles.pop("hook_style")
        if data.get("portee") == "da":
            kp = DOSSIER_ELEVE / "ma-da" / "kit.json"
            kp.parent.mkdir(parents=True, exist_ok=True)
            base = json.loads((kp if kp.exists() else DA_DEFAUT).read_text(encoding="utf-8"))
            if not kp.exists():
                base["nom"] = "Template 1"
            autre_format = (rendu.W, rendu.H) != (1080, 1920)
            aj = m.get("ajustements") or {}
            for sec, val in styles.items():
                val = dict(val)
                if autre_format:   # tailles et positions d'un autre format : elles restent sur cette vidéo
                    garde = {c: val.pop(c) for c in ("y", "taille", "marge_cotes", "contour") if c in val}
                    if garde:
                        aj.setdefault(sec, {}).update(garde)
                base.setdefault(sec, {}).update(val)
                for c in val:   # ce qui part dans la DA ne doit plus être écrasé par un ancien ajustement de la vidéo
                    aj.get(sec, {}).pop(c, None)
            m["ajustements"] = {s_: v for s_, v in aj.items() if v}
            base.setdefault("historique", []).append({"date": time.strftime("%Y-%m-%d"), "changement": "réglé dans le Studio",
                                                     "pourquoi": f"vidéo {self.projet.name}"})
            base["version"] = int(base.get("version", 1)) + 1
            kp.write_text(json.dumps(base, ensure_ascii=False, indent=2), encoding="utf-8")
        else:
            aj = m.get("ajustements") or {}
            for sec, val in styles.items():
                aj.setdefault(sec, {}).update(val)
            m["ajustements"] = aj
        self.montage.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")

    def fabriquer(self):
        def tache():
            ETAT.update(fabrication="en cours", fichier=None, erreur=None)
            try:
                m = self.lire()
                sortie = Path(m.get("sortie", "export/video-v1.mp4"))
                n = 1
                mt = re.match(r"(.*)-v(\d+)$", sortie.stem)
                base = mt.group(1) if mt else sortie.stem
                while (self.projet / sortie.parent / f"{base}-v{n}{sortie.suffix}").exists():
                    n += 1
                m["sortie"] = str(sortie.parent / f"{base}-v{n}{sortie.suffix}")
                self.montage.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
                out = rendu.rendre(self.montage)
                ETAT.update(fabrication="fini", fichier=str(out))
            except Exception as e:
                ETAT.update(fabrication="erreur", erreur=str(e)[-800:])
        with VERROU:
            if ETAT["fabrication"] != "en cours":
                threading.Thread(target=tache, daemon=True).start()

    def image(self, t):
        return rendu.rendre(self.montage, image=float(t))


def servir_fichier(h, chemin, type_mime):
    p = Path(chemin)
    if not p.exists():
        h.send_error(404)
        return
    taille = p.stat().st_size
    debut, fin = 0, taille - 1
    rng = h.headers.get("Range")
    if rng and rng.startswith("bytes="):
        a, _, b = rng[6:].partition("-")
        debut = int(a) if a else 0
        fin = int(b) if b else taille - 1
        h.send_response(206)
        h.send_header("Content-Range", f"bytes {debut}-{fin}/{taille}")
    else:
        h.send_response(200)
    h.send_header("Content-Type", type_mime)
    h.send_header("Accept-Ranges", "bytes")
    h.send_header("Content-Length", str(fin - debut + 1))
    h.send_header("Cache-Control", "no-store")
    h.end_headers()
    with open(p, "rb") as f:
        f.seek(debut)
        reste = fin - debut + 1
        while reste > 0:
            bloc = f.read(min(1 << 20, reste))
            if not bloc:
                break
            try:
                h.wfile.write(bloc)
            except (BrokenPipeError, ConnectionResetError):
                return
            reste -= len(bloc)


def gestionnaire(session):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def json(self, obj, code=200):
            b = json.dumps(obj, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def do_GET(self):
            u = urlparse(self.path)
            try:
                if u.path == "/":
                    servir_fichier(self, ICI / "studio.html", "text/html; charset=utf-8")
                elif u.path == "/api/etat":
                    self.json(session.etat())
                elif u.path == "/media/fond":
                    servir_fichier(self, session.fond, "video/mp4")
                elif u.path == "/media/affiche":
                    servir_fichier(self, session.travail / "studio-fond.jpg", "image/jpeg")
                elif u.path == "/media/fichier":
                    f = Path(ETAT["fichier"] or "")
                    servir_fichier(self, f, "video/mp4") if f.is_file() else self.send_error(404)
                elif u.path == "/media/image":
                    f = session.travail / "images" / Path(parse_qs(u.query).get("f", [""])[0]).name
                    servir_fichier(self, f, "image/png")
                elif u.path.startswith("/polices/"):
                    f = session.travail / "polices" / Path(u.path).name
                    servir_fichier(self, f, "font/ttf")
                else:
                    self.send_error(404)
            except Exception:
                self.json({"erreur": traceback.format_exc()[-800:]}, 500)

        def do_POST(self):
            u = urlparse(self.path)
            n = int(self.headers.get("Content-Length", 0) or 0)
            data = json.loads(self.rfile.read(n) or b"{}")
            try:
                if u.path == "/api/enregistrer":
                    session.enregistrer(data)
                    self.json({"ok": True})
                elif u.path == "/api/fabriquer":
                    if data:
                        session.enregistrer({**data, "portee": "video"})
                    session.fabriquer()
                    self.json({"ok": True})
                elif u.path == "/api/image":
                    if data.get("reglages"):
                        session.enregistrer({**data["reglages"], "portee": "video"})
                    png = session.image(data.get("t", 1.0))
                    self.json({"url": f"/media/image?f={png.name}&v={time.time()}"})
                elif u.path == "/api/capcut":
                    if data:
                        session.enregistrer({**data, "portee": "video"})
                    import capcut
                    try:
                        nom = capcut.envoyer(session.montage, ouvrir=True)
                        self.json({"ok": True, "nom": nom})
                    except SystemExit as e:
                        self.json({"ok": False, "message": str(e)})
                elif u.path == "/api/ouvrir":
                    import subprocess, platform
                    d = str(Path(ETAT["fichier"]).parent if ETAT["fichier"] else session.projet / "export")
                    subprocess.Popen(["open", d] if platform.system() == "Darwin" else ["explorer", d])
                    self.json({"ok": True})
                else:
                    self.send_error(404)
            except Exception:
                self.json({"erreur": traceback.format_exc()[-800:]}, 500)
    return H


def port_libre(depart=8765):
    for p in range(depart, depart + 40):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", p)) != 0:
                return p
    return 0


def main():
    a = [x for i, x in enumerate(sys.argv[1:], 1) if not x.startswith("--") and sys.argv[i - 1] != "--port"]
    if not a:
        sys.exit(__doc__)
    session = Session(a[0])
    rendu.preparer(session.montage)
    threading.Thread(target=session.preparer_fond, daemon=True).start()
    port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else port_libre()
    srv = ThreadingHTTPServer(("127.0.0.1", port), gestionnaire(session))
    url = f"http://127.0.0.1:{port}/"
    print(f"✓ Studio ouvert : {url}  (Ctrl+C pour fermer)", flush=True)
    if "--sans-navigateur" not in sys.argv:
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
