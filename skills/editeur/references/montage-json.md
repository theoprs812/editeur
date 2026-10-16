# montage.json : la recette d'une vidéo

Chaque vidéo a un fichier `travail/montage.json`. Claude l'écrit, `outils/rendu.py` le transforme en MP4.
On ne touche jamais aux fichiers d'origine : tout se lit dans `rushes/`, `b-roll/`, `musique/`, tout s'écrit dans `travail/` et `export/`.

Tous les temps sont en secondes. `debut` / `fin` = temps DANS le fichier source. `a` = temps sur la vidéo finale.

```json
{
  "format": "yap",
  "sortie": "export/ma-video-v1.mp4",
  "da": "auto",
  "plans": [
    {"source": "rushes/IMG_1234.MOV", "debut": 12.30, "fin": 18.75},
    {"source": "rushes/IMG_1234.MOV", "debut": 21.10, "fin": 25.40},
    {"source": "b-roll/plage.mp4", "debut": 2.0, "fin": 3.0, "son": false}
  ],
  "incrustations": [
    {"source": "b-roll/cafe.mp4", "a": 4.2, "duree": 1.0, "debut_source": 0.5, "mode": "plein"},
    {"source": "b-roll/capture.png", "a": 9.0, "duree": 2.0, "mode": "fenetre"}
  ],
  "hook": {"texte": "J'ai arrêté de poster tous les jours", "de": 0, "a": 3.0},
  "sous_titres": true,
  "textes": [{"texte": "3 erreurs que tout le monde fait", "de": 0, "a": 6.5, "position": "centre"}],
  "musique": {"source": "musique/son.mp3", "debut": 0, "niveau_db": -15},
  "zoom": []
}
```

## Les champs

| Champ | Rôle |
|---|---|
| `format_image` | `"9:16"` (par défaut), `"origine"` (garde le format du rush : 16:9 si filmé à l'horizontale), `"16:9"`, `"4:5"`, `"1:1"` |
| `format` | `yap`, `talking-head`, `vlog`, `one-shot`, `dix-shots`, `coupe-propre` |
| `sortie` | Le fichier final, toujours dans `export/`, avec un numéro de version (`-v1`, `-v2`…) |
| `da` | `"auto"` = la DA de l'élève (`ma-da/kit.json` du dossier Éditeur), sinon un chemin vers un `kit.json` |
| `plans` | La vidéo, dans l'ordre. Chaque plan = un morceau d'un fichier source. `son: false` coupe le son du plan (b-roll). Un plan sans image (fichier audio seul, voix off) donne un fond noir : il faut alors le couvrir d'incrustations |
| `incrustations` | Une image ou une vidéo posée PAR-DESSUS la vidéo, au temps `a` de la vidéo finale, pendant `duree`. Le son reste celui des plans. `mode: "plein"` = plein écran (b-roll), `"fenetre"` = carte au centre haut avec la personne derrière |
| `hook` | Le titre du début (hook texte). Gros, en haut, avec la boîte de la DA. Animé à l'entrée |
| `sous_titres` | `true` : les sous-titres se fabriquent tout seuls depuis les transcriptions (`travail/<nom>.mots.json`), mot par mot, 2 à 3 mots à la fois, mot dit en couleur |
| `textes` | Textes posés à l'écran hors sous-titres (one shot, dix shots, étiquettes). `position` : `haut`, `centre`, `bas` |
| `musique` | Une musique sous la vidéo. `niveau_db` = combien elle est sous la voix, en LU : `-15` sous une voix (on l'entend, elle ne couvre jamais la voix), `0` quand elle est au premier plan (one shot, 10 shots sans voix). `debut` = l'endroit du morceau où ça part : TOUJOURS sur le drop (le premier coup franc), jamais sur une intro calme ou un silence. Écoute ou mesure le volume (ebur128) pour le trouver |
| `ajustements` | Réglages de DA pour CETTE vidéo seulement, sans toucher à la DA de l'élève. Ex. visage qui remplit l'écran : `{"sous_titres": {"y": 1420}}` pour passer les sous-titres sous le menton ; `{"hook": {"y": 220}}` pour monter le texte du début |
| `zoom` | Vide par défaut. `[{"a": 5.0, "duree": 2.0, "echelle": 1.15}]` pour un zoom demandé par l'élève. Jamais de zoom automatique |

## Les commandes

`$EDITEUR` = le dossier de l'éditeur (voir SKILL.md, section « Où est l'éditeur »).

| Commande | Ce qu'elle fait |
|---|---|
| `python3 "$EDITEUR/outils/transcrire.py" rushes/IMG_1234.MOV` | Transcrit (Whisper, en local) → `travail/IMG_1234.mots.json` + `travail/IMG_1234.txt` lisible avec les temps |
| `python3 "$EDITEUR/outils/couper.py" travail/garde.json` | Prend les passages gardés par Claude (`garde.json`), enlève les blancs, les « euh » et les ratés, écrit les `plans` dans `travail/montage.json` |
| `python3 "$EDITEUR/outils/ou.py" travail/montage.json "faire les reps"` | Donne le moment exact (sur la vidéo finale) où une phrase est dite, pour poser un b-roll, un texte ou un zoom. `--tout` : tout le texte avec ses temps |
| `python3 "$EDITEUR/outils/planche.py" b-roll/` | Fait une planche d'images par vidéo (`travail/planches/`) pour que Claude voie ce qu'il y a dedans |
| `python3 "$EDITEUR/outils/rendu.py" travail/montage.json` | Fabrique la vidéo. `--apercu` : version rapide 540x960 pour vérifier ; `--image 3.5` : une seule image PNG à 3,5 s |
| `python3 "$EDITEUR/outils/studio.py" "<dossier de la vidéo>"` | Ouvre le Studio (mini-éditeur visuel) dans le navigateur. À lancer en arrière-plan |
| `python3 "$EDITEUR/outils/instagram.py" <lien>` | Télécharge un reel (yt-dlp) dans `references/` avec sa légende |

## garde.json (pour couper.py)

```json
{
  "style": "yap",
  "passages": [
    {"source": "rushes/IMG_1234.MOV", "debut": 12.1, "fin": 31.0},
    {"source": "rushes/IMG_1234.MOV", "debut": 40.2, "fin": 55.8}
  ]
}
```

`style` règle la coupe des blancs : `yap` = aucun blanc (tout ce qui dépasse 0,25 s saute), `normal` = blancs de plus de 0,5 s coupés.
Claude choisit les passages (la meilleure prise de chaque phrase, en général la dernière), le script fait la coupe fine au mot.
