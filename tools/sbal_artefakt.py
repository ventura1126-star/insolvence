#!/usr/bin/env python3
"""Připraví data pro Artifact „Insolvenční zákon v praxi" na claude.ai.

Artifact umí načíst jen soubory, které se k němu publikují, a nejjistější
způsob, jak mu podat zákon a výklad, je obyčejný skript, co je pověsí na
window. JSON se proto obalí přiřazením a zapíše čistě v ASCII (\\uXXXX) —
pak je jedno, s jakým kódováním se skript naservíruje.

Stránka samotná je v artefakt/index.html a publikuje se nástrojem Artifact
spolu s oběma vygenerovanými skripty.

Spuštění:  python3 tools/sbal_artefakt.py
"""
import json
from pathlib import Path

KOREN = Path(__file__).resolve().parent.parent
CIL = KOREN / "artefakt"

SOUBORY = [
    ("zakon.js", "zakon.json", "ZAKON"),
    ("vyklad.js", "vyklad.json", "VYKLAD"),
    ("temata.js", "temata.json", "TEMATA"),
]


def main():
    CIL.mkdir(exist_ok=True)
    for jmeno, zdroj, promenna in SOUBORY:
        data = json.loads((CIL / zdroj).read_text("utf-8"))
        text = "window.%s=%s;\n" % (
            promenna, json.dumps(data, ensure_ascii=True, separators=(",", ":"))
        )
        (CIL / jmeno).write_text(text, encoding="ascii")
        print(f"{CIL / jmeno}: {len(text) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
