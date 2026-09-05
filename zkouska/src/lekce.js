/**
 * Ranní desetiminutovky.
 *
 * Jedna lekce na každý den v měsíci: krátký výklad tématu a pak otázky z banky,
 * které se ho týkají. Číslo lekce je prostě den v měsíci, takže se nikde nemusí
 * ukládat, kde jsi skončil, nedá se to rozjet a prvního nového měsíce se to samo
 * vrátí na začátek. Za cenu toho, že v únoru se na poslední dvě až tři lekce
 * nedostane — proto do nich patří to nejmíň důležité.
 *
 * Dnešní lekce je poslední odemčená; předchozí dny zůstávají otevřené, aby šlo
 * dohnat, co jsi zameškal. Do budoucna se nedá koukat.
 */

export const LEKCI_V_MESICI = 31;

/** Lekce pro daný den, nebo null (krátký měsíc na poslední lekce nedosáhne). */
export function lekceProDen(lekce, datum = new Date()) {
  return lekce.find((l) => l.den === datum.getDate()) ?? null;
}

/** Lekce od prvního dne měsíce po dnešek, nejnovější první. */
export function odemceneLekce(lekce, datum = new Date()) {
  const dnes = datum.getDate();
  return lekce.filter((l) => l.den <= dnes).sort((a, b) => b.den - a.den);
}

/**
 * Otázky lekce v pořadí, v jakém jsou v ní uvedené.
 *
 * Lekce odkazuje na otázky jen jejich id, aby se nemusely držet dvakrát.
 * Chybějící id se přeskočí — lekce tak přežije i to, že se otázka z banky
 * ztratí, jen bude o kus kratší.
 */
export function otazkyLekce(lekce, otazky) {
  if (!lekce) return [];
  const podleId = new Map(otazky.map((o) => [o.id, o]));
  return lekce.otazky.map((id) => podleId.get(id)).filter(Boolean);
}

/** Kolik lekcí v měsíci ještě zbývá, dnešní nepočítaje. */
export function zbyvaLekci(lekce, datum = new Date()) {
  return lekce.filter((l) => l.den > datum.getDate()).length;
}
