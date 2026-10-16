---
name: ma-da
description: La direction artistique (DA) de l'élève dans le Studio : son template de texte du début, de sous-titres et de textes à l'écran, lu par chaque montage. Crée la DA classique, ou la recopie automatiquement depuis un reel que l'élève aime (lien Instagram ou fichier) en « Template 1, 2, 3… », montre un aperçu côte à côte, l'ajuste à ses retours. Se déclenche sur « mon style », « ma DA », « mes couleurs », « ma police », « fais-moi un template », « copie le style de ce reel », « change mes sous-titres », ou quand l'élève envoie un reel en disant qu'il aime son look. Charger d'abord la skill editeur.
---

# Ma DA

La DA de l'élève vit dans `~/Editeur/ma-da/kit.json`. Chaque montage la relit (`"da": "auto"`). Une DA = un template : `nom` (« Template 1 »), police, texte du début (`hook`), sous-titres, textes, fenêtre de b-roll. Les valeurs sont en pixels sur une image 1080x1920. Le modèle complet et commenté : `defaut.json` (dans ce dossier), la DA classique.

Plusieurs templates : `~/Editeur/ma-da/kit.json` est le template actif ; les autres sont rangés en `~/Editeur/ma-da/templates/template-2.json`, etc. « Passe sur le template 2 » = copier ce fichier sur `kit.json` (garde l'ancien dans `templates/`).

## Les champs que tu règles

| Champ | Ce que ça change |
|---|---|
| `police.famille`, `police.poids` | La police de base et sa graisse : 400 normal, 700 gras, 900 très gras. Par défaut **Instagram Sans**, la police du texte natif d'Instagram |
| `hook.police`, `sous_titres.police` | Une police différente pour le texte du début ou pour les sous-titres : `{"famille": "Montserrat", "poids": 800}`. Absent = la police de base |
| `hook.arrondi` | L'arrondi des coins de la boîte du texte du début (0,22 = comme Instagram ; 0 = carré) |
| `hook.taille`, `hook.couleur`, `hook.avec_fond`, `hook.fond`, `hook.y`, `hook.marge_cotes`, `hook.majuscules` | Le texte du début : taille, couleur du texte, boîte derrière ou non, couleur de la boîte, hauteur (haut du texte), largeur (plus la marge est grande, plus le texte passe à la ligne), majuscules |
| `hook.contour`, `hook.couleur_contour` | Sans boîte : contour autour des lettres |
| `sous_titres.taille`, `couleur`, `couleur_mot`, `contour`, `couleur_contour`, `y`, `mots_par_bloc`, `majuscules`, `avec_fond` | Les sous-titres : `couleur_mot` = couleur du mot en train d'être dit (`null` = pas de couleur), `y` = centre du sous-titre, `mots_par_bloc` = 1 à 4 |
| `textes.*` | Les textes posés à l'écran (one shot, mots-clés) |
| `fenetre.largeur`, `fenetre.y`, `fenetre.arrondi` | La carte de b-roll en mode fenêtre |

Le texte du début est dessiné comme le texte natif d'Instagram : une boîte par ligne, coins arrondis, lignes soudées. Polices installées d'office (`python3 "$EDITEUR/outils/police.py" --liste`) : Instagram Sans, TikTok Sans, Montserrat, Inter, Poppins, Anton, Bebas Neue, Archivo Black, DM Sans, Oswald, Roboto, Bricolage Grotesque, Playfair Display, Space Grotesk, Manrope, Lexend, League Spartan. Une autre police Google : `police.py "Nom"`. Limites : pas d'émojis animés, sous-titres sans boîte arrondie.

## Créer la DA depuis un reel (le cas principal)

1. **Récupérer le reel.** Lien : `python3 "$EDITEUR/outils/instagram.py" <lien>` (skill `instagram`). Fichier : utilise-le tel quel.
2. **Les images.** `python3 "$EDITEUR/outils/da.py" images <video>` : 5 images pleine taille + une planche dans `~/Editeur/ma-da/source/<nom>/`. Regarde la planche puis les images une par une.
3. **Lire la DA.** Pour le texte du début et pour les sous-titres, note : police (texte natif d'Instagram = Instagram Sans ; sinon la plus proche parmi les polices installées), graisse, taille en px (hauteur d'une majuscule ≈ 0,7 × taille), couleur du texte, boîte ou contour et leur couleur (code hexa lu sur l'image), position verticale (en px sur 1920), largeur, majuscules, nombre de mots par bloc, mot en couleur. Une image de 1080x1920 : mesure directement.
4. **Écrire le template.** Copie `defaut.json`, change ce que tu as lu, `nom` = « Template N » (N = le suivant), `source` = le lien. Installe la police : `python3 "$EDITEUR/outils/police.py" "Nom"`. Si un `kit.json` existe déjà, range-le d'abord dans `templates/`.
5. **Comparer.** `python3 "$EDITEUR/outils/da.py" apercu --comparer <image du reel avec texte et sous-titres>`. Regarde `~/Editeur/ma-da/apercu-template-N.png` : à gauche le reel, à droite ton template. Corrige taille, position, couleur, et recommence (3 essais maximum) jusqu'à ce que les deux se ressemblent.
6. **Montrer à l'élève.** « Voilà ton Template 1, recopié de ton reel : à gauche l'original, à droite ce que je vais mettre sur tes vidéos. 👉 À toi : écris ok, ou dis-moi ce que tu changes (plus gros, autre couleur, plus haut…). »

## Sans reel

Copie `defaut.json` vers `~/Editeur/ma-da/kit.json` avec `nom` = « Template 1 », lance l'aperçu sans `--comparer` et montre-le : « Voilà le style classique : texte du début en blanc sur fond noir… 👉 À toi : ok, ou envoie-moi un reel dont tu aimes le look. »

## Changer la DA en cours de route

L'élève dit « plus gros », « en jaune », « plus bas », « tout en majuscules » : modifie `kit.json`, ajoute une ligne dans `historique` (`{"date", "changement", "pourquoi"}`), relance l'aperçu, montre-le. Ce changement vaut pour toutes ses prochaines vidéos : dis-le-lui en une phrase. S'il veut le changement pour une seule vidéo, mets le `kit.json` modifié dans le dossier de la vidéo (`travail/kit.json`) et `"da": "travail/kit.json"` dans `montage.json`.

## Règles

- Jamais de police payante ou volée : uniquement Google Fonts (gratuites) ou une police que l'élève fournit (fichier `.ttf`/`.otf` dans `~/Editeur/ma-da/polices/`).
- Sous-titres et texte du début toujours dans la zone sûre : entre y = 220 et y = 1460, et à gauche de x = 960 (la colonne de boutons d'Instagram).
- Un texte du début lisible sans le son : contraste fort (boîte ou contour épais).
