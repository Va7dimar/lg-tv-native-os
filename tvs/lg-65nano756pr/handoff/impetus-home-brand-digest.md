# Impetus brand digest for Impetus Home (TV)

**Source of truth: the owner's monorepo, the one with `apps/impetus`** (the
owner's own repo on the PC you run on). Read these there, in this order:

| Path in that repo | What it holds |
|---|---|
| `apps/impetus/src/app/globals.css` | The site tokens, as CSS variables (ground, pane, line, muted, text, slab, key wall). Copy the values from here. |
| `docs/impetus/design-vision/brand/package/tokens.brand.json` and `brand.md` | The **brand greens** (`#1FB487` light, `#2C8C86` quiet, `#0E6A50` phthalo). They are not in `globals.css` yet, because they're "not yet on the site". |
| `apps/impetus/src/fonts/` | `Syncopate-Bold.woff2`, `Unbounded-Variable.woff2`, `IBMPlexMono-Regular.woff2`, and the `LICENSE-*.txt` files. Bundle the fonts **with** their licence files. Don't fetch from Google Fonts. |
| `apps/impetus/src/app/icon.svg`; `docs/impetus/design-vision/avatar/impetus-avatar-dark-128.png` and `-256.png` | The mark. For the webOS `icon` (80×80) and `largeIcon` (130×130), downscale the 128 and 256 PNGs, or render the SVG. Don't redraw or recolour it. |
| `.design-sync/guidelines`, `.design-sync/docs` | Colour, type, motion and composition rules, one doc per part. |
| `docs/impetus/design-vision/vision.md` | The numbered rulings that the rules cite. |
| `docs/impetus/design-vision/brand/package/`, `docs/impetus/design-vision/brand-taste/summary.md` | The brand layer: the green light, the halo, the press glow and the motion curves. |

The owner also shared the design-system artifact with your account:
<https://claude.ai/artifact/32kKsnrcTjnk1xTX3iypWF> (read
`project/README.md`, `colour.md`, `type.md`, `brand.md`, `tokens.json`).

The digest below is a quick reference, taken from that system (synced
2026-10-04, brand rulings 2026-10-23/24). Where it differs from the repo,
**the repo wins**. Only the parts a TV home screen needs. Don't invent new
colours.

## Colourway: primary only

"A dark, quiet place with one green thing alive inside it."

| Token | Hex | Job on the Home |
|---|---|---|
| `--color-ground` | `#000000` | The only background. True black: never grey, blue-black or cream. |
| ground light | radial of `#E6EAF1` at 10 %, centred at 22 % / 18 %, gone by 60 % | One fixed light at the top left. No vignette, no grain, no second light. |
| `--color-pane` | `#0D0E10` | Tile body (middle of the slab gradient). |
| `--color-slab-top` / `--color-slab-foot` | `#16181C` / `#0A0B0D` | Tile gradient, top to foot, plus a 1 px top sliver `inset 0 1px 0 rgba(230,234,241,.14)`. No border, no drop shadow. |
| `--color-key-wall` | `#1A1D21` | The 3 px wall down and right of anything pressable. A press moves onto it in 60 ms. |
| `--color-line` | `#34383E` | Hairlines; a control at rest. |
| `--color-muted` | `#8E959F` | Secondary text, tile labels, the date. |
| `--color-text` | `#E6EAF1` | Text, the clock, the focus ring. Nothing is lighter (never pure white). |
| `--color-brand-light` | `#1FB487` | **Focus halo only**: a soft green glow behind or around the focused tile, spilling onto the black. Never paint on a surface, never text. |
| `--color-brand-quiet` | `#2C8C86` | The quiet fill under the halo, and only that. Never a teal-soaked screen. |
| `--color-brand-phthalo` | `#0E6A50` | The mark's branch and the caret only. 3.2:1 on black, so never text. |

Signal hues keep their single meaning and don't appear on the Home unless
the meaning applies: found `#E39A3B`, wrong `#E8555F`, historic `#5FA89B`.
Discovery violet `#A394F5` is never interface.

## Type (three faces, each with one job; all SIL OFL on Google Fonts, bundle locally)

| Face | Use on the Home |
|---|---|
| **Syncopate 700** | Tile labels and section headings (`FORRIT`, `INNTÖK`, `HDMI 1`, `SJÓNVARP`). Uppercase, tracking **0.08em**, short strings only. Real `h1`/`h2` for headings. |
| **Unbounded 400** (variable 300–500) | Everything else you read: app names if longer than a short label, the date, messages. Sentence case. |
| **IBM Plex Mono 400** | Data only: the clock (`14:05`). Never labels or buttons. |

Case rule: CAPS = a thing you can open, sentence case = something to read,
mono = data.

Sizes are for viewing across the room at 1920×1080. Scale the site's 15 px
body up about 2×. Suggested starting points: tile label 28–32 px Syncopate,
date 30 px Unbounded in muted, clock 64 px Plex Mono in text. Tune on the TV.

## Shape and motion

- Everything is square (radius 0). Round shapes are only for marks.
- Still by default. A small thing snaps (60 ms, `cubic-bezier(0.23,1,0.32,1)`).
  A big thing glides (1100 ms, `cubic-bezier(0.16,1,0.3,1)`). Never float,
  bounce, or stop hard on a big thing.
- Focus: halo plus a 2 px `#E6EAF1` outline set 2 px outside the tile.
  Focus snaps, no fade.
- Press: a hard snap onto the key wall, the face stays dark, and a faint
  green halo flares. The face never lights up.

## Content and voice

- No emoji, no pill buttons, no gradient text, no cards inside cards, no
  icon on every item.
- Voice invites and never explains. If there is any greeting at all, keep it
  to a short imperative. The site's line is "Go in. Play around. See what
  happens.", but Home v1 needs no tagline.
- The Impetus mark (one fine line that forks: ink stem, phthalo branch) is
  for the **launcher icon only**, never inside the UI. Take it from
  `apps/impetus/src/app/icon.svg` or the `docs/impetus/design-vision/avatar/`
  PNGs (see the table above). Don't redraw or recolour it.

Secondary colourway (grey `#2A2A2C`, orange `#FF5A1F`, white): **not** for
v1. Never mix it with the green.
