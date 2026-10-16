#!/usr/bin/env python3
"""Envoie le montage dans CapCut (ordinateur) : un vrai projet CapCut, prêt à retoucher.

    python3 capcut.py travail/montage.json [--ouvrir]

Le projet « Editeur - <nom de la vidéo> » apparaît dans l'accueil de CapCut avec, chacun sur sa piste :
les coupes (rushes d'origine, pleine qualité), les b-roll, le texte du début, les sous-titres (un bloc par
groupe de mots, modifiables un par un) et la musique. L'élève retouche une coupe, corrige un sous-titre, exporte.
CapCut doit être FERMÉ pendant l'envoi (il réécrit sa liste de projets en quittant).
Basé sur pycapcut (installé par le studio).
"""
import json, os, platform, re, shutil, subprocess, sys, time, uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import rendu
from commun import ffmpeg, sonde, chemin, FPS

US = 1_000_000


def dossier_capcut():
    if platform.system() == "Windows":
        return Path(os.environ.get("LOCALAPPDATA", "")) / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft"
    return Path.home() / "Movies" / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft"


def capcut_ouvert():
    if platform.system() == "Windows":
        r = subprocess.run(["tasklist"], capture_output=True, text=True)
        return "CapCut.exe" in r.stdout
    return subprocess.run(["pgrep", "-x", "CapCut"], capture_output=True).returncode == 0


