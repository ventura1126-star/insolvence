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


def zkontroluj_lekce(otazky, odpovedi):
    """Ranní lekce odkazují na otázky jen jejich id — hlídá, že tam všechny jsou.

    Lekce s otázkou bez dohledané odpovědi by se v aplikaci ukázala bez rozboru,
    což je horší než kratší lekce.
    """
    soubor = KOREN / "zkouska/assets/lekce.json"
    if not soubor.exists():
        return []

    lekce = json.loads(soubor.read_text("utf-8"))
    chyby = []
    dny = [l["den"] for l in lekce]

    if sorted(dny) != list(range(1, len(lekce) + 1)):
        chyby.append(f"lekce: dny nejdou 1..{len(lekce)} bez mezer a duplicit")

    for l in lekce:
        for pole in ("nazev", "oblast", "vyklad"):
            if not l.get(pole):
                chyby.append(f"lekce {l['den']}: chybí {pole}")
        if len(l.get("otazky", [])) < 3:
            chyby.append(f"lekce {l['den']}: míň než 3 otázky")
        if len(set(l["otazky"])) != len(l["otazky"]):
            chyby.append(f"lekce {l['den']}: opakující se otázka")
        for oid in l["otazky"]:
            if oid not in otazky:
                chyby.append(f"lekce {l['den']}: otázka {oid} neexistuje")
            elif oid not in odpovedi:
                chyby.append(f"lekce {l['den']}: otázka {oid} nemá dohledanou odpověď")
            elif odpovedi[oid]["stav"] != "platna":
                chyby.append(f"lekce {l['den']}: otázka {oid} je zastaralá")

    print(f"lekcí           {len(lekce)}  "
          f"(otázek v nich {sum(len(l['otazky']) for l in lekce)})")
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

    chyby += zkontroluj_lekce(otazky, odpovedi)

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
