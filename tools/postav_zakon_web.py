#!/usr/bin/env python3
"""Postaví čtecí verzi zákona do docs/zakon/ pro GitHub Pages.

Richardův iPhone neotevře prohlížečku artefaktů na claude.ai — stránka naběhne
a za dvě vteřiny ji obal shodí. Táž stránka je ale obyčejné HTML, které se umí
obejít bez Clauda: když `window.claude` chybí, tlačítka na rozhovory se samy
skryjí a zbyde zákon, výklad, témata, hledání a tisk. Publikuje se proto
dvakrát ze stejného zdroje — jako Artifact (s rozhovory) a sem (ke čtení).

Spouští se po `npm run build:web`, protože `expo export` cílovou složku maže.

Spuštění:  python3 tools/postav_zakon_web.py
"""
import shutil
from pathlib import Path

KOREN = Path(__file__).resolve().parent.parent
ZDROJ = KOREN / "artefakt"
CIL = KOREN / "docs/zakon"

HLAVICKA = (
    '<!doctype html>\n<html lang="cs">\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
)

SOUBORY = ["index.html", "zakon.js", "vyklad.js", "temata.js", "pohledavky.js",
           "hra.js", "hra2.js", "hra3.js", "lhuty.js"]


def main():
    chybi = [s for s in SOUBORY if not (ZDROJ / s).exists()]
    if chybi:
        raise SystemExit(
            "chybí " + ", ".join(chybi) + " — spusť nejdřív tools/sbal_artefakt.py"
        )
    CIL.mkdir(parents=True, exist_ok=True)
    for s in SOUBORY:
        shutil.copy2(ZDROJ / s, CIL / s)
    # Artifact si kostru dokumentu přidá sám, Pages ne. Bez viewportu by
    # iPhone stránku vykreslil na 980 px a zmenšil — tedy nečitelně.
    stranka = CIL / "index.html"
    stranka.write_text(HLAVICKA + stranka.read_text("utf-8"), encoding="utf-8")
    celkem = sum((CIL / s).stat().st_size for s in SOUBORY)
    print(f"{CIL}: {len(SOUBORY)} souborů, {celkem / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
