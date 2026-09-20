# Zkouška IS

Trenažér na písemnou část **obecné zkoušky insolvenčního správce**.

Test u zkoušky má 70 otázek z okruhů audit, daně, obecné právo a exekuce a
insolvence; k úspěchu je potřeba 56 správně (80 %). App to kopíruje: ostrý test
v ostrém formátu, trénink po okruzích s vysvětlením a odkazem na paragraf, a
opakování toho, co ti nesedí.

Vedle testů je v appce celý **insolvenční zákon s výkladem** — znění podle
Sbírky a pod každým odstavcem vysvětlení, co znamená v praxi správce, na co si
dát pozor a co z něj bývá u zkoušky. Dá se v něm hledat podle čísla paragrafu
i podle slova (bez ohledu na diakritiku) a procházet paragraf po paragrafu.
Znění je v `assets/zakon.json` a generuje se, výklad je v `assets/vyklad.json`
a píše se ručně; kolečko u paragrafu v obsahu ukazuje, kolik z něj je hotové.

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
| Obecné právo a exekuce | 76 | 1 | 216 |
| Daně | 52 | 14 | 108 |
| Insolvence | 281 | 0 | 1 049 |
| **Celkem** | **469** | **16** | **1 433** |

Výklad zákona: **103 z 1 420 odstavců** (§ 1 až § 38 — základní ustanovení,
procesní subjekty a celý díl o insolvenčním správci). Zbytek přibývá po dávkách.

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
python3 tools/vytez_zakon.py               # znění zákona → artefakt/zakon.json
python3 tools/kontrola_odpovedi.py         # kontrola odpovědí i výkladu
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

`vytez_zakon.py` z toho staženého znění vyrobí `artefakt/zakon.json` —
482 paragrafů rozdělených na 1 420 odstavců i s částmi, hlavami a díly. Text
zákona se tedy nikde nepřepisuje ručně a po novele se dá celý přegenerovat;
výklad leží zvlášť v `artefakt/vyklad.json` a `kontrola_odpovedi.py` hlídá, že
po přegenerování nevisí u odstavce, který už v zákoně není. Obojí patří druhé
appce, proto to bydlí v `artefakt/`.

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

Web běží na <https://ventura1126-star.github.io/insolvence/> a je neindexovaný
(`noindex` v hlavičce). Repozitář je soukromý, stránka veřejná.

## Zákon s výkladem jako Artifact

Týž zákon a výklad běží i jako Artifact na claude.ai —
<https://claude.ai/artifact/17oidZ2ypcBMaJS8MHj4aF>. Navíc proti webové verzi
umí dvě věci, které statická stránka neumí. Pod každým odstavcem se dá rovnou
zeptat Claudea, a ten dostane v kontextu znění toho odstavce i výklad k němu.
Rozhovory se ukládají dvakrát: hned do prohlížeče (drží obnovení stránky a
nepotřebuje k tomu nic povolovat) a navíc na server (pak jsou vidět i na
druhém zařízení). Když server nejde, panel to napíše i s důvodem — mlčky se
to neztrácí. A celé se to dá
vytisknout — jeden paragraf, všechno s výkladem, nebo celý zákon, volitelně
i s uloženými rozhovory. Tisk má vlastní sazbu, ne obrázek obrazovky: místo
barevných ploch linky (plná u výkladu, tečkovaná u rozhovoru), každý paragraf
na novou stránku.

```bash
python3 tools/sbal_artefakt.py
```

Z `artefakt/zakon.json`, `vyklad.json` a `temata.json` vyrobí `zakon.js`,
`vyklad.js` a `temata.js` (data pověšená na `window`, čistě v ASCII kvůli
kódování) a ty se publikují spolu s `artefakt/index.html`. Vygenerované skripty
jsou mimo repo, stránka i data v něm jsou.

Vedle zákona má Artifact sekci **Mimo insolvenční zákon** (`temata.json`) —
21 témat ze ZOK a z občanského zákoníku, která do insolvenční praxe zasahují:
péče řádného hospodáře, § 66 ZOK, diskvalifikace, zajištění a jeho druhy,
odporovatelnost, započtení, SJM. Každý bod má vlastní rozhovor i tisk, stejně
jako odstavec zákona.

Dvě appky, každá na jedno: **Pages** trénuje otázky, **Artifact** nese zákon.
Odkaz mezi nimi vede z úvodní obrazovky Pages.
