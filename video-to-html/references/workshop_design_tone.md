---
type: note
project: "references"
source: codex
tags:
  - note
status: reference
---
# Workshop Design Tone

Use this reference when creating or revising the HTML visual design. The target tone is based on `2026 워크샵 ppt_design_tokens.md`.

## Visual Signature

- Light gray canvas with quiet report density.
- Off-white panels with thin gray borders.
- Four-pillar accent system using navy, green, purple, and charcoal.
- Strong title hierarchy, compact cards, and no marketing hero layout.
- Use color bars, top borders, and left borders for structure instead of decorative blobs or gradients.

## Palette

| Token | Hex | Usage |
|---|---|---|
| canvas | `#ECECEC`, `#F0F0F0`, `#E4E4E4` | page background and neutral blocks |
| panel | `#F7F7F4` | cards and panels |
| text primary | `#0C0C0C`, `#242424` | headings and body |
| text secondary | `#54546C` | labels and captions |
| hairline | `#B8B8B8`, `#C8C8C8` | borders and separators |
| pillar navy | `#0C3C84` | first accent, primary buttons |
| pillar green | `#0C5424` | second accent, flow active state |
| pillar purple | `#3C246C` | third accent |
| pillar charcoal | `#243C54` | fourth accent and navigation |
| cool tint | `#CCE4E4`, `#E0F0F0` | informational panels |
| lilac tint | `#CCCCE4`, `#E4E4FC` | supporting cards |
| mint tint | `#CCE4CC`, `#E4FCE4` | active or positive structure |

## Typography

- Prefer `Pretendard`, `Noto Sans KR`, `Malgun Gothic`, system sans-serif.
- Use large title type only in the first viewport.
- Keep section headings around 24~28px equivalent in HTML.
- Keep body text in 14~17px range.
- Do not use negative letter spacing or viewport-width font scaling.

## Components

- Hero: two-column report header with title and source panel. Use abstract diagonal color bands only as a restrained background cue.
- Panels: off-white background, one-pixel border, 4px radius, subtle shadow, and top accent border.
- Cards: compact, repeated items only. Do not nest cards inside cards.
- Filters and tabs: rectangular controls with 4px radius. Active state uses navy fill.
- Flow selector: vertical buttons on desktop, stacked on mobile. Active state uses mint fill and green left border.
- Tables: cool tint header row, thin gray grid, no heavy fills.
- Thumbnail: preserve aspect ratio with `width: 100%; height: auto; object-fit: contain;`.

## Avoid

- Purple-blue gradient-dominant UI.
- Rounded pill-heavy SaaS styling except tiny category tags.
- Decorative orbs, bokeh, or unrelated illustrations.
- Landing-page copy or promotional sections.
- External CSS, fonts, or JS libraries.
