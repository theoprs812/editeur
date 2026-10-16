#!/usr/bin/env python3
"""Les polices du Studio.

    python3 police.py --pack               le pack de base : Instagram Sans + les polices gratuites les plus utilisées en reels
    python3 police.py "Montserrat"         une police Google Fonts (gratuite), toutes ses graisses
    python3 police.py --instagram-sans     Instagram Sans seule (usage personnel, voir plus bas)
    python3 police.py --liste              les polices installées

Les fichiers vont dans ~/Editeur/ma-da/polices/ (nommés Famille_Nom-graisse.ttf). Le rendu et le Studio les trouvent tout seuls.
Instagram Sans : la police du texte natif d'Instagram. Meta ne la publie pas ; elle est gratuite pour un usage
personnel, récupérée sur un site de polices tiers et installée seulement sur l'ordinateur de l'élève, jamais partagée.
(Méthode reprise de l'AI Video Editor de Cut30.)
"""
import re, struct, sys, urllib.parse, urllib.request, zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from commun import DOSSIER_ELEVE

DOSSIER = DOSSIER_ELEVE / "ma-da" / "polices"
GRAISSES = [400, 500, 600, 700, 800, 900]
PACK = ["Montserrat", "Inter", "Poppins", "Anton", "Bebas Neue", "Archivo Black", "DM Sans", "Oswald", "Roboto",
        "Bricolage Grotesque", "Playfair Display", "Space Grotesk", "Manrope", "Lexend", "League Spartan"]
# Les polices du texte natif d'Instagram : (nom du fichier source, famille, graisse)
INSTAGRAM = [("Instagram Sans Light", "Instagram Sans", 300), ("Instagram Sans", "Instagram Sans", 400),
             ("Instagram Sans Medium", "Instagram Sans", 500), ("Instagram Sans Bold", "Instagram Sans", 700),
             ("Instagram Sans Condensed", "Instagram Sans Condensed", 400), ("Instagram Sans Condensed Bold", "Instagram Sans Condensed", 700),
             ("Instagram Sans Headline", "Instagram Sans Headline", 400)]
URL_IG = "https://fonts.cdnfonts.com/s/93599/{nom}.woff"
POLICES_MAC = Path.home() / "Library" / "Fonts"


def telecharger(url, ua="Wget/1.21"):
    p = urllib.parse.urlsplit(url)
    url = urllib.parse.urlunsplit(p._replace(path=urllib.parse.quote(p.path)))
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": ua}), timeout=30) as r:
        return r.read()


def woff_vers_ttf(data):
    """Déballe un fichier WOFF 1.0 en police TrueType/OpenType installable."""
    if data[:4] != b"wOFF":
        raise ValueError("pas un fichier WOFF")
    saveur, _, n = struct.unpack(">4sIH", data[4:14])
    tables = []
    for i in range(n):
        tag, off, lc, lo, cs = struct.unpack(">4sIIII", data[44 + 20 * i: 64 + 20 * i])
        brut = data[off: off + lc]
        t = zlib.decompress(brut) if lc < lo else brut
        tables.append((tag, cs, t))
    tables.sort(key=lambda e: e[0])
    p = 1
    while p * 2 <= n:
        p *= 2
    sr = p * 16
    tete = struct.pack(">4sHHHH", saveur, n, sr, p.bit_length() - 1, n * 16 - sr)
    recs, corps, off = b"", b"", 12 + 16 * n
    for tag, cs, t in tables:
        recs += struct.pack(">4sIII", tag, cs, off, len(t))
        bloc = t + b"\0" * (-len(t) % 4)
        corps += bloc
        off += len(bloc)
    return tete + recs + corps


def installer_google(famille, silencieux=False):
    DOSSIER.mkdir(parents=True, exist_ok=True)
    ok = []
    for g in GRAISSES:
        dst = DOSSIER / f"{famille.replace(' ', '_')}-{g}.ttf"
        if dst.exists():
            ok.append(g)
            continue
        try:
            css = telecharger(f"https://fonts.googleapis.com/css2?family={famille.replace(' ', '+')}:wght@{g}").decode()
        except Exception:
            continue
        m = re.search(r"url\((https://[^)]+\.ttf)\)", css)
        if m:
            dst.write_bytes(telecharger(m.group(1)))
            ok.append(g)
    if not ok:
        print(f"✗ « {famille} » introuvable sur Google Fonts (vérifie l'orthographe).")
    elif not silencieux:
        print(f"✓ {famille} ({', '.join(map(str, ok))})")
    return bool(ok)


def installer_instagram_sans():
    """Toutes les polices Instagram, dans ~/Editeur/ma-da/polices et (Mac) dans ~/Library/Fonts,
    pour que CapCut et les autres applis les proposent aussi."""
    import platform, shutil
    DOSSIER.mkdir(parents=True, exist_ok=True)
    deja = {f.name.replace("_", "").replace(" ", "").split("-")[0] for f in POLICES_MAC.glob("*.[ot]tf")} if POLICES_MAC.exists() else set()
    deja -= {f"{fam.replace(' ', '')}" for _, fam, _ in INSTAGRAM if any(POLICES_MAC.glob(f"{fam.replace(' ', '_')}-*"))}
    for nom, famille, g in INSTAGRAM:
        dst = DOSSIER / f"{famille.replace(' ', '_')}-{g}.ttf"
        if not dst.exists():
            try:
                data = telecharger(URL_IG.format(nom=nom), ua="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)")
            except Exception:
                continue
            dst.write_bytes(woff_vers_ttf(data) if data[:4] == b"wOFF" else data)
        if platform.system() == "Darwin":
            POLICES_MAC.mkdir(parents=True, exist_ok=True)
            mac = POLICES_MAC / dst.name
            if not mac.exists() and famille.replace(" ", "") not in deja:   # pas de doublon si la police est déjà installée
                shutil.copy2(dst, mac)
    print("✓ Polices Instagram : Instagram Sans, Instagram Sans Condensed, Instagram Sans Headline "
          "(usage personnel : installées sur cet ordinateur seulement, jamais partagées)")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == "--liste":
        print("\n".join(sorted(p.name for p in DOSSIER.glob("*.[ot]tf"))) if DOSSIER.exists() else "(aucune)")
    elif a[0] == "--instagram-sans":
        installer_instagram_sans()
    elif a[0] == "--pack":
        try:
            installer_instagram_sans()
        except Exception as e:
            print(f"✗ Instagram Sans pas récupérée ({e}) : la DA prendra TikTok Sans à la place.")
        for f in PACK:
            installer_google(f)
    else:
        installer_google(" ".join(a))
