import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
// Vlastní SafeAreaView z react-native je zastaralý, SDK 54 odkazuje sem.
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';

import otazky from './assets/otazky.json';
import odpovedi from './assets/odpovedi.json';
import zakon from './assets/zakon.json';
import vyklad from './assets/vyklad.json';
import {
  OTAZEK_V_TESTU,
  hraniceUspechu,
  jeSpravne,
  pokrytiOkruhu,
  sestavTest,
  vyhodnot,
  zodpovezene,
} from './src/test';
import {
  hledej,
  najdiParagraf,
  obsah,
  pokrytiVykladu,
  sousedi,
  vykladOdstavce,
  vylozenoVParagrafu,
} from './src/zakon';
import { aktualizujChyby, nactiChyby, ulozChyby } from './src/ulozeni';

const theme = {
  paper: '#FBF9F6',
  ink: '#1A1714',
  muted: '#8A8078',
  rule: '#E6E0D8',
  accent: '#B4603A',
  spravne: '#2E7D52',
  spatne: '#B4453A',
};

export default function App() {
  // 'domu' | 'zakon' | { rezim: 'ostry' | 'chyby' }
  // | { rezim: 'trenink', oblast } | { paragraf: '38' }
  const [kam, setKam] = useState('domu');
  const [chyby, setChyby] = useState([]);

  useEffect(() => {
    nactiChyby().then(setChyby);
  }, []);

  const zapisChyby = useCallback((zmena) => {
    setChyby((puvodni) => {
      const dalsi = aktualizujChyby(puvodni, zmena);
      ulozChyby(dalsi);
      return dalsi;
    });
  }, []);

  return (
    <SafeAreaProvider>
      <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
        <StatusBar barStyle="dark-content" backgroundColor={theme.paper} />
        {kam === 'domu' ? (
          <Domu chyby={chyby} onOtevri={setKam} />
        ) : kam === 'zakon' ? (
          <Zakon onOtevri={setKam} onZpet={() => setKam('domu')} />
        ) : kam.paragraf ? (
          <Paragraf
            cislo={kam.paragraf}
            onOtevri={setKam}
            onZpet={() => setKam('zakon')}
          />
        ) : (
          <Beh
            zadani={kam}
            chyby={chyby}
            onZapisChyby={zapisChyby}
            onZpet={() => setKam('domu')}
          />
        )}
      </SafeAreaView>
    </SafeAreaProvider>
  );
}

function Domu({ chyby, onOtevri }) {
  const pokryti = useMemo(() => pokrytiOkruhu(otazky, odpovedi), []);
  const pripraveno = useMemo(() => zodpovezene(otazky, odpovedi).length, []);

  return (
    <ScrollView contentContainerStyle={styles.domu} showsVerticalScrollIndicator={false}>
      <View style={styles.hlavicka}>
        <Text style={styles.nazev}>Zkouška IS</Text>
        <Text style={styles.podnadpis}>
          Obecná zkouška insolvenčního správce. Test má 70 otázek, projít znamená
          {' '}
          {hraniceUspechu(OTAZEK_V_TESTU)} správně.
        </Text>
      </View>

      <KartaZakona onOtevri={onOtevri} />

      <Volba
        popisek="Ostrý test"
        napoveda={`${OTAZEK_V_TESTU} otázek jako u zkoušky, vyhodnocení až na konci`}
        onPress={() => onOtevri({ rezim: 'ostry' })}
        neaktivni={pripraveno === 0}
      />
      <Volba
        popisek="Moje chyby"
        napoveda={
          chyby.length ? `${chyby.length} otázek k dotažení` : 'Zatím nemáš co opakovat'
        }
        onPress={() => onOtevri({ rezim: 'chyby' })}
        neaktivni={chyby.length === 0}
      />

      <Text style={styles.sekce}>Trénink po okruzích</Text>
      {pokryti.map((o) => (
        <Volba
          key={o.oblast}
          popisek={o.oblast}
          napoveda={`${o.hotovo} z ${o.celkem} otázek připraveno`}
          onPress={() => onOtevri({ rezim: 'trenink', oblast: o.oblast })}
          neaktivni={o.hotovo === 0}
        />
      ))}

      <Text style={styles.patka}>
        Otázky vydalo Ministerstvo spravedlnosti v roce 2014 a od té doby je
        nahradila novější, neveřejná sada. Odpovědi jsou dohledané podle dnešního
        znění předpisů — kde novela nabízené varianty přežila jen zčásti, je otázka
        označená jako zastaralá a do ostrého testu nejde.
      </Text>
    </ScrollView>
  );
}

