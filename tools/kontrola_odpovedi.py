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


def zkontroluj_temata():
    """Témata mimo insolvenční zákon — hlídá jen to, co jde strojově.

    Prázdný bod nebo chybějící pramen by se v aplikaci ukázal jako díra;
    duplicitní id by tiše přebilo jiné téma.
    """
    soubor = KOREN / "artefakt/temata.json"
    if not soubor.exists():
        return []
    temata = json.loads(soubor.read_text("utf-8"))
    chyby = []
    videna = set()
    for t in temata:
        for pole in ("id", "oblast", "nazev", "pramen", "body"):
            if not t.get(pole):
                chyby.append(f"téma {t.get('id', '?')}: chybí {pole}")
        if t.get("id") in videna:
            chyby.append(f"téma {t['id']}: id se opakuje")
        videna.add(t.get("id"))
        for i, b in enumerate(t.get("body", [])):
            if not b.get("nadpis") or not b.get("text", "").strip():
                chyby.append(f"téma {t.get('id')} bod {i}: prázdný nadpis nebo text")
    print(f"témata         {len(temata)} "
          f"({sum(len(t.get('body', [])) for t in temata)} bodů)")
    return chyby


def _citace(uzel):
    """Všechny citace insolvenčního zákona kdekoli ve scénáři hry."""
    if isinstance(uzel, dict):
        if "par" in uzel:
            yield uzel
        for v in uzel.values():
            yield from _citace(v)
    elif isinstance(uzel, list):
        for v in uzel:
            yield from _citace(v)


def zkontroluj_hru(zakon):
    """Minihra cituje paragrafy a v artefaktu na ně jde kliknout.

    Citace, která po novele míří na neexistující paragraf, odstavec nebo
    písmeno, by hráče poslala do prázdna — a hůř, učila by ho číslo, které
    už neplatí. Proto se každá ověří proti zakon.json.
    """
    soubor = KOREN / "artefakt/hra.json"
    if not soubor.exists():
        return []
    hra = json.loads(soubor.read_text("utf-8"))
    paragrafy = {p["paragraf"]: p for p in zakon}
    chyby = []

    pocet = 0
    for c in _citace(hra):
        pocet += 1
        oznaceni = f"§ {c['par']}" + (f" odst. {c['odst']}" if c.get("odst") else "")
        p = paragrafy.get(c["par"])
        if p is None:
            chyby.append(f"hra: {oznaceni} — takový paragraf v zákoně není")
            continue
        odstavec = None
        if c.get("odst"):
            odstavec = next((o for o in p["odstavce"] if o["cislo"] == c["odst"]), None)
            if odstavec is None:
                chyby.append(f"hra: {oznaceni} — takový odstavec není")
                continue
        if c.get("pism"):
            texty = [odstavec["text"]] if odstavec else [o["text"] for o in p["odstavce"]]
            vzor = re.compile(r"(^|\n)\s*" + re.escape(c["pism"]) + r"\)")
            if not any(vzor.search(t) for t in texty):
                chyby.append(f"hra: {oznaceni} písm. {c['pism']} — takové písmeno není")

    videna = set()
    for u in hra.get("udalosti", []):
        if u["id"] in videna:
            chyby.append(f"hra: událost {u['id']} — id se opakuje")
        videna.add(u["id"])
        if not 2 <= len(u.get("volby", [])) <= 4:
            chyby.append(f"hra: událost {u['id']} — má mít 2 až 4 volby")
        for i, v in enumerate(u.get("volby", [])):
            if not v.get("dusledek", "").strip() or not v.get("citace"):
                chyby.append(f"hra: událost {u['id']} volba {i} — chybí důsledek nebo citace")
    lhuty = hra.get("lhuty", {})
    for u in hra.get("udalosti", []):
        for v in u.get("volby", []):
            for lh in v.get("efekty", {}).get("lhuta", []) + v.get("efekty", {}).get("splnit", []):
                klic = lh["id"] if isinstance(lh, dict) else lh
                if klic not in lhuty:
                    chyby.append(f"hra: událost {u['id']} — neznámá lhůta {klic}")

    print(f"hra            {len(hra.get('udalosti', []))} událostí, {pocet} citací")
    return chyby


def zkontroluj_vyklad():
    """Výklad se píše ručně vedle znění zákona — hlídá, že se nerozešly.

    zakon.json se přegeneruje z e-Sbírky po každé novele, a novela umí odstavec
    přečíslovat i zrušit. Výklad, který pak visí u odstavce, co v zákoně není,
    by se v aplikaci tiše ztratil — tady je aspoň vidět.
    """
    zakon_s = KOREN / "artefakt/zakon.json"
    vyklad_s = KOREN / "artefakt/vyklad.json"
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

    chyby += zkontroluj_temata()
    chyby += zkontroluj_hru(zakon)

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
