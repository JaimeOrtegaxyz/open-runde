from __future__ import annotations

from pathlib import Path

import glyphsLib
from ufo2ft import compileOTF


GRID = 64
STROKE = GRID * 3
X_HEIGHT = 1536
CAP_HEIGHT = 2048
ASCENDER = 2048
DESCENDER = -576


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def source_glyphs() -> Path:
    return repo_root() / "src" / "glyphs" / "OpenRunde-Regular.glyphs"


def build_dir() -> Path:
    return Path(__file__).resolve().parent / "build"


def output_otf() -> Path:
    return build_dir() / "OpenRunde-PixelFamilyDemo-Regular.otf"


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


def clear_glyph(glyph) -> None:
    glyph.clearContours()
    glyph.clearComponents()


def draw_box_o(glyph, top: int = X_HEIGHT, bottom: int = 0) -> None:
    left, right = fit_box(int(glyph.width))
    clear_glyph(glyph)
    pen = glyph.getPen()
    add_rect(pen, left, bottom, right, bottom + STROKE)
    add_rect(pen, left, top - STROKE, right, top)
    add_rect(pen, left, bottom + STROKE, left + STROKE, top - STROKE)
    add_rect(pen, right - STROKE, bottom + STROKE, right, top - STROKE)


def draw_box_c(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    clear_glyph(glyph)
    pen = glyph.getPen()
    add_rect(pen, left, 0, right - STROKE, STROKE)
    add_rect(pen, left, X_HEIGHT - STROKE, right - STROKE, X_HEIGHT)
    add_rect(pen, left, STROKE, left + STROKE, X_HEIGHT - STROKE)


def draw_box_e(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    mid_y = GRID * 10
    clear_glyph(glyph)
    pen = glyph.getPen()
    add_rect(pen, left, 0, right, STROKE)
    add_rect(pen, left, X_HEIGHT - STROKE, right, X_HEIGHT)
    add_rect(pen, left, STROKE, left + STROKE, X_HEIGHT - STROKE)
    add_rect(pen, left, mid_y, right - STROKE, mid_y + STROKE)
    add_rect(pen, right - STROKE, mid_y + STROKE, right, X_HEIGHT)


def draw_box_r(glyph) -> None:
    left = GRID * 2
    stem_right = left + STROKE
    shoulder_right = stem_right + GRID * 8
    nub_left = shoulder_right - STROKE
    shoulder_bottom = GRID * 12
    clear_glyph(glyph)
    pen = glyph.getPen()
    add_rect(pen, left, 0, stem_right, X_HEIGHT)
    add_rect(pen, stem_right, X_HEIGHT - STROKE, shoulder_right, X_HEIGHT)
    add_rect(pen, nub_left, shoulder_bottom, shoulder_right, X_HEIGHT)


def draw_box_n(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    clear_glyph(glyph)
    pen = glyph.getPen()
    add_rect(pen, left, 0, left + STROKE, X_HEIGHT)
    add_rect(pen, right - STROKE, 0, right, X_HEIGHT)
    add_rect(pen, left + STROKE, X_HEIGHT - STROKE, right - STROKE, X_HEIGHT)


def draw_box_u(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    clear_glyph(glyph)
    pen = glyph.getPen()
    add_rect(pen, left, STROKE, left + STROKE, X_HEIGHT)
    add_rect(pen, right - STROKE, STROKE, right, X_HEIGHT)
    add_rect(pen, left, 0, right, STROKE)


def draw_box_h(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    clear_glyph(glyph)
    pen = glyph.getPen()
    add_rect(pen, left, 0, left + STROKE, ASCENDER)
    add_rect(pen, right - STROKE, 0, right, X_HEIGHT)
    add_rect(pen, left + STROKE, X_HEIGHT - STROKE, right - STROKE, X_HEIGHT)


def draw_box_m(glyph) -> None:
    left = GRID * 3
    width = int(glyph.width)
    right = width - GRID * 3
    inner_width = right - left
    gap = GRID * 2
    stem_width = STROKE
    bridge = (inner_width - stem_width * 3 - gap * 2) // 2
    mid_left = left + stem_width + bridge + gap
    right_stem_left = mid_left + stem_width + bridge + gap

    clear_glyph(glyph)
    pen = glyph.getPen()
    add_rect(pen, left, 0, left + stem_width, X_HEIGHT)
    add_rect(pen, mid_left, 0, mid_left + stem_width, X_HEIGHT)
    add_rect(pen, right_stem_left, 0, right_stem_left + stem_width, X_HEIGHT)
    add_rect(pen, left + stem_width, X_HEIGHT - STROKE, mid_left, X_HEIGHT)
    add_rect(pen, mid_left + stem_width, X_HEIGHT - STROKE, right_stem_left, X_HEIGHT)


def draw_box_b(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    clear_glyph(glyph)
    pen = glyph.getPen()
    add_rect(pen, left, 0, left + STROKE, ASCENDER)
    add_rect(pen, left, 0, right, STROKE)
    add_rect(pen, left, X_HEIGHT - STROKE, right, X_HEIGHT)
    add_rect(pen, right - STROKE, STROKE, right, X_HEIGHT - STROKE)


def draw_box_d(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    clear_glyph(glyph)
    pen = glyph.getPen()
    add_rect(pen, left, 0, right, STROKE)
    add_rect(pen, left, X_HEIGHT - STROKE, right, X_HEIGHT)
    add_rect(pen, left, STROKE, left + STROKE, X_HEIGHT - STROKE)
    add_rect(pen, right - STROKE, 0, right, ASCENDER)


def draw_box_p(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    clear_glyph(glyph)
    pen = glyph.getPen()
    add_rect(pen, left, 0, right, STROKE)
    add_rect(pen, left, X_HEIGHT - STROKE, right, X_HEIGHT)
    add_rect(pen, left, DESCENDER, left + STROKE, X_HEIGHT)
    add_rect(pen, right - STROKE, STROKE, right, X_HEIGHT - STROKE)


def draw_box_q(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    clear_glyph(glyph)
    pen = glyph.getPen()
    add_rect(pen, left, 0, right, STROKE)
    add_rect(pen, left, X_HEIGHT - STROKE, right, X_HEIGHT)
    add_rect(pen, left, STROKE, left + STROKE, X_HEIGHT - STROKE)
    add_rect(pen, right - STROKE, DESCENDER, right, X_HEIGHT)


def draw_box_zero(glyph) -> None:
    draw_box_o(glyph, top=CAP_HEIGHT, bottom=0)


def main() -> None:
    build_dir().mkdir(parents=True, exist_ok=True)

    ufos = glyphsLib.load_to_ufos(str(source_glyphs()))
    if not ufos:
        raise RuntimeError("No UFOs were produced from the source Glyphs file")

    ufo = ufos[0]
    ufo.info.familyName = "Open Runde Pixel Family Demo"
    ufo.info.styleName = "Regular"
    ufo.info.styleMapFamilyName = "Open Runde Pixel Family Demo"
    ufo.info.openTypeNamePreferredFamilyName = "Open Runde Pixel Family Demo"
    ufo.info.openTypeNamePreferredSubfamilyName = "Regular"
    ufo.info.postscriptFontName = "OpenRundePixelFamilyDemo-Regular"

    draw_box_o(ufo["o"])
    draw_box_c(ufo["c"])
    draw_box_e(ufo["e"])
    draw_box_r(ufo["r"])
    draw_box_n(ufo["n"])
    draw_box_u(ufo["u"])
    draw_box_h(ufo["h"])
    draw_box_m(ufo["m"])
    draw_box_b(ufo["b"])
    draw_box_d(ufo["d"])
    draw_box_p(ufo["p"])
    draw_box_q(ufo["q"])
    draw_box_zero(ufo["zero"])

    font = compileOTF(ufo)
    font.save(output_otf())

    print(f"Wrote {output_otf()}")


if __name__ == "__main__":
    main()
