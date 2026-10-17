#!/usr/bin/env python3
"""La banque de musiques du Studio : celle de Théo, synchronisée toute seule depuis son ordinateur.

    python3 musiques.py --code <code d'accès>   enregistre le code (étape « Active la banque de musiques » du tuto, lancée par l'élève lui-même) puis synchronise
    python3 musiques.py --sync [--silencieux]   récupère les nouveaux morceaux (lancé à chaque ouverture de Claude)
    python3 musiques.py --liste                 les musiques disponibles, par style

Chez Théo, chaque morceau ajouté dans sa bibliothèque part tout seul (toutes les 15 min) vers un dépôt GitHub privé.
Chez l'élève, ce dépôt est lu avec une clé de lecture seule (le code d'accès), sans compte GitHub.
Les morceaux arrivent dans ~/Editeur/musiques/<style>/. Le code n'est jamais écrit dans le dépôt public du Studio.
Les morceaux libres de droits fournis avec le Studio (musiques-libres/) sont copiés aussi.
"""
import base64, os, platform, shutil, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from commun import DOSSIER_ELEVE, EDITEUR, AUDIO_EXT

MUSIQUES = DOSSIER_ELEVE / "musiques"
CLE = DOSSIER_ELEVE / ".config" / "musiques.cle"
DEPOT = "git@github.com:theoprs812/studio-musiques.git"
LIBRES = EDITEUR / "musiques-libres"


def dire(txt, silencieux):
    if not silencieux:
        print(txt, flush=True)


def copier_libres():
    for f in LIBRES.rglob("*") if LIBRES.exists() else []:
        if f.suffix.lower() in AUDIO_EXT:
            dst = MUSIQUES / f.relative_to(LIBRES)
            if not dst.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dst)


def git(*args):
    env = dict(os.environ)
    nul = "NUL" if platform.system() == "Windows" else "/dev/null"
    env["GIT_SSH_COMMAND"] = (f'ssh -i "{CLE}" -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new '
                              f'-o UserKnownHostsFile="{DOSSIER_ELEVE / ".config" / "known_hosts"}" -o LogLevel=ERROR')
    return subprocess.run(["git", "-C", str(MUSIQUES), *args], capture_output=True, text=True, env=env)


def synchroniser(silencieux=False):
    MUSIQUES.mkdir(parents=True, exist_ok=True)
    copier_libres()
    if not CLE.exists():
        dire("Pas de code d'accès à la banque de musiques : colle la commande de l'étape « Active la banque de musiques » du tuto dans le Terminal (ou PowerShell).", silencieux)
        return 0
    if not (MUSIQUES / ".git").exists():
        git("init", "-q", "-b", "main")
        git("remote", "add", "origin", DEPOT)
    avant = set(git("ls-files").stdout.splitlines())
    r = git("fetch", "-q", "--depth", "1", "origin", "main")
    if r.returncode != 0:
        dire(f"Banque de musiques injoignable pour l'instant ({r.stderr.strip()[:140]}).", silencieux)
        return 0
    git("reset", "-q", "--hard", "origin/main")
    apres = set(git("ls-files").stdout.splitlines())
    nouveaux = [f for f in apres - avant if Path(f).suffix.lower() in AUDIO_EXT]
    for f in sorted(nouveaux)[:20]:
        dire(f"  + {f}", silencieux)
    dire(f"✓ Banque de musiques à jour ({len(nouveaux)} nouveau(x) morceau(x), {len([f for f in apres if Path(f).suffix.lower() in AUDIO_EXT])} en tout).", silencieux)
    return len(nouveaux)


def enregistrer_code(code):
    CLE.parent.mkdir(parents=True, exist_ok=True)
    CLE.write_bytes(base64.b64decode(code.strip()))
    if platform.system() != "Windows":
        os.chmod(CLE, 0o600)


def liste():
    if not MUSIQUES.exists():
        print("(aucune musique)")
        return
    for d in sorted(p for p in MUSIQUES.iterdir() if p.is_dir()):
        morceaux = sorted(f.stem for f in d.iterdir() if f.suffix.lower() in AUDIO_EXT)
        if morceaux:
            print(f"{d.name} ({len(morceaux)}) : " + " · ".join(morceaux))


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == "--code" and len(a) > 1:
        enregistrer_code(a[1])
        synchroniser()
    elif a[0] == "--sync":
        synchroniser(silencieux="--silencieux" in a)
    elif a[0] == "--liste":
        liste()
    else:
        sys.exit(__doc__)