/**
 * Výkladový text.
 *
 * Píše se s hvězdičkami kolem zdůrazněných míst, protože v JSON se důraz jinak
 * zapsat nedá; tady se rozpadne na běžné a tučné úseky. React Native markdown
 * sám nerenderuje, takže bez tohohle by se hvězdičky vypsaly doslova.
 */
function Vyklad({ text }) {
  return (
    <View style={styles.vyklad}>
      {text.split('\n\n').map((odstavec, i) => (
        <Text key={i} style={styles.vykladText}>
          {odstavec.split('**').map((usek, j) =>
            j % 2 ? (
              <Text key={j} style={styles.vykladDuraz}>
                {usek}
              </Text>
            ) : (
              usek
            )
          )}
        </Text>
      ))}
    </View>
  );
}

/**
 * Karta zákona na úvodní obrazovce.
 *
 * Místo denní dávky se nabízí celý zákon k procházení — výklad u odstavce
 * dává smysl číst tehdy, když na ten odstavec člověk narazí, ne podle data.
 */
function KartaZakona({ onOtevri }) {
  const { hotovo, celkem } = useMemo(() => pokrytiVykladu(zakon, vyklad), []);

  return (
    <View>
      <Text style={styles.sekce}>Zákon s výkladem</Text>
      <Pressable
        onPress={() => onOtevri('zakon')}
        accessibilityRole="button"
        accessibilityLabel="Insolvenční zákon s výkladem"
        style={({ pressed }) => [styles.karta, pressed && styles.volbaStisk]}
      >
        <Text style={styles.kartaNadnadpis}>Zákon č. 182/2006 Sb.</Text>
        <Text style={styles.kartaNazev}>Insolvenční zákon</Text>
        <Text style={styles.volbaNapoveda}>
          {zakon.length} paragrafů · výklad k {hotovo} z {celkem} odstavců
        </Text>
      </Pressable>
    </View>
  );
}

/** Obsah zákona: hledání, a pod ním části a hlavy s paragrafy. */
function Zakon({ onOtevri, onZpet }) {
  const [dotaz, setDotaz] = useState('');
  const casti = useMemo(() => obsah(zakon), []);
  const nalezene = useMemo(() => hledej(zakon, dotaz), [dotaz]);
  const hleda = dotaz.trim().length > 0;

  return (
    <ScrollView
      contentContainerStyle={styles.domu}
      showsVerticalScrollIndicator={false}
      keyboardShouldPersistTaps="handled"
    >
      <Zpet onPress={onZpet} popisek="← Domů" />
      <Text style={styles.nazev}>Insolvenční zákon</Text>
      <Text style={styles.podnadpis}>
        Znění podle Sbírky, pod každým odstavcem výklad, co znamená v praxi
        správce. Kde výklad ještě není, stojí aspoň zákon.
      </Text>

      <TextInput
        value={dotaz}
        onChangeText={setDotaz}
        placeholder="Číslo paragrafu nebo slovo"
        placeholderTextColor={theme.muted}
        autoCorrect={false}
        autoCapitalize="none"
        accessibilityLabel="Hledat v zákoně"
        style={styles.hledani}
      />

      {hleda ? (
        nalezene.length ? (
          nalezene.map((p) => (
            <RadekParagrafu key={p.paragraf} paragraf={p} onOtevri={onOtevri} />
          ))
        ) : (
          <Text style={styles.patka}>Nic takového v zákoně není.</Text>
        )
      ) : (
        casti.map((cast) => (
          <View key={cast.nazev}>
            <Text style={styles.sekce}>{cast.nazev}</Text>
            {cast.hlavy.map((hlava) => (
              <View key={`${cast.nazev}/${hlava.nazev}`}>
                {hlava.nazev && <Text style={styles.podsekce}>{hlava.nazev}</Text>}
                {hlava.paragrafy.map((p) => (
                  <RadekParagrafu key={p.paragraf} paragraf={p} onOtevri={onOtevri} />
                ))}
              </View>
            ))}
          </View>
        ))
      )}
    </ScrollView>
  );
}

