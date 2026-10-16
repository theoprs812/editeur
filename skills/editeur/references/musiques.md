# Choisir la musique

La banque de musiques de Théo arrive toute seule dans `~/Editeur/musiques/<style>/` : chaque morceau qu'il ajoute chez lui part vers un dépôt privé, et `outils/musiques.py` le récupère à chaque ouverture de Claude. Les bruitages sont dans `~/Editeur/musiques/bruitages/` (interface, memes, réactions, transitions). `python3 "$EDITEUR/outils/musiques.py" --liste` les montre par style.

| Style | Le son | Pour quel format |
|---|---|---|
| `chill/` | beats posés, groove léger | vlog, lifestyle, b-roll détendu |
| `hard/` | rap/trap lourd, basse qui tape | punchlines, montée d'énergie, flex |
| `reflexion/` | ambient, piano, nappes, électro lente | analyse, talking head, constat qui fait réfléchir |
| `emotion/` | piano/voix, lent, chargé | histoire perso, prise de conscience |
| `suspense/` | tension, inquiétant | teaser, révélation, mystère |
| `inspirant/` | montée, lumineux, motivant | déclic, transformation, fin de vidéo |
| `sigma/` | slowed/reverb sombre, mélancolie | discipline, solitude, mindset |
| `phonk/` | phonk, cowbell, agressif | édits rapides, sport, intensité, 10 shots |
| `youtube-libre/` | ambient, piano (Kevin MacLeod, CC BY 4.0) | YouTube : créditer « Musique : Kevin MacLeod (incompetech.com), licence CC BY 4.0 » |

## Règles

- Propose 2 morceaux du style qui colle (avec leur nom), l'élève choisit. Une musique de son dossier `musique/` passe toujours avant.
- **Départ sur le drop** : jamais à 0 s si le morceau commence par une intro calme ou un silence. Trouve le premier coup franc (volume par 0,1 s avec ffmpeg `ebur128`) et mets-le dans `musique.debut`. On doit entendre la musique dès la première image.
- Sous une voix : `niveau_db: -15`. Sans voix (one shot, 10 shots sans voix) : `0`.
- Ces morceaux servent à caler le montage. Pour poster sur Instagram, le plus sûr reste d'ajouter le même son depuis la bibliothèque d'Instagram (licence gérée par Instagram) : dis-le à l'élève une fois.