def rgb(h):
    h = (h or "#FFFFFF").lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def loudness(f, debut=0.0, duree=60.0):
    r = subprocess.run([ffmpeg(), "-v", "info", "-ss", f"{debut:.2f}", "-t", f"{duree:.2f}", "-i", str(f), "-vn",
                        "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True)
    m = re.findall(r"I:\s+(-?[0-9.]+) LUFS", r.stderr)
    return float(m[-1]) if m else -20.0


def police_capcut(cc, famille):
    """Les polices que CapCut connaît ; sinon la police par défaut de CapCut."""
    table = {"montserrat": "Montserrat", "poppins": "Poppins_Bold"}
    nom = table.get(str(famille).lower())
    return getattr(cc.FontType, nom, None) if nom else None


def envoyer(montage_path, ouvrir=False):
    try:
        import pycapcut as cc
    except ImportError:
        sys.exit("pycapcut manque. Dis à Claude : « installe mon studio ».")
    racine = dossier_capcut()
    if not racine.exists():
        sys.exit("CapCut n'est pas installé sur cet ordinateur (ou n'a jamais été ouvert). Installe-le depuis capcut.com, ouvre-le une fois, puis recommence.")
    if capcut_ouvert():
        sys.exit("CapCut est ouvert : ferme-le complètement (Cmd+Q sur Mac), puis recommence.")

    montage_path, projet, m, k = rendu.preparer(montage_path)
    W, H = rendu.W, rendu.H
    plans_t, total = rendu.plans_temps(m)

    nom = f"Editeur - {projet.name}"
    n = 2
    while (racine / nom).exists():
        nom = f"Editeur - {projet.name} v{n}"
        n += 1
    dossier = cc.DraftFolder(str(racine))
    script = dossier.create_draft(nom, W, H, FPS)
    try:
        construire(cc, script, projet, m, k, W, H, plans_t, total, racine / nom / "Resources" / "editeur")
    except Exception:
        shutil.rmtree(racine / nom, ignore_errors=True)   # pas de projet à moitié fait dans CapCut
        raise
    script.save()
    inscrire(racine, nom, total)
    print(f"✓ Projet CapCut « {nom} » créé ({total:.1f} s). Ouvre CapCut : il est en haut de tes projets.")
    if ouvrir:
        if platform.system() == "Darwin":
            subprocess.Popen(["open", "-a", "CapCut"])
        else:
            subprocess.Popen(["cmd", "/c", "start", "", "capcut://"], shell=False)
    return nom


def lier_media(src, dossier_media):
    """CapCut Mac est « sandboxé » : il ne lit que ce qui est dans ~/Movies. On y relie le fichier (lien physique,
    zéro espace disque en plus), ou on le copie si le lien est impossible. Windows : rien à faire."""
    src = Path(src)
    if platform.system() != "Darwin":
        return str(src)
    dossier_media.mkdir(parents=True, exist_ok=True)
    dst = dossier_media / src.name
    i = 2
    while dst.exists() and not os.path.samefile(dst, src):
        dst = dossier_media / f"{src.stem}-{i}{src.suffix}"
        i += 1
    if not dst.exists():
        try:
            os.link(src, dst)
        except OSError:
            shutil.copy2(src, dst)
    return str(dst)


POLICES_TEXTES = {}   # id du texte CapCut → fichier de police (Instagram Sans, etc.)


def police_locale(k, sec, dossier_media):
    """Le fichier de la police d'un élément, relié dans le projet (CapCut ne lit que ~/Movies)."""
    from commun import fichier_police, DOSSIER_ELEVE, POLICES
    p = (k.get(sec) or {}).get("police") or k["police"]
    f = fichier_police([DOSSIER_ELEVE / "ma-da" / "polices", POLICES], p.get("famille", ""), p.get("poids", 700))
    return (lier_media(f, dossier_media), p.get("famille")) if f else None


def construire(cc, script, projet, m, k, W, H, plans_t, total, dossier_media):
    media = lambda f: lier_media(f, dossier_media)
    POLICES_TEXTES.clear()
    pol_st, pol_hk = police_locale(k, "sous_titres", dossier_media), police_locale(k, "hook", dossier_media)

    # 1. Les coupes, sur la piste principale (rushes d'origine)
    script.add_track(cc.TrackType.video)
    voix_ref = None
    for p, off, dur in plans_t:
        src = chemin(projet, p["source"]).resolve()
        info = sonde(src)
        reglage = None
        if info.get("video") and not info.get("image_fixe"):
            sw, sh = info["largeur"], info["hauteur"]
            contenir, couvrir = min(W / sw, H / sh), max(W / sw, H / sh)
            if abs(couvrir / contenir - 1) > 0.01:
                reglage = cc.ClipSettings(scale_x=couvrir / contenir, scale_y=couvrir / contenir)
        if not info.get("image_fixe"):   # jamais au-delà de la fin du fichier (arrondis d'images)
            dur = min(dur, info["duree"] - p["debut"] - 0.001)
        avec_son = p.get("son", True) is not False and info.get("son")
        if avec_son and voix_ref is None:
            voix_ref = (src, p["debut"])
        t0, t1 = round(off * US), round((off + dur) * US)   # bornes arrondies une fois : jamais de chevauchement
        seg = cc.VideoSegment(media(src), cc.trange(t0, t1 - t0),
                              source_timerange=cc.trange(round(p["debut"] * US), t1 - t0),
                              volume=1.0 if avec_son else 0.0, clip_settings=reglage)
        script.add_segment(seg)

    # 2. Les b-roll, sur une piste au-dessus
    fen = k["fenetre"]
    if m.get("incrustations"):
        script.add_track(cc.TrackType.video, "b-roll", relative_index=1)
        for inc in m["incrustations"]:
            src = chemin(projet, inc["source"]).resolve()
            info = sonde(src)
            sw, sh = info.get("largeur", W), info.get("hauteur", H)
            contenir = min(W / sw, H / sh)
            if inc.get("mode", "plein") == "fenetre":
                L = fen.get("largeur", 880)
                ech = L / (sw * contenir)
                haut = sh * contenir * ech
                cx = fen["x"] + L / 2 if "x" in fen else W / 2
                cy = fen.get("y", 260) + haut / 2
                reglage = cc.ClipSettings(scale_x=ech, scale_y=ech, transform_x=(cx - W / 2) / (W / 2), transform_y=-(cy - H / 2) / (H / 2))
            else:
                ech = max(W / sw, H / sh) / contenir
                reglage = cc.ClipSettings(scale_x=ech, scale_y=ech)
            d = float(inc.get("duree", 1.0))
            if not info.get("image_fixe"):
                d = min(d, info["duree"] - float(inc.get("debut_source", 0)) - 0.001)
            kw = {} if info.get("image_fixe") else {"source_timerange": cc.trange(round(float(inc.get("debut_source", 0)) * US), round(d * US))}
            script.add_segment(cc.VideoSegment(media(src), cc.trange(round(float(inc["a"]) * US), round(d * US)), volume=0.0,
                                               clip_settings=reglage, **kw), "b-roll")

    # 3. Les sous-titres, un bloc par groupe de mots
    st = k["sous_titres"]
    if m.get("sous_titres", True):
        script.add_track(cc.TrackType.text, "sous-titres")
        blocs = rendu.blocs_sous_titres(projet, plans_t, int(st.get("mots_par_bloc", 3)))
        fam = ((st.get("police") or k["police"]).get("famille"))
        for i, b in enumerate(blocs):
            fin = min(b[-1]["e"] + 0.25, blocs[i + 1][0]["s"] if i + 1 < len(blocs) else total)
            texte = " ".join(w["w"].rstrip(".,;:") for w in b)
            texte = texte.upper() if st.get("majuscules") else texte
            debut = round(b[0]["s"] * US)
            seg = cc.TextSegment(texte, cc.trange(debut, max(round(fin * US) - debut, 100_000)),
                                 font=police_capcut(cc, fam),
                                 style=cc.TextStyle(size=st.get("taille", 80) / 6.5, bold=True, color=rgb(st.get("couleur")), align=1,
                                                    auto_wrapping=True, max_line_width=0.8),
                                 border=cc.TextBorder(color=rgb(st.get("couleur_contour")), width=min(100, st.get("contour", 6) * 7)) if st.get("contour") else None,
                                 clip_settings=cc.ClipSettings(transform_y=-(st.get("y", 1330) - H / 2) / (H / 2)))
            script.add_segment(seg, "sous-titres")
            if pol_st:
                POLICES_TEXTES[seg.material_id] = pol_st

    # 4. Le texte du début
    h, hk = m.get("hook"), k["hook"]
    if h and h.get("texte"):
        script.add_track(cc.TrackType.text, "texte du début", relative_index=2)
        texte = h["texte"].upper() if hk.get("majuscules") else h["texte"]
        de, a = float(h.get("de", 0)), min(total, float(h.get("a", 3)))
        fam = ((hk.get("police") or k["police"]).get("famille"))
        lignes = max(1, round(len(texte) / 24))
        cy = hk.get("y", 300) + lignes * hk.get("taille", 88) * 0.6
        seg = cc.TextSegment(texte, cc.trange(round(de * US), round((a - de) * US)), font=police_capcut(cc, fam),
                             style=cc.TextStyle(size=hk.get("taille", 88) / 8, bold=True, color=rgb(hk.get("couleur")), align=1,
                                                auto_wrapping=True, max_line_width=0.78),
                             background=cc.TextBackground(color=hk.get("fond", "#FFFFFF"), round_radius=0.35, style=1) if hk.get("avec_fond") else None,
                             clip_settings=cc.ClipSettings(transform_y=-(cy - H / 2) / (H / 2)))
        script.add_segment(seg, "texte du début")
        if pol_hk:
            POLICES_TEXTES[seg.material_id] = pol_hk

    # 5. La musique, calée sur la voix
    mu = m.get("musique")
    if mu and mu.get("source"):
        src = chemin(projet, mu["source"]).resolve()
        duree_mu = sonde(src)["duree"] - float(mu.get("debut", 0))
        niveau = float(mu.get("niveau_db", k["musique"]["niveau_db"]))
        if voix_ref and niveau < 0:
            gain = loudness(voix_ref[0], voix_ref[1], 30) + niveau - loudness(src, float(mu.get("debut", 0)), 60)
        else:
            gain = -14 - loudness(src, float(mu.get("debut", 0)), 60)
        script.add_track(cc.TrackType.audio, "musique")
        d = min(total, duree_mu)
        script.add_segment(cc.AudioSegment(media(src), cc.trange(0, round(d * US)),
                                           source_timerange=cc.trange(round(float(mu.get("debut", 0)) * US), round(d * US)),
                                           volume=round(min(1.0, 10 ** (gain / 20)), 3)), "musique")



def poser_polices(contenu):
    """Remplace la police par défaut de CapCut par la vraie (Instagram Sans…), comme une police système."""
    if not POLICES_TEXTES:
        return
    j = json.loads(contenu.read_text(encoding="utf-8"))
    for t in j.get("materials", {}).get("texts", []):
        pol = POLICES_TEXTES.get(t.get("id"))
        if not pol:
            continue
        chemin_f, titre = pol
        t.update(font_path=chemin_f, font_title=titre, font_id="", font_resource_id="", font_name="")
        try:
            c = json.loads(t["content"])
            for st in c.get("styles", []):
                st["font"] = {"path": chemin_f, "id": ""}
            t["content"] = json.dumps(c, ensure_ascii=False)
        except (KeyError, ValueError):
            pass
    contenu.write_text(json.dumps(j, ensure_ascii=False), encoding="utf-8")


def version_locale(racine):
    """Les numéros de version du CapCut de l'élève, lus dans son projet le plus récent.
    Sans ça, CapCut dit « créé avec une version plus récente » et refuse d'ouvrir."""
    projets = sorted((p for p in racine.glob("*/draft_info.json") if not p.parent.name.startswith("Editeur - ")),
                     key=lambda p: p.stat().st_mtime, reverse=True)
    for p in projets[:5]:
        try:
            j = json.loads(p.read_text(encoding="utf-8"))
        except (ValueError, UnicodeDecodeError):
            continue   # projet chiffré (versions récentes) : on essaie le suivant
        if j.get("new_version") and j.get("platform"):
            return {c: j[c] for c in ("version", "new_version", "platform", "last_modified_platform") if c in j}
    return None


def aligner_version(d, racine):
    v = version_locale(racine)
    if not v:
        return
    for nomf in ("draft_content.json", "draft_info.json"):
        f = d / nomf
        if f.exists():
            j = json.loads(f.read_text(encoding="utf-8"))
            j.update(v)
            f.write_text(json.dumps(j, ensure_ascii=False), encoding="utf-8")


def inscrire(racine, nom, total):
    """Complète la fiche du projet et l'ajoute à la liste des projets de CapCut (sauvegarde de la liste avant)."""
    d = racine / nom
    contenu = d / "draft_content.json"
    poser_polices(contenu)
    shutil.copy2(contenu, d / "draft_info.json")   # CapCut ordinateur lit draft_info.json, d'autres versions draft_content.json
    aligner_version(d, racine)
    maintenant = int(time.time() * US)
    did = str(uuid.uuid4()).upper()
    meta_p = d / "draft_meta_info.json"
    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    meta.update(draft_fold_path=str(d), draft_name=nom, draft_root_path=str(racine), draft_id=did,
                tm_draft_create=maintenant, tm_draft_modified=maintenant, tm_duration=int(total * US))
    meta_p.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    racine_p = racine / "root_meta_info.json"
    if racine_p.exists():
        shutil.copy2(racine_p, racine / f"root_meta_info.avant-editeur.json")
        r = json.loads(racine_p.read_text(encoding="utf-8"))
        fiche = {"draft_cloud_last_action_download": False, "draft_cloud_purchase_info": "", "draft_cloud_template_id": "",
                 "draft_cloud_tutorial_info": "", "draft_cloud_videocut_purchase_info": "", "draft_cover": str(d / "draft_cover.jpg"),
                 "draft_fold_path": str(d), "draft_id": did, "draft_is_ai_shorts": False, "draft_is_invisible": False,
                 "draft_json_file": str(d / "draft_info.json"), "draft_name": nom, "draft_new_version": "",
                 "draft_root_path": str(racine), "draft_timeline_materials_size": 0, "draft_type": "",
                 "tm_draft_cloud_completed": "", "tm_draft_cloud_modified": 0, "tm_draft_create": maintenant,
                 "tm_draft_modified": maintenant, "tm_draft_removed": 0, "tm_duration": int(total * US)}
        r.setdefault("all_draft_store", []).insert(0, fiche)
        if isinstance(r.get("draft_ids"), int):
            r["draft_ids"] += 1
        racine_p.write_text(json.dumps(r, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    envoyer(a[0], ouvrir="--ouvrir" in a)
