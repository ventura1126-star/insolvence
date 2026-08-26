/**
 * Sestavení a vyhodnocení testu.
 *
 * Ostrý test kopíruje písemnou část obecné zkoušky: 70 otázek namíchaných ze
 * všech čtyř okruhů, k úspěchu je potřeba 56 správně (80 %).
 * Zdroj: https://insolvence.justice.cz/zkousky-insolvencnich-spravcu/obecna-jak-zkouska-probiha/
 *
 * Do testu jdou jen otázky, ke kterým je dohledaná odpověď platná podle
 * dnešního znění předpisů. Otázky označené jako zastaralé (novela mezitím
 * změnila právo tak, že žádná z nabízených variant už neplatí) se míchají
 * jen do tréninku, kde je u nich vidět vysvětlení, co se změnilo — v ostrém
 * testu by učily neplatné právo.
 *
 * Správných variant může být u jedné otázky víc. Ministerstvo formát nikde
 * nepopisuje, ale samotné otázky to vynucují: u „Povinnou součástí účetní
 * závěrky je" jsou podle § 18 odst. 1 zákona o účetnictví správné rovnou tři
 * z nabízených variant. Otázka se proto počítá za správnou jen tehdy, když
 * označené varianty přesně odpovídají těm správným — nic navíc, nic navíc.
 */

export const OTAZEK_V_TESTU = 70;
export const PROCENT_K_USPECHU = 0.8;

/** Kolik otázek je potřeba zodpovědět správně z daného počtu. */
export function hraniceUspechu(pocetOtazek) {
  return Math.ceil(pocetOtazek * PROCENT_K_USPECHU);
}

/** Malý deterministický PRNG (mulberry32). Stejný seed, stejná posloupnost. */
function mulberry32(seed) {
  let a = seed >>> 0;
  return function next() {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Zamíchané pole (Fisher–Yates), beze změny vstupu. */
function zamichej(pole, rand) {
  const out = pole.slice();
  for (let i = out.length - 1; i > 0; i -= 1) {
    const j = Math.floor(rand() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

/** Otázky, ke kterým je dohledaná odpověď — jen ty jde vyhodnotit. */
export function zodpovezene(otazky, odpovedi, { vcetneZastaralych = false } = {}) {
  return otazky.filter((o) => {
    const odp = odpovedi[o.id];
    if (!odp) return false;
    return vcetneZastaralych || odp.stav !== 'zastarala';
  });
}

/**
 * Přehled, kolik otázek je v každém okruhu připraveno k procvičování.
 *
 * Počítají se i otázky označené jako zastaralé — trénink okruhu je ukazuje,
 * takže by číslo jinak slibovalo míň, než kolik jich přijde.
 */
export function pokrytiOkruhu(otazky, odpovedi) {
  const podle = new Map();
  for (const o of otazky) {
    const zaznam = podle.get(o.oblast) ?? { oblast: o.oblast, celkem: 0, hotovo: 0 };
    zaznam.celkem += 1;
    if (odpovedi[o.id]) zaznam.hotovo += 1;
    podle.set(o.oblast, zaznam);
  }
  return [...podle.values()];
}

/**
 * Sestaví test o `pocet` otázkách.
 *
 * Zastoupení okruhů kopíruje jejich podíl v bance otázek — insolvence je v ní
 * dominantní (73 %) a stejně tak na zkoušce. Kde na okruh nezbývá dost
 * zodpovězených otázek, doplní se test odjinud, ať má vždycky plný počet.
 */
export function sestavTest(
  otazky,
  odpovedi,
  seed = Date.now(),
  pocet = OTAZEK_V_TESTU,
  { vcetneZastaralych = false } = {}
) {
  const rand = mulberry32(seed);
  const kDispozici = zodpovezene(otazky, odpovedi, { vcetneZastaralych });
  if (kDispozici.length === 0) return [];

  const podil = new Map();
  for (const o of otazky) podil.set(o.oblast, (podil.get(o.oblast) ?? 0) + 1);

  const vybrane = [];
  const zbytek = [];

  for (const [oblast, vBance] of podil) {
    const fond = zamichej(
      kDispozici.filter((o) => o.oblast === oblast),
      rand
    );
    const kvota = Math.round((vBance / otazky.length) * pocet);
    vybrane.push(...fond.slice(0, kvota));
    zbytek.push(...fond.slice(kvota));
  }

  // Zaokrouhlování kvót i mělké okruhy nechávají test nedopečený nebo přeplněný.
  const doplnek = zamichej(zbytek, rand).slice(0, Math.max(0, pocet - vybrane.length));
  return zamichej([...vybrane, ...doplnek].slice(0, pocet), rand);
}

/** Označil uživatel přesně ty varianty, které jsou správné? */
export function jeSpravne(oznacene, spravne) {
  if (!Array.isArray(oznacene) || !Array.isArray(spravne)) return false;
  if (oznacene.length !== spravne.length) return false;
  const hledane = new Set(spravne);
  return oznacene.every((i) => hledane.has(i));
}

/**
 * Vyhodnotí test.
 *
 * `volby` je mapa id otázky → pole označených variant; nezodpovězená otázka se
 * počítá jako chyba, stejně jako u zkoušky. Částečně označená otázka taky —
 * půlbody se neudělují.
 */
export function vyhodnot(test, volby, odpovedi) {
  const podleOblasti = new Map();
  const chyby = [];
  let spravne = 0;

  for (const o of test) {
    const zaznam = podleOblasti.get(o.oblast) ?? { oblast: o.oblast, spravne: 0, celkem: 0 };
    zaznam.celkem += 1;

    if (jeSpravne(volby[o.id], odpovedi[o.id]?.spravne)) {
      spravne += 1;
      zaznam.spravne += 1;
    } else {
      chyby.push(o.id);
    }
    podleOblasti.set(o.oblast, zaznam);
  }

  const potreba = hraniceUspechu(test.length);
  return {
    spravne,
    celkem: test.length,
    potreba,
    prosel: spravne >= potreba,
    procenta: test.length ? Math.round((spravne / test.length) * 100) : 0,
    chyby,
    podleOblasti: [...podleOblasti.values()],
  };
}
