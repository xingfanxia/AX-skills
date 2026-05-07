# theme.json anatomy — clawd-on-desk schema reference

Schema version 1. Fields with `?` are optional (sensible defaults applied by theme-loader).

```jsonc
{
  "schemaVersion": 1,                      // required
  "name": "Display Name",                  // required, Unicode-safe (e.g. "小肥")
  "author": "user",                        // optional
  "version": "1.0.0",                      // optional
  "description": "...",                    // optional, shown in tooltip

  // Render canvas geometry
  "viewBox": {
    "x": 0, "y": 0,
    "width": 266, "height": 200            // standard for clawd-on-desk
  },

  "layout": {
    "contentBox": {                        // where the cat actually lives within viewBox
      "x": 36, "y": 10, "width": 194, "height": 160
    },
    "centerX": 133,
    "baselineY": 170,
    "visibleHeightRatio": 0.35,            // fraction of cat height visible at idle
    "baselineBottomRatio": 0.05            // padding from bottom edge
  },

  // Eye-tracking is for SVG-based themes (calico). Set false for AI-generated APNG themes.
  "eyeTracking": { "enabled": false },

  // State → APNG file mapping. Required.
  "states": {
    "idle":         ["munchkin-idle-dozing.apng"],
    "yawning":      ["munchkin-idle-dozing.apng"],   // alias to idle-dozing
    "dozing":       ["munchkin-idle-dozing.apng"],   // alias
    "collapsing":   ["munchkin-collapse-sleep.apng"],
    "thinking":     ["munchkin-thinking.apng"],
    "working":      ["munchkin-working-typing.apng"],
    "error":        ["munchkin-error.apng"],
    "attention":    ["munchkin-happy.apng"],         // attention = small celebration
    "notification": ["munchkin-notification.apng"],
    "sleeping":     ["munchkin-sleeping.apng"],
    "waking":       ["munchkin-wake.apng"]
  },

  // For "working" state, you can ramp up animation as session count grows.
  "workingTiers": [
    { "minSessions": 1, "file": "munchkin-working-typing.apng" }
  ],

  // Idle loops (background ambient motion)
  "idleAnimations": [
    { "file": "munchkin-idle-dozing.apng", "duration": 5000 }
  ],

  // Per-state minimum display + auto-return timings (ms)
  "timings": {
    "minDisplay": {
      "attention": 5000,
      "error": 5000,
      "notification": 5200,
      "working": 1000,
      "thinking": 1000
    },
    "autoReturn": {
      "attention": 5000,
      "error": 5000,
      "notification": 5200
    },
    "dndSkipYawn": true,
    "collapseDuration": 800,
    "wakeDuration": 1500,
    "deepSleepTimeout": 600000,            // 10 min idle → deep sleep
    "mouseIdleTimeout": 20000,             // 20s no mouse → idle dozing
    "mouseSleepTimeout": 60000             // 60s no mouse → sleeping
  },

  // Click hit-boxes (in viewBox coords)
  "hitBoxes": {
    "default":  { "x": 80, "y": 30, "w": 106, "h": 140 },
    "sleeping": { "x": 60, "y": 60, "w": 146, "h": 100 }   // wider when curled
  },

  "sleepingHitboxFiles": [
    "munchkin-sleeping.apng",
    "munchkin-collapse-sleep.apng"
  ],

  // Click reactions (left, right, drag)
  "reactions": {
    "clickLeft":  { "file": "munchkin-react-poke.apng", "duration": 2500 },
    "clickRight": { "file": "munchkin-react-poke.apng", "duration": 2500 }
  },

  "miniMode": { "supported": false },        // set true if you generate mini-mode APNGs
  "transitions": {},                          // advanced: state-to-state transition overrides

  // Per-file rendering scale + offset tuning
  "objectScale": {
    "widthRatio": 0.58,                       // global scale ratios
    "heightRatio": 0.44,
    "imgWidthRatio": 0.6,
    "objBottom": 0.05,
    "imgBottom": 0.05,
    "offsetX": 0.21,
    "offsetY": 0.28,

    // Per-file overrides — bump for fluffy breeds (Ragdoll, Persian)
    "fileScales": {
      "munchkin-idle-dozing.apng": 1.05,    // short-coat baseline
      "munchkin-thinking.apng": 1.20,
      "munchkin-working-typing.apng": 1.20
      // ...
    }
  }
}
```

## Common patterns

### Aliasing states

If you only generated `idle-dozing` (and not separate `yawning` / `dozing`), alias them:

```json
"states": {
  "idle":    ["munchkin-idle-dozing.apng"],
  "yawning": ["munchkin-idle-dozing.apng"],
  "dozing":  ["munchkin-idle-dozing.apng"]
}
```

clawd-on-desk's runtime treats them as the same animation but uses the state name for transition logic.

### Disabling eye tracking

Calico's eye-tracking depends on SVG element IDs we don't have for AI-generated APNGs:

```json
"eyeTracking": { "enabled": false }
```

### Disabling mini-mode

If you didn't generate mini-mode APNGs (smaller "tray pet" variants):

```json
"miniMode": { "supported": false }
```

### Bumping fluffy-breed scales

Ragdoll (long coat) example — every fileScale bumped ~0.05:

```json
"fileScales": {
  "ragdoll-idle-dozing.apng": 1.10,    // Munchkin equivalent: 1.05
  "ragdoll-thinking.apng": 1.25,       // Munchkin: 1.20
  "ragdoll-working-typing.apng": 1.25, // Munchkin: 1.20
  "ragdoll-notification.apng": 1.07,   // Munchkin: 1.02
  "ragdoll-error.apng": 1.30,          // Munchkin: 1.25
  "ragdoll-happy.apng": 1.25           // Munchkin: 1.20
}
```

## Validation

After generating theme.json:

```bash
cd ~/projects/products/clawd-on-desk
node -e '
  const path = require("path");
  const tl = require("./src/theme-loader");
  tl.init(path.resolve("./src"), null);
  const t = tl.loadTheme("<your-pet-id>", { strict: true });
  console.log("OK:", t.name, "states=", Object.keys(t.states).length);
'
```

Expected: prints `OK: <name> states=11`. Errors thrown by `loadTheme` indicate schema issues.

`generate.py` runs this validation automatically before declaring the theme installed.

## See also

- [`themes/calico/theme.json`](https://github.com/anthropics/clawd-on-desk/blob/main/themes/calico/theme.json) in clawd-on-desk — fully-featured baseline with mini-mode + eye-tracking.
- [`src/theme-loader.js`](https://github.com/anthropics/clawd-on-desk/blob/main/src/theme-loader.js) — strict-validation logic + defaults.
