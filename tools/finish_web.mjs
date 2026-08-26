/**
 * Doladí sestavený web po `expo export`.
 *
 * Dvě věci, které Expo samo neudělá:
 *  - hlavičkové tagy pro přidání na plochu telefonu (Expo <head> generuje samo
 *    a žádný hook na doplnění nenabízí),
 *  - soubor .nojekyll, bez kterého GitHub Pages spustí Jekyll a ten složku
 *    _expo s bundlem přeskočí — web se pak načte prázdný.
 */
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';

const dir = process.argv[2] || 'docs';
const file = join(dir, 'index.html');

if (!existsSync(file)) {
  console.error(`  ${file} nenalezen — spusť nejdřív export`);
  process.exit(1);
}

const tags = [
  `<meta name="apple-mobile-web-app-capable" content="yes" />`,
  `<meta name="apple-mobile-web-app-title" content="Zkouška IS" />`,
  `<meta name="apple-mobile-web-app-status-bar-style" content="default" />`,
  `<meta name="theme-color" content="#FBF9F6" />`,
  `<meta name="robots" content="noindex" />`,
];

let html = readFileSync(file, 'utf8');
const chybejici = tags.filter((t) => !html.includes(t.match(/name="([^"]+)"/)[1]));

if (chybejici.length) {
  html = html.replace('</head>', `  ${chybejici.join('\n  ')}\n</head>`);
  writeFileSync(file, html);
}

writeFileSync(join(dir, '.nojekyll'), '');

console.log(`  doplněno ${chybejici.length} tagů, zapsán .nojekyll`);
