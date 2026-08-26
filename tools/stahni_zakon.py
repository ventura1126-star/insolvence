#!/usr/bin/env python3
"""Stáhne aktuální znění právního předpisu do prostého textu a nechá si ho lokálně.

Odpovědi k testovým otázkám se musí opírat o dnešní znění předpisu, ne o znění
z roku 2014, kdy otázky vznikly — u insolvence je mezi tím oddlužovací novela
(31/2019 Sb.) a řada dalších změn. Tenhle skript slouží k tomu, aby šlo znění
paragrafu při psaní odpovědi skutečně přečíst.

Použití:
    python tools/stahni_zakon.py 1991-563 2006-182 ...
    python tools/stahni_zakon.py --paragraf 3 1991-563

Předpisy jsou veřejné a autorskoprávně volné (§ 3 písm. a) autorského zákona).
"""

import argparse
import html
import re
import subprocess
import sys
from pathlib import Path

CACHE = Path(__file__).resolve().parent.parent / "_zdroje" / "zakony"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"

ZNAME = {
    "1991-563": "zákon o účetnictví",
    "1992-586": "zákon o daních z příjmů",
    "1963-99": "občanský soudní řád",
    "2001-120": "exekuční řád",
    "2004-235": "zákon o DPH",
    "2006-182": "insolvenční zákon",
    "2006-262": "zákoník práce",
    "2006-312": "zákon o insolvenčních správcích",
    "2009-93": "zákon o auditorech",
    "2009-280": "daňový řád",
    "2012-89": "občanský zákoník",
    "2012-90": "zákon o obchodních korporacích",
}


def na_text(html_zdroj):
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html_zdroj)
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = re.sub(r"(?i)</(p|div|li|tr|h\d)>", "\n", s)
    s = html.unescape(re.sub(r"(?s)<[^>]+>", " ", s))
    s = s.replace("\xa0", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r" *\n *", "\n", s)
    return re.sub(r"\n{3,}", "\n\n", s).strip()


def stahni(kod, obnovit=False):
    CACHE.mkdir(parents=True, exist_ok=True)
    cil = CACHE / f"{kod}.txt"
    if cil.exists() and not obnovit:
        return cil

    url = f"https://www.zakonyprolidi.cz/cs/{kod}"
    hotovo = subprocess.run(
        ["curl", "-sS", "-L", "-A", UA, url], capture_output=True, text=True
    )
    if hotovo.returncode != 0:
        sys.exit(f"stažení {kod} selhalo: {hotovo.stderr.strip()}")

    text = na_text(hotovo.stdout)
    if len(text) < 5000:
        sys.exit(f"{kod}: podezřele krátký výstup ({len(text)} znaků), zkontroluj zdroj")

    cil.write_text(text, encoding="utf-8")
    return cil


def vypis_paragraf(cesta, cislo):
    """Vypíše jeden paragraf — od jeho nadpisu po začátek následujícího."""
    text = cesta.read_text(encoding="utf-8")
    zacatek = re.compile(rf"^§ {re.escape(cislo)}$", re.M)
    dalsi = re.compile(r"^§ \S+$", re.M)

    # První výskyt v obsahu je jen odkaz; bere se poslední, tedy vlastní text.
    starty = [m.start() for m in zacatek.finditer(text)]
    if not starty:
        print(f"§ {cislo} nenalezen", file=sys.stderr)
        return
    zac = starty[-1]
    konec = dalsi.search(text, zac + 1)
    print(text[zac : konec.start() if konec else zac + 6000])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kody", nargs="+", help="např. 2006-182 (rok-číslo)")
    ap.add_argument("--paragraf", help="vypsat jen tenhle paragraf")
    ap.add_argument("--obnovit", action="store_true", help="stáhnout znovu")
    args = ap.parse_args()

    for kod in args.kody:
        cesta = stahni(kod, args.obnovit)
        if args.paragraf:
            vypis_paragraf(cesta, args.paragraf)
        else:
            kb = cesta.stat().st_size // 1024
            print(f"{kod:<10} {ZNAME.get(kod, '?'):<34} {kb:>5} kB  {cesta}")


if __name__ == "__main__":
    main()
