# EPTC Best Academic Paper Award certificate (redesign)

`out/EPTC_Best_Academic_Paper_Certificate.pptx` is 10 × 7.5 in, the same size as the original EPTC 2024 certificate.

- **Editable:** every piece of wording is its own text box (conference, date, award title, "is presented to", authors, affiliations, "for the paper", paper title, signatory names and roles). They are named in PowerPoint's Selection Pane.
- **Background:** the golden frame (metallic band, guilloche pattern, Art Deco corners, faint rosette and gold circuit traces) is the slide background image, so it can't be moved by accident. To change it: Design → Format Background.
- **Movable pictures:** the gold seal, the logos and the signatures can be moved or swapped (right-click → Change Picture).
- **Fonts:** Cambria (headings, names, paper title) and Calibri (details) ship with Office.

Rebuild after changing the artwork or wording in the scripts:
```bash
npm install && node make_art.js && node build_certificate.js
```
