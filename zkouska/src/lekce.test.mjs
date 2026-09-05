/**
 * Kontroluje, co ranní lekce slibují: dnešek je poslední odemčený, do budoucna
 * se nekouká, prvního se to vrátí na začátek a lekce přežije chybějící otázku.
 *
 * Spuštění:  node zkouska/src/lekce.test.mjs
 */
import assert from 'node:assert/strict';
import { lekceProDen, odemceneLekce, otazkyLekce, zbyvaLekci } from './lekce.js';

const lekce = Array.from({ length: 31 }, (_, i) => ({
  den: i + 1,
  nazev: `lekce ${i + 1}`,
  otazky: [`q-${i + 1}-a`, `q-${i + 1}-b`],
}));

const otazky = lekce.flatMap((l) => l.otazky.map((id) => ({ id, otazka: id })));

let passed = 0;

function test(name, fn) {
  fn();
  passed += 1;
  console.log('  ok  ' + name);
}

test('lekce dne je ta se shodným dnem v měsíci', () => {
  assert.equal(lekceProDen(lekce, new Date(2026, 8, 1)).den, 1);
  assert.equal(lekceProDen(lekce, new Date(2026, 8, 17)).den, 17);
});

test('krátký měsíc na poslední lekce nedosáhne', () => {
  // Únor 2026 má 28 dnů, takže lekce 29 až 31 v něm nepřijdou na řadu.
  const unor = new Date(2026, 1, 28);
  assert.equal(lekceProDen(lekce, unor).den, 28);
  assert.equal(odemceneLekce(lekce, unor).length, 28);
});

test('odemčené jsou dnešek a dny před ním, nejnovější první', () => {
  const dostupne = odemceneLekce(lekce, new Date(2026, 8, 5));
  assert.deepEqual(dostupne.map((l) => l.den), [5, 4, 3, 2, 1]);
});

test('do budoucích lekcí se nedá dostat', () => {
  const dostupne = odemceneLekce(lekce, new Date(2026, 8, 5));
  assert.equal(dostupne.some((l) => l.den > 5), false);
});

test('prvního se to vrátí na začátek', () => {
  const prvniho = odemceneLekce(lekce, new Date(2026, 9, 1));
  assert.deepEqual(prvniho.map((l) => l.den), [1]);
  assert.equal(zbyvaLekci(lekce, new Date(2026, 9, 1)), 30);
});

test('otázky lekce se dohledají podle id a drží pořadí', () => {
  const dnesni = lekceProDen(lekce, new Date(2026, 8, 3));
  const nalezene = otazkyLekce(dnesni, otazky);
  assert.deepEqual(nalezene.map((o) => o.id), ['q-3-a', 'q-3-b']);
});

test('chybějící otázka lekci nerozbije, jen ji zkrátí', () => {
  const dnesni = lekceProDen(lekce, new Date(2026, 8, 3));
  const bezJedne = otazky.filter((o) => o.id !== 'q-3-a');
  assert.deepEqual(otazkyLekce(dnesni, bezJedne).map((o) => o.id), ['q-3-b']);
  assert.deepEqual(otazkyLekce(null, otazky), []);
});

console.log(`\n${passed} testů prošlo`);
