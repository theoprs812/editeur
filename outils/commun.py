"""Outils partagés de l'Éditeur : chemins, ffmpeg, lecture des médias, DA."""
import json, os, platform, shutil, subprocess, sys
from pathlib import Path

EDITEUR = Path(__file__).resolve().parent.parent
POLICES = EDITEUR / "polices"
DA_DEFAUT = EDITEUR / "skills" / "ma-da" / "defaut.json"
W, H, FPS = 1080, 1920, 30
DOSSIER_ELEVE = Path(os.environ.get("EDITEUR_DOSSIER", str(Path.home() / "Editeur")))

VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi", ".mts"}
AUDIO_EXT = {".m4a", ".mp3", ".wav", ".aac", ".flac", ".ogg", ".opus"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".heic"}


def outil(nom):
    """Trouve ffmpeg, ffprobe, yt-dlp, whisper-cli même hors du PATH (apps de bureau).
    ffmpeg : on prend d'abord ffmpeg-full (Homebrew), le seul qui a les sous-titres et les couleurs iPhone."""
    candidats = []
    if nom in ("ffmpeg", "ffprobe"):
        candidats += [f"/opt/homebrew/opt/ffmpeg-full/bin/{nom}", f"/usr/local/opt/ffmpeg-full/bin/{nom}"]
    p = shutil.which(nom)
    if p:
        candidats.append(p)
    candidats += [str(Path(d) / nom) for d in ["/opt/homebrew/bin", "/usr/local/bin", str(Path.home() / ".local/bin")]]
    if platform.system() == "Windows":
        candidats += [str(c) for c in Path(os.environ.get("LOCALAPPDATA", "")).glob(f"Microsoft/WinGet/Packages/*/**/{nom}.exe")]
    for c in candidats:
        if c and Path(c).exists():
            return c
    return None


def ffmpeg():
    p = outil("ffmpeg")
    if not p:
        sys.exit("ffmpeg manque. Dis à Claude : « installe mon éditeur ».")
    return p


def lancer(cmd, quiet=True):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        msg = (r.stderr or "")[-3000:]
        raise RuntimeError(f"La commande a échoué : {' '.join(map(str, cmd[:6]))}…\n{msg}")
    return r.stdout


def sonde(chemin):
    """Durée, taille, rotation, son, HDR d'un fichier."""
    fp = outil("ffprobe") or ffmpeg().replace("ffmpeg", "ffprobe")
    out = lancer([fp, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(chemin)])
    j = json.loads(out)
    v = next((s for s in j["streams"] if s["codec_type"] == "video" and s.get("disposition", {}).get("attached_pic") != 1), None)
    a = next((s for s in j["streams"] if s["codec_type"] == "audio"), None)
    info = {"duree": float(j["format"].get("duration", 0) or 0), "son": a is not None, "video": v is not None}
    if v:
        w, h = int(v.get("width", 0)), int(v.get("height", 0))
        rot = 0
        for sd in v.get("side_data_list", []) or []:
            if "rotation" in sd:
                rot = int(sd["rotation"])
        rot = int(v.get("tags", {}).get("rotate", rot))
        if abs(rot) in (90, 270):
            w, h = h, w
        info.update(largeur=w, hauteur=h, hdr=v.get("color_transfer") in ("arib-std-b67", "smpte2084"),
                    image_fixe=Path(chemin).suffix.lower() in IMAGE_EXT)
    return info


def kit(chemin=None, dossier_projet=None):
    """Charge la DA : chemin donné, sinon ma-da/kit.json du dossier Éditeur de l'élève, sinon la DA par défaut."""
    base = json.loads(DA_DEFAUT.read_text(encoding="utf-8"))
    cible = None
    if chemin and chemin != "auto":
        cible = Path(chemin)
        if dossier_projet and not cible.is_absolute():
            cible = Path(dossier_projet) / cible
    elif dossier_projet:
        for d in [Path(dossier_projet), *Path(dossier_projet).resolve().parents]:
            if (d / "ma-da" / "kit.json").exists():
                cible = d / "ma-da" / "kit.json"
                break
    if cible is None and (DOSSIER_ELEVE / "ma-da" / "kit.json").exists():
        cible = DOSSIER_ELEVE / "ma-da" / "kit.json"
    if cible and cible.exists():
        perso = json.loads(cible.read_text(encoding="utf-8"))
        for k, v in perso.items():
            if isinstance(v, dict) and isinstance(base.get(k), dict):
                base[k].update(v)
            else:
                base[k] = v
        base["_fichier"] = str(cible)
    return base


def mots(source, projet):
    """Les mots transcrits d'une source : travail/<nom>.mots.json."""
    p = Path(projet) / "travail" / (Path(source).stem + ".mots.json")
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))["mots"]
    return None


def chemin(projet, source):
    """Un chemin de montage.json : relatif au dossier de la vidéo, absolu, ou ~/... (bibliothèque de l'élève)."""
    s = str(source)
    if s.startswith("~"):
        return Path(os.path.expanduser(s))
    p = Path(s)
    return p if p.is_absolute() else Path(projet) / p


FORMATS = {"9:16": (1080, 1920), "16:9": (1920, 1080), "4:5": (1080, 1350), "1:1": (1080, 1080)}


def format_image(m, projet):
    """La taille de la vidéo finale : 9:16 par défaut, ou "origine" = le format du premier rush."""
    f = m.get("format_image", "9:16")
    if f == "origine":
        for p in m.get("plans", []):
            i = sonde(chemin(projet, p["source"]))
            if i.get("video") and not i.get("image_fixe"):
                r = i["largeur"] / max(1, i["hauteur"])
                f = "16:9" if r > 1.2 else "1:1" if r > 0.9 else "4:5" if r > 0.7 else "9:16"
                break
        else:
            f = "9:16"
    return FORMATS.get(f, FORMATS["9:16"])


def adapter_kit(k, w, h):
    """La DA est écrite pour du 1080x1920. Pour un autre format, on recalcule tailles et positions."""
    if (w, h) == (1080, 1920):
        return k
    paysage = w > h
    f = 0.72 if paysage else 0.9
    ry = h / 1920
    for sec in ("hook", "sous_titres", "textes"):
        if sec in k:
            k[sec]["taille"] = round(k[sec].get("taille", 60) * f)
            k[sec]["contour"] = max(0, round(k[sec].get("contour", 0) * f))
    if paysage:
        k["hook"].update(y=round(h * 0.07), marge_cotes=round(w * 0.2))
        k["sous_titres"].update(y=round(h * 0.86), marge_cotes=round(w * 0.15))
        k["textes"]["marge_cotes"] = round(w * 0.15)
        k["fenetre"].update(largeur=round(w * 0.36), y=round(h * 0.1), hauteur_max=round(h * 0.62), x=round(w * 0.6))
    else:
        k["hook"]["y"] = round(k["hook"].get("y", 300) * ry)
        k["sous_titres"]["y"] = round(k["sous_titres"].get("y", 1330) * ry)
        k["fenetre"].update(y=round(k["fenetre"].get("y", 250) * ry), hauteur_max=round(k["fenetre"].get("hauteur_max", 880) * ry))
    return k


def dossier_projet(fichier):
    """Le dossier de la vidéo : le parent de rushes/, b-roll/, travail/… (même depuis un sous-dossier)."""
    f = Path(os.path.abspath(fichier))
    for d in list(f.parents)[:4]:
        if d.name in ("travail", "export", "rushes", "b-roll", "musique"):
            return d.parent
    return f.parent
