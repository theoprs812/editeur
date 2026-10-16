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
    """Trouve ffmpeg, ffprobe, yt-dlp, whisper-cli même hors du PATH (apps de bureau)."""
    p = shutil.which(nom)
    if p:
        return p
    for d in ["/opt/homebrew/bin", "/usr/local/bin", str(Path.home() / ".local/bin")]:
        c = Path(d) / nom
        if c.exists():
            return str(c)
    if platform.system() == "Windows":
        for c in Path(os.environ.get("LOCALAPPDATA", "")).glob(f"Microsoft/WinGet/Packages/*/**/{nom}.exe"):
            return str(c)
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


def dossier_projet(fichier):
    """Le dossier de la vidéo = le parent de travail/ si on est dedans."""
    f = Path(os.path.abspath(fichier))
    d = f.parent
    return d.parent if d.name in ("travail", "export", "rushes", "b-roll") else d
