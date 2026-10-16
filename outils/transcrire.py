#!/usr/bin/env python3
"""Transcrit une vidéo ou un audio, en local, avec les temps de chaque mot.

    python3 transcrire.py rushes/IMG_1234.MOV [autres fichiers...]

Écrit travail/<nom>.mots.json ({"mots": [{"s": 1.2, "e": 1.5, "w": "Bonjour"}, ...]})
et travail/<nom>.txt (une ligne par phrase avec son temps, pour que Claude lise vite).
Mac : whisper-cli (whisper.cpp). Windows ou sans whisper-cli : faster-whisper (pip).
"""
import json, platform, subprocess, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from commun import ffmpeg, outil, lancer, dossier_projet

MODELES = [Path.home() / "Library/Application Support/whisper.cpp/models" / m
           for m in ("ggml-large-v3-turbo-q5_0.bin", "ggml-large-v3-turbo.bin")]


def wav(src, dst):
    lancer([ffmpeg(), "-y", "-v", "error", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000", str(dst)])


def avec_whisper_cpp(w, langue):
    modele = next((m for m in MODELES if m.exists()), None)
    exe = outil("whisper-cli")
    if not (modele and exe):
        return None
    base = str(w)[:-4]
    lancer([exe, "-m", str(modele), "-f", str(w), "-l", langue, "-ml", "1", "-sow", "-oj", "-of", base, "-np"])
    j = json.loads(Path(base + ".json").read_text(encoding="utf-8", errors="replace"))
    res = []
    for seg in j.get("transcription", []):
        t = seg["text"].strip()
        if not t or t.startswith("["):
            continue
        m = {"s": seg["offsets"]["from"] / 1000, "e": seg["offsets"]["to"] / 1000, "w": t}
        if res and not any(c.isalnum() for c in t):   # ponctuation seule : collée au mot d'avant
            res[-1]["w"] += t
            continue
        res.append(m)
    return res


def avec_faster_whisper(w, langue):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("Aucun moteur de transcription. Dis à Claude : « installe mon éditeur ».")
    m = WhisperModel("large-v3-turbo", device="auto", compute_type="int8")
    segs, _ = m.transcribe(str(w), language=langue, word_timestamps=True, vad_filter=False)
    return [{"s": round(x.start, 3), "e": round(x.end, 3), "w": x.word.strip()} for s in segs for x in (s.words or []) if x.word.strip()]


def lisible(mots):
    lignes, cur, t0 = [], [], None
    for m in mots:
        if t0 is None:
            t0 = m["s"]
        cur.append(m["w"])
        if m["w"][-1:] in ".?!" or len(cur) >= 14:
            lignes.append(f"[{t0:7.2f} → {m['e']:7.2f}] {' '.join(cur)}")
            cur, t0 = [], None
    if cur:
        lignes.append(f"[{t0:7.2f} → {mots[-1]['e']:7.2f}] {' '.join(cur)}")
    return "\n".join(lignes) + "\n"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    langue = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--langue=")), "fr")
    if not args:
        sys.exit(__doc__)
    for src in args:
        src = Path(src)
        travail = dossier_projet(src) / "travail"
        travail.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            w = Path(tmp) / "son.wav"
            wav(src, w)
            res = None if platform.system() == "Windows" else avec_whisper_cpp(w, langue)
            if res is None:
                res = avec_faster_whisper(w, langue)
        (travail / f"{src.stem}.mots.json").write_text(json.dumps({"source": str(src), "mots": res}, ensure_ascii=False, indent=0), encoding="utf-8")
        (travail / f"{src.stem}.txt").write_text(lisible(res), encoding="utf-8")
        print(f"✓ {src.name} : {len(res)} mots → travail/{src.stem}.txt")


if __name__ == "__main__":
    main()
