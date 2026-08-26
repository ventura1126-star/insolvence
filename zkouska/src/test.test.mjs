/**
 * Kontroluje, co test slibuje: ostrý test má plný počet otázek, drží poměr
 * okruhů, nepouští dovnitř otázky bez odpovědi ani zastaralé, a vyhodnocení
 * počítá hranici 80 % stejně jako zkušební komise.
 *
 * Spuštění:  node zkouska/src/test.test.mjs
 */
import assert from 'node:assert/strict';
import {
  hraniceUspechu,
  jeSpravne,
  pokrytiOkruhu,
  sestavTest,
  vyhodnot,
  zodpovezene,
} from './test.js';

const OBLASTI = ['Insolvence', 'Obecné právo a exekuce', 'Daně', 'Audit'];
// Poměr zhruba jako ve skutečné bance: 73 / 15 / 8 / 4 %.
const POCTY = [730, 150, 80, 40];

const otazky = OBLASTI.flatMap((oblast, i) =>
  Array.from({ length: POCTY[i] }, (_, n) => ({
    id: `${oblast}-${n}`,
    oblast,
    otazka: `otázka ${n}`,
    varianty: ['a', 'b', 'c', 'd', 'žádná odpověď není správná'],
  }))
);

const odpovedi = Object.fromEntries(
  // Každá pátá otázka má schválně dvě správné varianty.
  otazky.map((o, i) => [
    o.id,
    { spravne: i % 5 === 0 ? [0, 2] : [i % 5], pramen: '§ 1', stav: 'platna' },
  ])
);

let passed = 0;

function test(name, fn) {
  fn();
  passed += 1;
  console.log('  ok  ' + name);
}

test('hranice úspěchu je 56 ze 70', () => {
  assert.equal(hraniceUspechu(70), 56);
  assert.equal(hraniceUspechu(10), 8);
});

test('bez dohledaných odpovědí nevznikne žádný test', () => {
  assert.deepEqual(sestavTest(otazky, {}), []);
});

test('ostrý test má 70 otázek a žádnou dvakrát', () => {
  const t = sestavTest(otazky, odpovedi, 1);
  assert.equal(t.length, 70);
  assert.equal(new Set(t.map((o) => o.id)).size, 70);
});

test('okruhy jsou zastoupené zhruba podle podílu v bance', () => {
  const t = sestavTest(otazky, odpovedi, 42);
  const kolik = (oblast) => t.filter((o) => o.oblast === oblast).length;
  // 73 % ze 70 je ~51; tolerance na zaokrouhlení kvót.
  assert.ok(Math.abs(kolik('Insolvence') - 51) <= 2, `insolvence: ${kolik('Insolvence')}`);
  assert.ok(kolik('Audit') >= 1, 'i nejmenší okruh se musí objevit');
  assert.equal(OBLASTI.every((o) => kolik(o) > 0), true);
});

test('stejný seed dá stejný test, jiný seed jiný', () => {
  const ids = (seed) => sestavTest(otazky, odpovedi, seed).map((o) => o.id);
  assert.deepEqual(ids(7), ids(7));
  assert.notDeepEqual(ids(7), ids(8));
});

test('zastaralé otázky se do ostrého testu nedostanou', () => {
  const sZastaralymi = { ...odpovedi };
  for (const o of otazky.slice(0, 700)) {
    sZastaralymi[o.id] = { ...sZastaralymi[o.id], stav: 'zastarala' };
  }
  const t = sestavTest(otazky, sZastaralymi, 3);
  assert.equal(t.some((o) => sZastaralymi[o.id].stav === 'zastarala'), false);
  // Zbylých otázek je pořád dost na plný test.
  assert.equal(t.length, 70);
});

test('trénink si zastaralé otázky vyžádat může, ostrý test ne', () => {
  const sZastaralymi = { ...odpovedi };
  for (const o of otazky.slice(0, 700)) {
    sZastaralymi[o.id] = { ...sZastaralymi[o.id], stav: 'zastarala' };
  }
  const jeZastarala = (o) => sZastaralymi[o.id].stav === 'zastarala';

  const ostry = sestavTest(otazky, sZastaralymi, 3);
  assert.equal(ostry.some(jeZastarala), false, 'ostrý test je nesmí obsahovat');

  const trenink = sestavTest(otazky, sZastaralymi, 3, 70, { vcetneZastaralych: true });
  assert.equal(trenink.some(jeZastarala), true, 'trénink je ukázat musí');
});

