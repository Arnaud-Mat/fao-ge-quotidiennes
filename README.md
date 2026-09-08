# FAO Genève — Archive quotidienne

Récupère automatiquement, chaque jour ouvré, la dernière édition PDF de la
Feuille d'avis officielle du canton de Genève ([fao.ge.ch/quotidiennes](https://fao.ge.ch/quotidiennes))
et l'archive dans ce dépôt — PDF **et texte brut extrait**, pour que le
contenu soit directement exploitable (recherche par mots-clés, ex: antennes
5G) sans avoir à re-parser le PDF.

## Fonctionnement réel

- Une **tâche planifiée Claude** (liée à l'ordinateur d'Arnaud, hors GitHub
-   Actions) tourne toutes les heures de 7h à 19h UTC, du lundi au vendredi.
-   - Elle pilote un vrai navigateur Chrome (via Claude in Chrome) pour :
    -   1. ouvrir fao.ge.ch/quotidiennes et laisser la vérification anti-bot se
        2.      résoudre automatiquement (elle bloque les requêtes serveur/datacenter,
        3.       seul un vrai navigateur humain passe) ;
        4.     2. repérer la dernière édition et son PDF ;
        5.   3. vérifier sur GitHub si le PDF du jour existe déjà (évite les doublons) ;
             4.   4. télécharger le PDF, en extraire le texte (via pdf.js, exécuté dans la
                  5.      page) ;
                  6.    5. committer les deux fichiers dans `pdfs/<année>/` via l'interface web
                        6.      GitHub.
                        7.  - Comme le Mac peut être éteint à certaines heures, le passage horaire
                            -   répété permet de rattraper l'archive dès que l'ordinateur est rallumé
                            -     dans la fenêtre 7h-19h UTC.
                          
                            - ## Contenu du dépôt
                          
                            - - `pdfs/<année>/<AAAA-MM-JJ>.pdf` — édition archivée
                              - - `pdfs/<année>/<AAAA-MM-JJ>.txt` — texte brut extrait du PDF (si
                                -   l'extraction a réussi ce jour-là)
                                -   - `fetch_quotidienne.py` — script Playwright de référence, utilisable en
                                    -   local (voir plus bas), pas utilisé par la tâche planifiée elle-même
                                    -   - `.github/workflows/daily.yml` — **non fonctionnel en production** :
                                        -   le CAPTCHA "Friendly Captcha" du site bloque systématiquement les IP
                                        -     datacenter de GitHub Actions (confirmé par 2 runs échoués). Conservé
                                        -   pour référence historique uniquement.
                                     
                                        -   ## En local (script de référence, hors automatisation)
                                     
                                        -   ```bash
                                            pip install playwright
                                            python -m playwright install chromium
                                            python fetch_quotidienne.py
                                            ```
                                            
