---
name: vlog
description: Monter un vlog, la vidéo où la voix de l'élève raconte une histoire (souvent en 7 temps) par-dessus des dizaines de petits clips de sa vie, avec un hook texte dès la première image, des sous-titres et une musique sous la voix. Se déclenche quand l'élève dit « monte mon vlog », « j'ai filmé ma journée », « j'ai ma voix off et mes clips », « fais mon Hero's journey », « talk & edit ». Charger d'abord la skill editeur.
---

# Vlog

## Ce que c'est
Le cours Vlog V2 de Théo : un problème, une tentative, un échec, un déclic, une suite, racontés par la voix pendant que l'image montre la vie. La formule du montage : « une voix off de 45 secondes, c'est 45 plans d'une seconde ».
Vertical 1080x1920, pour Reels et TikTok.

## Quand le proposer
- L'élève a une voix qui raconte (enregistrée face caméra ou en voix off seule) et des clips de b-roll.
- Deux cas du cours. **Talk & edit** : il se filme en parlant, le b-roll passe par-dessus, sa tête bouche les trous. **Overdub** : sa voix seule, il faut une image pour chaque seconde.
- Des clips sans aucune voix et sans projet d'en enregistrer : propose `dix-shots` (version musique) ou `one-shot`.

## Structure
1. **Hook, la première seconde.** Le problème arrive avant tout, sans bonjour. L'image d'ouverture est le hook shot : le plan le plus fort de toute la vidéo, même s'il vient de la fin de l'histoire. Demande à l'élève s'il l'a mis en favori.
2. **Corps : les 7 temps du cours.** Problème, backstory, tentative, échec, déclic, percée, suite. Le temps 4 (l'échec) doit se VOIR : un chiffre à l'écran, un objet raté, un message qui dit non. Vérifie qu'il a des images.
3. **Fin : la suite.** Annoncée sans être résolue, pour donner envie de revenir. On coupe sur le dernier mot.

Le prompt d'arc du cours vise 60 à 90 secondes.

## Coupes
- La voix d'abord : elle file sans trou. Enlève respirations, « euh » et reprises.
- Chaque plan de b-roll dure entre une demi-seconde et une seconde au montage, jamais plus (cours V2). Les clips captés font 2 à 5 secondes : prends le meilleur morceau.
- Change d'image quand la voix nomme une chose nouvelle. Dans le cours, la voix dit ce que l'élève pense ou ressent, et l'image montre ce qui se passe à ce moment-là de l'histoire.
- Varie gros plan, plan moyen, plan large (la règle des 3 plans du cours). Le cours demande au moins 5 plans de l'élève dans la vidéo : place-les.
- Coupes franches, pas de fondu.

## Texte et sous-titres
- `hook` : un titre fort dès 0 s, tenu pendant la première phrase. Il doit arrêter le scroll sans le son : un enjeu précis, jamais une étiquette du genre « vlog jour 3 ». Propose 3 hooks à l'élève et laisse-le choisir.
- `sous_titres: true` sur toute la voix.
- `textes` : rare. Le chiffre de l'échec (temps 4) mérite souvent un texte.

## B-roll et incrustations
- Le b-roll passe en `incrustations`, `mode: "plein"`, `duree` entre 0.5 et 1.0.
- Talk & edit : les `plans` sont la face caméra, le b-roll couvre la plupart du temps, la tête revient quand il n'y a pas d'image.
- Overdub : le plan est le fichier audio seul (fond noir). Chaque seconde doit être couverte par une incrustation : compte et préviens l'élève s'il manque des clips.
- Lance `planche.py b-roll/` pour voir les clips avant de les placer.

## Musique et son
- Une musique sous la voix (le cours 4.13 dit de monter sur la musique), choisie par l'élève dans `musique/`, `niveau_db: -12`.
- Jamais de musique générée. Si `musique/` est vide, pas de champ `musique`, et dis-lui : « Au moment de poster, ajoute un son tendance dans Instagram, mets-le bas pour qu'on entende ta voix. »

## Remplir garde.json / montage.json
`garde.json` : `"style": "yap"` pour une voix sans trou. Passe en `"normal"` seulement si l'élève veut une respiration avant une révélation.
```json
{"style": "yap", "passages": [
  {"source": "rushes/voix.m4a", "debut": 3.1, "fin": 47.8}
]}
```
Après `couper.py`, complète `montage.json` :
```json
{"format": "vlog", "sortie": "export/vlog-villa-v1.mp4", "da": "auto",
 "incrustations": [
   {"source": "b-roll/villa-large.MOV", "a": 0, "duree": 1.0, "debut_source": 0.4, "mode": "plein"},
   {"source": "b-roll/porte-main.MOV", "a": 1.0, "duree": 0.7, "debut_source": 1.2, "mode": "plein"}
 ],
 "hook": {"texte": "Mon client a refusé mon reel", "de": 0, "a": 3.0},
 "sous_titres": true, "textes": [],
 "musique": {"source": "musique/lofi.mp3", "debut": 0, "niveau_db": -12}, "zoom": []}
```

## À éviter
- Un hook faible ou une étiquette en ouverture.
- Un plan de b-roll qui dure plus d'une seconde.
- Une image qui ne colle pas à ce que dit la voix.
- Sauter l'échec : sans le temps 4, la vidéo devient un compte rendu.
- Une musique plus forte que la voix.
- Tout zoom ajouté de toi-même.
