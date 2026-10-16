---
name: instagram
description: Télécharge des reels Instagram (et TikTok, YouTube Shorts) dans l'Éditeur avec yt-dlp, puis s'en sert : comme modèle de style (DA), comme plan à intégrer dans une vidéo (b-roll, réaction, preuve), comme musique, ou comme référence de rythme pour un montage. Se déclenche dès que l'élève colle un lien instagram.com/reel, /p/, tiktok.com, youtube.com/shorts, ou dit « télécharge ce reel », « intègre-moi ça », « mets ce reel dans ma vidéo », « je veux le même montage que ça ». Charger d'abord la skill editeur.
---

# Instagram (et les autres liens)

## Télécharger

`python3 "$EDITEUR/outils/instagram.py" <lien> [<lien> ...]`

- Par défaut dans `~/Editeur/references/<compte>-<id>/` : `video.mp4` + `legende.txt` (légende, compte, date, vues et likes publics).
- Pour un plan à mettre dans une vidéo : `--dossier "<dossier de la vidéo>/b-roll"`.
- Pour une musique : `--audio` (garde aussi un `.m4a`), puis copie-le dans `~/Editeur/musiques/`.
- Si Instagram demande d'être connecté, l'outil réessaie avec la session du navigateur de l'élève. Sur Mac, une fenêtre peut demander l'accès au trousseau : « Une fenêtre demande ton mot de passe pour lire ta session Instagram. Tape le mot de passe de ton Mac et clique sur Autoriser. »
- Un compte privé ou un reel supprimé ne se télécharge pas : dis-le simplement.

Dis à l'élève ce que tu as récupéré en une ligne (« J'ai le reel de @compte, 21 s, 12 000 vues »), puis demande ce qu'on en fait si ce n'est pas clair :

```
Qu'est-ce que j'en fais ?
1. Je copie son style pour tes vidéos (texte, sous-titres, couleurs)
2. Je le mets dans ta vidéo (en fenêtre ou en plein écran)
3. Je monte ta vidéo avec le même rythme
4. Je garde sa musique
```

## 1. Copier le style

Skill `ma-da`, à partir de `video.mp4`.

## 2. L'intégrer dans une vidéo (« intègre-moi ça »)

- Télécharge dans `b-roll/` de la vidéo en cours, puis `planche.py` dessus pour voir les bons moments.
- Dans `montage.json`, une incrustation : `"mode": "fenetre"` par défaut (la personne qui parle reste visible derrière, c'est le format réaction), `"plein"` si l'élève le demande. Garde 1 à 3 s, le moment qui illustre ce qui est dit à cet instant.
- Le son du reel n'est pas repris (le son reste celui de l'élève). Si l'élève veut faire entendre le reel, coupe sa voix à ce moment-là : ajoute le reel comme un plan normal (avec son) dans `plans` au lieu d'une incrustation.
- Rappelle-lui une fois : citer le compte d'origine dans la légende ou à l'écran.

## 3. Le même rythme

Transcris le reel (`transcrire.py`), regarde sa planche, mesure : durée, nombre de plans, durée moyenne d'un plan, quand arrive le texte du début, s'il y a de la musique. Écris ce que tu en retiens dans `travail/reference.md` (5 lignes) et applique-le au plan de montage. On s'inspire du rythme, on ne recopie jamais le texte.

## 4. La musique

`--audio`, copie le `.m4a` dans `~/Editeur/musiques/` sous un nom clair (« son-tendance-octobre.m4a »). Rappel : pour poster, mieux vaut ajouter le même son directement dans Instagram (il est sous licence là-bas et la vidéo rejoint la page du son) ; la version téléchargée sert à caler le montage.
