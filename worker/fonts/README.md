# Caption fonts

| Family | Files | In git? | Licence |
|---|---|---|---|
| Jost (Futura look-alike) | `Jost-*.ttf` | yes | SIL Open Font License, `OFL-Jost.txt` |
| Inter (SF Pro look-alike) | `Inter-*.ttf` | yes | SIL Open Font License, `OFL-Inter.txt` |
| Instagram Sans | `Instagram_Sans_*.ttf`, `Instagram_Sans_Headline.otf` | no | Jordan's licence |
| SF Pro Display | `SF-Pro-Display-{Regular,Medium,Bold}.otf` | no | Jordan's licence |
| Helvetica Neue | `Helvetica-Neue-{Roman,Medium,Bold,Heavy}.otf` | no | Jordan's licence |

Licensed files stay out of git (`.gitignore`). On Railway they come from the private bucket. Locally, drop
them in this folder with exactly these names. The tool only offers a family when all its files are present
(`trialreels/config.py`, `FONTS`). Never add Avenir Next (renders italic).
