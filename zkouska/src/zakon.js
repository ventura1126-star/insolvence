/**
 * Insolvenční zákon s výkladem.
 *
 * Znění zákona (assets/zakon.json) se generuje z e-Sbírky nástrojem
 * tools/vytez_zakon.py a ručně se do něj nesahá — v aplikaci má stát přesně
 * to, co je ve Sbírce. Výklad (assets/vyklad.json) je psaný ručně a leží
 * vedle, klíčovaný číslem paragrafu a v něm číslem odstavce. Paragraf bez
 * číslovaných odstavců má jediný odstavec pod klíčem BEZ_CISLA.
 *
 * Díky tomu jde zákon kdykoli přegenerovat po novele, aniž by se ztratil
 * výklad; kontrola v tools/kontrola_odpovedi.py pak ukáže, který výklad visí
 * u odstavce, který už v zákoně není.
 */

export const BEZ_CISLA = '-';

/** Klíč odstavce ve vyklad.json. */
export function klicOdstavce(odstavec) {
  return odstavec.cislo ?? BEZ_CISLA;
}

/** Výklad k jednomu odstavci, nebo null. */
export function vykladOdstavce(vyklad, paragraf, odstavec) {
  return vyklad[paragraf.paragraf]?.[klicOdstavce(odstavec)] ?? null;
}

/** Kolik odstavců paragrafu už má výklad. */
export function vylozenoVParagrafu(vyklad, paragraf) {
  return paragraf.odstavce.filter((o) => vykladOdstavce(vyklad, paragraf, o)).length;
}

/**
 * Zákon rozdělený na části a v nich na hlavy, v pořadí, v jakém stojí v zákoně.
 *
 * Hlubší úrovně (díl, oddíl) se do obsahu nepromítají — zákon by se tím
 * rozdrobil na desítky skupin po dvou paragrafech a hledalo by se v tom hůř
 * než v prostém seznamu. Zůstávají u paragrafu jako drobečková navigace.
 */
export function obsah(zakon) {
  const casti = [];
  for (const p of zakon) {
    let cast = casti[casti.length - 1];
    if (!cast || cast.nazev !== p.cast) {
      cast = { nazev: p.cast, hlavy: [] };
      casti.push(cast);
    }
    let hlava = cast.hlavy[cast.hlavy.length - 1];
    // Část bez hlav (např. část třetí) dostane jednu bezejmennou skupinu.
    if (!hlava || hlava.nazev !== p.hlava) {
      hlava = { nazev: p.hlava, paragrafy: [] };
      cast.hlavy.push(hlava);
    }
    hlava.paragrafy.push(p);
  }
  return casti;
}

/** Paragraf podle čísla („38“, „7b“), nebo null. */
export function najdiParagraf(zakon, cislo) {
  return zakon.find((p) => p.paragraf === cislo) ?? null;
}

/** Předchozí a následující paragraf v pořadí zákona. */
export function sousedi(zakon, cislo) {
  const i = zakon.findIndex((p) => p.paragraf === cislo);
  if (i < 0) return { predchozi: null, dalsi: null };
  return {
    predchozi: zakon[i - 1] ?? null,
    dalsi: zakon[i + 1] ?? null,
  };
}

/**
 * Vyhledávání v zákoně.
 *
 * Číslo se bere jako číslo paragrafu (a přesná shoda jde první), cokoli
 * jiného se hledá v názvu paragrafu i ve znění odstavců. Diakritika se
 * ignoruje, aby „zajisteny veritel“ našlo totéž co „zajištěný věřitel“.
 */
export function hledej(zakon, dotaz, limit = 40) {
  const hledane = bezDiakritiky(dotaz).trim();
  if (!hledane) return [];

  const cislo = hledane.replace(/^§\s*/, '');
  if (/^\d+[a-z]?$/.test(cislo)) {
    const presne = zakon.filter((p) => p.paragraf === cislo);
    const zacina = zakon.filter((p) => p.paragraf !== cislo && p.paragraf.startsWith(cislo));
    return [...presne, ...zacina].slice(0, limit);
  }

  const nalezene = [];
  for (const p of zakon) {
    const vNazvu = p.nazev && bezDiakritiky(p.nazev).includes(hledane);
    const vTextu = p.odstavce.some((o) => bezDiakritiky(o.text).includes(hledane));
    if (vNazvu || vTextu) nalezene.push({ paragraf: p, vNazvu: !!vNazvu });
  }
  // Shoda v názvu je skoro vždy to, co člověk hledal; text až za ní.
  nalezene.sort((a, b) => Number(b.vNazvu) - Number(a.vNazvu));
  return nalezene.slice(0, limit).map((n) => n.paragraf);
}

function bezDiakritiky(text) {
  return text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
}

/** Kolik odstavců zákona už má výklad, celkem. */
export function pokrytiVykladu(zakon, vyklad) {
  const celkem = zakon.reduce((soucet, p) => soucet + p.odstavce.length, 0);
  const hotovo = zakon.reduce((soucet, p) => soucet + vylozenoVParagrafu(vyklad, p), 0);
  return { hotovo, celkem };
}