function RadekParagrafu({ paragraf, onOtevri }) {
  const hotovo = vylozenoVParagrafu(vyklad, paragraf);
  const vse = hotovo === paragraf.odstavce.length;

  return (
    <Pressable
      onPress={() => onOtevri({ paragraf: paragraf.paragraf })}
      accessibilityRole="button"
      accessibilityLabel={`§ ${paragraf.paragraf}${paragraf.nazev ? `, ${paragraf.nazev}` : ''}`}
      style={({ pressed }) => [styles.radekParagrafu, pressed && styles.volbaStisk]}
    >
      <Text style={styles.cisloParagrafu}>§ {paragraf.paragraf}</Text>
      <Text style={styles.nazevParagrafu} numberOfLines={2}>
        {paragraf.nazev ?? prvniSlova(paragraf.odstavce[0].text)}
      </Text>
      {/* Tečka u paragrafu, kde výklad chybí nebo je jen část — ať je vidět,
          kde se dá číst dál a kde zatím stojí holý zákon. */}
      <Text style={[styles.znacka, vse && styles.znackaHotovo]}>
        {vse ? '●' : hotovo ? '◐' : '○'}
      </Text>
    </Pressable>
  );
}

/** Paragraf bez názvu se v seznamu představí začátkem svého znění. */
function prvniSlova(text, limit = 60) {
  const jeden = text.replace(/\s+/g, ' ').trim();
  return jeden.length > limit ? `${jeden.slice(0, limit)}…` : jeden;
}

/** Jeden paragraf: znění po odstavcích a pod každým odstavcem jeho výklad. */
function Paragraf({ cislo, onOtevri, onZpet }) {
  const paragraf = useMemo(() => najdiParagraf(zakon, cislo), [cislo]);
  const { predchozi, dalsi } = useMemo(() => sousedi(zakon, cislo), [cislo]);

  if (!paragraf) {
    return (
      <View style={styles.stred}>
        <Text style={styles.nadpisVysledku}>Paragraf není</Text>
        <Zpet onPress={onZpet} popisek="← Zpátky" />
      </View>
    );
  }

  const kdeJsem = [paragraf.cast, paragraf.hlava, paragraf.dil, paragraf.oddil]
    .filter(Boolean)
    .join(' · ');

  return (
    <ScrollView contentContainerStyle={styles.beh} showsVerticalScrollIndicator={false}>
      <Zpet onPress={onZpet} popisek="← Obsah" />

      {/* Většina paragrafů nadpis nemá — pak je nadpisem samo číslo, ať se
          nahoře nevypisuje prázdná fráze. */}
      {paragraf.nazev ? (
        <>
          <Text style={styles.postup}>§ {paragraf.paragraf}</Text>
          <Text style={styles.zneni}>{paragraf.nazev}</Text>
        </>
      ) : (
        <Text style={styles.zneni}>§ {paragraf.paragraf}</Text>
      )}
      <Text style={styles.drobecky}>{kdeJsem}</Text>

      {paragraf.odstavce.map((odstavec, i) => (
        <Odstavec
          key={odstavec.cislo ?? i}
          odstavec={odstavec}
          vyklad={vykladOdstavce(vyklad, paragraf, odstavec)}
        />
      ))}

      <View style={styles.prechod}>
        {predchozi ? (
          <Pressable
            onPress={() => onOtevri({ paragraf: predchozi.paragraf })}
            accessibilityRole="button"
            hitSlop={8}
            style={styles.odkaz}
          >
            <Text style={styles.odkazText}>← § {predchozi.paragraf}</Text>
          </Pressable>
        ) : (
          <View />
        )}
        {dalsi && (
          <Pressable
            onPress={() => onOtevri({ paragraf: dalsi.paragraf })}
            accessibilityRole="button"
            hitSlop={8}
            style={styles.odkaz}
          >
            <Text style={styles.odkazText}>§ {dalsi.paragraf} →</Text>
          </Pressable>
        )}
      </View>
    </ScrollView>
  );
}