test('když je zodpovězeno málo otázek, test je kratší, ne vymyšlený', () => {
  const par = Object.fromEntries(
    otazky.slice(0, 12).map((o) => [o.id, { spravne: [0], stav: 'platna' }])
  );
  const t = sestavTest(otazky, par, 5);
  assert.equal(t.length, 12);
});

test('zodpovezene filtruje chybějící i zastaralé', () => {
  const smes = {
    [otazky[0].id]: { spravne: [0], stav: 'platna' },
    [otazky[1].id]: { spravne: [0], stav: 'zastarala' },
  };
  assert.equal(zodpovezene(otazky, smes).length, 1);
  assert.equal(zodpovezene(otazky, smes, { vcetneZastaralych: true }).length, 2);
});

test('u víc správných variant se musí trefit celá sada', () => {
  assert.equal(jeSpravne([0, 2], [0, 2]), true);
  assert.equal(jeSpravne([2, 0], [0, 2]), true, 'na pořadí nezáleží');
  assert.equal(jeSpravne([0], [0, 2]), false, 'částečná odpověď je chyba');
  assert.equal(jeSpravne([0, 2, 3], [0, 2]), false, 'nic navíc');
  assert.equal(jeSpravne([], [0]), false);
  assert.equal(jeSpravne(undefined, [0]), false, 'nezodpovězeno');
  assert.equal(jeSpravne([0], undefined), false, 'otázka bez dohledané odpovědi');
});

test('vyhodnocení: nezodpovězená otázka je chyba', () => {
  const t = sestavTest(otazky, odpovedi, 11);
  const vsechnySpravne = Object.fromEntries(t.map((o) => [o.id, odpovedi[o.id].spravne]));

  const plny = vyhodnot(t, vsechnySpravne, odpovedi);
  assert.equal(plny.spravne, 70);
  assert.equal(plny.procenta, 100);
  assert.equal(plny.prosel, true);
  assert.deepEqual(plny.chyby, []);

  const prazdny = vyhodnot(t, {}, odpovedi);
  assert.equal(prazdny.spravne, 0);
  assert.equal(prazdny.prosel, false);
  assert.equal(prazdny.chyby.length, 70);
});

test('vyhodnocení: 56 správně projde, 55 ne', () => {
  const t = sestavTest(otazky, odpovedi, 13);
  const volby = (kolik) =>
    Object.fromEntries(
      t.map((o, i) => [o.id, i < kolik ? odpovedi[o.id].spravne : [(odpovedi[o.id].spravne[0] + 1) % 5]])
    );
  assert.equal(vyhodnot(t, volby(56), odpovedi).prosel, true);
  assert.equal(vyhodnot(t, volby(55), odpovedi).prosel, false);
});

test('vyhodnocení rozepíše výsledek po okruzích', () => {
  const t = sestavTest(otazky, odpovedi, 17);
  const v = vyhodnot(t, {}, odpovedi);
  assert.equal(
    v.podleOblasti.reduce((s, o) => s + o.celkem, 0),
    70
  );
  assert.equal(v.podleOblasti.every((o) => OBLASTI.includes(o.oblast)), true);
});

test('pokrytí okruhů hlásí hotovo proti celku, zastaralé počítá taky', () => {
  const auditOtazky = otazky.filter((o) => o.oblast === 'Audit');
  const par = Object.fromEntries(
    auditOtazky.map((o, i) => [
      o.id,
      { spravne: [0], stav: i < 5 ? 'zastarala' : 'platna' },
    ])
  );
  const audit = pokrytiOkruhu(otazky, par).find((o) => o.oblast === 'Audit');
  // Trénink okruhu zastaralé otázky ukazuje, takže patří i do počtu.
  assert.deepEqual(audit, { oblast: 'Audit', celkem: 40, hotovo: 40 });
  const dane = pokrytiOkruhu(otazky, par).find((o) => o.oblast === 'Daně');
  assert.equal(dane.hotovo, 0);
});

console.log(`\n${passed} testů prošlo`);
