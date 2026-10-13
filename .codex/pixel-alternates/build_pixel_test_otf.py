from __future__ import annotations

from pathlib import Path

import glyphsLib
from ufo2ft import compileOTF


GRID = 64
STROKE = GRID * 3
X_HEIGHT = 1536
ASCENDER = 2048
DESCENDER = -576


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def source_glyphs() -> Path:
    return repo_root() / "src" / "glyphs" / "OpenRunde-Regular.glyphs"


def build_dir() -> Path:
    return Path(__file__).resolve().parent / "build"


def output_otf() -> Path:
    return build_dir() / "OpenRunde-PixelTest-Regular.otf"


def add_rect(pen, x0: int, y0: int, x1: int, y1: int) -> None:
    pen.moveTo((x0, y0))
    pen.lineTo((x1, y0))
    pen.lineTo((x1, y1))
    pen.lineTo((x0, y1))
    pen.closePath()


def fit_box(width: int, left_margin: int = GRID * 3, right_margin: int = GRID * 3) -> tuple[int, int]:
    usable = width - left_margin - right_margin
    box_width = max(GRID * 6, (usable // GRID) * GRID)
    return left_margin, left_margin + box_width


def replace_with_pixel_o(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    glyph.clearContours()
    glyph.clearComponents()
    pen = glyph.getPen()
    add_rect(pen, left, 0, right, STROKE)
    add_rect(pen, left, X_HEIGHT - STROKE, right, X_HEIGHT)
    add_rect(pen, left, STROKE, left + STROKE, X_HEIGHT - STROKE)
    add_rect(pen, right - STROKE, STROKE, right, X_HEIGHT - STROKE)


def replace_with_pixel_e(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    mid_y = GRID * 10
    glyph.clearContours()
    glyph.clearComponents()
    pen = glyph.getPen()
    add_rect(pen, left, 0, right, STROKE)
    add_rect(pen, left, X_HEIGHT - STROKE, right, X_HEIGHT)
    add_rect(pen, left, STROKE, left + STROKE, X_HEIGHT - STROKE)
    add_rect(pen, left, mid_y, right - STROKE, mid_y + STROKE)
    add_rect(pen, right - STROKE, mid_y + STROKE, right, X_HEIGHT)


def replace_with_pixel_r(glyph) -> None:
    left = GRID * 2
    stem_right = left + STROKE
    shoulder_right = stem_right + GRID * 8
    nub_left = shoulder_right - STROKE
    shoulder_bottom = GRID * 12
    glyph.clearContours()
    glyph.clearComponents()
    pen = glyph.getPen()
    add_rect(pen, left, 0, stem_right, X_HEIGHT)
    add_rect(pen, stem_right, X_HEIGHT - STROKE, shoulder_right, X_HEIGHT)
    add_rect(pen, nub_left, shoulder_bottom, shoulder_right, X_HEIGHT)


def replace_with_pixel_d(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    glyph.clearContours()
    glyph.clearComponents()
    pen = glyph.getPen()
    add_rect(pen, left, 0, right, STROKE)
    add_rect(pen, left, X_HEIGHT - STROKE, right, X_HEIGHT)
    add_rect(pen, left, STROKE, left + STROKE, X_HEIGHT - STROKE)
    add_rect(pen, right - STROKE, 0, right, ASCENDER)


def replace_with_pixel_p(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    glyph.clearContours()
    glyph.clearComponents()
    pen = glyph.getPen()
    add_rect(pen, left, 0, right, STROKE)
    add_rect(pen, left, X_HEIGHT - STROKE, right, X_HEIGHT)
    add_rect(pen, left, DESCENDER, left + STROKE, X_HEIGHT)
    add_rect(pen, right - STROKE, STROKE, right, X_HEIGHT - STROKE)


def replace_with_pixel_n(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    glyph.clearContours()
    glyph.clearComponents()
    pen = glyph.getPen()
    add_rect(pen, left, 0, left + STROKE, X_HEIGHT)
    add_rect(pen, right - STROKE, 0, right, X_HEIGHT)
    add_rect(pen, left + STROKE, X_HEIGHT - STROKE, right - STROKE, X_HEIGHT)


def replace_with_pixel_u(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    glyph.clearContours()
    glyph.clearComponents()
    pen = glyph.getPen()
    add_rect(pen, left, STROKE, left + STROKE, X_HEIGHT)
    add_rect(pen, right - STROKE, STROKE, right, X_HEIGHT)
    add_rect(pen, left, 0, right, STROKE)


def main() -> None:
    build_dir().mkdir(parents=True, exist_ok=True)

    ufos = glyphsLib.load_to_ufos(str(source_glyphs()))
    if not ufos:
        raise RuntimeError("No UFOs were produced from the source Glyphs file")

    ufo = ufos[0]
    ufo.info.familyName = "Open Runde Pixel Test"
    ufo.info.styleName = "Regular"
    ufo.info.styleMapFamilyName = "Open Runde Pixel Test"
    ufo.info.openTypeNamePreferredFamilyName = "Open Runde Pixel Test"
    ufo.info.openTypeNamePreferredSubfamilyName = "Regular"
    ufo.info.postscriptFontName = "OpenRundePixelTest-Regular"

    replace_with_pixel_o(ufo["o"])
    replace_with_pixel_e(ufo["e"])
    replace_with_pixel_r(ufo["r"])
    replace_with_pixel_d(ufo["d"])
    replace_with_pixel_p(ufo["p"])
    replace_with_pixel_n(ufo["n"])
    replace_with_pixel_u(ufo["u"])

    font = compileOTF(ufo)
    font.save(output_otf())

    print(f"Wrote {output_otf()}")


if __name__ == "__main__":
    main()
