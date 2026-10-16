#!/usr/bin/env python3
"""Fabrique la vidéo à partir de travail/montage.json.

    python3 rendu.py travail/montage.json              vidéo finale 1080x1920 (export/)
    python3 rendu.py travail/montage.json --apercu     version rapide 540x960 pour vérifier
    python3 rendu.py travail/montage.json --image 3.5  une image PNG à 3,5 s (travail/images/)

Étape 1 : chaque plan devient un petit clip propre (travail/cache/, réutilisé tant qu'il ne change pas).
Étape 2 : on assemble, on pose les incrustations, le hook, les textes, les sous-titres et la musique.
"""
import hashlib, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from commun import ffmpeg, lancer, sonde, kit, mots, dossier_projet, chemin, fichier_police, format_image, adapter_kit, POLICES, W, H, FPS, IMAGE_EXT, DOSSIER_ELEVE

TONEMAP = "zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv"


# ---------- étape 1 : les plans ----------

def clip_plan(projet, p, cache):
    src = chemin(projet, p["source"]).resolve()
    info = sonde(src)
    dur = round((p["fin"] - p["debut"]) * FPS) / FPS
    if dur <= 0:
        raise ValueError(f"Plan vide : {p}")
    avec_son = p.get("son", True) and info["son"]
    cle = hashlib.md5(json.dumps([str(src), src.stat().st_mtime, p["debut"], dur, avec_son, W, H, 3]).encode()).hexdigest()[:12]
    out = cache / f"{src.stem}-{cle}.mkv"
    if out.exists():
        return out, dur
    cmd = [ffmpeg(), "-y", "-v", "error"]
    if info.get("video") and not info.get("image_fixe"):
        cmd += ["-ss", f"{p['debut']:.3f}", "-i", str(src)]
        vf = (TONEMAP + "," if info.get("hdr") else "") + \
            f"fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,format=yuv420p"
        vmap = "0:v:0"
    elif info.get("image_fixe"):
        cmd += ["-loop", "1", "-t", f"{dur:.3f}", "-i", str(src)]
        vf = f"fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,format=yuv420p"
        vmap = "0:v:0"
    else:  # audio seul (voix off) : fond noir, à couvrir d'incrustations
        cmd += ["-ss", f"{p['debut']:.3f}", "-i", str(src), "-f", "lavfi", "-i", f"color=c=black:s={W}x{H}:r={FPS}"]
        vf, vmap = "format=yuv420p", "1:v:0"
    if avec_son:
        af = f"aresample=48000,aformat=channel_layouts=stereo,apad,atrim=0:{dur:.4f},afade=t=in:d=0.008,afade=t=out:st={max(0, dur - 0.012):.4f}:d=0.012"
        cmd += ["-filter_complex", f"[{vmap}]{vf}[v];[0:a:0]{af}[a]", "-map", "[v]", "-map", "[a]"]
    else:
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                "-filter_complex", f"[{vmap}]{vf}[v]", "-map", "[v]", "-map", f"{2 if vmap == '1:v:0' else 1}:a"]
    cmd += ["-frames:v", str(round(dur * FPS)), "-t", f"{dur:.4f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "14",
            "-g", str(FPS), "-c:a", "pcm_s16le", str(out)]
    lancer(cmd)
    return out, dur


