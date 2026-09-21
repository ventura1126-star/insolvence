# Příprava na zkoušku insolvenčního správce

Richard Muzatko se připravuje na **obecnou zkoušku insolvenčního správce**.
Mluv s ním česky. Repozitář je soukromý, `ventura1126-star/insolvence`.

## Dvě aplikace, dvě session

Ať se práce neprolíná, má každá appka vlastní konverzaci. **Zjisti si na
začátku, ve které jsi**, a do té druhé nesahej, ledaže o to výslovně požádá.

### 1. Zkouška IS — trenažér otázek

- Web: <https://ventura1126-star.github.io/insolvence/> (GitHub Pages z `docs/`)
- Kód: `zkouska/` — Expo SDK 54, React Native Web
- Data: `zkouska/assets/otazky.json`, `zkouska/assets/odpovedi.json`
- Náplň: dohledávání odpovědí, režimy testu, trénink po okruzích, moje chyby

### 2. Insolvenční zákon v praxi — Artifact

- Web: <https://claude.ai/artifact/17oidZ2ypcBMaJS8MHj4aF>
- Kód: `artefakt/index.html` (jedna stránka, prostý HTML/JS, bez frameworku)
- Data: `artefakt/zakon.json`, `artefakt/vyklad.json`, `artefakt/temata.json`
- Náplň: znění zákona, výklad po odstavcích, témata mimo insolvenční zákon,
  rozhovory s Claudem, tisk
- Rozhovory: jeden sdílený **postranní panel** (na širokém displeji sloupec
  vedle textu, na telefonu přes celou obrazovku), každé vlákno má **název** a
  všechna se dají najít v přehledu **Moje rozhovory** (`#rozhovory`). Ukládají
  se dvojmo — do prohlížeče hned a na server pro druhé zařízení; selhání
  serveru se **nesmí zamlčet**, panel o něm píše i s důvodem.
- Na jednom místě může běžet **víc konverzací** vedle sebe, aby šly uzavírat.
  První má klíč místa (`36-1`), další příponu `~2`, `~3` — starší data tím
  zůstala platná. Klíč se na místo rozkládá přes `mistoZKlice`; pozor, že
  `36-1` není předponou `36-11`, proto se porovnává s vlnovkou.

Publikuje se nástrojem Artifact. Z jiné konverzace je potřeba předat `url`,
jinak vznikne nový artefakt místo aktualizace toho stávajícího.

## Pravidlo, které platí pro obojí: odpovědi se nevymýšlejí

Otázky vydalo ministerstvo bez klíče a výklad píšeme sami. **Nic se neodhaduje
zpaměti.** Každé tvrzení se ověří proti staženému znění předpisu:

```bash
python3 tools/stahni_zakon.py 2006-182            # stáhne a nacachuje předpis
python3 tools/stahni_zakon.py 2012-90 --paragraf 66   # vypíše jeden paragraf
```

Předpisy leží v `_zdroje/zakony/` (mimo repo). Nejpoužívanější: `2006-182`
(insolvenční zákon), `2012-89` (občanský zákoník), `2012-90` (ZOK), `1963-99`
(o. s. ř.), `2001-120` (exekuční řád), `1992-586` (daně z příjmů), `2004-235`
(DPH), `1991-563` (účetnictví), `2009-93` (auditoři).

Kde zákon jednoznačnou odpověď nedává, **otázku raději přeskoč**, než abys
hádal. Změnilo-li se právo tak, že žádná nabízená varianta neplatí, dostane
odpověď `"stav": "zastarala"` a povinnou `poznamka`, co se změnilo.

Narazíš-li na to, že je zastaralý nějaký podklad od Richarda (starší přehled,
text od jiného modelu), **řekni mu to napřímo** — je to cennější než tiše
opravit. Příklad: § 68 ZOK o ručení jednatele byl zrušen k 1. 1. 2021 a
nahrazen § 66, který funguje jinak.

## Jak psát výklad

Ne parafráze zákona, ale **práce správce**: konkrétní situace, jména, částky,
rozhodnutí, které správce musí udělat. Stálé obsazení, ať se případy nabalují:

- **Truhlárna Bureš s.r.o.** — 6,8 mil. dluhů, hala, stroje, 11 zaměstnanců;
  běžný konkurs
- **paní Dvořáková** — krachlá kavárna, 1,4 mil.; oddlužení
- **Strojírna Kolář a.s.** — obrat 180 mil.; reorganizace, mezera krytí
- **skupina Vltava** — koncern, převody mezi sestrami
- věřitelé: banka se zástavou na cizím domě, dodavatel Hrubý, Kovařík s ručením

V JSON se důraz zapisuje `**takhle**` a odstavce oddělují prázdným řádkem.

## Než něco pustíš ven

```bash
python3 tools/kontrola_odpovedi.py      # odpovědi, výklad i témata
cd zkouska && npm test                  # logika testu
cd zkouska && npm run build:web         # export do docs/ pro Pages
python3 tools/sbal_artefakt.py          # data pro Artifact
```

Po každé dávce **commitni a pushni sám**, nečekej, až o to Richard požádá —
Pages se z `main` nasadí samy a Artifact se publikuje nástrojem.

## Věci, o které se nepřipravit

- **Expo SDK 54 je strop** — Richardův iPhone dál nepustí Expo Go. Po zásahu do
  závislostí spusť `npx expo install --fix` a zkontroluj, že `react-native`
  zůstalo na 0.81.x. Viz `zkouska/AGENTS.md`.
- **`baseUrl` v `zkouska/app.json`** musí odpovídat názvu repozitáře
  (`/insolvence`), jinak si stránka nenajde bundle.
- **`.nojekyll`** v `docs/` — bez něj Jekyll přeskočí složku `_expo`.
- **Vygenerované soubory** `artefakt/zakon.js`, `vyklad.js`, `temata.js` jsou
  mimo repo; zdrojové `.json` v něm jsou.
