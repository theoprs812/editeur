---
name: one-shot
description: Monter un one shot, la vidéo d'un seul plan (deux ou trois au plus) avec un mur de texte par-dessus et une musique, où personne ne parle et où le texte fait tout le travail. Se déclenche quand l'élève dit « fais-moi un one shot », « mets ce texte sur ma vidéo », « j'ai un clip et une phrase drôle », « personne ne sait que… », ou dépose un clip court avec une idée de texte. Charger d'abord la skill editeur.
---

# One shot

## Ce que c'est
Le cours one shot de Théo : « un seul plan (deux ou trois max), un mur de texte par-dessus ». La vidéo montre un moment, le texte fait tout le boulot, et ce qui marche, c'est le contraste entre l'image et le texte.
Vertical 1080x1920, pour Reels et TikTok.

## Quand le proposer
- L'élève a 1 à 3 clips d'un moment (lui dedans de préférence) et une phrase ou un texte à poser dessus.
- Il ne veut pas parler face caméra : le cours dit que c'est le format pour briser la glace.
- Si les clips sont nombreux et différents, propose `dix-shots`. S'il parle, ce n'est plus un one shot.

## Structure
1. **Hook = le texte, dès la première image.** Le cours 4.10 : il doit accrocher dans les 2 secondes, court, fort, lisible.
2. **Corps = le même plan qui continue.** Le texte ne bouge pas.
3. **Fin.** Quand on a eu le temps de lire le texte une fois. Le cours 4.10 dit de l'afficher assez longtemps : 7 à 10 secondes, pas 3. Un texte satirique long peut tenir plus, s'il est drôle les gens le lisent.

## Coupes
- Un seul plan par défaut. Deux ou trois au plus, et seulement s'ils avancent (il marche plus loin, avant puis après). Jamais des clips sans rapport.
- S'il y en a plusieurs : coupes franches, sur le temps fort de la musique.
- Choisis le morceau où l'image est calme au milieu du cadre, pour que le texte se lise.

## Texte et sous-titres
- Un seul bloc dans `textes`, de 0 s jusqu'à la fin, `position: "centre"`. Il ne change pas entre les plans.
- Pas de champ `hook` (le texte EST le hook, on n'empile pas un titre dessus) et `sous_titres: false`.
- Avant le rendu, vérifie le contraste avec l'élève. Dis-lui : « Ce qu'on voit et ce que dit ton texte, est-ce que c'est bien différent ? Plus c'est différent, plus c'est drôle. »
- Les 4 leviers du cours pour l'aider à écrire : l'autodérision, le relatable, la satire gentille, le détournement de phrase.
- Garde le même style de texte d'une vidéo à l'autre (règle du cours) : c'est la DA de l'élève (`da: "auto"`). S'il préfère le style natif d'Instagram, rends la vidéo sans texte et dis-lui de l'écrire dans l'app.
- Le texte ne cache pas le visage.

## B-roll et incrustations
- Aucune. Le clip est la vidéo.

## Musique et son
- Toujours une musique, au premier plan : `niveau_db: 0`. Le son du clip coupé : `son: false` sur chaque plan.
- La musique vient de `musique/`, l'élève la choisit. Le cours dit : pas besoin du son ultra tendance, un truc qui colle et qu'il aime, sans fin trop brutale. Jamais de musique générée.
- Si `musique/` est vide : pas de champ `musique`, et dis-lui : « Ajoute la musique dans Instagram quand tu postes. Choisis un son que tu aimes et qui colle à ton texte. »

## Remplir garde.json / montage.json
Pas de parole, donc pas de `garde.json` ni de `couper.py`. Écris les `plans` toi-même dans `montage.json` :
```json
{"format": "one-shot", "sortie": "export/housse-couette-v1.mp4", "da": "auto",
 "plans": [{"source": "rushes/arrivee.MOV", "debut": 4.0, "fin": 13.0, "son": false}],
 "incrustations": [], "sous_titres": false,
 "textes": [{"texte": "Il ne le sait pas encore, mais on doit mettre la housse de couette en rentrant", "de": 0, "a": 9.0, "position": "centre"}],
 "musique": {"source": "musique/son.mp3", "debut": 0, "niveau_db": 0}, "zoom": []}
```

## À éviter
- Un texte qui dit la même chose que l'image : sans contraste, pas de blague.
- Plus de 3 plans, ou des plans qui n'avancent pas.
- Un texte qui bouge, change entre les plans ou cache le visage.
- Une image chargée derrière le texte.
- Couper avant qu'on ait pu lire.
- Tout zoom ajouté de toi-même.