def clip_incrustation(projet, inc, fen, cache):
    """Prépare une incrustation vidéo une seule fois, déjà à sa taille finale (plein écran ou fenêtre)."""
    src = chemin(projet, inc["source"]).resolve()
    info = sonde(src)
    d = round(float(inc.get("duree", 1.0)) * FPS) / FPS
    fenetre = inc.get("mode", "plein") == "fenetre"
    L, Hm = fen.get("largeur", 880), fen.get("hauteur_max", 880)
    cle = hashlib.md5(json.dumps([str(src), src.stat().st_mtime, inc.get("debut_source", 0), d, fenetre, L, Hm, W, H, 2]).encode()).hexdigest()[:12]
    out = cache / f"inc-{src.stem}-{cle}.mkv"
    if out.exists():
        return out
    pre = TONEMAP + "," if info.get("hdr") else ""
    taille = f"scale={L}:-2,crop={L}:'min(ih,{Hm})'" if fenetre else \
        f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}"
    if info.get("image_fixe"):
        entree = ["-loop", "1", "-t", f"{d:.3f}", "-i", str(src)]
    else:
        entree = ["-ss", f"{inc.get('debut_source', 0):.3f}", "-i", str(src)]
    lancer([ffmpeg(), "-y", "-v", "error", *entree, "-an", "-vf", f"{pre}fps={FPS},{taille},setsar=1,format=yuv420p",
            "-frames:v", str(round(d * FPS)), "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", str(out)])
    return out


# ---------- sous-titres, hook, textes : un fichier .ass ----------

def couleur(hexa, alpha=0):
    h = (hexa or "#FFFFFF").lstrip("#")
    return f"&H{alpha:02X}{h[4:6]}{h[2:4]}{h[0:2]}".upper()