function Odstavec({ odstavec, vyklad: text }) {
  return (
    <View style={styles.odstavec}>
      <Text style={styles.textZakona}>
        {odstavec.cislo && <Text style={styles.cisloOdstavce}>({odstavec.cislo}) </Text>}
        {odstavec.text}
      </Text>
      {text ? (
        <View style={styles.rozbor}>
          <Text style={styles.verdikt}>V praxi</Text>
          <Vyklad text={text} />
        </View>
      ) : (
        <Text style={styles.poznamka}>Výklad k tomuhle odstavci ještě nemám.</Text>
      )}
    </View>
  );
}

function Volba({ popisek, napoveda, onPress, neaktivni }) {
  return (
    <Pressable
      onPress={neaktivni ? undefined : onPress}
      disabled={neaktivni}
      accessibilityRole="button"
      accessibilityLabel={popisek}
      accessibilityState={{ disabled: !!neaktivni }}
      style={({ pressed }) => [
        styles.volba,
        pressed && styles.volbaStisk,
        neaktivni && styles.volbaNeaktivni,
      ]}
    >
      <Text style={[styles.volbaPopisek, neaktivni && styles.textNeaktivni]}>{popisek}</Text>
      <Text style={styles.volbaNapoveda}>{napoveda}</Text>
    </Pressable>
  );
}

/** Připraví sadu otázek pro zvolený režim. */
function sadaProRezim(zadani, chyby) {
  if (zadani.rezim === 'ostry') return sestavTest(otazky, odpovedi);
  if (zadani.rezim === 'chyby') {
    const hledane = new Set(chyby);
    return otazky.filter((o) => hledane.has(o.id));
  }
  const vOkruhu = otazky.filter((o) => o.oblast === zadani.oblast);
  // V tréninku se ukazují i zastaralé otázky — právě u nich je vidět, co novela
  // změnila, což je samo o sobě k učení.
  return sestavTest(vOkruhu, odpovedi, Date.now(), Math.min(20, vOkruhu.length), {
    vcetneZastaralych: true,
  });
}

