/**
 * Co si app pamatuje mezi spuštěními.
 *
 * Drží se jen seznam otázek, které jsi zodpověděl špatně — z něj se skládá
 * trénink chyb. Správně zodpovězená otázka ze seznamu vypadne, takže se sám
 * vyprazdňuje a nepotřebuje žádnou další správu.
 *
 * Selhání úložiště se schválně polyká: bez uložených chyb se dá zkoušet dál,
 * kdežto pád celé obrazovky kvůli nedostupnému AsyncStorage by byl horší než
 * ztráta historie.
 */
import AsyncStorage from '@react-native-async-storage/async-storage';

const KLIC = 'zkouska:chyby';

export async function nactiChyby() {
  try {
    const ulozene = await AsyncStorage.getItem(KLIC);
    const pole = ulozene ? JSON.parse(ulozene) : [];
    return Array.isArray(pole) ? pole : [];
  } catch {
    return [];
  }
}

export async function ulozChyby(idcka) {
  try {
    await AsyncStorage.setItem(KLIC, JSON.stringify([...new Set(idcka)]));
  } catch {
    // Historie chyb není to, kvůli čemu by měla app spadnout.
  }
}

/** Přidá nové chyby a odebere otázky, které už umíš. */
export function aktualizujChyby(puvodni, { pridat = [], odebrat = [] }) {
  const dalsi = new Set(puvodni);
  for (const id of pridat) dalsi.add(id);
  for (const id of odebrat) dalsi.delete(id);
  return [...dalsi];
}
