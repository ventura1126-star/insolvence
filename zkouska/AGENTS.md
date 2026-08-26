# Expo HAS CHANGED

This project runs on **Expo SDK 54**, not the latest.

Read the exact versioned docs at https://docs.expo.dev/versions/v54.0.0/ before
writing any code.

Do not upgrade the SDK. Richard's iPhone is on an older iOS, so the App Store gives
him an Expo Go capped at SDK 54 — the device sets the ceiling, not the project. After
any dependency work run `npx expo install --fix` and check that `react-native` stays
on 0.81.x.

# Odpovědi se nevymýšlejí

Každá odpověď v `assets/odpovedi.json` musí být dohledaná v aktuálním znění
předpisu a nést odkaz na konkrétní paragraf. Nesprávná odpověď je horší než
žádná — u zkoušky s hranicí 80 % se z ní naučí neplatné právo.

Znění předpisů stáhne `../tools/stahni_zakon.py`, kontrolu konzistence dělá
`../tools/kontrola_odpovedi.py`. Obojí spouštěj před commitem.
