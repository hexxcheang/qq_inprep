# EPTC 2026 registration counter backdrop (6 m × 3 m)

For the registration counter at Sands Expo and Convention Centre, in front of the event hall.

## Print files (`out/`)
| File | Use |
|---|---|
| `EPTC2026_registration_backdrop_6x3m_scale1-10_bleed.pdf` | **Send to the printer.** Drawn at 1:10 (610 × 310 mm), so print at **1000 %** for 6000 × 3000 mm. Includes 50 mm bleed on every side at full size (5 mm in the file). The TrimBox is set. |
| `EPTC2026_registration_backdrop_6x3m_scale1-10.pdf` | The same at trim size (600 × 300 mm at 1:10), for review |
| `EPTC2026_registration_backdrop_preview.png` | Screen preview |
| `EPTC2026_registration_backdrop_counter_mockup.png` | Preview with a 1 m counter in front, to check what stays visible |

The PDF is drawn at 1:10 because PDF pages can't be more than about 5 m wide. The EPTC logo, text, circuit graphics and skyline are vector, so they stay sharp at full size. Sponsor logos are the files from the EPTC website, placed as images.

## Layout (full-size mm, from top-left)
- **Left half:** the EPTC 2026 logo (2.34 m wide, vector). Under it: "28th Electronics Packaging Technology Conference · 1 – 4 December 2026 · Sands Expo and Convention Centre, Singapore · IEEE EPS Flagship Conference in the Asia-Pacific Region". Then the **REGISTRATION** ribbon at y 1500–1830, its bottom edge 1.17 m above the floor.
- **Right half:** the sponsor wall (2.7 × 1.8 m, y 170–1970) with Diamond, Platinum, Gold, Silver and Bronze tiers. Logos are sized by area, so wide and square logos look equally weighted.
- **Bottom 1 m:** background only (circuit traces, solder-ball dots, and Marina Bay Sands rising out of the bottom brand bar). This part is expected to be hidden by the counter. All key content sits above 1 m.

## Sponsor logos
Source: https://eptc-ieee.net/2026%20SPONSORS?sid=32 (taken 7 Nov 2026), listed in `sponsors.json` with files in `assets/sponsors/`.

**Still needed:** two Bronze logos fail to load on the EPTC website itself (the server returns 403), so they appear as dashed placeholders:
- ASE (aseglobal.com)
- one more Bronze sponsor with no link on the site. Alphabetically it sits between ASE and Brewer Science.

**Low resolution at full size** (run `node build_backdrop.js` to see the list). Ask these sponsors for vector logos (AI, EPS, SVG or PDF):
- Very low, will look blurry: Applied Materials (30 dpi), SPIL (26), Fujifilm (32), Lintec (35)
- Borderline: Brewer Science (69), Evatec (62), STMicroelectronics (82), Lam Research (85)

To swap one in, put the new file in `assets/sponsors/` (PNG; vector can be converted to a high-resolution PNG), update `file` and `px` in `sponsors.json`, and rebuild.

## Rebuild
```bash
cd backdrop && npm install && node build_backdrop.js
```
Sizes, bleed, scale and counter height are constants at the top of `build_backdrop.js`. The EPTC logo was traced to vector (`assets/eptc2026_logo_vector.svg`) from the website's 763 px logo. Ask the organisers for the original vector logo if they have one.
