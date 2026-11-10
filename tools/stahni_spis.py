#!/usr/bin/env python3
"""Stáhne dokumenty insolvenčního spisu z insolvenčního rejstříku (ISIR).

Skutečné spisy jsou nejlepší předloha pro hru i pro výklad — je v nich vidět,
v jakém pořadí se věci opravdu dějí a co správce skutečně píše. Stránka
s detailem spisu je veřejná a jde stáhnout bez přihlášení; tenhle skript ji
rozebere po oddílech a stáhne PDF k jednotlivým událostem.

Dokumenty obsahují osobní údaje dlužníků a věřitelů. Ukládají se proto do
_zdroje/spisy/, které je mimo git — do repozitáře ani do Artifactu se nedostanou.
Ve hře se ze spisu bere jen průběh řízení; jména, částky a místa jsou vymyšlené.

Adresu spisu získáte v rejstříku: https://isir.justice.cz → vyhledat dlužníka
→ u výsledku „Detail“ → zkopírovat adresu z prohlížeče.

Použití:
    python3 tools/stahni_spis.py ADRESA                  # jen vypíše dokumenty
    python3 tools/stahni_spis.py ADRESA --jen A8 B3 P2-2 # stáhne vybrané
    python3 tools/stahni_spis.py ADRESA --oddil B        # celý oddíl B
    python3 tools/stahni_spis.py ADRESA --vse            # celý spis
"""

import argparse
import re
import sys
import unicodedata
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

KOREN = Path(__file__).resolve().parent.parent
CIL = KOREN / "_zdroje" / "spisy"
ZAKLAD = "https://isir.justice.cz"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"

ODDILY = {
    "A": "Řízení do úpadku",
    "B": "Řízení po úpadku",
    "C": "Incidenční spory",
    "D": "Ostatní",
    "P": "Přihlášky",
}


class Rozbor(HTMLParser):
    """Projde stránku detailu a posbírá řádky tabulek po oddílech.

    Oddíl pozná podle nadpisu h4 s id „…_oddil_X“; řádek je každé <tr>
    s buňkami <td>. U odkazu na PDF si pamatuje, ve kterém sloupci byl —
    v jednom je hlavní dokument, ve vedlejším PDF portfolio.
    """

    def __init__(self):
        super().__init__()
        self.oddil = None
        self.radky = []
        self._radek = None
        self._bunka = None
        self._v_h4 = False
        self._text = []
        self.hlavicka = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "h4" and "oddil_" in (a.get("id") or ""):
            self.oddil = a["id"].rsplit("_", 1)[-1].upper()
        if tag == "tr":
            self._radek = {"oddil": self.oddil, "bunky": [], "odkazy": []}
        if tag in ("td", "th") and self._radek is not None:
            self._bunka = []
        if tag == "br" and self._bunka is not None:
            self._bunka.append("; ")
        if tag == "a" and self._radek is not None and "dokument.PDF" in (a.get("href") or ""):
            sloupec = len(self._radek["bunky"])
            self._radek["odkazy"].append({"href": a["href"], "sloupec": sloupec})

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._radek is not None and self._bunka is not None:
            self._radek["bunky"].append(" ".join("".join(self._bunka).split()))
            self._bunka = None
        if tag == "tr" and self._radek is not None:
            self.radky.append(self._radek)
            self._radek = None

    def handle_data(self, data):
        if self._bunka is not None:
            self._bunka.append(data)
        self._text.append(data)


