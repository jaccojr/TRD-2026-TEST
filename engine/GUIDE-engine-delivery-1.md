# Engine delivery 1 (v0.1.1-PRELIMINARY): what goes where

v0.1.1 (2026-09-25): the language files now sit next to `index.html` instead of in a `lang/` subfolder. The first upload lost the subfolder, so the engine couldn't load its texts. One flat folder avoids that.

Delivery 1 contains: the layout with no fixed tab bar, the language switch (NL/EN), the Today tab, the header with the emergency buttons and SOS screen, the footer, and the compare page. The Route, Camp and Prep tabs only show a placeholder for now (deliveries 2–4).

## 1. What you upload

Only the folder `engine/` from the zip. Nothing at the root of the repo changes: v2.29 keeps running there.

| File | What it is |
|---|---|
| `engine/index.html` | The engine app. Contains no event facts at all |
| `engine/event.json` | TRD-2026 in the new data format (converted from data.js) |
| `engine/ui.*.json`, `engine/sport-cycling.*.json`, `engine/weather.*.json` | 6 language files, each in NL and EN |
| `engine/weather-keymap.json` | Translates the weather keys (`1-2` → `s1-fs2`), so the engine reads the existing `weather.json` |
| `engine/sw.js` | The engine's own service worker (own cache `engine-trd2026-v0.1.1`, scope `/engine/` only) |
| `engine/compare.html` | The compare page: v2.29 and the engine side by side |

The photos, logos, climb charts and GPX files are **not** in the folder. The engine uses the ones already in the repo (one folder up).

## 2. How to upload (GitHub website, on a computer)

1. Unzip the zip. You get a folder `engine` with 12 files and no subfolders.
2. Open **https://github.com/jaccojr/TRD-2026-TEST/tree/main/engine** (the existing `engine` folder in the repo).
3. Click **Add file → Upload files**.
4. Select **all 12 files** inside your unzipped `engine` folder and drag them onto the page. Files with the same name are replaced.
5. Commit message, e.g. `engine v0.1.1`, then **Commit changes**.
6. Wait 1–2 minutes for GitHub Pages.

**Important: github.com vs github.io.** `github.com/jaccojr/TRD-2026-TEST/...` is where the files are stored (the repo). The website that runs the app is **`jaccojr.github.io/TRD-2026-TEST/...`**. Opening a github.com address with a file path gives a 404.

## 3. Where you test

| What | Address | On |
|---|---|---|
| Compare page | `https://jaccojr.github.io/TRD-2026-TEST/engine/compare.html` | Computer or iPad (needs ~800 px width) |
| Engine on its own | `https://jaccojr.github.io/TRD-2026-TEST/engine/` | Phone |
| v2.29 (reference) | `https://jaccojr.github.io/TRD-2026-TEST/` | Phone or computer |

**Compare page:**
1. Open it. The left frame (v2.29) asks for the TEST password once (`fedaia`). After that both frames open straight away.
2. Click a moment in the row of buttons (e.g. `17/9 12:00`), or set date and time yourself. Both apps jump to that moment.
3. Tabs at the top switch both apps. `Camp` = `Camping` in v2.29.
4. `Engine language` switches only the engine (v2.29 is Dutch only).
5. `Real time` puts both back on the actual date and time.

**On the phone (engine on its own):** scroll, switch tabs, lock and unlock the phone a few times, switch to another app and back. The tab bar must stay at the bottom at all times (rule 37). Use the Demo day bar at the top to jump through the days, as in v2.29.

## 4. What is different on purpose

Please don't report these as bugs; do report anything else.

- **Language switch** NL/EN in the header.
- **Tab bar** is part of the layout, not a floating layer. The content scrolls between header and tab bar.
- **Numbers** follow the language: `34,1` / `1.050` in Dutch, `34.1` / `1,050` in English. v2.29 showed some raw numbers (`34.1`, `1050`) in the Dutch screen.
- **Last evening** (18/9 after 17:30): no empty "Start (morgen) —" row. v2.29 showed it.
- **After the event**: the breakfast line only shows on the departure day (19/9). v2.29 kept showing it on every later date.
- **"Before the start" card** disappears at start + 2 h, rounded up to the half hour: 10:00 normally, 14:00 on the prologue. On stage 4 (start 07:45) that is also 10:00, same as v2.29.
- **Footer**: version shows `v0.1-PRELIMINARY (engine)`. No "Weer testen" and "Analytics" buttons yet.
- **Partners** are picked at random per session, so left and right can show different logos. That's the same rule as v2.29.

## 5. Known limits of this delivery

- Route, Camp and Prep are placeholders.
- No GoatCounter analytics in the engine yet.
- No password gate on `/engine/`. The content is the same public event data, so this is only a note.
- The cover photo only shows on production, not on TEST (same as v2.29).
- Personal start/finish times can't be set yet (that's the Route tab); Today uses the default times, like v2.29 does for a rider who never touched the slider.

## 6. If something looks old or stuck on the phone

The engine has its own cache, separate from v2.29. If the phone still shows an older engine version after an upload:
1. Close the tab and open `/engine/` again (the service worker updates on the next load).
2. If that doesn't help: iPhone **Settings → Safari → Advanced → Website Data**, remove `jaccojr.github.io`. This also clears v2.29's TEST data, so you'll need to enter the password again.

Every later delivery bumps the cache name (`engine-trd2026-v0.1.1`, `v0.2` …), the TRD lesson about stale files.

One thing to know: v2.29's own service worker deletes every cache that isn't its own whenever **it** gets a new version. As long as the root `sw.js` isn't changed, that doesn't happen. If it ever does, the engine simply downloads its files again.

## 7. Undo

Delete the `engine` folder in the repo (GitHub: open the folder → each file → delete, or one commit from a computer). v2.29 at the root is not affected either way.