function Beh({ zadani, chyby, onZapisChyby, onZpet }) {
  const [sada] = useState(() => sadaProRezim(zadani, chyby));
  const [poradi, setPoradi] = useState(0);
  const [volby, setVolby] = useState({});
  const [odhaleno, setOdhaleno] = useState(false);
  const [hotovo, setHotovo] = useState(false);

  const ostry = zadani.rezim === 'ostry';
  const otazka = sada[poradi];

  const prepni = (index) => {
    if (odhaleno) return;
    setVolby((p) => {
      const soucasne = p[otazka.id] ?? [];
      const dalsi = soucasne.includes(index)
        ? soucasne.filter((i) => i !== index)
        : [...soucasne, index];
      return { ...p, [otazka.id]: dalsi };
    });
  };

  const dal = () => {
    // V tréninku se odpověď ukáže hned, v ostrém testu až na konci — proto se
    // tlačítko chová jinak podle režimu.
    if (!ostry && !odhaleno) {
      setOdhaleno(true);
      return;
    }
    setOdhaleno(false);
    if (poradi + 1 < sada.length) setPoradi(poradi + 1);
    else setHotovo(true);
  };

  const vysledek = useMemo(
    () => (hotovo ? vyhodnot(sada, volby, odpovedi) : null),
    [hotovo, sada, volby]
  );

  useEffect(() => {
    if (!vysledek) return;
    onZapisChyby({
      pridat: vysledek.chyby,
      odebrat: sada.map((o) => o.id).filter((id) => !vysledek.chyby.includes(id)),
    });
  }, [vysledek]);

  if (sada.length === 0) {
    return (
      <View style={styles.stred}>
        <Text style={styles.nadpisVysledku}>Není co zkoušet</Text>
        <Text style={styles.patka}>K tomuhle okruhu zatím nejsou dohledané odpovědi.</Text>
        <Zpet onPress={onZpet} popisek="← Zpátky" />
      </View>
    );
  }

  if (vysledek) return <Vysledek vysledek={vysledek} ostry={ostry} onZpet={onZpet} />;

  const odp = odpovedi[otazka.id];
  const oznacene = volby[otazka.id] ?? [];

  return (
    <ScrollView contentContainerStyle={styles.beh} showsVerticalScrollIndicator={false}>
      <Zpet onPress={onZpet} popisek="← Konec" />

      <Text style={styles.postup}>
        {poradi + 1} / {sada.length}
        {'   ·   '}
        {otazka.oblast}
      </Text>
      <Text style={styles.zneni}>{otazka.otazka}</Text>

      {otazka.varianty.map((v, i) => (
        <Varianta
          key={i}
          text={v}
          oznacena={oznacene.includes(i)}
          odhaleno={odhaleno}
          jeSpravna={!!odp && odp.spravne.includes(i)}
          onPress={() => prepni(i)}
        />
      ))}

      {odhaleno && odp && <Rozbor odpoved={odp} trefa={jeSpravne(oznacene, odp.spravne)} />}

      <Pressable
        onPress={dal}
        accessibilityRole="button"
        style={({ pressed }) => [styles.tlacitko, pressed && styles.tlacitkoStisk]}
      >
        <Text style={styles.tlacitkoText}>
          {!ostry && !odhaleno
            ? 'Zkontrolovat'
            : poradi + 1 < sada.length
              ? 'Další otázka'
              : 'Vyhodnotit'}
        </Text>
      </Pressable>
    </ScrollView>
  );
}

function Varianta({ text, oznacena, odhaleno, jeSpravna, onPress }) {
  // Po odhalení nese barvu správnost, ne to, co jsi zaškrtl — jinak by nebylo
  // poznat, kterou variantu jsi minul.
  const stav = odhaleno ? (jeSpravna ? 'spravne' : oznacena ? 'spatne' : null) : null;

  return (
    <Pressable
      onPress={onPress}
      disabled={odhaleno}
      accessibilityRole="checkbox"
      accessibilityState={{ checked: oznacena }}
      style={({ pressed }) => [
        styles.varianta,
        oznacena && styles.variantaOznacena,
        stav === 'spravne' && styles.variantaSpravne,
        stav === 'spatne' && styles.variantaSpatne,
        pressed && !odhaleno && styles.volbaStisk,
      ]}
    >
      <View style={[styles.zaskrt, oznacena && styles.zaskrtOznaceny]}>
        {oznacena && <Text style={styles.zaskrtZnak}>✓</Text>}
      </View>
      <Text style={styles.variantaText}>{text}</Text>
    </Pressable>
  );
}

function Rozbor({ odpoved, trefa }) {
  return (
    <View style={styles.rozbor}>
      <Text style={[styles.verdikt, { color: trefa ? theme.spravne : theme.spatne }]}>
        {trefa ? 'Správně' : 'Špatně'}
      </Text>
      <Text style={styles.pramen}>{odpoved.pramen}</Text>
      <Text style={styles.vysvetleni}>{odpoved.vysvetleni}</Text>
      {odpoved.stav === 'zastarala' && (
        <Text style={styles.varovani}>Pozor, zastaralá otázka. {odpoved.poznamka}</Text>
      )}
      {odpoved.stav !== 'zastarala' && odpoved.poznamka ? (
        <Text style={styles.poznamka}>{odpoved.poznamka}</Text>
      ) : null}
    </View>
  );
}

