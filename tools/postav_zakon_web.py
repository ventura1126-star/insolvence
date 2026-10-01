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

SOUBORY = ["index.html", "zakon.js", "vyklad.js", "temata.js"]


def main():
    chybi = [s for s in SOUBORY if not (ZDROJ / s).exists()]
    if chybi:
        raise SystemExit(
            "chybí " + ", ".join(chybi) + " — spusť nejdřív tools/sbal_artefakt.py"
        )
    CIL.mkdir(parents=True, exist_ok=True)
    for s in SOUBORY:
        shutil.copy2(ZDROJ / s, CIL / s)
    celkem = sum((CIL / s).stat().st_size for s in SOUBORY)
    print(f"{CIL}: {len(SOUBORY)} souborů, {celkem / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
