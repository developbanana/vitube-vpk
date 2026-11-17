#!/usr/bin/env python3
"""Regenerate assets/font_ja.ttf, the Japanese fallback font bundled in the VPK.

Noto Sans JP is OFL-1.1; the licence text is assets/FONT-JA-LICENSE.txt and the
upstream is https://github.com/google/fonts/tree/main/ofl/notosansjp.

Download the variable font once, then run this script:

    curl -fL -o NotoSansJP.ttf \
      'https://raw.githubusercontent.com/google/fonts/main/ofl/notosansjp/NotoSansJP%5Bwght%5D.ttf'
    python3 -m pip install fonttools
    python3 tools/make-ja-font.py NotoSansJP.ttf

The subset keeps JIS X 0208 (derived from CP932), kana, Japanese punctuation,
ASCII and the full/half-width forms. That is what Japanese YouTube titles and
the Japanese UI need; dropping the other ~14,000 CJK ideographs keeps the
result at ~2.3 MB instead of ~4.8 MB.

The output is a static wght=400 instance with hinting kept: the app renders at
14, 18, 21 and 36 px, and hinted outlines are visibly cleaner at 14 px.
"""

import argparse
import sys

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont


def wanted_codepoints():
    """JIS X 0208 via CP932, plus the blocks the UI itself uses."""
    cps = set()
    for lead in range(0x81, 0x100):
        for trail in range(0x40, 0x100):
            try:
                ch = bytes([lead, trail]).decode("cp932")
            except UnicodeDecodeError:
                continue
            if len(ch) == 1 and ord(ch) >= 0x80:
                cps.add(ord(ch))
    for lo, hi in [
        (0x0020, 0x007E),  # ASCII
        (0x00A0, 0x00FF),  # Latin-1 punctuation used by titles
        (0x2000, 0x206F),  # general punctuation
        (0x2100, 0x214F),  # letterlike symbols
        (0x2190, 0x21FF),  # arrows (log viewer hints)
        (0x2460, 0x24FF),  # enclosed alphanumerics
        (0x25A0, 0x25FF),  # geometric shapes (face buttons)
        (0x3000, 0x30FF),  # CJK punctuation, hiragana, katakana
        (0x31F0, 0x31FF),  # katakana phonetic extensions
        (0xFF00, 0xFFEF),  # full/half-width forms
    ]:
        cps.update(range(lo, hi + 1))
    return cps


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="NotoSansJP[wght].ttf from Google Fonts")
    parser.add_argument("-o", "--output", default="assets/font_ja.ttf")
    args = parser.parse_args()

    font = TTFont(args.source)
    if "fvar" in font:
        instantiateVariableFont(font, {"wght": 400}, inplace=True)

    cps = wanted_codepoints()
    options = subset.Options()
    options.layout_features = ["kern"]
    options.notdef_glyph = True
    options.notdef_outline = True
    options.recommended_glyphs = True
    options.hinting = True
    options.glyph_names = False
    options.name_IDs = ["*"]

    subsetter = subset.Subsetter(options)
    subsetter.populate(unicodes=cps)
    subsetter.subset(font)
    font.save(args.output)

    print(f"wrote {args.output}: {len(cps)} requested code points, "
          f"{len(font.getGlyphOrder())} glyphs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
