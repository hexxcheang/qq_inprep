# EPTC 2026 name badge (A6 portrait, lanyard)

Size: 105 × 148 mm (A6 portrait). All categories use the same background. Only the category ribbon colour changes.

| Category | Ribbon | Text |
|---|---|---|
| Organising Committee | Orange `#E8601C` | white |
| Keynote Speaker | Blue `#1F5FAE` | white |
| Invited Speaker | Green `#2E8540` | white |
| PDC / FC Instructor | Purple `#6A3D9A` (proposed) | white |
| Panelist | Magenta `#C2185B` (proposed) | white |
| Student Volunteer | Yellow `#F5C400` (proposed) | dark |
| Delegate | none (white, hairline borders) | brand brown |
| Student | none (white, hairline borders) | brand brown |

## Layout (mm from top)
- 0–4: brand gradient bar · 7–10: lanyard slot guide (dashed, 20 × 3.2 mm)
- 12–36: EPTC 2026 logo, top centre
- 38–47: “28th Electronics Packaging Technology Conference · 1 – 4 December 2026 · Singapore”
- 53–86: **FULL NAME** (shrinks to fit, wraps if needed) + AFFILIATION
- 88–101: category ribbon (full width)
- 105–136: QR code area, 31 × 31 mm (right) · Marina Bay Sands, ~40 × 18 mm with label, ~5 % of the badge (left)
- 141–148: brand footer bar (eptc-ieee.net · IEEE EPS Flagship Conference)

## Files
- `out/EPTC2026_badges_A6.pdf`: 8 pages, one per category, exact trim size
- `out/EPTC2026_badges_A6_print_bleed3mm.pdf`: the same pages with 3 mm bleed (111 × 154 mm, TrimBox set) for the printer
- `out/0X_<category>.png`: preview of each badge
- `out/EPTC2026_badges_overview.png`: all 8 side by side
- `out/html/`: the HTML for each badge

## Rebuild / edit
```bash
cd badge && npm install && node build_badges.js
```
To change labels, colours or the placeholder text, edit `CATEGORIES`, `NAME` and `AFFILIATION` at the top of `build_badges.js`.
Uses the Inter font and Playwright's Chromium. Fonts are embedded in the PDFs.