def style(nom, police, gras, s, align=5, marge=110):
    box = s.get("avec_fond")
    bs = 3 if box else 1
    contour = max(14, s.get("taille", 60) // 4) if box else s.get("contour", 0)
    coul_contour = couleur(s.get("fond", "#000000")) if box else couleur(s.get("couleur_contour", "#000000"))
    return (f"Style: {nom},{police},{s.get('taille', 60)},{couleur(s.get('couleur'))},{couleur(s.get('couleur'))},"
            f"{coul_contour},{couleur('#000000', 0x80)},{gras},0,0,0,100,100,0,0,{bs},{contour},"
            f"{s.get('ombre', 0)},{align},{marge},{marge},0,1")


def t_ass(t):
    t = max(0, t)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def nettoie(txt, maj):
    txt = txt.replace("{", "(").replace("}", ")").replace("\n", " ")
    txt = txt.upper() if maj else txt
    return re.sub(r" ([?!:;»])", r"\\h\1", txt).replace("« ", "«\\h")   # pas de « ? » seul en début de ligne


def blocs_sous_titres(projet, plans_t, n_max):
    """Les mots de toutes les sources, replacés sur le temps de la vidéo finale, groupés par 2-3."""
    tl = []
    for p, off, dur in plans_t:
        if p.get("son", True) is False:
            continue
        ws = mots(p["source"], projet) or []
        for m in ws:
            if m["s"] >= p["debut"] - 0.02 and m["e"] <= p["fin"] + 0.05:
                s = off + max(0, m["s"] - p["debut"])
                e = min(off + dur, off + (m["e"] - p["debut"]))
                tl.append({"s": s, "e": max(e, s + 0.05), "w": m["w"]})
    blocs, cur = [], []
    for i, m in enumerate(tl):
        cur.append(m)
        fin_phrase = m["w"][-1:] in ".?!,;:"
        trou = i + 1 < len(tl) and tl[i + 1]["s"] - m["e"] > 0.45
        long = sum(len(x["w"]) + 1 for x in cur) > 20
        if len(cur) >= n_max or fin_phrase or trou or long:
            blocs.append(cur)
            cur = []
    if cur:
        blocs.append(cur)
    return blocs


def police_element(k, sec):
    """La police d'un élément : la sienne (k[sec]["police"]) sinon celle de la DA."""
    p = (k.get(sec) or {}).get("police") or k["police"]
    return p.get("famille", k["police"]["famille"]), int(p.get("poids", 700 if p.get("gras", True) else 400))


def ecrire_ass(projet, m, k, plans_t, total, chemin, hook_image=False):
    st, hk, tx = k["sous_titres"], k["hook"], k["textes"]
    lignes = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 0",
              "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
              "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
              "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
              style("Sous", *police_element(k, "sous_titres"), st, 5, st.get("marge_cotes", 120)),
              style("Hook", *police_element(k, "hook"), hk, 8, hk.get("marge_cotes", 110)),
              style("Texte", *police_element(k, "textes"), tx, 5, tx.get("marge_cotes", 110)),
              "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    pop = "{\\fscx82\\fscy82\\t(0,110,\\fscx100\\fscy100)}"
    if m.get("sous_titres", True):
        coul_mot = st.get("couleur_mot")
        blocs = blocs_sous_titres(projet, plans_t, int(st.get("mots_par_bloc", 3)))
        for bi, b in enumerate(blocs):
            fin_bloc = min(b[-1]["e"] + 0.25, blocs[bi + 1][0]["s"] if bi + 1 < len(blocs) else total)
            mots_txt = [nettoie(x["w"].rstrip(".,;:"), st.get("majuscules")) for x in b]
            anim = pop if st.get("animation") == "pop" else ""
            pos = f"{{\\an5\\pos({W // 2},{st.get('y', 1220)})}}"
            if not coul_mot:
                lignes.append(f"Dialogue: 1,{t_ass(b[0]['s'])},{t_ass(fin_bloc)},Sous,,0,0,0,,{pos}{anim}{' '.join(mots_txt)}")
                continue
            for wi, x in enumerate(b):
                de = x["s"] if wi else b[0]["s"]
                a = b[wi + 1]["s"] if wi + 1 < len(b) else fin_bloc
                txt = " ".join((f"{{\\c{couleur(coul_mot)}}}{w}{{\\c{couleur(st.get('couleur'))}}}" if j == wi else w)
                               for j, w in enumerate(mots_txt))
                lignes.append(f"Dialogue: 1,{t_ass(de)},{t_ass(a)},Sous,,0,0,0,,{pos}{anim if wi == 0 else ''}{txt}")
    h = m.get("hook")
    if h and h.get("texte") and not hook_image:
        anim = "{\\fscx80\\fscy80\\t(0,160,\\fscx100\\fscy100)}" if hk.get("animation") == "pop" else ""
        lignes.append(f"Dialogue: 3,{t_ass(h.get('de', 0))},{t_ass(min(total, h.get('a', 3)))},Hook,,0,0,0,,"
                      f"{{\\an8\\pos({W // 2},{hk.get('y', 300)})}}{anim}{nettoie(h['texte'], hk.get('majuscules'))}")
    ys = {"haut": round(H * 0.22), "centre": H // 2, "bas": round(H * 0.7)}
    for t in m.get("textes", []):
        y = t.get("y", ys.get(t.get("position", "centre"), H // 2))
        txt = nettoie(t["texte"], tx.get("majuscules")).replace("\\n", "\\N")
        lignes.append(f"Dialogue: 2,{t_ass(t.get('de', 0))},{t_ass(min(total, t.get('a', total)))},Texte,,0,0,0,,"
                      f"{{\\an5\\pos({W // 2},{y})}}{pop if t.get('animation', 'pop') == 'pop' else ''}{txt}")
    chemin.write_text("\n".join(lignes) + "\n", encoding="utf-8")


def polices_ok(k, dossier):
    """Une police absente de l'ordinateur → TikTok Sans (fournie avec le studio), jamais une police système au hasard."""
    for sec in (None, "hook", "sous_titres", "textes"):
        p = k["police"] if sec is None else (k.get(sec) or {}).get("police")
        if p and not fichier_police([dossier], p.get("famille", ""), p.get("poids", 700)):
            print(f"  (police « {p.get('famille')} » absente : TikTok Sans à la place)")
            p["famille"] = "TikTok Sans"


# ---------- le texte du début façon Instagram (image) ----------

def hook_instagram(texte, hk, fichier_police, largeur_max, out):
    """Dessine le texte du début comme le texte natif d'Instagram : une boîte par ligne, coins arrondis,
    lignes fondues en une seule forme. Rendu en 2x puis réduit (bords lisses). Renvoie (largeur, hauteur)."""
    from PIL import Image, ImageDraw, ImageFont
    X = 2
    em = hk.get("taille", 88) * 0.70 * X
    f = ImageFont.truetype(str(fichier_police), round(em))
    if hk.get("majuscules"):
        texte = texte.upper()
    texte = re.sub(r" ([?!:;»])", "\u00a0\\1", texte).replace("« ", "«\u00a0")   # jamais un « ? » seul en début de ligne
    arr = float(hk.get("arrondi", 0.22))
    pad_x, pad_y = em * 0.36, em * 0.07
    rayon = arr * X if arr > 1 else em * arr   # arrondi > 1 : en pixels ; sinon en fraction de la taille
    haut_ligne = em * 1.2
    utile = largeur_max * X - 2 * pad_x
    def couper_lignes(largeur):
        out = []
        for para in texte.split("\n"):
            cur = ""
            for mot in para.split(" "):
                if not mot:
                    continue
                essai = (cur + " " + mot).strip()
                if cur and f.getlength(essai) > largeur:
                    out.append(cur)
                    cur = mot
                else:
                    cur = essai
            if cur:
                out.append(cur)
        return out
    lignes = couper_lignes(utile)
    # lignes équilibrées : la plus petite largeur qui garde le même nombre de lignes (pas de mot orphelin)
    bas, haut = utile * 0.4, utile
    for _ in range(18):
        milieu = (bas + haut) / 2
        if len(couper_lignes(milieu)) <= len(lignes):
            haut = milieu
        else:
            bas = milieu
    lignes = couper_lignes(haut)
    larg = [f.getlength(l) for l in lignes]
    boite = hk.get("avec_fond", True)
    L = int(max(larg) + 2 * pad_x + 4 * X)
    Ht = int(len(lignes) * (haut_ligne + 2 * pad_y) + 4 * X)
    img = Image.new("RGBA", (L, Ht), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = L / 2
    rects = []
    y = 2 * X
    for w in larg:
        h = haut_ligne + 2 * pad_y
        rects.append((cx - w / 2 - pad_x, y, cx + w / 2 + pad_x, y + h))
        y += h
    if boite:
        fond = hk.get("fond", "#FFFFFF")
        for r in rects:
            d.rounded_rectangle(r, radius=rayon, fill=fond)
        for a, b in zip(rects, rects[1:]):   # on soude les lignes entre elles
            x0, x1 = max(a[0], b[0]), min(a[2], b[2])
            d.rectangle((x0, a[3] - rayon, x1, b[1] + rayon), fill=fond)
    contour = 0 if boite else int(hk.get("contour", 0) * X)
    for (x0, y0, x1, y1), ligne in zip(rects, lignes):
        d.text((cx, (y0 + y1) / 2), ligne, font=f, fill=hk.get("couleur", "#000000"), anchor="mm",
               stroke_width=contour, stroke_fill=hk.get("couleur_contour", "#000000"))
    img = img.resize((L // X, Ht // X), Image.LANCZOS)
    img.save(out)
    return img.size


def preparer_hook(m, k, travail):
    """Image du texte du début si Pillow et la police sont là ; sinon le .ass s'en charge (boîtes carrées)."""
    h, hk = m.get("hook"), k["hook"]
    if not (h and h.get("texte")) or hk.get("moteur") == "ass":
        return None
    try:
        import PIL  # noqa
    except ImportError:
        return None
    fam, poids = police_element(k, "hook")
    f = fichier_police([dossier_polices(travail, k)], fam, poids)
    if not f:
        return None
    out = travail / "hook.png"
    w, hh = hook_instagram(h["texte"], hk, f, W - 2 * hk.get("marge_cotes", 100), out)
    return out, w, hh


# ---------- étape 2 : l'assemblage ----------

def dossier_polices(travail, k):
    """Toutes les polices utiles dans un seul dossier : celles du studio + celles de l'élève (ma-da/polices)."""
    import shutil
    d = travail / "polices"
    d.mkdir(exist_ok=True)
    sources = [POLICES, DOSSIER_ELEVE / "ma-da" / "polices"]
    if k.get("_fichier"):
        sources.append(Path(k["_fichier"]).parent / "polices")
    for s in sources:
        for f in list(s.glob("*.ttf")) + list(s.glob("*.otf")) if s.exists() else []:
            if not (d / f.name).exists():
                shutil.copy2(f, d / f.name)
    return d


def echappe_filtre(p):
    return str(p).replace("\\", "/").replace(":", "\\:").replace("'", "\\'").replace(",", "\\,")


def preparer(montage_path):
    """Lit montage.json, choisit le format d'image, charge la DA adaptée à ce format. Sert aussi au studio."""
    global W, H
    montage_path = Path(montage_path).resolve()
    projet = dossier_projet(montage_path)
    m = json.loads(montage_path.read_text(encoding="utf-8"))
    W, H = format_image(m, projet)
    k = adapter_kit(kit(m.get("da", "auto"), projet), W, H)
    for section, valeurs in (m.get("ajustements") or {}).items():   # réglages de DA pour CETTE vidéo seulement
        if isinstance(valeurs, dict) and isinstance(k.get(section), dict):
            k[section].update(valeurs)
    return montage_path, projet, m, k


def plans_temps(m):
    """[(plan, début sur la vidéo finale, durée)] sans rien encoder."""
    out, off = [], 0.0
    for p in m.get("plans", []):
        dur = round((p["fin"] - p["debut"]) * FPS) / FPS
        out.append((p, off, dur))
        off += dur
    return out, off


def rendre(montage_path, apercu=False, image=None, sans_textes=False, sortie=None):
    montage_path, projet, m, k = preparer(montage_path)
    travail = projet / "travail"
    # cache commun à toutes les vidéos de l'élève : un rush déjà préparé n'est jamais refait
    cache = DOSSIER_ELEVE / ".cache" if DOSSIER_ELEVE.exists() else travail / "cache"
    cache.mkdir(parents=True, exist_ok=True)
    if not m.get("plans"):
        sys.exit("montage.json n'a aucun plan.")
    if m.get("zoom"):
        print("  (les zooms ne sont pas encore gérés dans cette version, ils sont ignorés)")

    plans_t, liste, off = [], [], 0.0
    for i, p in enumerate(m["plans"]):
        clip, dur = clip_plan(projet, p, cache)
        plans_t.append((p, off, dur))
        liste.append(f"file '{clip.as_posix()}'")
        off += dur
        print(f"\r  plans prêts : {i + 1}/{len(m['plans'])}", end="", flush=True)
    print()
    total = off
    concat = travail / "concat.txt"
    concat.write_text("\n".join(liste) + "\n", encoding="utf-8")
    ass = travail / "textes.ass"
    polices_ok(k, dossier_polices(travail, k))
    hook_img = None if sans_textes else preparer_hook(m, k, travail)
    ecrire_ass(projet, m, k, plans_t, total, ass, hook_image=bool(hook_img))

    cmd = [ffmpeg(), "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(concat)]
    filt, vlab, n_in = [], "[0:v]", 1
    fen = k["fenetre"]
    for j, inc in enumerate(m.get("incrustations", [])):
        a, d = float(inc["a"]), float(inc.get("duree", 1.0))
        cmd += ["-i", str(clip_incrustation(projet, inc, fen, cache))]
        pre = ""
        if inc.get("mode", "plein") == "fenetre":
            L, R = fen.get("largeur", 880), fen.get("arrondi", 40)
            coin = (f"geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='if(gt(abs(W/2-X),W/2-{R})*gt(abs(H/2-Y),H/2-{R}),"
                    f"if(lte(hypot({R}-(W/2-abs(W/2-X)),{R}-(H/2-abs(H/2-Y))),{R}),255,0),255)'")
            filt.append(f"[{n_in}:v]format=rgba,{coin},"
                        f"fade=t=in:st=0:d=0.12:alpha=1,setpts=PTS-STARTPTS+{a}/TB[i{j}]")
            px = fen["x"] if "x" in fen else "(W-w)/2"
            pos = f"x={px}:y='{fen.get('y', 260)}+40*max(0,1-(t-{a})/0.15)'"
        else:
            filt.append(f"[{n_in}:v]setpts=PTS-STARTPTS+{a}/TB[i{j}]")
            pos = "x=0:y=0"
        filt.append(f"{vlab}[i{j}]overlay={pos}:enable='between(t,{a},{a + d})':eof_action=pass[b{j}]")
        vlab, n_in = f"[b{j}]", n_in + 1
    if hook_img:   # texte du début façon Instagram : petite entrée « pop » puis fixe
        png, hw, hh = hook_img
        h = m["hook"]
        de, a_ = float(h.get("de", 0)), min(total, float(h.get("a", 3)))
        y0 = k["hook"].get("y", 300)
        cmd += ["-loop", "1", "-t", f"{a_ - de:.3f}", "-i", str(png)]
        anim = "scale=w='trunc(iw*min(1,0.82+0.18*t/0.16)/2)*2':h=-2:eval=frame,fade=t=in:st=0:d=0.08:alpha=1," \
            if k["hook"].get("animation", "pop") == "pop" else ""
        filt.append(f"[{n_in}:v]format=rgba,{anim}setpts=PTS-STARTPTS+{de}/TB[hk]")
        filt.append(f"{vlab}[hk]overlay=x='(W-w)/2':y='{y0}+({hh}-h)/2':enable='between(t,{de},{a_})':eof_action=pass[bh]")
        vlab, n_in = "[bh]", n_in + 1
    fin_v = "null" if sans_textes else f"subtitles='{echappe_filtre(ass)}':fontsdir='{echappe_filtre(dossier_polices(travail, k))}'"
    if apercu:
        fin_v += f",scale={W // 2}:{H // 2}"
    filt.append(f"{vlab}{fin_v},format=yuv420p[vout]")

    mu = m.get("musique") if image is None else None
    if mu and mu.get("source"):
        cmd += ["-stream_loop", "-1", "-ss", f"{mu.get('debut', 0):.3f}", "-i", str(chemin(projet, mu["source"]).resolve())]
        niveau = float(mu.get("niveau_db", k["musique"]["niveau_db"]))   # en LU sous la voix (0 = musique au premier plan)
        fin_f = max(0.0, total - 1.2)
        filt.append(f"[{n_in}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{total:.3f},"
                    f"loudnorm=I={-16 + niveau:.1f}:TP=-2:LRA=11,afade=t=in:d=0.02,afade=t=out:st={fin_f:.3f}:d=1.2[mus]")
        filt.append("[0:a]loudnorm=I=-16:TP=-2:LRA=11[voix]")
        filt.append("[voix][mus]amix=inputs=2:duration=first:normalize=0[mix]")
        alab = "[mix]"
    else:
        alab = "[0:a]"
    filt.append(f"{alab}loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]")

    if image is not None:
        out = travail / "images" / f"image-{float(image):06.2f}.png"
        out.parent.mkdir(exist_ok=True)
        cmd += ["-filter_complex", ";".join(filt[:-1]), "-map", "[vout]", "-ss", f"{float(image):.3f}", "-frames:v", "1", str(out)]
    else:
        sortie_forcee, sortie = sortie, m.get("sortie", "export/video-v1.mp4")
        out = projet / sortie
        if apercu:
            out = travail / ("apercu-" + Path(sortie).name)
        if sortie_forcee:
            out = Path(sortie_forcee)
        out.parent.mkdir(parents=True, exist_ok=True)
        enc = ["-c:v", "libx264", "-preset", "ultrafast" if apercu else "medium", "-crf", "26" if apercu else "18",
               "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart"]
        cmd += ["-filter_complex", ";".join(filt), "-map", "[vout]", "-map", "[aout]", *enc, "-t", f"{total:.3f}", str(out)]
    lancer(cmd)
    print(f"✓ {out}  ({total:.1f} s)")
    return out


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    img = args[args.index("--image") + 1] if "--image" in args else None
    rendre(args[0], apercu="--apercu" in args, image=img)
