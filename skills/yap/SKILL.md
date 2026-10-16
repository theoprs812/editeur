---
name: yap
description: Monter un yap, la vidéo où l'élève parle face caméra avec son téléphone dans un vrai décor (assis, en marchant, dans sa voiture), sans aucun blanc, avec un titre en haut et des sous-titres. Se déclenche quand l'élève dit « fais-moi un yap », « monte mon yap », « j'ai parlé face caméra, tu peux couper ? », « enlève les blancs », ou dépose une prise où il parle sans plan d'images. Charger d'abord la skill editeur.
---

# Yap

## Ce que c'est
Le cours 4.9 de Théo : « tu poses une caméra d'iPhone, tu parles, tu publies ». Un monologue structuré, une seule idée, et le montage vit ou meurt sur son rythme : aucun temps mort.
Vertical 1080x1920, pour Reels et TikTok.

## Quand le proposer
- L'élève parle face caméra dans un vrai lieu (Standard yap assis, Walking yap, Car yap) et ce qu'il dit porte la vidéo.
- Il n'a rien de spécial à montrer, ou il veut faire simple. C'est le format du tout premier rendu (cours 4.9, niveau 0 vers 1).
- S'il a scripté mot à mot un conseil éducatif, propose plutôt `talking-head`.

## Structure
1. **Hook, de 0 à 3 s.** La voix démarre à 0 s, jamais d'ouverture muette. Le cours dit : 2 à 3 secondes pour convaincre. Zéro intro : si l'élève dit son nom ou « hey les gars », tu coupes.
2. **Corps.** Hook → intro → point 1 → point 2 (structure du cours 4.9), ou une liste. Un seul sujet, complet.
3. **Fin.** Pas d'outro. On coupe net sur le dernier mot du dernier point. Le « voilà, abonnez-vous » tue la rétention : il saute.

Durée cible pour un débutant : 30 à 60 secondes (checklist du cours), 30 secondes pour un premier yap.

## Coupes
- C'est le cœur du format : **aucun blanc**. Respirations, « euh », faux départs, phrases répétées : tout part. Un mot enchaîne sur le suivant.
- Le cours recommande la méthode Recut : l'élève se tait pour réfléchir puis reprend. Le rush est donc plein de silences et de reprises. Garde la meilleure prise de chaque phrase, en général la dernière.
- **Regarde la fin du rush.** Théo apprend à ses élèves à refaire leur intro à la fin du tournage, quand ils sont plus à l'aise. Si un hook refait existe en fin de fichier, c'est lui qui ouvre la vidéo.
- Coupes franches uniquement, pas de transition. Les jump cuts entre deux phrases sont normaux.

## Texte et sous-titres
- `hook` : un titre gros, en haut, de 0 s jusqu'à la fin de la phrase de hook (au moins 3 s). Une affirmation courte tirée de ce que dit l'élève. Propose-le à l'élève avant le rendu.
- `sous_titres: true`, toujours. Le cours le dit : 60 % des gens regardent sans le son.
- Pas d'autres `textes`.

## B-roll et incrustations
- Aucune par défaut (niveau 0 vers 1 : « pas de liste, pas de graphique »).
- Une image de temps en temps si l'élève nomme un truc qu'on doit voir, et qu'il l'a déposée dans `b-roll/`.
- Graphic yap (palier au-dessus, seulement si l'élève le demande et fournit les images) : un visuel toutes les 2 secondes, soit 30 images pour 60 s. Mode `"plein"` pour le full screen overlay, `"fenetre"` pour le yap cadré avec la tête en bas.

## Musique et son
- La voix seule, du début à la fin. Pas de musique par défaut.
- Si l'élève veut une musique et qu'il a mis un fichier dans `musique/` : `niveau_db: -22`. Jamais de musique générée. Sinon dis-lui : « Si tu veux un son, ajoute-le dans Instagram au moment de poster, prends un son tendance. »

## Remplir garde.json / montage.json
`garde.json` : `"style": "yap"` (tout blanc de plus de 0,25 s saute). L'ordre des passages est l'ordre de la vidéo : le hook refait de la fin passe en premier.
```json
{"style": "yap", "passages": [
  {"source": "rushes/IMG_0412.MOV", "debut": 301.2, "fin": 305.9},
  {"source": "rushes/IMG_0412.MOV", "debut": 14.0, "fin": 48.6}
]}
```
Après `couper.py`, complète `montage.json` :
```json
{"format": "yap", "sortie": "export/yap-matcha-v1.mp4", "da": "auto",
 "incrustations": [], "hook": {"texte": "Personne ne te dit ça sur le matcha", "de": 0, "a": 3.2},
 "sous_titres": true, "textes": [], "zoom": []}
```
Pas de champ `musique` sauf si l'élève en a choisi une.

## À éviter
- Un seul blanc ou une respiration laissés.
- Une ouverture lente ou silencieuse, une présentation, un « hey les gars ».
- Une outro.
- Oublier le titre ou les sous-titres.
- Des images sur chaque phrase quand l'élève n'a pas demandé un graphic yap.
- Tout zoom ajouté de toi-même.
