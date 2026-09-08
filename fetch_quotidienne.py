#!/usr/bin/env python3
"""
Télécharge la dernière édition PDF de la FAO Genève (Feuille d'avis officielle,
quotidiennes) depuis https://fao.ge.ch/quotidiennes et l'enregistre dans pdfs/.

Le site place une page anti-bot ("Vous allez être redirigé...") devant le
contenu réel : elle pose un cookie via JS puis recharge la page. Un simple
requests/curl reste bloqué dessus, donc on passe par un vrai navigateur
(Playwright + Chromium) qui exécute le JS normalement.

Sortie : pdfs/<AAAA>/<AAAA-MM-JJ>.pdf (idempotent — ne réécrit pas un fichier
déjà présent) + mise à jour de pdfs/latest.json avec les métadonnées de la
dernière édition récupérée.
"""

import json
import re
import sys
import unicodedata
from datetime import date, datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

FAO_URL = "https://fao.ge.ch/quotidiennes"
ROOT = Path(__file__).resolve().parent
PDF_DIR = ROOT / "pdfs"

MOIS = {
    "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5,
    "juin": 6, "juillet": 7, "août": 8, "aout": 8, "septembre": 9,
    "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12,
}


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def parse_date_from_text(text: str) -> date | None:
    """Extrait une date depuis un texte du type 'La quotidienne du 7 septembre 2026'."""
    m = re.search(r"(\d{1,2})\s+([A-Za-zéûîôàè]+)\s+(\d{4})", text)
    if not m:
        return None
    day, month_name, year = m.groups()
    month = MOIS.get(strip_accents(month_name.lower()))
    if not month:
        return None
    return date(int(year), month, int(day))


def main() -> int:
    PDF_DIR.mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="fr-CH",
        )
        page = context.new_page()
        page.goto(FAO_URL, wait_until="networkidle", timeout=60_000)

        # Page anti-bot : elle affiche "Vous allez être redirigé..." puis se
        # recharge automatiquement une fois le cookie posé. On attend que le
        # vrai contenu (lien PDF) apparaisse, avec plusieurs tentatives
        # (attente + reload) avant d'abandonner.
        found = False
        last_error = None
        for attempt in range(4):
            try:
                page.wait_for_selector("text=Version PDF imprimable", timeout=15_000)
                found = True
                break
            except Exception as exc:
                last_error = exc
                print(f"Tentative {attempt + 1} échouée, titre={page.title()!r}, url={page.url!r}")
                page.wait_for_timeout(5000)
                try:
                    page.reload(wait_until="networkidle", timeout=60_000)
                except Exception:
                    pass

        if not found:
            snippet = page.inner_text("body")[:2000]
            print("Contenu de la page après échec :\n" + snippet, file=sys.stderr)
            raise last_error

        # Le premier bloc de la liste = l'édition la plus récente.
        first_article = page.locator("article").first
        article_text = first_article.inner_text()
        edition_date = parse_date_from_text(article_text) or date.today()

        pdf_link = first_article.get_by_text("Version PDF imprimable").first
        href = pdf_link.get_attribute("href")
        if not href:
            print("Impossible de trouver le lien PDF sur la page.", file=sys.stderr)
            return 1

        pdf_url = href if href.startswith("http") else f"https://fao.ge.ch{href}"

        year_dir = PDF_DIR / str(edition_date.year)
        year_dir.mkdir(exist_ok=True)
        out_path = year_dir / f"{edition_date.isoformat()}.pdf"

        if out_path.exists():
            print(f"Déjà présent, rien à faire : {out_path}")
        else:
            resp = context.request.get(pdf_url)
            if resp.status != 200:
                print(f"Échec du téléchargement ({resp.status}) : {pdf_url}", file=sys.stderr)
                return 1
            body = resp.body()
            if not body.startswith(b"%PDF"):
                print("La réponse ne ressemble pas à un PDF (probablement bloquée par l'anti-bot).", file=sys.stderr)
                return 1
            out_path.write_bytes(body)
            print(f"Téléchargé : {out_path} ({len(body)} octets)")

        latest = {
            "date": edition_date.isoformat(),
            "source_url": pdf_url,
            "local_path": str(out_path.relative_to(ROOT)),
            "fetched_at": datetime.utcnow().isoformat() + "Z",
        }
        (PDF_DIR / "latest.json").write_text(json.dumps(latest, ensure_ascii=False, indent=2) + "\n")

        browser.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