def stahni(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def bez_diakritiky(t):
    t = unicodedata.normalize("NFD", t)
    return "".join(c for c in t if not unicodedata.combining(c))


def nazev_souboru(text, delka=60):
    t = re.sub(r"[^A-Za-z0-9]+", "-", bez_diakritiky(text)).strip("-")
    return t[:delka].rstrip("-") or "dokument"


def rozeber(html):
    p = Rozbor()
    p.feed(html)
    cely = " ".join("".join(p._text).split())
    m = re.search(r"Spisová značka\s+(.+?)\s+vedená u", cely)
    znacka = m.group(1).replace(" / ", "/") if m else "neznama-znacka"

    dokumenty = []
    for r in p.radky:
        b = r["bunky"]
        if not r["oddil"] or len(b) < 4 or not re.match(r"^(P\d+ - )?\d+\.$", b[0]):
            continue
        # První buňka je pořadí („3.“ nebo „P2 - 1.“), pak datum, čas, popis.
        cislo = b[0].rstrip(".").replace(" ", "")
        oznaceni = cislo if cislo.startswith("P") else r["oddil"] + cislo
        hlavni_sloupec = min((o["sloupec"] for o in r["odkazy"]), default=None)
        for o in r["odkazy"]:
            dokumenty.append({
                "oznaceni": oznaceni,
                "datum": b[1],
                "popis": b[3],
                "vedlejsi": o["sloupec"] != hlavni_sloupec,
                "url": ZAKLAD + o["href"] if o["href"].startswith("/") else o["href"],
            })
    return znacka, dokumenty


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("adresa", help="adresa stránky Detail insolvenčního řízení z isir.justice.cz")
    ap.add_argument("--jen", nargs="+", metavar="OZN", help="stáhnout jen tyto dokumenty (např. A8 B3 P2-2)")
    ap.add_argument("--oddil", nargs="+", metavar="X", help="stáhnout celé oddíly (A B C D P)")
    ap.add_argument("--vse", action="store_true", help="stáhnout celý spis")
    ap.add_argument("--bez-vedlejsich", action="store_true", help="vynechat vedlejší dokumenty (PDF portfolia)")
    a = ap.parse_args()

    if "isir.justice.cz" not in a.adresa:
        sys.exit("Čekám adresu stránky Detail z isir.justice.cz.")

    html = stahni(a.adresa).decode("utf-8", errors="replace")
    znacka, dokumenty = rozeber(html)
    if not dokumenty:
        sys.exit("Na stránce jsem nenašel žádné dokumenty — je to opravdu stránka Detail?")

    print(f"Spis {znacka}: {len(dokumenty)} dokumentů")
    oddil = None
    for d in dokumenty:
        o = d["oznaceni"][0]
        if o != oddil:
            oddil = o
            print(f"\n  Oddíl {o} — {ODDILY.get(o, '')}")
        print(f"    {d['oznaceni']:<6} {d['datum']}  {d['popis'][:70]}{'  (vedlejší)' if d['vedlejsi'] else ''}")

    vyber = []
    if a.vse:
        vyber = dokumenty
    else:
        jen = {x.upper() for x in (a.jen or [])}
        oddily = {x.upper() for x in (a.oddil or [])}
        vyber = [d for d in dokumenty if d["oznaceni"].upper() in jen or d["oznaceni"][0] in oddily]
    if a.bez_vedlejsich:
        vyber = [d for d in vyber if not d["vedlejsi"]]
    if not vyber:
        print("\nNic ke stažení nevybráno — přidejte --jen, --oddil nebo --vse.")
        return

    slozka = CIL / nazev_souboru(znacka, 80)
    slozka.mkdir(parents=True, exist_ok=True)
    print(f"\nStahuji {len(vyber)} dokumentů do {slozka}")
    for d in vyber:
        den = "-".join(reversed(d["datum"].split(".")))
        jmeno = f"{d['oznaceni']}_{den}_{nazev_souboru(d['popis'])}{'_vedlejsi' if d['vedlejsi'] else ''}.pdf"
        soubor = slozka / jmeno
        if soubor.exists():
            print(f"  už je   {jmeno}")
            continue
        data = stahni(d["url"])
        soubor.write_bytes(data)
        print(f"  staženo {jmeno}  ({len(data) // 1024} kB)")


if __name__ == "__main__":
    main()
