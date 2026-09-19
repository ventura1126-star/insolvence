#!/usr/bin/env python3
"""Zkontroluje soubor odpovědí proti otázkám.

Odpovědi se píšou ručně, takže je snadné se seknout v id otázky nebo v indexu
varianty — a chybná odpověď je horší než žádná, protože se z ní člověk naučí
nesprávné právo. Tenhle skript hlídá to, co se hlídat dá strojově.
"""

import json
import re
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent.parent
POVINNE = {"spravne", "pramen", "vysvetleni", "stav"}
STAVY = {"platna", "zastarala"}

# Většina otázek končí variantou typu „žádná odpověď není správná" — tu nelze
# kombinovat s konkrétní variantou. Část otázek ale má na posledním místě
# běžné tvrzení (typ „Zakroužkujte nepravdivé tvrzení"), a tam kombinace smysl
# dává, takže se pozná podle znění, ne podle pozice.
ZADNA = re.compile(r"(žádná|ani jedna).{0,30}(správná|není správná)", re.I)


def zkontroluj_vyklad():
    """Výklad se píše ručně vedle znění zákona — hlídá, že se nerozešly.

    zakon.json se přegeneruje z e-Sbírky po každé novele, a novela umí odstavec
    přečíslovat i zrušit. Výklad, který pak visí u odstavce, co v zákoně není,
    by se v aplikaci tiše ztratil — tady je aspoň vidět.
    """
    zakon_s = KOREN / "zkouska/assets/zakon.json"
    vyklad_s = KOREN / "zkouska/assets/vyklad.json"
    if not zakon_s.exists() or not vyklad_s.exists():
        return ["chybí zakon.json nebo vyklad.json — spusť tools/vytez_zakon.py"]

    zakon = json.loads(zakon_s.read_text("utf-8"))
    vyklad = json.loads(vyklad_s.read_text("utf-8"))
    chyby = []

    # Odstavec bez čísla (paragraf o jediné větě) má ve výkladu klíč „-".
    odstavce = {
        p["paragraf"]: {o["cislo"] or "-" for o in p["odstavce"]} for p in zakon
    }

    for cislo, k_odstavcum in vyklad.items():
        if cislo not in odstavce:
            chyby.append(f"výklad § {cislo}: takový paragraf v zákoně není")
            continue
        for odstavec, text in k_odstavcum.items():
            if odstavec not in odstavce[cislo]:
                chyby.append(f"výklad § {cislo} odst. {odstavec}: takový odstavec není")
            elif not text.strip():
                chyby.append(f"výklad § {cislo} odst. {odstavec}: prázdný text")

    celkem = sum(len(o) for o in odstavce.values())
    hotovo = sum(
        1
        for cislo, k in vyklad.items()
        for odstavec in k
        if odstavec in odstavce.get(cislo, ())
    )
    print(f"zákon           {len(zakon)} paragrafů, {celkem} odstavců")
    print(f"výklad          {hotovo} odstavců ({100 * hotovo // celkem} %)")
    return chyby


def main():
    otazky = {
        o["id"]: o
        for o in json.loads((KOREN / "zkouska/assets/otazky.json").read_text("utf-8"))
    }
    odpovedi = json.loads((KOREN / "zkouska/assets/odpovedi.json").read_text("utf-8"))

    chyby = []
    for oid, odp in odpovedi.items():
        otazka = otazky.get(oid)
        if otazka is None:
            chyby.append(f"{oid}: taková otázka neexistuje")
            continue

        chybi = POVINNE - odp.keys()
        if chybi:
            chyby.append(f"{oid}: chybí pole {', '.join(sorted(chybi))}")
        if odp.get("stav") not in STAVY:
            chyby.append(f"{oid}: neznámý stav {odp.get('stav')!r}")
        if odp.get("stav") == "zastarala" and not odp.get("poznamka"):
            chyby.append(f"{oid}: zastaralá otázka musí mít poznámku, co se změnilo")

        spravne = odp.get("spravne")
        if not isinstance(spravne, list) or not spravne:
            chyby.append(f"{oid}: 'spravne' musí být neprázdné pole indexů")
            continue
        if len(set(spravne)) != len(spravne):
            chyby.append(f"{oid}: opakující se index ve 'spravne'")
        for i in spravne:
            if not isinstance(i, int) or not 0 <= i < len(otazka["varianty"]):
                chyby.append(f"{oid}: index {i!r} mimo rozsah 0–{len(otazka['varianty']) - 1}")
        # Sázka na jistotu „žádná odpověď není správná" spolu s konkrétní
        # variantou je vnitřně rozporná — jedno z toho je omyl.
        posledni = len(otazka["varianty"]) - 1
        if posledni in spravne and len(spravne) > 1 and ZADNA.search(otazka["varianty"][posledni]):
            chyby.append(f"{oid}: „žádná odpověď\" se nedá kombinovat s jinou variantou")

    chyby += zkontroluj_vyklad()

    hotovo = sum(1 for o in odpovedi.values() if o.get("stav") == "platna")
    print(f"otázek celkem   {len(otazky)}")
    print(f"odpovědí        {len(odpovedi)}  (platných {hotovo}, zastaralých {len(odpovedi) - hotovo})")

    podle = {}
    for oid in odpovedi:
        if oid in otazky:
            podle[otazky[oid]["oblast"]] = podle.get(otazky[oid]["oblast"], 0) + 1
    for oblast, kolik in sorted(podle.items(), key=lambda x: -x[1]):
        celkem = sum(1 for o in otazky.values() if o["oblast"] == oblast)
        print(f"  {oblast:<24} {kolik:>4} / {celkem}")

    if chyby:
        print(f"\n{len(chyby)} chyb:", file=sys.stderr)
        for c in chyby:
            print(f"  {c}", file=sys.stderr)
        return 1
    print("\nbez chyb")
    return 0


if __name__ == "__main__":
    sys.exit(main())
