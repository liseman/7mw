# 7MW

The dead-simple seven-minute workout. One button. Twelve exercises. No accounts, no ads, no data collection, no upsells.

The workout is a 12-exercise high-intensity circuit, no equipment needed: 30 seconds of work per exercise with a 10-second buffer between exercises, in this order — jumping jacks, steam engine, push-ups, crunches, hip raises, squats, tricep lifts, plank, high knees, lunges, push-up + rotation, side plank (15 seconds per side, with a mid-cue to switch).

Voice cues are pre-generated with ElevenLabs and bundled as assets; the app makes zero network calls at runtime. Each exercise has a hand-keyframed animation of an anime guy demonstrating the move (see `figure.js`).

## Develop

```sh
npm install
npm start          # Expo dev server (i = iOS, a = Android, w = web)
npm run typecheck
```

## Regenerate assets

```sh
ELEVENLABS_API_KEY=... npm run audio:regen   # real voice cues (voice "luke1")
npm run audio:placeholders                   # offline beep stand-ins
npm run icons:regen                          # icon / splash / favicon
node scripts/preview-anims.mjs               # contact sheet of all animations
```

There's also a `Regenerate voice cues` GitHub Actions workflow (needs an `ELEVENLABS_API_KEY` repo secret) that commits regenerated audio.

## Ship

- **Web**: pushed to `main` → deployed to GitHub Pages by `.github/workflows/deploy.yml`.
- **iOS / TestFlight**: the `Build iOS and submit to TestFlight` workflow runs `eas build --auto-submit` (needs an `EXPO_TOKEN` repo secret), or locally: `npm run build:ios`.
- **Android**: `npx eas-cli build --platform android --profile production`.