function Vysledek({ vysledek, ostry, onZpet }) {
  return (
    <ScrollView contentContainerStyle={styles.beh} showsVerticalScrollIndicator={false}>
      <Zpet onPress={onZpet} popisek="← Domů" />

      <Text style={styles.nadpisVysledku}>
        {vysledek.spravne} / {vysledek.celkem}
      </Text>
      <Text
        style={[
          styles.verdiktVelky,
          { color: vysledek.prosel ? theme.spravne : theme.spatne },
        ]}
      >
        {vysledek.procenta} %{ostry ? (vysledek.prosel ? ' — prošel bys' : ' — neprošel bys') : ''}
      </Text>
      {ostry && (
        <Text style={styles.patka}>
          U zkoušky je potřeba {vysledek.potreba} správně z {vysledek.celkem}.
        </Text>
      )}

      <View style={styles.cara} />

      {vysledek.podleOblasti.map((o) => (
        <View key={o.oblast} style={styles.radekOblasti}>
          <Text style={styles.oblastNazev}>{o.oblast}</Text>
          <Text style={styles.oblastSkore}>
            {o.spravne} / {o.celkem}
          </Text>
        </View>
      ))}

      {vysledek.chyby.length > 0 && (
        <Text style={styles.patka}>
          {vysledek.chyby.length} otázek přibylo do „Moje chyby“ k dotažení.
        </Text>
      )}
    </ScrollView>
  );
}

