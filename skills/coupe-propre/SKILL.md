---
name: coupe-propre
description: Le montage le plus simple de l'Éditeur : l'élève donne une ou plusieurs vidéos filmées (face caméra, iPhone), l'Éditeur garde la meilleure prise de chaque phrase, coupe les blancs, les « euh » et les ratés, ajoute les sous-titres, le texte du début s'il en veut un, et pose automatiquement ses plans de b-roll s'il en a mis dans le dossier b-roll. Se déclenche sur « coupe juste », « coupe-moi les blancs », « enlève les ratés », « garde que les bons moments », « fais simple », « nettoie ma vidéo », « intègre mon b-roll ». Charger d'abord la skill editeur.
---

# Coupe propre

Pour l'élève qui veut juste une vidéo propre : il s'est filmé, il a recommencé ses phrases plusieurs fois, il y a des blancs. On garde le bon, on enlève le reste, on sous-titre. Aucun choix de format à faire.

## Les étapes

1. **Écouter tout.** `transcrire.py` sur chaque rush, lis les `.txt` en entier.
2. **Garder la meilleure prise.** Quand une phrase est dite plusieurs fois, garde la dernière prise complète, sauf si elle est ratée (coupée, bafouillée, rire). Quand l'élève dit à voix haute « je la refais », « coupe ça », « non attends », jette la prise qui précède. Enlève aussi le début (« c'est bon ça tourne ? ») et la fin (il se lève, il coupe la caméra).
3. **Les passages.** Écris `travail/garde.json` avec `"style": "normal"` (blancs de plus de 0,5 s coupés) ; `"style": "yap"` si l'élève veut que ça aille vite (« plus rythmé », « aucun blanc »). Lance `couper.py`.
4. **Le b-roll, s'il y en a.** `planche.py b-roll/`, regarde chaque planche, note dans `travail/b-roll.md` ce que montre chaque fichier. Pose chaque plan au moment où la phrase en parle : incrustation `"mode": "plein"` de 1 à 2 s, jamais pendant les 3 premières secondes (le visage et le texte du début d'abord), jamais deux d'affilée sans revenir au visage. Un plan qui ne colle à rien ne va pas dans la vidéo : dis-le à l'élève en une ligne.
5. **Le texte du début.** Si la vidéo commence par une phrase forte, propose 3 textes du début courts (7 mots max), recommande-en un. L'élève peut dire « pas de texte ».
6. **Animations.** Les sous-titres et le texte du début apparaissent avec un petit effet d'entrée (déjà réglé dans la DA). Rien d'autre par défaut : pas de zoom, pas de transition.
7. **Musique.** Seulement si l'élève en a mis une dans `musique/` ou dans `~/Editeur/musiques/` : `niveau_db: -22`, baissée sous la voix.
8. **Vérifier, montrer, corriger** comme dans la skill editeur.

## Exemple de montage.json

```json
{
  "format": "coupe-propre",
  "sortie": "export/ma-video-v1.mp4",
  "da": "auto",
  "plans": ["… écrits par couper.py …"],
  "hook": {"texte": "Personne ne te dit ça sur Instagram", "de": 0, "a": 3.0},
  "sous_titres": true,
  "incrustations": [
    {"source": "b-roll/IMG_2201.MOV", "a": 6.5, "duree": 1.5, "debut_source": 2.0, "mode": "plein"}
  ]
}
```

## Ce que tu dis à la fin

« J'ai gardé tes meilleures prises : ta vidéo passe de 2 min 40 de rushes à 52 s. J'ai enlevé 14 blancs et 6 phrases ratées, et posé 3 de tes plans de b-roll. 👉 À toi : regarde-la et dis-moi ce que tu changes, ou écris parfait. »
