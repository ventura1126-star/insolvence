/**
 * Kontroluje procházení zákona: obsah drží pořadí, hledání najde paragraf
 * podle čísla i podle slova bez diakritiky a výklad se páruje se správným
 * odstavcem — včetně paragrafu bez číslovaných odstavců.
 *
 * Spuštění:  node zkouska/src/zakon.test.mjs
 */
import assert from 'node:assert/strict';
import {
  BEZ_CISLA,
  hledej,
  najdiParagraf,
  obsah,
  pokrytiVykladu,
  sousedi,
  vykladOdstavce,
  vylozenoVParagrafu,
} from './zakon.js';

const zakon = [
  {
    paragraf: '1',
    nazev: 'Předmět úpravy',
    cast: 'ČÁST PRVNÍ',
    hlava: 'HLAVA I',
    odstavce: [{ cislo: null, text: 'Tento zákon upravuje řešení úpadku.' }],
  },
  {
    paragraf: '3',
    nazev: 'Úpadek',
    cast: 'ČÁST PRVNÍ',
    hlava: 'HLAVA I',
    odstavce: [
      { cislo: '1', text: 'Dlužník je v úpadku, jestliže má více věřitelů.' },
      { cislo: '2', text: 'Má se za to, že dlužník není schopen plnit.' },
    ],
  },
  {
    paragraf: '7b',
    nazev: 'Místní příslušnost',
    cast: 'ČÁST PRVNÍ',
    hlava: 'HLAVA II',
    odstavce: [{ cislo: '1', text: 'Pro insolvenční řízení je příslušný soud.' }],
  },
  {
    paragraf: '244',
    nazev: null,
    cast: 'ČÁST DRUHÁ',
    hlava: 'HLAVA I',
    odstavce: [{ cislo: '1', text: 'Konkurs je způsob řešení úpadku.' }],
  },
];

const vyklad = {
  1: { [BEZ_CISLA]: 'K čemu zákon je.' },
  3: { 1: 'Tři znaky úpadku.' },
};

let passed = 0;

function test(name, fn) {
  fn();
  passed += 1;
  console.log('  ok  ' + name);
}

test('obsah seskupí podle částí a hlav a drží pořadí zákona', () => {
  const casti = obsah(zakon);
  assert.deepEqual(casti.map((c) => c.nazev), ['ČÁST PRVNÍ', 'ČÁST DRUHÁ']);
  assert.deepEqual(casti[0].hlavy.map((h) => h.nazev), ['HLAVA I', 'HLAVA II']);
  assert.deepEqual(
    casti[0].hlavy[0].paragrafy.map((p) => p.paragraf),
    ['1', '3']
  );
});

test('paragraf se najde podle čísla i s písmenem', () => {
  assert.equal(najdiParagraf(zakon, '7b').nazev, 'Místní příslušnost');
  assert.equal(najdiParagraf(zakon, '999'), null);
});

test('sousedi vrátí předchozí a další, na krajích null', () => {
  assert.equal(sousedi(zakon, '3').predchozi.paragraf, '1');
  assert.equal(sousedi(zakon, '3').dalsi.paragraf, '7b');
  assert.equal(sousedi(zakon, '1').predchozi, null);
  assert.equal(sousedi(zakon, '244').dalsi, null);
});

test('hledání čísla dá přesnou shodu první', () => {
  assert.deepEqual(hledej(zakon, '7').map((p) => p.paragraf), ['7b']);
  assert.deepEqual(hledej(zakon, '§ 3').map((p) => p.paragraf), ['3']);
});

test('hledání slova ignoruje diakritiku a velikost písmen', () => {
  assert.deepEqual(hledej(zakon, 'upadku').map((p) => p.paragraf), ['1', '3', '244']);
  assert.deepEqual(hledej(zakon, 'ÚPADKU').map((p) => p.paragraf), ['1', '3', '244']);
});

test('shoda v názvu jde před shodou v textu', () => {
  // § 3 se jmenuje Úpadek, § 1 a § 244 mají „úpadku" jen ve znění.
  assert.deepEqual(hledej(zakon, 'upad').map((p) => p.paragraf), ['3', '1', '244']);
});

test('prázdný dotaz nevrací nic', () => {
  assert.deepEqual(hledej(zakon, '   '), []);
});

test('výklad se páruje s odstavcem, i s tím nečíslovaným', () => {
  const p1 = najdiParagraf(zakon, '1');
  assert.equal(vykladOdstavce(vyklad, p1, p1.odstavce[0]), 'K čemu zákon je.');
  const p3 = najdiParagraf(zakon, '3');
  assert.equal(vykladOdstavce(vyklad, p3, p3.odstavce[0]), 'Tři znaky úpadku.');
  assert.equal(vykladOdstavce(vyklad, p3, p3.odstavce[1]), null);
});

test('chybějící výklad paragrafu nespadne', () => {
  const p = najdiParagraf(zakon, '244');
  assert.equal(vykladOdstavce(vyklad, p, p.odstavce[0]), null);
  assert.equal(vylozenoVParagrafu(vyklad, p), 0);
});

test('pokrytí počítá odstavce, ne paragrafy', () => {
  assert.deepEqual(pokrytiVykladu(zakon, vyklad), { hotovo: 2, celkem: 5 });
});

console.log(`\n${passed} testů prošlo`);
