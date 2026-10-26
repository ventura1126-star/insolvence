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


# Vzorec u cvičení je obyčejná aritmetika; nic jiného se v něm nesmí objevit.
VZOREC = re.compile(r"^[0-9+\-*/()., ]*$")


def _spocitej(vzorec):
    import math
    holy = vzorec.replace("ceil", "").replace("round", "")
    if not VZOREC.match(holy):
        raise ValueError("nepovolený znak")
    return eval(vzorec, {"__builtins__": {}}, {"ceil": math.ceil, "round": round})


def zkontroluj_ucetnictvi():
    """Lekce manažerského účetnictví — počítá se v nich, takže se přepočítávají.

    Každý řádek tabulky se „soucet" musí sedět na průběžný součet řádků nad ním
    a každé cvičení s číselnou odpovědí musí mít vzorec, který na ni vyjde.
    Překlep v čísle by jinak naučil špatný postup a nikdo by si ho nevšiml.
    """
    soubor = KOREN / "artefakt/ucetnictvi.json"
    if not soubor.exists():
        return []
    data = json.loads(soubor.read_text("utf-8"))
    chyby = []
    videna = set()
    tabulek = cviceni = 0
    for lekce in data.get("lekce", []):
        lid = lekce.get("id", "?")
        for pole in ("id", "cislo", "nazev", "perex", "pramen", "body"):
            if not lekce.get(pole):
                chyby.append(f"lekce {lid}: chybí {pole}")
        if not re.fullmatch(r"[a-z0-9]+", lid):
            # Id je součástí klíče rozhovoru „m-<id>-<bod>", pomlčka by ho rozbila.
            chyby.append(f"lekce {lid}: id smí mít jen malá písmena a číslice")
        if lid in videna:
            chyby.append(f"lekce {lid}: id se opakuje")
        videna.add(lid)
        for i, b in enumerate(lekce.get("body", [])):
            if not b.get("nadpis") or not b.get("text", "").strip():
                chyby.append(f"lekce {lid} bod {i}: prázdný nadpis nebo text")
            tab = b.get("tabulka")
            if not tab:
                continue
            tabulek += 1
            # Tabulka má buď jeden sloupec částek, nebo víc (rozpočet po
            # týdnech). Každý sloupec se sčítá zvlášť; řádek „prevod" musí
            # navazovat na poslední součet předchozího sloupce.
            sloupcu = len(tab.get("sloupce") or [None])
            prubezne = [0] * sloupcu
            posledni = [None] * sloupcu
            for r in tab.get("radky", []):
                hodnoty = r.get("kc")
                if sloupcu == 1:
                    hodnoty = [hodnoty]
                if (not isinstance(hodnoty, list) or len(hodnoty) != sloupcu
                        or not all(isinstance(h, (int, float)) for h in hodnoty)):
                    chyby.append(f"lekce {lid} bod {i}: řádek {r.get('t')!r} nemá "
                                 f"{sloupcu} čísel")
                    continue
                for s_, h in enumerate(hodnoty):
                    if r.get("soucet"):
                        if abs(h - prubezne[s_]) > 0.5:
                            chyby.append(f"lekce {lid} bod {i} sloupec {s_ + 1}: {r['t']!r} "
                                         f"je {h}, součet řádků nad ním je {prubezne[s_]}")
                        posledni[s_] = h
                    else:
                        prubezne[s_] += h
            for r in tab.get("radky", []):
                if not r.get("prevod") or sloupcu == 1:
                    continue
                for s_ in range(1, sloupcu):
                    if posledni[s_ - 1] is not None and abs(r["kc"][s_] - posledni[s_ - 1]) > 0.5:
                        chyby.append(f"lekce {lid} bod {i} sloupec {s_ + 1}: {r['t']!r} "
                                     f"nenavazuje na konečný stav předchozího sloupce")
        for i, c in enumerate(lekce.get("cviceni", [])):
            cviceni += 1
            if not c.get("zadani") or not c.get("reseni"):
                chyby.append(f"lekce {lid} cvičení {i}: chybí zadání nebo řešení")
            if "odpoved" not in c:
                continue
            if not c.get("vzorec"):
                chyby.append(f"lekce {lid} cvičení {i}: číselná odpověď bez vzorce")
                continue
            try:
                vysledek = _spocitej(c["vzorec"])
            except Exception as e:  # noqa: BLE001 — chceme vidět jakoukoli chybu vzorce
                chyby.append(f"lekce {lid} cvičení {i}: vzorec nejde spočítat ({e})")
                continue
            if abs(vysledek - c["odpoved"]) > 0.005:
                chyby.append(f"lekce {lid} cvičení {i}: vzorec dává {vysledek}, "
                             f"odpověď je {c['odpoved']}")
    print(f"účetnictví     {len(data.get('lekce', []))} lekcí, "
          f"{tabulek} tabulek, {cviceni} cvičení")
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


def zkontroluj_uvody(zakon):
    """Laické úvody k hlavám — hlídá, že se nerozešly se zákonem.

    Úvod se páruje s hlavou dvojicí cast + hlava a jeho osa odkazuje na
    paragrafy číslem v poli „od". Novela umí hlavu přejmenovat i paragraf
    zrušit; pak by úvod zmizel ze seznamu nebo by skok vedl do prázdna,
    aniž by si toho kdokoli všiml.
    """
    zdroj = KOREN / "artefakt/uvody.json"
    if not zdroj.exists():
        return []
    uvody = json.loads(zdroj.read_text("utf-8"))
    chyby = []
    hlavy = {(p["cast"], p["hlava"]) for p in zakon}
    cisla = {p["paragraf"] for p in zakon}
    videna = set()
    for u in uvody:
        kde = u.get("nazev") or u.get("id")
        if u["id"] in videna:
            chyby.append(f"úvod {kde}: id {u['id']} se opakuje")
        videna.add(u["id"])
        if (u["cast"], u["hlava"]) not in hlavy:
            chyby.append(f"úvod {kde}: taková hlava v zákoně není")
        if not u.get("perex", "").strip():
            chyby.append(f"úvod {kde}: chybí perex")
        for b in u.get("bloky", []):
            if not b.get("nadpis", "").strip() or not b.get("text", "").strip():
                chyby.append(f"úvod {kde}: blok bez nadpisu nebo bez textu")
        for d in u.get("osa", []):
            if d.get("od") not in cisla:
                chyby.append(f"úvod {kde}: osa odkazuje na § {d.get('od')}, který v zákoně není")
            if not d.get("nazev", "").strip() or not d.get("veta", "").strip():
                chyby.append(f"úvod {kde}: položka osy bez názvu nebo bez věty")
    print(f"úvody          {len(uvody)} hlav z {len(hlavy)}")
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
    chyby += zkontroluj_ucetnictvi()
    chyby += zkontroluj_uvody(zakon)
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
