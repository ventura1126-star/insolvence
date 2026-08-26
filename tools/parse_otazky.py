#!/usr/bin/env python3
"""Rozparsuje PDF s testovými otázkami ke zkouškám insolvenčních správců do JSON.

Zdroj: https://insolvence.justice.cz/wp-content/uploads/2018/01/Otazky_od_1_1_2014_*.pdf

Struktura se čte z vodorovných souřadnic textu, ne z odsazení v extrahovaném
textu — znění otázek i variant se lámou přes víc řádků a v prostém textu nejde
zalomení spolehlivě odlišit od začátku další otázky. V souřadnicích jsou ale tři
úrovně zarovnání čitelné napřímo a ve všech čtyřech PDF stejně:

    x ≈ 71   znění otázky (a jeho pokračovací řádky)
    x ≈ 98   varianta odpovědi — vždy a jen tyto řádky nesou odrážku
    x ≈ 116  pokračovací řádek zalomené varianty (předsazené odsazení)

Pozn.: nelze se spolehnout na to, že poslední varianta je "žádná odpověď není
správná" — část otázek má místo toho "ani jedna definice není správná" nebo pět
běžných tvrzení (typ "Zakroužkujte nepravdivé tvrzení").

Správné odpovědi PDF neobsahuje, doplňují se zvlášť.
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from pypdf import PdfReader

BULLET = "\uf0b7"

X_VARIANTA = 90.0  # pod tím je znění otázky, nad tím varianta
X_POKRACOVANI = 110.0  # nad tím je zalomená varianta

OBLASTI = {
    "audit": "Audit",
    "dane": "Daně",
    "obecne_pravo_a_exekuce": "Obecné právo a exekuce",
    "insolvence": "Insolvence",
}

HLAVICKA = re.compile(r"^\s*(?:Testové otázky ke zkouškám|Oblast\s*[-–]|\d+\s*$)")


def radky(path):
    """(x, text) po řádcích, v pořadí čtení, bez hlaviček a čísel stran."""
    for page in PdfReader(path).pages:
        shluky = defaultdict(list)

        def visit(text, cm, tm, font_dict, font_size, shluky=shluky):
            if text.strip():
                shluky[round(tm[5], 1)].append((round(tm[4], 1), text))

        page.extract_text(visitor_text=visit)

        for y in sorted(shluky, reverse=True):
            usporadane = sorted(shluky[y])
            x = min(c[0] for c in usporadane)
            text = "".join(c[1] for c in usporadane).replace("\n", "").strip()
            text = text.replace(BULLET, "").strip()
            if text and not HLAVICKA.match(text):
                yield x, text, any(BULLET in c[1] for c in usporadane)


def parse(path, oblast_key):
    otazky = []
    znen, varianty = [], []

    def uzavri():
        if znen:
            otazky.append(
                {
                    "id": f"{oblast_key}-{len(otazky) + 1:04d}",
                    "oblast": OBLASTI[oblast_key],
                    "otazka": " ".join(znen),
                    "varianty": varianty[:],
                }
            )
        znen.clear()
        varianty.clear()

    for x, text, ma_odrazku in radky(path):
        if ma_odrazku or X_VARIANTA <= x < X_POKRACOVANI:
            varianty.append(text)
        elif x >= X_POKRACOVANI:
            if varianty:
                varianty[-1] += " " + text
            else:
                znen.append(text)
        else:
            if varianty:  # nová otázka začíná až po sadě variant
                uzavri()
            znen.append(text)

    uzavri()
    return otazky


def main():
    korenov = Path(__file__).resolve().parent.parent
    zdroje = korenov / "_zdroje"
    vse, problemy = [], []

    for key in OBLASTI:
        otazky = parse(zdroje / f"Otazky_od_1_1_2014_{key}.pdf", key)
        for o in otazky:
            if len(o["varianty"]) != 5:
                problemy.append(
                    f"{o['id']}: {len(o['varianty'])} variant — {o['otazka'][:70]!r}"
                )
        print(f"{OBLASTI[key]:<24} {len(otazky):>5} otázek")
        vse.extend(otazky)

    print(f"{'CELKEM':<24} {len(vse):>5} otázek")

    if problemy:
        print(f"\n{len(problemy)} problémů:", file=sys.stderr)
        for p in problemy[:25]:
            print(f"  {p}", file=sys.stderr)

    out = korenov / "zkouska" / "assets" / "otazky.json"
    out.write_text(json.dumps(vse, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n→ {out.relative_to(korenov)} ({out.stat().st_size // 1024} kB)")
    return 1 if problemy else 0


if __name__ == "__main__":
    sys.exit(main())
