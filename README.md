# Zkouška IS

Trenažér na písemnou část **obecné zkoušky insolvenčního správce**.

Test u zkoušky má 70 otázek z okruhů audit, daně, obecné právo a exekuce a
insolvence; k úspěchu je potřeba 56 správně (80 %). App to kopíruje: ostrý test
v ostrém formátu, trénink po okruzích s vysvětlením a odkazem na paragraf, a
opakování toho, co ti nesedí.

Po testu následuje ještě případová studie a ústní část — ty app neřeší.
Zdroj: <https://insolvence.justice.cz/zkousky-insolvencnich-spravcu/obecna-jak-zkouska-probiha/>

## Než to začneš používat, dvě věci

**Sada otázek je z roku 2014 a ministerstvo ji nahradilo.** Testový systém prošel
koncem roku 2020 zásadní revizí, aktuální banka je neveřejná a podstatně větší.
Tohle je tréninkový materiál na témata zkoušky, ne seznam otázek, které u ní
padnou.

**Odpovědi jsou neoficiální.** PDF ministerstva správné odpovědi neobsahují —
každá je tu dohledaná ručně proti dnešnímu znění předpisů a nese odkaz na
paragraf, ze kterého plyne. U části sporných ustanovení jde o nejlepší výklad,
ne o jistotu. Odkaz na paragraf je tam právě proto, aby šlo ověřovat, ne věřit.

Kde novela mezitím změnila právo tak, že žádná z nabízených variant už neplatí,
je otázka označená `"stav": "zastarala"` a poznámkou, co se změnilo. Takové
otázky se do ostrého testu nemíchají, aby neučily neplatné právo, ale v tréninku
se ukazují — na nich je změna vidět nejlíp.

## Stav odpovědí

| Okruh | Odpovědí | Z toho zastaralých | Otázek celkem |
|---|---:|---:|---:|
| Audit | 60 | 1 | 60 |
| Obecné právo a exekuce | 61 | 1 | 216 |
| Daně | 52 | 14 | 108 |
| Insolvence | 27 | 0 | 1 049 |
| **Celkem** | **200** | **16** | **1 433** |

## Spuštění

```bash
cd zkouska && npm install && npm start
```

Nainstaluj **Expo Go** z App Storu a načti QR kód z terminálu; telefon a Mac musí
být na stejné Wi-Fi. Projekt běží na **Expo SDK 54** — nepovyšovat, viz
[zkouska/AGENTS.md](zkouska/AGENTS.md).

Testy logiky: `cd zkouska && npm test`

## Odkud se berou data

```bash
python3 -m venv .venv && .venv/bin/pip install -r tools/requirements.txt
```

```bash
.venv/bin/python tools/parse_otazky.py     # PDF ministerstva → otazky.json
python3 tools/stahni_zakon.py 2006-182     # znění předpisu k psaní odpovědí
python3 tools/kontrola_odpovedi.py         # kontrola odpovědí proti otázkám
```

Virtuální prostředí potřebuje jen parser (kvůli `pypdf`); zbylé dva skripty si
vystačí se standardní knihovnou.

`parse_otazky.py` si čtyři PDF stáhne z `insolvence.justice.cz` do `_zdroje/`
(mimo repo) a rozparsuje je. Strukturu čte z vodorovných souřadnic textu, ne
z odsazení — znění otázek i variant se lámou přes víc řádků a v prostém textu
nejde zalomení odlišit od začátku další otázky. Projde 1 432 z 1 433 otázek; ta
jediná výjimka je vada v PDF ministerstva, kde otázka o počtu členů věřitelského
výboru má jen jednu variantu.

`stahni_zakon.py` stahuje aktuální znění předpisů a umí vypsat konkrétní
paragraf (`--paragraf 3`). Předpisy jsou autorskoprávně volné.

### Formát odpovědi

```json
"insolvence-0014": {
  "spravne": [1],
  "pramen": "§ 3 odst. 4 insolvenčního zákona",
  "vysvetleni": "O předlužení jde tehdy, má-li dlužník více věřitelů a …",
  "stav": "platna"
}
```

`spravne` je pole indexů do `varianty` dané otázky — správných variant může být
víc a otázka se počítá za správnou jen při přesné shodě celé sady. Ministerstvo
formát testu nikde nepopisuje, ale otázky to vynucují: u „Povinnou součástí
účetní závěrky je" jsou podle § 18 odst. 1 zákona o účetnictví správné rovnou
tři varianty. Zastaralá odpověď má navíc povinné `poznamka`.

## Nasazení

```bash
cd zkouska && npm run build:web
```

Vyexportuje web do `docs/`, doplní hlavičkové tagy pro přidání na plochu telefonu
a zapíše `.nojekyll` (bez něj GitHub Pages spustí Jekyll a ten složku `_expo`
s bundlem přeskočí). Pak stačí commitnout a pushnout — GitHub Actions web
republikují samy.

`baseUrl` v `zkouska/app.json` musí odpovídat názvu repozitáře (`/insolvence`),
jinak si stránka nenajde bundle a načte se prázdná.

**Pozor:** GitHub Pages ze soukromého repozitáře fungují jen na placeném plánu
(GitHub Pro a výš). Na free plánu se web nenasadí — app pak jde spouštět lokálně
přes `npm start`, což na učení stačí.
