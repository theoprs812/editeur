---
name: talking-head
description: Monter un talking head éducatif, la vidéo face caméra scriptée mot à mot où l'élève donne UN conseil concret (erreur courante, mythe, tuto en étapes, méthode, astuces, à faire / à ne pas faire, comparaison). Se déclenche quand l'élève dit « monte mon talking head », « j'ai tourné mon éducatif », « c'est mon rendu Common Mistake », « j'ai lu mon script face caméra ». Charger d'abord la skill editeur.
---

# Talking head

## Ce que c'est
Le cours 4.8 de Théo : « le talking head éducatif, c'est scripté mot à mot, face caméra, et ça délivre UNE valeur concrète que le viewer peut appliquer dès qu'il pose son téléphone ». Le montage reste sobre : coupes serrées, un titre, des sous-titres, un mot-clé ou un chiffre à l'écran au bon moment.
Vertical 1080x1920, pour Reels et TikTok.

## Quand le proposer
- L'élève a lu un script (130 à 150 mots, d'après le cours) face caméra pour transmettre un conseil.
- Il parle d'une des 7 familles : Common Mistake, Myths vs Facts, Step-by-Step, Framework, Quick Tips, À faire / À ne pas faire, Comparaison.
- S'il donne son avis à chaud sans script, c'est un `yap`. S'il change de cadrage à chaque idée, c'est un `dix-shots`.

## Structure
1. **Hook.** La voix démarre à 0 s. Zéro intro, zéro « salut c'est moi » : le cours le répète, aucun exemple ne se présente. Le hook ouvre large, pour le plus grand nombre.
2. **Corps.** La rétention passe par des étapes, une liste ou une histoire (méthode H-R-R du cours). On descend du large vers le détail d'expert.
3. **Fin.** Le reward (ce qu'il garde en posant le téléphone) puis le CTA prévu par l'élève (follow, save, description, question). On coupe juste après le dernier mot du CTA.

Durée : celle du script. Le cours donne 130 mots pour 45 secondes, 150 pour 60.

## Coupes
- Coupes serrées. Le cours recommande la méthode Recut (l'élève se tait quand il cherche ses mots, l'app coupe les silences) : enlève tous les blancs, les « euh », les faux départs.
- Garde la meilleure prise de chaque phrase du script, en général la dernière. Suis l'ordre du script, même si l'élève a tourné dans le désordre.
- Si l'élève a refait son intro à la fin du rush (astuce du cours), prends cette version pour le hook.
- Coupes franches. Jump cuts normaux.

## Texte et sous-titres
- `hook` : un titre à l'écran dès 0 s (la checklist du cours exige « sous-titres + titre à l'écran »), tenu pendant la phrase de hook.
- `sous_titres: true`, obligatoire : « la majorité regarde sans le son ».
- `textes` : un mot-clé ou un chiffre quand l'élève le dit (le nom de l'erreur, l'étape 1, le chiffre clé). Sobre. Position `centre` pour ne pas recouvrir le titre en haut, quelques-uns par vidéo au plus.

## B-roll et incrustations
- Aucune par défaut. Le cours vend ce format comme le plus rapide : « pas de b-roll à capter toute la journée ».
- Si l'élève fournit des images de ce qu'il explique (capture, objet, geste) : incrustation `"fenetre"` au moment où il le nomme, pour qu'on le voie toujours derrière.
- Monter en gamme (seulement s'il le demande et fournit les images) : un visuel toutes les 2 à 3 secondes, règle du cours greenscreen.

## Musique et son
- La voix d'abord. Pas de musique par défaut.
- Si l'élève a choisi un fichier dans `musique/` : `niveau_db: -15`. Jamais de musique générée. Sinon dis-lui : « Tu peux ajouter un son tendance dans Instagram quand tu postes, tout bas sous ta voix. »

## Remplir garde.json / montage.json
`garde.json` : `"style": "yap"` (tout blanc de plus de 0,25 s saute), passages dans l'ordre du script.
```json
{"style": "yap", "passages": [
  {"source": "rushes/IMG_2201.MOV", "debut": 188.4, "fin": 192.0},
  {"source": "rushes/IMG_2201.MOV", "debut": 9.5, "fin": 61.3}
]}
```
Après `couper.py`, complète `montage.json` :
```json
{"format": "talking-head", "sortie": "export/erreur-swing-v1.mp4", "da": "auto",
 "incrustations": [], "hook": {"texte": "L'erreur n°1 au kettlebell swing", "de": 0, "a": 3.0},
 "sous_titres": true,
 "textes": [{"texte": "Tibias verticaux", "de": 14.2, "a": 16.0, "position": "centre"}],
 "zoom": []}
```

## À éviter
- Une intro, une présentation, des preuves sociales en ouverture.
- Laisser des blancs : ça casse la sensation d'expertise.
- Un texte à l'écran sur chaque phrase : un mot-clé au bon moment suffit.
- Oublier le CTA s'il est dans le rush.
- Tout zoom ajouté de toi-même.
