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
DOT_BOTTOM = 1792


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def source_glyphs() -> Path:
    return repo_root() / "src" / "glyphs" / "OpenRunde-Regular.glyphs"


def build_dir() -> Path:
    return Path(__file__).resolve().parent / "build"


def output_otf() -> Path:
    return build_dir() / "OpenRunde-PixelCaseDemo-v8-Regular.otf"


def snap_down(value: int) -> int:
    return (value // GRID) * GRID


def snap_nearest(value: float) -> int:
    return int(round(value / GRID) * GRID)


def clear_glyph(glyph) -> None:
    glyph.clearContours()
    glyph.clearComponents()


def add_rect(rects: set[tuple[int, int, int, int]], x0: int, y0: int, x1: int, y1: int) -> None:
    rects.add((x0, y0, x1, y1))


def draw_rects(glyph, rects: set[tuple[int, int, int, int]]) -> None:
    clear_glyph(glyph)
    pen = glyph.getPen()
    for x0, y0, x1, y1 in sorted(rects):
        pen.moveTo((x0, y0))
        pen.lineTo((x1, y0))
        pen.lineTo((x1, y1))
        pen.lineTo((x0, y1))
        pen.closePath()


def add_bitmap(
    rects: set[tuple[int, int, int, int]],
    rows: list[str],
    x_offset: int,
    y_offset: int = 0,
    cell_size: int = GRID,
) -> None:
    row_count = len(rows)
    for row_index, row in enumerate(rows):
        y = y_offset + (row_count - row_index - 1) * cell_size
        for col_index, cell in enumerate(row):
            if cell != "#":
                continue
            x = x_offset + col_index * cell_size
            add_rect(rects, x, y, x + cell_size, y + cell_size)


def macro_x_offset(width: int, cols: int) -> int:
    return snap_nearest((width - cols * STROKE) / 2)


def fit_box(width: int, left_margin: int = GRID * 3, right_margin: int = GRID * 3) -> tuple[int, int]:
    usable = width - left_margin - right_margin
    box_width = max(GRID * 6, (usable // GRID) * GRID)
    return left_margin, left_margin + box_width


def center_stem(width: int) -> tuple[int, int]:
    left = snap_down((width - STROKE) // 2)
    return left, left + STROKE


def stair_points(dx_cells: int, dy_cells: int, prefer_vertical: bool) -> list[tuple[int, int]]:
    abs_dx = abs(dx_cells)
    abs_dy = abs(dy_cells)
    sx = 1 if dx_cells >= 0 else -1
    sy = 1 if dy_cells >= 0 else -1
    x = 0
    y = 0
    err = abs_dx - abs_dy
    points: list[tuple[int, int]] = [(x, y)]

    while x != dx_cells or y != dy_cells:
        e2 = 2 * err
        next_x = x
        next_y = y
        moved_x = False
        moved_y = False

        if e2 > -abs_dy:
            err -= abs_dy
            next_x += sx
            moved_x = True
        if e2 < abs_dx:
            err += abs_dx
            next_y += sy
            moved_y = True

        if moved_x and moved_y:
            if prefer_vertical:
                points.append((x, next_y))
            else:
                points.append((next_x, y))

        x = next_x
        y = next_y
        points.append((x, y))

    deduped: list[tuple[int, int]] = []
    for point in points:
        if not deduped or deduped[-1] != point:
            deduped.append(point)
    return deduped


def add_stair_diag(
    rects: set[tuple[int, int, int, int]],
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    prefer_vertical: bool | None = None,
) -> None:
    dx_cells = int(round((x1 - x0) / GRID))
    dy_cells = int(round((y1 - y0) / GRID))
    if prefer_vertical is None:
        prefer_vertical = abs(dy_cells) >= abs(dx_cells)

    for cx, cy in stair_points(dx_cells, dy_cells, prefer_vertical):
        x = x0 + cx * GRID
        y = y0 + cy * GRID
        add_rect(rects, x, y, x + STROKE, y + STROKE)


def draw_o(glyph, top: int = X_HEIGHT, bottom: int = 0) -> None:
    left, right = fit_box(int(glyph.width))
    rects: set[tuple[int, int, int, int]] = set()
    add_rect(rects, left, bottom, right, bottom + STROKE)
    add_rect(rects, left, top - STROKE, right, top)
    add_rect(rects, left, bottom + STROKE, left + STROKE, top - STROKE)
    add_rect(rects, right - STROKE, bottom + STROKE, right, top - STROKE)
    draw_rects(glyph, rects)


def draw_c(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    rects: set[tuple[int, int, int, int]] = set()
    add_rect(rects, left, 0, right - STROKE, STROKE)
    add_rect(rects, left, X_HEIGHT - STROKE, right - STROKE, X_HEIGHT)
    add_rect(rects, left, STROKE, left + STROKE, X_HEIGHT - STROKE)
    draw_rects(glyph, rects)


def draw_e(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    mid_y = GRID * 10
    rects: set[tuple[int, int, int, int]] = set()
    add_rect(rects, left, 0, right, STROKE)
    add_rect(rects, left, X_HEIGHT - STROKE, right, X_HEIGHT)
    add_rect(rects, left, STROKE, left + STROKE, X_HEIGHT - STROKE)
    add_rect(rects, left, mid_y, right - STROKE, mid_y + STROKE)
    add_rect(rects, right - STROKE, mid_y + STROKE, right, X_HEIGHT)
    draw_rects(glyph, rects)


def draw_a(glyph) -> None:
    rows = [
        ".####.",
        "#....#",
        "#....#",
        ".....#",
        "..####",
        ".#...#",
        ".#...#",
        "..###.",
    ]
    x_offset = macro_x_offset(int(glyph.width), len(rows[0]))
    rects: set[tuple[int, int, int, int]] = set()
    add_bitmap(rects, rows, x_offset, cell_size=STROKE)
    draw_rects(glyph, rects)


def draw_g(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    rects: set[tuple[int, int, int, int]] = set()
    add_rect(rects, left, 0, right, STROKE)
    add_rect(rects, left, X_HEIGHT - STROKE, right, X_HEIGHT)
    add_rect(rects, left, STROKE, left + STROKE, X_HEIGHT - STROKE)
    add_rect(rects, right - STROKE, DESCENDER, right, X_HEIGHT)
    add_rect(rects, left + STROKE, DESCENDER, right, DESCENDER + STROKE)
    draw_rects(glyph, rects)


def draw_r(glyph) -> None:
    left = GRID * 2
    stem_right = left + STROKE
    shoulder_right = stem_right + GRID * 8
    nub_left = shoulder_right - STROKE
    shoulder_bottom = GRID * 12
    rects: set[tuple[int, int, int, int]] = set()
    add_rect(rects, left, 0, stem_right, X_HEIGHT)
    add_rect(rects, stem_right, X_HEIGHT - STROKE, shoulder_right, X_HEIGHT)
    add_rect(rects, nub_left, shoulder_bottom, shoulder_right, X_HEIGHT)
    draw_rects(glyph, rects)


def draw_n(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    rects: set[tuple[int, int, int, int]] = set()
    add_rect(rects, left, 0, left + STROKE, X_HEIGHT)
    add_rect(rects, right - STROKE, 0, right, X_HEIGHT)
    add_rect(rects, left + STROKE, X_HEIGHT - STROKE, right - STROKE, X_HEIGHT)
    draw_rects(glyph, rects)


def draw_u(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    rects: set[tuple[int, int, int, int]] = set()
    add_rect(rects, left, STROKE, left + STROKE, X_HEIGHT)
    add_rect(rects, right - STROKE, STROKE, right, X_HEIGHT)
    add_rect(rects, left, 0, right, STROKE)
    draw_rects(glyph, rects)


def draw_h(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    rects: set[tuple[int, int, int, int]] = set()
    add_rect(rects, left, 0, left + STROKE, ASCENDER)
    add_rect(rects, right - STROKE, 0, right, X_HEIGHT)
    add_rect(rects, left + STROKE, X_HEIGHT - STROKE, right - STROKE, X_HEIGHT)
    draw_rects(glyph, rects)


def draw_m(glyph) -> None:
    left = GRID * 3
    width = int(glyph.width)
    right = width - GRID * 3
    inner_width = right - left
    gap = GRID * 2
    stem_width = STROKE
    bridge = (inner_width - stem_width * 3 - gap * 2) // 2
    mid_left = left + stem_width + bridge + gap
    right_stem_left = mid_left + stem_width + bridge + gap
    rects: set[tuple[int, int, int, int]] = set()
    add_rect(rects, left, 0, left + stem_width, X_HEIGHT)
    add_rect(rects, mid_left, 0, mid_left + stem_width, X_HEIGHT)
    add_rect(rects, right_stem_left, 0, right_stem_left + stem_width, X_HEIGHT)
    add_rect(rects, left + stem_width, X_HEIGHT - STROKE, mid_left, X_HEIGHT)
    add_rect(rects, mid_left + stem_width, X_HEIGHT - STROKE, right_stem_left, X_HEIGHT)
    draw_rects(glyph, rects)


def draw_b(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    rects: set[tuple[int, int, int, int]] = set()
    add_rect(rects, left, 0, left + STROKE, ASCENDER)
    add_rect(rects, left, 0, right, STROKE)
    add_rect(rects, left, X_HEIGHT - STROKE, right, X_HEIGHT)
    add_rect(rects, right - STROKE, STROKE, right, X_HEIGHT - STROKE)
    draw_rects(glyph, rects)


def draw_d(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    rects: set[tuple[int, int, int, int]] = set()
    add_rect(rects, left, 0, right, STROKE)
    add_rect(rects, left, X_HEIGHT - STROKE, right, X_HEIGHT)
    add_rect(rects, left, STROKE, left + STROKE, X_HEIGHT - STROKE)
    add_rect(rects, right - STROKE, 0, right, ASCENDER)
    draw_rects(glyph, rects)


def draw_p(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    rects: set[tuple[int, int, int, int]] = set()
    add_rect(rects, left, 0, right, STROKE)
    add_rect(rects, left, X_HEIGHT - STROKE, right, X_HEIGHT)
    add_rect(rects, left, DESCENDER, left + STROKE, X_HEIGHT)
    add_rect(rects, right - STROKE, STROKE, right, X_HEIGHT - STROKE)
    draw_rects(glyph, rects)


def draw_q(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    rects: set[tuple[int, int, int, int]] = set()
    add_rect(rects, left, 0, right, STROKE)
    add_rect(rects, left, X_HEIGHT - STROKE, right, X_HEIGHT)
    add_rect(rects, left, STROKE, left + STROKE, X_HEIGHT - STROKE)
    add_rect(rects, right - STROKE, DESCENDER, right, X_HEIGHT)
    draw_rects(glyph, rects)


def draw_i(glyph) -> None:
    width = int(glyph.width)
    stem_left, stem_right = center_stem(width)
    rects: set[tuple[int, int, int, int]] = set()
    add_rect(rects, stem_left, 0, stem_right, X_HEIGHT)
    add_rect(rects, stem_left, DOT_BOTTOM, stem_right, DOT_BOTTOM + STROKE)
    draw_rects(glyph, rects)


def draw_j(glyph) -> None:
    width = int(glyph.width)
    stem_left, stem_right = center_stem(width)
    rects: set[tuple[int, int, int, int]] = set()
    add_rect(rects, stem_left, DESCENDER, stem_right, X_HEIGHT)
    add_rect(rects, stem_left, DOT_BOTTOM, stem_right, DOT_BOTTOM + STROKE)
    draw_rects(glyph, rects)


def draw_l(glyph) -> None:
    width = int(glyph.width)
    stem_left, stem_right = center_stem(width)
    rects: set[tuple[int, int, int, int]] = set()
    add_rect(rects, stem_left, 0, stem_right, ASCENDER)
    draw_rects(glyph, rects)


def draw_t(glyph) -> None:
    width = int(glyph.width)
    stem_left, stem_right = center_stem(width)
    left, right = fit_box(width, GRID * 2, GRID * 2)
    cross_y = X_HEIGHT - STROKE
    rects: set[tuple[int, int, int, int]] = set()
    add_rect(rects, stem_left, 0, stem_right, ASCENDER)
    add_rect(rects, left, cross_y, right, cross_y + STROKE)
    draw_rects(glyph, rects)


def draw_f(glyph) -> None:
    width = int(glyph.width)
    stem_left = GRID * 2
    stem_right = stem_left + STROKE
    left, right = fit_box(width, GRID, GRID)
    cross_y = GRID * 10
    rects: set[tuple[int, int, int, int]] = set()
    add_rect(rects, stem_left, 0, stem_right, ASCENDER)
    add_rect(rects, left, ASCENDER - STROKE, right, ASCENDER)
    add_rect(rects, left, cross_y, right - STROKE, cross_y + STROKE)
    draw_rects(glyph, rects)


def draw_k(glyph) -> None:
    rows = [
        "#....#",
        "#...#.",
        "#..#..",
        "#.#...",
        "##....",
        "##....",
        "#.#...",
        "#..#..",
        "#...#.",
        "#....#",
    ]
    x_offset = macro_x_offset(int(glyph.width), len(rows[0]))
    rects: set[tuple[int, int, int, int]] = set()
    add_bitmap(rects, rows, x_offset, y_offset=GRID, cell_size=STROKE)
    draw_rects(glyph, rects)


def draw_s(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    mid_y = GRID * 10
    rects: set[tuple[int, int, int, int]] = set()
    add_rect(rects, left, X_HEIGHT - STROKE, right, X_HEIGHT)
    add_rect(rects, left, mid_y, right, mid_y + STROKE)
    add_rect(rects, left, 0, right, STROKE)
    add_rect(rects, left, mid_y + STROKE, left + STROKE, X_HEIGHT - STROKE)
    add_rect(rects, right - STROKE, STROKE, right, mid_y)
    draw_rects(glyph, rects)


def draw_v(glyph) -> None:
    rows = [
        "#.....#",
        "#.....#",
        ".#...#.",
        ".#...#.",
        "..#.#..",
        "..#.#..",
        "...#...",
        "...#...",
    ]
    x_offset = macro_x_offset(int(glyph.width), len(rows[0]))
    rects: set[tuple[int, int, int, int]] = set()
    add_bitmap(rects, rows, x_offset, cell_size=STROKE)
    draw_rects(glyph, rects)


def draw_w(glyph) -> None:
    rows = [
        "#.........#",
        "#.........#",
        ".#.......#.",
        ".#...#...#.",
        "..#.#.#.#..",
        "..#.#.#.#..",
        "...#...#...",
        "...#...#...",
    ]
    x_offset = macro_x_offset(int(glyph.width), len(rows[0]))
    rects: set[tuple[int, int, int, int]] = set()
    add_bitmap(rects, rows, x_offset, cell_size=STROKE)
    draw_rects(glyph, rects)


def draw_x(glyph) -> None:
    rows = [
        "#.....#",
        "#.....#",
        ".#...#.",
        "..#.#..",
        "...#...",
        "..#.#..",
        ".#...#.",
        "#.....#",
    ]
    x_offset = macro_x_offset(int(glyph.width), len(rows[0]))
    rects: set[tuple[int, int, int, int]] = set()
    add_bitmap(rects, rows, x_offset, cell_size=STROKE)
    draw_rects(glyph, rects)


def draw_y(glyph) -> None:
    rows = [
        "#.....#",
        "#.....#",
        ".#...#.",
        ".#...#.",
        "..#.#..",
        "...#...",
        "...#...",
        "...#...",
        "...#...",
        "...#...",
        "...#...",
    ]
    x_offset = macro_x_offset(int(glyph.width), len(rows[0]))
    rects: set[tuple[int, int, int, int]] = set()
    add_bitmap(rects, rows, x_offset, y_offset=DESCENDER, cell_size=STROKE)
    draw_rects(glyph, rects)


def draw_z(glyph) -> None:
    rows = [
        "######",
        ".....#",
        "....#.",
        "...#..",
        "..#...",
        ".#....",
        "#.....",
        "######",
    ]
    x_offset = macro_x_offset(int(glyph.width), len(rows[0]))
    rects: set[tuple[int, int, int, int]] = set()
    add_bitmap(rects, rows, x_offset, cell_size=STROKE)
    draw_rects(glyph, rects)


def draw_zero(glyph) -> None:
    draw_o(glyph, top=CAP_HEIGHT, bottom=0)


def draw_cap_c(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    rects: set[tuple[int, int, int, int]] = set()
    add_rect(rects, left, 0, right - STROKE, STROKE)
    add_rect(rects, left, CAP_HEIGHT - STROKE, right - STROKE, CAP_HEIGHT)
    add_rect(rects, left, STROKE, left + STROKE, CAP_HEIGHT - STROKE)
    draw_rects(glyph, rects)


def draw_cap_d(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    rects: set[tuple[int, int, int, int]] = set()
    add_rect(rects, left, 0, right, STROKE)
    add_rect(rects, left, CAP_HEIGHT - STROKE, right, CAP_HEIGHT)
    add_rect(rects, left, STROKE, left + STROKE, CAP_HEIGHT - STROKE)
    add_rect(rects, right - STROKE, STROKE, right, CAP_HEIGHT - STROKE)
    draw_rects(glyph, rects)


def draw_cap_e(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    mid_y = snap_nearest((CAP_HEIGHT - STROKE) / 2)
    rects: set[tuple[int, int, int, int]] = set()
    add_rect(rects, left, 0, right, STROKE)
    add_rect(rects, left, CAP_HEIGHT - STROKE, right, CAP_HEIGHT)
    add_rect(rects, left, STROKE, left + STROKE, CAP_HEIGHT - STROKE)
    add_rect(rects, left, mid_y, right - STROKE, mid_y + STROKE)
    draw_rects(glyph, rects)


def draw_cap_f(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    mid_y = snap_nearest((CAP_HEIGHT - STROKE) / 2)
    rects: set[tuple[int, int, int, int]] = set()
    add_rect(rects, left, STROKE, left + STROKE, CAP_HEIGHT)
    add_rect(rects, left, CAP_HEIGHT - STROKE, right, CAP_HEIGHT)
    add_rect(rects, left, mid_y, right - STROKE, mid_y + STROKE)
    draw_rects(glyph, rects)


def draw_cap_g(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    mid_y = snap_nearest((CAP_HEIGHT - STROKE) / 2)
    mid_left = snap_nearest((left + right) / 2)
    rects: set[tuple[int, int, int, int]] = set()
    add_rect(rects, left, 0, right, STROKE)
    add_rect(rects, left, CAP_HEIGHT - STROKE, right, CAP_HEIGHT)
    add_rect(rects, left, STROKE, left + STROKE, CAP_HEIGHT - STROKE)
    add_rect(rects, right - STROKE, STROKE, right, mid_y)
    add_rect(rects, mid_left, mid_y, right, mid_y + STROKE)
    draw_rects(glyph, rects)


def draw_cap_h(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    mid_y = snap_nearest((CAP_HEIGHT - STROKE) / 2)
    rects: set[tuple[int, int, int, int]] = set()
    add_rect(rects, left, 0, left + STROKE, CAP_HEIGHT)
    add_rect(rects, right - STROKE, 0, right, CAP_HEIGHT)
    add_rect(rects, left + STROKE, mid_y, right - STROKE, mid_y + STROKE)
    draw_rects(glyph, rects)


def draw_cap_i(glyph) -> None:
    stem_left, stem_right = center_stem(int(glyph.width))
    rects: set[tuple[int, int, int, int]] = set()
    add_rect(rects, stem_left, 0, stem_right, CAP_HEIGHT)
    draw_rects(glyph, rects)


def draw_cap_j(glyph) -> None:
    left, right = fit_box(int(glyph.width), GRID * 2, GRID * 2)
    stem_left = right - STROKE
    rects: set[tuple[int, int, int, int]] = set()
    add_rect(rects, left, CAP_HEIGHT - STROKE, right, CAP_HEIGHT)
    add_rect(rects, stem_left, STROKE, right, CAP_HEIGHT - STROKE)
    add_rect(rects, left, 0, right, STROKE)
    draw_rects(glyph, rects)


def draw_cap_l(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    rects: set[tuple[int, int, int, int]] = set()
    add_rect(rects, left, 0, right, STROKE)
    add_rect(rects, left, STROKE, left + STROKE, CAP_HEIGHT)
    draw_rects(glyph, rects)


def draw_cap_p(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    mid_y = snap_nearest((CAP_HEIGHT - STROKE) / 2)
    rects: set[tuple[int, int, int, int]] = set()
    add_rect(rects, left, 0, left + STROKE, CAP_HEIGHT)
    add_rect(rects, left, CAP_HEIGHT - STROKE, right, CAP_HEIGHT)
    add_rect(rects, left, mid_y, right, mid_y + STROKE)
    add_rect(rects, right - STROKE, mid_y + STROKE, right, CAP_HEIGHT - STROKE)
    draw_rects(glyph, rects)


def draw_cap_q(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    rects: set[tuple[int, int, int, int]] = set()
    add_rect(rects, left, 0, right, STROKE)
    add_rect(rects, left, CAP_HEIGHT - STROKE, right, CAP_HEIGHT)
    add_rect(rects, left, STROKE, left + STROKE, CAP_HEIGHT - STROKE)
    add_rect(rects, right - STROKE, STROKE, right, CAP_HEIGHT - STROKE)
    add_rect(rects, right - STROKE, DESCENDER, right, STROKE)
    draw_rects(glyph, rects)


def draw_cap_s(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    mid_y = snap_nearest((CAP_HEIGHT - STROKE) / 2)
    rects: set[tuple[int, int, int, int]] = set()
    add_rect(rects, left, CAP_HEIGHT - STROKE, right, CAP_HEIGHT)
    add_rect(rects, left, mid_y, right, mid_y + STROKE)
    add_rect(rects, left, 0, right, STROKE)
    add_rect(rects, left, mid_y + STROKE, left + STROKE, CAP_HEIGHT - STROKE)
    add_rect(rects, right - STROKE, STROKE, right, mid_y)
    draw_rects(glyph, rects)


def draw_cap_t(glyph) -> None:
    stem_left, stem_right = center_stem(int(glyph.width))
    left, right = fit_box(int(glyph.width), GRID * 2, GRID * 2)
    rects: set[tuple[int, int, int, int]] = set()
    add_rect(rects, stem_left, 0, stem_right, CAP_HEIGHT)
    add_rect(rects, left, CAP_HEIGHT - STROKE, right, CAP_HEIGHT)
    draw_rects(glyph, rects)


def draw_cap_u(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    rects: set[tuple[int, int, int, int]] = set()
    add_rect(rects, left, STROKE, left + STROKE, CAP_HEIGHT)
    add_rect(rects, right - STROKE, STROKE, right, CAP_HEIGHT)
    add_rect(rects, left, 0, right, STROKE)
    draw_rects(glyph, rects)


def draw_cap_b(glyph) -> None:
    left, right = fit_box(int(glyph.width))
    mid_y = snap_nearest((CAP_HEIGHT - STROKE) / 2)
    rects: set[tuple[int, int, int, int]] = set()
    add_rect(rects, left, 0, left + STROKE, CAP_HEIGHT)
    add_rect(rects, left, 0, right, STROKE)
    add_rect(rects, left, mid_y, right, mid_y + STROKE)
    add_rect(rects, left, CAP_HEIGHT - STROKE, right, CAP_HEIGHT)
    add_rect(rects, right - STROKE, STROKE, right, mid_y)
    add_rect(rects, right - STROKE, mid_y + STROKE, right, CAP_HEIGHT - STROKE)
    draw_rects(glyph, rects)


def draw_cap_a(glyph) -> None:
    rows = [
        "...##...",
        "..#..#..",
        ".#....#.",
        "#......#",
        "#......#",
        "########",
        "#......#",
        "#......#",
        "#......#",
        "#......#",
    ]
    rects: set[tuple[int, int, int, int]] = set()
    add_bitmap(rects, rows, macro_x_offset(int(glyph.width), len(rows[0])), y_offset=GRID, cell_size=STROKE)
    draw_rects(glyph, rects)


def draw_cap_k(glyph) -> None:
    rows = [
        "#.....#",
        "#....#.",
        "#...#..",
        "#..#...",
        "###....",
        "#..#...",
        "#...#..",
        "#....#.",
        "#.....#",
        "#.....#",
    ]
    rects: set[tuple[int, int, int, int]] = set()
    add_bitmap(rects, rows, macro_x_offset(int(glyph.width), len(rows[0])), y_offset=GRID, cell_size=STROKE)
    draw_rects(glyph, rects)


def draw_cap_m(glyph) -> None:
    rows = [
        "#........#",
        "##......##",
        "#.#....#.#",
        "#..#..#..#",
        "#...##...#",
        "#........#",
        "#........#",
        "#........#",
        "#........#",
        "#........#",
    ]
    rects: set[tuple[int, int, int, int]] = set()
    add_bitmap(rects, rows, macro_x_offset(int(glyph.width), len(rows[0])), y_offset=GRID, cell_size=STROKE)
    draw_rects(glyph, rects)


def draw_cap_n(glyph) -> None:
    rows = [
        "#......#",
        "##.....#",
        "#.#....#",
        "#..#...#",
        "#...#..#",
        "#....#.#",
        "#.....##",
        "#......#",
        "#......#",
        "#......#",
    ]
    rects: set[tuple[int, int, int, int]] = set()
    add_bitmap(rects, rows, macro_x_offset(int(glyph.width), len(rows[0])), y_offset=GRID, cell_size=STROKE)
    draw_rects(glyph, rects)


def draw_cap_r(glyph) -> None:
    rows = [
        "#####.",
        "#....#",
        "#....#",
        "#....#",
        "#####.",
        "#.#...",
        "#..#..",
        "#...#.",
        "#....#",
        "#.....",
    ]
    rects: set[tuple[int, int, int, int]] = set()
    add_bitmap(rects, rows, macro_x_offset(int(glyph.width), len(rows[0])), y_offset=GRID, cell_size=STROKE)
    draw_rects(glyph, rects)


def draw_cap_v(glyph) -> None:
    rows = [
        "#......#",
        "#......#",
        "#......#",
        ".#....#.",
        ".#....#.",
        "..#..#..",
        "..#..#..",
        "...##...",
        "...##...",
        "...##...",
    ]
    rects: set[tuple[int, int, int, int]] = set()
    add_bitmap(rects, rows, macro_x_offset(int(glyph.width), len(rows[0])), y_offset=GRID, cell_size=STROKE)
    draw_rects(glyph, rects)


def draw_cap_w(glyph) -> None:
    rows = [
        "#..........#",
        "#..........#",
        "#..........#",
        ".#........#.",
        ".#...##...#.",
        "..#..##..#..",
        "..#.#..#.#..",
        "...##..##...",
        "...#....#...",
        "...#....#...",
    ]
    rects: set[tuple[int, int, int, int]] = set()
    add_bitmap(rects, rows, macro_x_offset(int(glyph.width), len(rows[0])), y_offset=GRID, cell_size=STROKE)
    draw_rects(glyph, rects)


def draw_cap_x(glyph) -> None:
    rows = [
        "#......#",
        "#......#",
        ".#....#.",
        "..#..#..",
        "...##...",
        "...##...",
        "..#..#..",
        ".#....#.",
        "#......#",
        "#......#",
    ]
    rects: set[tuple[int, int, int, int]] = set()
    add_bitmap(rects, rows, macro_x_offset(int(glyph.width), len(rows[0])), y_offset=GRID, cell_size=STROKE)
    draw_rects(glyph, rects)


def draw_cap_y(glyph) -> None:
    rows = [
        "#......#",
        "#......#",
        ".#....#.",
        "..#..#..",
        "...##...",
        "...##...",
        "...##...",
        "...##...",
        "...##...",
        "...##...",
    ]
    rects: set[tuple[int, int, int, int]] = set()
    add_bitmap(rects, rows, macro_x_offset(int(glyph.width), len(rows[0])), y_offset=GRID, cell_size=STROKE)
    draw_rects(glyph, rects)


def draw_cap_z(glyph) -> None:
    rows = [
        "########",
        "......#.",
        ".....#..",
        "....#...",
        "...#....",
        "..#.....",
        ".#......",
        "#.......",
        "#.......",
        "########",
    ]
    rects: set[tuple[int, int, int, int]] = set()
    add_bitmap(rects, rows, macro_x_offset(int(glyph.width), len(rows[0])), y_offset=GRID, cell_size=STROKE)
    draw_rects(glyph, rects)


def main() -> None:
    build_dir().mkdir(parents=True, exist_ok=True)

    ufos = glyphsLib.load_to_ufos(str(source_glyphs()))
    if not ufos:
        raise RuntimeError("No UFOs were produced from the source Glyphs file")

    ufo = ufos[0]
    ufo.info.familyName = "Open Runde Pixel Case Demo v8"
    ufo.info.styleName = "Regular"
    ufo.info.styleMapFamilyName = "Open Runde Pixel Case Demo v8"
    ufo.info.openTypeNamePreferredFamilyName = "Open Runde Pixel Case Demo v8"
    ufo.info.openTypeNamePreferredSubfamilyName = "Regular"
    ufo.info.postscriptFontName = "OpenRundePixelCaseDemoV8-Regular"

    draw_a(ufo["a"])
    draw_b(ufo["b"])
    draw_c(ufo["c"])
    draw_d(ufo["d"])
    draw_e(ufo["e"])
    draw_f(ufo["f"])
    draw_g(ufo["g"])
    draw_h(ufo["h"])
    draw_i(ufo["i"])
    draw_j(ufo["j"])
    draw_k(ufo["k"])
    draw_l(ufo["l"])
    draw_m(ufo["m"])
    draw_n(ufo["n"])
    draw_o(ufo["o"])
    draw_p(ufo["p"])
    draw_q(ufo["q"])
    draw_r(ufo["r"])
    draw_s(ufo["s"])
    draw_t(ufo["t"])
    draw_u(ufo["u"])
    draw_v(ufo["v"])
    draw_w(ufo["w"])
    draw_x(ufo["x"])
    draw_y(ufo["y"])
    draw_z(ufo["z"])
    draw_zero(ufo["zero"])

    draw_cap_a(ufo["A"])
    draw_cap_b(ufo["B"])
    draw_cap_c(ufo["C"])
    draw_cap_d(ufo["D"])
    draw_cap_e(ufo["E"])
    draw_cap_f(ufo["F"])
    draw_cap_g(ufo["G"])
    draw_cap_h(ufo["H"])
    draw_cap_i(ufo["I"])
    draw_cap_j(ufo["J"])
    draw_cap_k(ufo["K"])
    draw_cap_l(ufo["L"])
    draw_cap_m(ufo["M"])
    draw_cap_n(ufo["N"])
    draw_o(ufo["O"], top=CAP_HEIGHT, bottom=0)
    draw_cap_p(ufo["P"])
    draw_cap_q(ufo["Q"])
    draw_cap_r(ufo["R"])
    draw_cap_s(ufo["S"])
    draw_cap_t(ufo["T"])
    draw_cap_u(ufo["U"])
    draw_cap_v(ufo["V"])
    draw_cap_w(ufo["W"])
    draw_cap_x(ufo["X"])
    draw_cap_y(ufo["Y"])
    draw_cap_z(ufo["Z"])

    font = compileOTF(ufo)
    font.save(output_otf())

    print(f"Wrote {output_otf()}")


if __name__ == "__main__":
    main()
