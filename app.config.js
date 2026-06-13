// Dynamic Expo config.
//
// `experiments.baseUrl` is a WEB-ONLY setting (serves the web export from a
// subpath, e.g. GitHub Pages at /7mw). When it lives in the static app.json it
// also leaks into the NATIVE asset-embedding step, prefixing every bundled
// asset with the base path and producing a broken/colliding directory path —
// which fails the iOS/Android build with `ENOTDIR ... mkdir .../7mw/assets/...`.
//
// So we only apply baseUrl when explicitly building for web, signalled by the
// EXPO_WEB_BASE_URL env var (set in the `build:web` script and the Pages deploy
// workflow). Native EAS builds never set it, so they bundle assets at the root.
module.exports = ({ config }) => {
  const baseUrl = process.env.EXPO_WEB_BASE_URL;
  if (baseUrl) {
    config.experiments = { ...(config.experiments || {}), baseUrl };
  }
  return config;
};
