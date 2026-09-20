# -*- coding: utf-8 -*-
"""
Vytěží insolvenční zákon ze staženého znění do artefakt/zakon.json.

Text zákona se nikde nepřepisuje ručně — bere se doslova z toho, co stáhl
stahni_zakon.py, aby v aplikaci stálo přesně to, co je ve Sbírce. Ručně se
píše jen výklad, a ten leží vedle v artefakt/vyklad.json.

Struktura zdroje je naštěstí jednoduchá: nadpisy (ČÁST, HLAVA, Díl, Oddíl,
§ N) stojí každý na vlastním řádku, hned za § může být jeho název a pak
teprve text. Odstavce začínají „(1)“, písmena „a)“ a patří vždy k odstavci
nad sebou. Paragraf bez čísel v závorkách má jediný nečíslovaný odstavec.

Spuštění:  python3 tools/vytez_zakon.py
"""
import json
import re
import sys
from pathlib import Path

ZDROJ = Path("_zdroje/zakony/2006-182.txt")
CIL = Path("artefakt/zakon.json")

CAST = re.compile(r"^ČÁST (PRVNÍ|DRUHÁ|TŘETÍ|ČTVRTÁ|PÁTÁ)$")
HLAVA = re.compile(r"^HLAVA [IVXL]+$")
DIL = re.compile(r"^Díl \d+$")
ODDIL = re.compile(r"^Oddíl \d+$")
PARAGRAF = re.compile(r"^§ (\d+[a-z]*)$")
ODSTAVEC = re.compile(r"^\((\d+)\)\s*(.*)$")
# Odkaz na poznámku pod čarou: „ 75 )“. Písmena „a)“ mezeru před závorkou nemají.
POZNAMKA = re.compile(r" \d+[a-z]?\s\)")
# Nadpis paragrafu nikdy nekončí tečkou a nezačíná malým písmenem ani závorkou.
NADPIS = re.compile(r"^[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][^.]*$")


def nacti_radky():
    if not ZDROJ.exists():
        sys.exit(f"chybí {ZDROJ} — spusť nejdřív tools/stahni_zakon.py 2006-182")
    radky = [r.strip() for r in ZDROJ.read_text(encoding="utf-8").split("\n")]
    # Před vlastním zákonem je obsah a navigace webu, za ním přechodná
    # ustanovení novel. Bereme jen to mezi.
    zacatek = next(
        i for i, r in enumerate(radky)
        if r == "Parlament se usnesl na tomto zákoně České republiky:"
    )
    konec = next(
        i for i, r in enumerate(radky[zacatek:], zacatek)
        if r.startswith("Přechodné ustanovení zavedeno")
        or r.startswith("Přechodná ustanovení zavedena")
    )
    return [r for r in radky[zacatek + 1:konec] if r]


def vytez():
    radky = nacti_radky()
    paragrafy = []
    kde = {"cast": None, "hlava": None, "dil": None, "oddil": None}
    aktualni = None
    ceka_nadpis = False

    def uzavri():
        if aktualni:
            paragrafy.append(aktualni)

    i = 0
    while i < len(radky):
        r = radky[i]

        for klic, vzor, hloubka in (
            ("cast", CAST, 0), ("hlava", HLAVA, 1), ("dil", DIL, 2), ("oddil", ODDIL, 3)
        ):
            if vzor.match(r):
                # Za nadpisem úrovně stojí na dalším řádku její název.
                nazev = radky[i + 1] if i + 1 < len(radky) else ""
                kde[klic] = f"{r} — {nazev}"
                # Nižší úrovně se vstupem do vyšší ruší.
                for nizsi in list(kde)[hloubka + 1:]:
                    kde[nizsi] = None
                i += 2
                break
        else:
            m = PARAGRAF.match(r)
            if m:
                uzavri()
                aktualni = {
                    "paragraf": m.group(1),
                    "nazev": None,
                    **{k: v for k, v in kde.items()},
                    "odstavce": [],
                }
                ceka_nadpis = True
                i += 1
                continue

            if aktualni is None:
                i += 1
                continue

            if ceka_nadpis:
                ceka_nadpis = False
                # Název paragrafu je nepovinný; poznáme ho podle toho, že za ním
                # ještě následuje text a sám větou není.
                if NADPIS.match(r) and not ODSTAVEC.match(r) and len(r) < 90:
                    aktualni["nazev"] = r
                    i += 1
                    continue

            m = ODSTAVEC.match(r)
            if m:
                aktualni["odstavce"].append({"cislo": m.group(1), "text": m.group(2)})
            elif aktualni["odstavce"]:
                aktualni["odstavce"][-1]["text"] += "\n" + r
            else:
                # Paragraf bez číslovaných odstavců.
                aktualni["odstavce"].append({"cislo": None, "text": r})
            i += 1

    uzavri()
    return paragrafy


def main():
    paragrafy = vytez()
    for p in paragrafy:
        for o in p["odstavce"]:
            o["text"] = POZNAMKA.sub("", o["text"])
    CIL.write_text(
        json.dumps(paragrafy, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    odstavcu = sum(len(p["odstavce"]) for p in paragrafy)
    cislovanych = sum(1 for p in paragrafy for o in p["odstavce"] if o["cislo"])
    print(f"{CIL}: {len(paragrafy)} paragrafů, {odstavcu} odstavců "
          f"(z toho {cislovanych} číslovaných)")
    bez = [p["paragraf"] for p in paragrafy if not p["odstavce"]]
    if bez:
        print("bez textu:", ", ".join(bez))


if __name__ == "__main__":
    main()