function Zpet({ onPress, popisek }) {
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={popisek.replace('← ', '')}
      hitSlop={16}
      style={styles.zpet}
    >
      <Text style={styles.zpetText}>{popisek}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: theme.paper },

  domu: { paddingHorizontal: 24, paddingBottom: 40, gap: 12 },
  hlavicka: { marginTop: 24, marginBottom: 24 },
  nazev: { fontSize: 38, fontWeight: '600', letterSpacing: -1, color: theme.ink },
  podnadpis: { marginTop: 10, fontSize: 15, lineHeight: 22, color: theme.muted },
  sekce: {
    marginTop: 26,
    marginBottom: 2,
    fontSize: 12,
    letterSpacing: 1.4,
    textTransform: 'uppercase',
    color: theme.accent,
  },

  volba: {
    borderWidth: 1,
    borderColor: theme.rule,
    borderRadius: 16,
    paddingVertical: 20,
    paddingHorizontal: 20,
    backgroundColor: '#FFFFFF',
  },
  volbaStisk: { backgroundColor: '#F3EEE7' },

  karta: {
    borderRadius: 16,
    paddingVertical: 22,
    paddingHorizontal: 20,
    backgroundColor: theme.ink,
  },
  kartaNadnadpis: {
    fontSize: 12,
    letterSpacing: 1.2,
    textTransform: 'uppercase',
    color: theme.accent,
  },
  kartaNazev: {
    marginTop: 8,
    marginBottom: 6,
    fontSize: 22,
    fontWeight: '600',
    letterSpacing: -0.4,
    color: theme.paper,
  },
  odkaz: { paddingVertical: 12, alignSelf: 'flex-start' },
  prechod: {
    marginTop: 28,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },

  podsekce: {
    marginTop: 18,
    marginBottom: 6,
    fontSize: 13,
    lineHeight: 19,
    color: theme.muted,
  },
  hledani: {
    marginTop: 8,
    marginBottom: 4,
    borderWidth: 1,
    borderColor: theme.rule,
    borderRadius: 12,
    paddingVertical: 13,
    paddingHorizontal: 16,
    fontSize: 16,
    color: theme.ink,
    backgroundColor: '#FFFFFF',
  },
  radekParagrafu: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 13,
    borderBottomWidth: 1,
    borderBottomColor: theme.rule,
  },
  cisloParagrafu: {
    width: 58,
    fontSize: 15,
    fontWeight: '600',
    color: theme.accent,
  },
  nazevParagrafu: { flex: 1, fontSize: 15, lineHeight: 21, color: theme.ink },
  znacka: { fontSize: 11, color: theme.rule },
  znackaHotovo: { color: theme.spravne },

  drobecky: {
    marginTop: -14,
    marginBottom: 24,
    fontSize: 13,
    lineHeight: 19,
    color: theme.muted,
  },
  odstavec: { marginBottom: 26 },
  textZakona: { fontSize: 16, lineHeight: 25, color: theme.ink },
  cisloOdstavce: { fontWeight: '600', color: theme.accent },
  odkazText: { fontSize: 15, color: theme.accent },

  vyklad: { marginTop: 4, gap: 16 },
  vykladText: { fontSize: 17, lineHeight: 27, color: theme.ink },
  vykladDuraz: { fontWeight: '600' },
  volbaNeaktivni: { backgroundColor: 'transparent', borderStyle: 'dashed' },
  volbaPopisek: { fontSize: 19, fontWeight: '500', color: theme.ink },
  textNeaktivni: { color: theme.muted },
  volbaNapoveda: { marginTop: 5, fontSize: 14, color: theme.muted },

  beh: { paddingHorizontal: 24, paddingBottom: 48 },
  stred: { flex: 1, justifyContent: 'center', paddingHorizontal: 24, gap: 12 },
  zpet: { paddingVertical: 12, alignSelf: 'flex-start' },
  zpetText: { fontSize: 16, color: theme.muted },

  postup: {
    marginTop: 8,
    fontSize: 12,
    letterSpacing: 1.2,
    textTransform: 'uppercase',
    color: theme.accent,
  },
  zneni: {
    marginTop: 12,
    marginBottom: 22,
    fontSize: 21,
    lineHeight: 29,
    color: theme.ink,
    fontWeight: '500',
  },

  varianta: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    borderWidth: 1,
    borderColor: theme.rule,
    borderRadius: 14,
    paddingVertical: 15,
    paddingHorizontal: 16,
    marginBottom: 10,
    backgroundColor: '#FFFFFF',
  },
  variantaOznacena: { borderColor: theme.ink },
  variantaSpravne: { borderColor: theme.spravne, backgroundColor: '#F1F8F3' },
  variantaSpatne: { borderColor: theme.spatne, backgroundColor: '#FBF2F1' },
  variantaText: { flex: 1, fontSize: 16, lineHeight: 23, color: theme.ink },

  zaskrt: {
    width: 22,
    height: 22,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: theme.rule,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 1,
  },
  zaskrtOznaceny: { borderColor: theme.ink, backgroundColor: theme.ink },
  zaskrtZnak: { color: '#FFFFFF', fontSize: 13, lineHeight: 16 },

  rozbor: {
    marginTop: 14,
    padding: 18,
    borderRadius: 14,
    backgroundColor: '#F3EEE7',
    gap: 8,
  },
  verdikt: { fontSize: 13, letterSpacing: 1.2, textTransform: 'uppercase', fontWeight: '600' },
  pramen: { fontSize: 14, color: theme.ink, fontWeight: '500' },
  vysvetleni: { fontSize: 15, lineHeight: 23, color: theme.ink },
  poznamka: { fontSize: 14, lineHeight: 21, color: theme.muted, fontStyle: 'italic' },
  varovani: { fontSize: 14, lineHeight: 21, color: theme.spatne },

  tlacitko: {
    marginTop: 24,
    borderRadius: 999,
    paddingVertical: 17,
    alignItems: 'center',
    backgroundColor: theme.ink,
  },
  tlacitkoStisk: { opacity: 0.85 },
  tlacitkoText: { color: theme.paper, fontSize: 16, fontWeight: '500' },

  nadpisVysledku: {
    marginTop: 16,
    fontSize: 46,
    fontWeight: '600',
    letterSpacing: -1.5,
    color: theme.ink,
  },
  verdiktVelky: { marginTop: 6, fontSize: 19, fontWeight: '500' },
  cara: { height: 1, backgroundColor: theme.rule, marginVertical: 26 },
  radekOblasti: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 9,
  },
  oblastNazev: { fontSize: 16, color: theme.ink },
  oblastSkore: { fontSize: 16, color: theme.muted },

  patka: { marginTop: 22, fontSize: 13, lineHeight: 20, color: theme.muted },
});
