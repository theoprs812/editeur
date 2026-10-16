---
name: dix-shots
description: Monter un 10 shots, la vidéo faite de plein de plans courts qui s'enchaînent (cadrages différents, plans de coupe) pour garder l'attention par le mouvement. Version principale avec la voix de l'élève qui file en continu, version sans voix montée sur la musique. Se déclenche quand l'élève dit « fais-moi un 10 shots », « dix shots », « monte ça de façon dynamique », « j'ai filmé sous plein d'angles », « fais un montage rapide de mes clips ». Charger d'abord la skill editeur.
---

# 10 shots

## Ce que c'est
Le cours 4.12 de Théo : « une vidéo construite sur plusieurs plans courts qui s'enchaînent », parce que « chaque changement de plan relance l'attention ». Le 10 est une image : on multiplie les plans au lieu de rester planté. C'est la version dynamisée du talking head.
Vertical 1080x1920, pour Reels et TikTok.

## Quand le proposer
- **Avec voix (par défaut, le cours 4.12).** L'élève parle et a filmé plusieurs cadrages (angle, distance large ou serrée, petit mouvement) plus des plans de coupe de ce dont il parle. Bon choix quand le sujet serait un peu plat en talking head simple, ou pour un process, un « une journée avec moi », une démo.
- **Sans voix.** Des clips d'un lieu, d'un objet, d'une expérience, et personne ne parle : montage rapide sur la musique.
- Un seul cadrage face caméra : `yap` ou `talking-head`. Une voix off qui raconte une histoire sur du b-roll : `vlog`.

## Structure
**Avec voix**
1. **Hook.** La voix démarre à 0 s, sur le cadrage le plus fort.
2. **Corps.** Chaque nouvelle idée = un nouveau plan. Le montage suit le sens.
3. **Fin.** Coupe sur le dernier mot.

**Sans voix**
1. **Hook shot, 1,5 à 3 s, jamais plus.** L'image la plus forte, le titre dessus dès 0 s. Il coupe sur le drop de la musique.
2. **Corps.** Des plans d'environ 1 s (0,5 à 1 s), tous à peu près de la même longueur. 12 à 20 plans, pour 13 à 20 s au total.
3. **Fin.** Un dernier plan un peu plus long sur la plus belle image, ou une fin à pleine vitesse sur un temps de la musique.

## Coupes
- Coupes franches, pas de transition.
- Avec voix : la voix file en continu, seules les images changent (règle du cours). On change de plan quand l'idée change, jamais pour changer.
- Sans voix : chaque coupe tombe sur un temps de la musique. Chaque plan montre une chose nouvelle ou un angle nouveau : pas trois fois la même chose.
- Ne fabrique jamais un plan serré en zoomant dans un plan large : pas de zoom automatique. Si l'élève n'a qu'un cadrage, dis-le-lui et propose un `yap`.

## Texte et sous-titres
- Avec voix : `hook` dès 0 s pendant la phrase de hook, `sous_titres: true`.
- Sans voix : un seul titre de 5 à 7 mots dans `textes`, `position: "centre"`, de 0 s jusqu'au premier changement de partie (ou toute la vidéo si l'élève préfère). Pas de champ `hook`, `sous_titres: false`.

## B-roll et incrustations
- Avec voix : les plans de coupe vont en `incrustations` `"plein"` au moment où l'élève nomme la chose (il parle d'un outil, on voit l'outil). Le cours demande au moins 5 à 6 cadrages différents et 2 plans de coupe : si l'élève en a moins, préviens-le.
- Sans voix : les clips sont les `plans` eux-mêmes, `son: false`. Lance `planche.py` pour choisir.

## Musique et son
- Avec voix : pas de musique par défaut. Si l'élève en a mis une dans `musique/`, `niveau_db: -12`.
- Sans voix : musique toujours, au premier plan, `niveau_db: 0`. Choisis le moment du drop avec l'élève avant de couper.
- Jamais de musique générée. Si `musique/` est vide, pas de champ `musique`, et dis-lui : « Ajoute un son tendance dans Instagram au moment de poster. » Sans voix, préviens-le que les coupes ne tomberont pas sur le rythme du son qu'il choisira.

## Remplir garde.json / montage.json
Avec voix, `garde.json` : `"style": "yap"`, un passage par idée, chacun pris dans le fichier du cadrage voulu.
```json
{"style": "yap", "passages": [
  {"source": "rushes/large.MOV", "debut": 2.0, "fin": 6.4},
  {"source": "rushes/serre.MOV", "debut": 7.1, "fin": 12.8},
  {"source": "rushes/profil.MOV", "debut": 13.0, "fin": 19.5}
]}
```
Après `couper.py`, complète `montage.json` :
```json
{"format": "dix-shots", "sortie": "export/routine-matin-v1.mp4", "da": "auto",
 "incrustations": [{"source": "b-roll/cafe.MOV", "a": 8.0, "duree": 1.0, "debut_source": 0.5, "mode": "plein"}],
 "hook": {"texte": "Ma routine pour écrire 3 scripts avant 9h", "de": 0, "a": 3.0},
 "sous_titres": true, "textes": [], "zoom": []}
```
Sans voix : pas de `garde.json`, écris les `plans` toi-même (`son: false`), `textes` pour le titre, `musique` à `niveau_db: 0`.

## À éviter
- Changer de plan sans logique : le cours dit que ça devient épileptique et fatigant.
- Couper la voix pour suivre les images.
- Moins de 8 plans dans la version sans voix, ou la même chose montrée 3 fois.
- Faire parler quelqu'un dans la version sans voix.
- Tout zoom ajouté de toi-même.
