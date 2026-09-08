# FAO Genève — Archive quotidienne

Récupère automatiquement, chaque jour ouvré, la dernière édition PDF de la
Feuille d'avis officielle du canton de Genève ([fao.ge.ch/quotidiennes](https://fao.ge.ch/quotidiennes))
et l'archive dans ce dépôt.

## Fonctionnement

- Un [workflow GitHub Actions](.github/workflows/daily.yml) tourne du lundi
-   au vendredi à 09:00 UTC.
-   - Il exécute `fetch_quotidienne.py`, qui pilote un navigateur headless
    -   (Playwright/Chromium) pour passer la page anti-bot du site, récupérer le
    -     lien de la dernière édition et télécharger le PDF.
    - - Le fichier est enregistré sous `pdfs/<année>/<AAAA-MM-JJ>.pdf`, et
      -   `pdfs/latest.json` pointe toujours vers la dernière édition récupérée.
      -   - Le workflow commit et push automatiquement le nouveau PDF s'il n'existe
          -   pas déjà.
       
          -   ## Lancer manuellement
       
          -   Depuis l'onglet Actions du dépôt : Récupération quotidienne FAO Genève, puis
          -   Run workflow.
       
          -   ## En local
       
          -   pip install playwright
          -   python -m playwright install chromium
          -   python fetch_quotidienne.py
          -   
