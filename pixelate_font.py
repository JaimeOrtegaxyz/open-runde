"""
Generate pixelated versions of Open Runde.

Rasterizes each glyph outline onto a grid, applies shape-aware corrections
(symmetry, border smoothing with counter protection), converts to merged
rectangles, and rebuilds CFF charstrings. All metrics preserved for swappability.
"""

import os
import math
from collections import deque
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from PIL import Image, ImageDraw


# ── Configuration ──────────────────────────────────────────────────────────────

GRID = 256           # pixel size in font units
SUPERSAMPLE = 8      # 8x supersampling for accurate coverage
GRID_Y_MIN = -768    # floor(descender / GRID) * GRID
GRID_Y_MAX = 2816    # UPM, snapped to grid
GRID_ROWS = (GRID_Y_MAX - GRID_Y_MIN) // GRID
THRESHOLD = 0.5      # coverage threshold (>=)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DESKTOP = os.path.join(BASE_DIR, "src", "desktop")
SRC_WEB = os.path.join(BASE_DIR, "src", "web")
OUT_DIR = os.path.join(BASE_DIR, "test_output")

WEIGHTS = ["Regular", "Medium", "Semibold", "Bold"]


# ── Bezier flattening ─────────────────────────────────────────────────────────

def flatten_cubic(p0, p1, p2, p3, tolerance=0.5):
    dx = p3[0] - p0[0]
    dy = p3[1] - p0[1]
    d = max(
        abs((p1[0] - p3[0]) * dy - (p1[1] - p3[1]) * dx),
        abs((p2[0] - p3[0]) * dy - (p2[1] - p3[1]) * dx),
    )
    if d * d <= tolerance * tolerance * (dx * dx + dy * dy):
        return [p3]
    m01 = ((p0[0]+p1[0])/2, (p0[1]+p1[1])/2)
    m12 = ((p1[0]+p2[0])/2, (p1[1]+p2[1])/2)
    m23 = ((p2[0]+p3[0])/2, (p2[1]+p3[1])/2)
    m012 = ((m01[0]+m12[0])/2, (m01[1]+m12[1])/2)
    m123 = ((m12[0]+m23[0])/2, (m12[1]+m23[1])/2)
    mid = ((m012[0]+m123[0])/2, (m012[1]+m123[1])/2)
    return flatten_cubic(p0, m01, m012, mid, tolerance) + \
           flatten_cubic(mid, m123, m23, p3, tolerance)


def flatten_quadratic(p0, p1, p2, tolerance=0.5):
    dx = p2[0] - p0[0]
    dy = p2[1] - p0[1]
    d = abs((p1[0] - p2[0]) * dy - (p1[1] - p2[1]) * dx)
    if d * d <= tolerance * tolerance * (dx * dx + dy * dy):
        return [p2]
    m01 = ((p0[0]+p1[0])/2, (p0[1]+p1[1])/2)
    m12 = ((p1[0]+p2[0])/2, (p1[1]+p2[1])/2)
    mid = ((m01[0]+m12[0])/2, (m01[1]+m12[1])/2)
    return flatten_quadratic(p0, m01, mid, tolerance) + \
           flatten_quadratic(mid, m12, p2, tolerance)


# ── Rasterization ─────────────────────────────────────────────────────────────

def extract_contours(operations):
    contours = []
    current = []
    for op, args in operations:
        if op == 'moveTo':
            if current:
                contours.append(current)
            current = [args[0]]
        elif op == 'lineTo':
            current.append(args[0])
        elif op == 'curveTo':
            if current:
                pts = flatten_cubic(current[-1], args[0], args[1], args[2])
                current.extend(pts)
        elif op == 'qCurveTo':
            if current:
                off_curves = list(args[:-1])
                on_curve = args[-1]
                if len(off_curves) == 1:
                    pts = flatten_quadratic(current[-1], off_curves[0], on_curve)
                    current.extend(pts)
                else:
                    p0 = current[-1]
                    for i, oc in enumerate(off_curves):
                        if i < len(off_curves) - 1:
                            next_oc = off_curves[i + 1]
                            implied = ((oc[0]+next_oc[0])/2, (oc[1]+next_oc[1])/2)
                            pts = flatten_quadratic(p0, oc, implied)
                            current.extend(pts)
                            p0 = implied
                        else:
                            pts = flatten_quadratic(p0, oc, on_curve)
                            current.extend(pts)
        elif op in ('closePath', 'endPath'):
            if current:
                contours.append(current)
            current = []
    if current:
        contours.append(current)
    return contours


def rasterize_glyph(operations, advance_width):
    """
    Rasterize glyph outline onto the pixel grid.
    Returns (binary, coverage) — both as (grid_rows, grid_cols) arrays.
    """
    grid_cols = max(1, math.ceil(advance_width / GRID))
    img_w = grid_cols * SUPERSAMPLE
    img_h = GRID_ROWS * SUPERSAMPLE

    if not operations:
        empty = np.zeros((GRID_ROWS, grid_cols))
        return empty >= THRESHOLD, empty

    contours = extract_contours(operations)
    if not contours:
        empty = np.zeros((GRID_ROWS, grid_cols))
        return empty >= THRESHOLD, empty

    scale = SUPERSAMPLE / GRID

    def to_pixel(pt):
        return (pt[0] * scale, img_h - (pt[1] - GRID_Y_MIN) * scale)

    result = np.zeros((img_h, img_w), dtype=np.uint8)

    for contour in contours:
        if len(contour) < 3:
            continue
        polygon = [to_pixel(pt) for pt in contour]
        flat = []
        for pt in polygon:
            flat.extend(pt)
        if len(flat) < 6:
            continue
        layer = Image.new('L', (img_w, img_h), 0)
        draw = ImageDraw.Draw(layer)
        draw.polygon(flat, fill=255)
        layer_arr = np.array(layer, dtype=np.uint8)
        filled_mask = layer_arr > 127
        result = np.where(filled_mask, 255 - result, result)

    pad_h = GRID_ROWS * SUPERSAMPLE - result.shape[0]
    pad_w = grid_cols * SUPERSAMPLE - result.shape[1]
    if pad_h > 0 or pad_w > 0:
        result = np.pad(result, ((0, max(0, pad_h)), (0, max(0, pad_w))))

    result = result[:GRID_ROWS * SUPERSAMPLE, :grid_cols * SUPERSAMPLE]
    blocks = result.reshape(GRID_ROWS, SUPERSAMPLE, grid_cols, SUPERSAMPLE)
    coverage = blocks.mean(axis=(1, 3)) / 255.0

    binary = coverage >= THRESHOLD
    return binary, coverage


# ── Shape corrections ─────────────────────────────────────────────────────────

def correct_shapes(binary, coverage):
    """
    Post-process the binary pixel grid for shape quality.
    Three passes, each conservative and well-targeted:
      1. Vertical symmetry (left-right mirror)
      2. Horizontal symmetry (top-bottom mirror)
      3. Border smoothing with counter protection
    """
    binary = enforce_symmetry(binary, coverage, flip_axis=1)
    binary = enforce_symmetry(binary, coverage, flip_axis=0)
    binary = smooth_border(binary, coverage)
    return binary


def enforce_symmetry(binary, coverage, flip_axis):
    """
    If the glyph is nearly symmetric along the given axis, make it exactly
    symmetric using confidence-based voting.

    For each asymmetric pixel pair, the pixel with higher confidence
    (further from the threshold) determines the state of both.
    This avoids making shapes gratuitously bolder or thinner.

    flip_axis=1: vertical (left-right), flip_axis=0: horizontal (top-bottom)
    """
    rows, cols = binary.shape

    # Find bounding box of filled pixels
    filled_rows = np.any(binary, axis=1)
    filled_cols = np.any(binary, axis=0)
    if not filled_rows.any() or not filled_cols.any():
        return binary

    r0 = np.argmax(filled_rows)
    r1 = rows - np.argmax(filled_rows[::-1])
    c0 = np.argmax(filled_cols)
    c1 = cols - np.argmax(filled_cols[::-1])

    bb_cov = coverage[r0:r1, c0:c1]
    bb_bin = binary[r0:r1, c0:c1]
    bb_h, bb_w = bb_cov.shape

    if (flip_axis == 1 and bb_w < 2) or (flip_axis == 0 and bb_h < 2):
        return binary

    # Check if the glyph is symmetric: compare coverage with its mirror
    flipped_cov = np.flip(bb_cov, axis=flip_axis)
    mask = (bb_cov > 0.05) | (flipped_cov > 0.05)
    if mask.sum() == 0:
        return binary

    diff = np.abs(bb_cov - flipped_cov)
    mean_diff = diff[mask].mean()

    if mean_diff > 0.15:
        return binary

    # Symmetric! Use confidence-based voting for each asymmetric pixel pair
    flipped_bin = np.flip(bb_bin, axis=flip_axis)
    new_bb = bb_bin.copy()

    dim = bb_w if flip_axis == 1 else bb_h
    half = dim // 2

    for idx in range(half):
        if flip_axis == 1:
            mirror_idx = bb_w - 1 - idx
            slice_a = (slice(None), idx)
            slice_b = (slice(None), mirror_idx)
        else:
            mirror_idx = bb_h - 1 - idx
            slice_a = (idx, slice(None))
            slice_b = (mirror_idx, slice(None))

        a_bin = bb_bin[slice_a]
        b_bin = bb_bin[slice_b]
        a_cov = bb_cov[slice_a]
        b_cov = bb_cov[slice_b]

        # Only fix pixels where the two sides disagree
        disagree = a_bin != b_bin

        if not disagree.any():
            continue

        # Confidence = distance from threshold
        a_conf = np.abs(a_cov - THRESHOLD)
        b_conf = np.abs(b_cov - THRESHOLD)

        # The more confident pixel wins
        a_wins = a_conf >= b_conf

        resolved = np.where(a_wins, a_bin, b_bin)

        new_bb[slice_a] = np.where(disagree, resolved, a_bin)
        new_bb[slice_b] = np.where(disagree, resolved, b_bin)

    result = binary.copy()
    result[r0:r1, c0:c1] = new_bb
    return result


def find_exterior(binary):
    """
    Flood-fill from grid edges to find all exterior (non-enclosed) empty pixels.
    Returns a boolean array where True = exterior empty space.
    """
    rows, cols = binary.shape
    exterior = np.zeros_like(binary, dtype=bool)
    queue = deque()

    # Seed from all empty edge pixels
    for y in range(rows):
        for x in [0, cols - 1]:
            if not binary[y, x] and not exterior[y, x]:
                exterior[y, x] = True
                queue.append((y, x))
    for x in range(cols):
        for y in [0, rows - 1]:
            if not binary[y, x] and not exterior[y, x]:
                exterior[y, x] = True
                queue.append((y, x))

    # BFS
    while queue:
        y, x = queue.popleft()
        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ny, nx = y + dy, x + dx
            if 0 <= ny < rows and 0 <= nx < cols:
                if not binary[ny, nx] and not exterior[ny, nx]:
                    exterior[ny, nx] = True
                    queue.append((ny, nx))

    return exterior


def is_diagonal_step(binary, y, x):
    """
    Check if this pixel is part of a diagonal staircase.
    A diagonal step has exactly 2 orthogonal neighbors forming an L,
    with the diagonal corner (completing a 2x2 square) being empty.
    """
    rows, cols = binary.shape
    l_patterns = [
        ((-1, 0), (0, -1), (-1, -1)),
        ((-1, 0), (0,  1), (-1,  1)),
        (( 1, 0), (0, -1), ( 1, -1)),
        (( 1, 0), (0,  1), ( 1,  1)),
    ]
    for (dy1, dx1), (dy2, dx2), (dy3, dx3) in l_patterns:
        ny1, nx1 = y + dy1, x + dx1
        ny2, nx2 = y + dy2, x + dx2
        ny3, nx3 = y + dy3, x + dx3
        n1_ok = 0 <= ny1 < rows and 0 <= nx1 < cols and binary[ny1, nx1]
        n2_ok = 0 <= ny2 < rows and 0 <= nx2 < cols and binary[ny2, nx2]
        n3_empty = not (0 <= ny3 < rows and 0 <= nx3 < cols) or not binary[ny3, nx3]
        if n1_ok and n2_ok and n3_empty:
            return True
    return False


def smooth_border(binary, coverage):
    """
    Clean up border pixels with counter protection.

    Rules:
    - Remove bumps: filled pixel with ≤1 orthogonal neighbor AND low coverage
      AND not a diagonal step AND not an isolated component (dot of i, etc.)
    - Fill notches: empty pixel with 3+ orthogonal filled neighbors AND
      decent coverage AND is EXTERIOR (not inside a counter)
    """
    rows, cols = binary.shape
    result = binary.copy()

    for _pass in range(2):
        prev = result.copy()
        exterior = find_exterior(prev)

        for y in range(rows):
            for x in range(cols):
                # Count orthogonal filled neighbors
                n4 = 0
                for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < rows and 0 <= nx < cols and prev[ny, nx]:
                        n4 += 1

                if prev[y, x]:
                    # ── BUMP REMOVAL ──
                    if n4 > 1:
                        continue  # well-connected, not a bump

                    # Only 0 or 1 orthogonal neighbor — potential bump
                    # Don't remove if it's a diagonal step
                    if is_diagonal_step(prev, y, x):
                        continue

                    # Don't remove if it's totally isolated (n4=0 and no diagonal
                    # neighbors) — it might be an intentional dot (i, j, :, etc.)
                    if n4 == 0:
                        diag_neighbors = 0
                        for dy, dx in [(-1,-1),(-1,1),(1,-1),(1,1)]:
                            ny, nx = y + dy, x + dx
                            if 0 <= ny < rows and 0 <= nx < cols and prev[ny, nx]:
                                diag_neighbors += 1
                        if diag_neighbors == 0:
                            continue  # isolated dot, keep it

                    # Remove if coverage is below confidence threshold
                    if coverage[y, x] < 0.6:
                        result[y, x] = False

                else:
                    # ── NOTCH FILLING ──
                    # Only fill if exterior (NOT inside a counter)
                    if not exterior[y, x]:
                        continue

                    if n4 >= 3 and coverage[y, x] > 0.30:
                        result[y, x] = True

    return result


# ── Rectangle merging ─────────────────────────────────────────────────────────

def merge_pixels_to_rects(binary):
    rows, cols = binary.shape
    visited = np.zeros_like(binary, dtype=bool)
    rects = []
    for y in range(rows):
        for x in range(cols):
            if not binary[y, x] or visited[y, x]:
                continue
            w = 0
            while x + w < cols and binary[y, x + w] and not visited[y, x + w]:
                w += 1
            h = 1
            while y + h < rows:
                row_ok = True
                for dx in range(w):
                    if not binary[y + h, x + dx] or visited[y + h, x + dx]:
                        row_ok = False
                        break
                if not row_ok:
                    break
                h += 1
            visited[y:y+h, x:x+w] = True
            rects.append((x, y, w, h))
    return rects


def rects_to_font_coords(rects):
    font_rects = []
    for gx, gy, gw, gh in rects:
        fx = gx * GRID
        fy = GRID_Y_MAX - (gy + gh) * GRID
        fw = gw * GRID
        fh = gh * GRID
        font_rects.append((fx, fy, fw, fh))
    return font_rects


# ── CFF charstring building ──────────────────────────────────────────────────

def rects_to_t2_program(font_rects, advance_width, nominal_width_x):
    width_delta = advance_width - nominal_width_x
    program = [width_delta]
    if not font_rects:
        program.append('endchar')
        return program
    pen_x, pen_y = 0, 0
    for fx, fy, fw, fh in font_rects:
        dx = fx - pen_x
        dy = fy - pen_y
        program.extend([dx, dy, 'rmoveto'])
        program.extend([fw, 'hlineto'])
        program.extend([fh, 'vlineto'])
        program.extend([-fw, 'hlineto'])
        pen_x = fx
        pen_y = fy + fh
    program.append('endchar')
    return program


# ── Font naming ──────────────────────────────────────────────────────────────

def update_font_names(font, weight):
    cff = font['CFF '].cff
    td = cff.topDictIndex[0]
    old_ps = cff.fontNames[0]
    cff.fontNames[0] = old_ps.replace("OpenRunde", "OpenRundePixel")
    if hasattr(td, 'FullName'):
        td.FullName = td.FullName.replace("Open Runde", "Open Runde Pixel")
    if hasattr(td, 'FamilyName'):
        td.FamilyName = td.FamilyName.replace("Open Runde", "Open Runde Pixel")
    for record in font['name'].names:
        try:
            text = record.toUnicode()
        except UnicodeDecodeError:
            continue
        new_text = text.replace("OpenRunde", "OpenRundePixel")
        new_text = new_text.replace("Open Runde", "Open Runde Pixel")
        if new_text != text:
            record.string = new_text


# ── Main processing ──────────────────────────────────────────────────────────

def process_weight(weight):
    src_path = os.path.join(SRC_DESKTOP, f"OpenRunde-{weight}.otf")
    print(f"\n{'='*60}")
    print(f"Processing: {weight}")
    print(f"{'='*60}")

    font = TTFont(src_path)
    cff = font['CFF '].cff
    td = cff.topDictIndex[0]
    charstrings = td.CharStrings
    private = td.Private
    nominal_width_x = private.nominalWidthX
    hmtx = font['hmtx']
    glyph_order = font.getGlyphOrder()
    glyph_set = font.getGlyphSet()

    total = len(glyph_order)
    empty_count = 0
    pixel_count = 0
    corrected_count = 0

    for i, glyph_name in enumerate(glyph_order):
        if (i + 1) % 500 == 0 or i == total - 1:
            print(f"  [{i+1}/{total}] glyphs processed...")

        if glyph_name in hmtx.metrics:
            advance_width = hmtx.metrics[glyph_name][0]
        else:
            advance_width = 0

        pen = RecordingPen()
        try:
            glyph_set[glyph_name].draw(pen)
        except Exception:
            cs = charstrings[glyph_name]
            cs.program = [advance_width - nominal_width_x, 'endchar']
            cs.bytecode = None
            empty_count += 1
            continue

        binary, coverage = rasterize_glyph(pen.value, advance_width)

        if not binary.any():
            cs = charstrings[glyph_name]
            cs.program = [advance_width - nominal_width_x, 'endchar']
            cs.bytecode = None
            empty_count += 1
            continue

        before = binary.copy()
        binary = correct_shapes(binary, coverage)
        if not np.array_equal(before, binary):
            corrected_count += 1

        rects = merge_pixels_to_rects(binary)
        font_rects = rects_to_font_coords(rects)
        program = rects_to_t2_program(font_rects, advance_width, nominal_width_x)

        cs = charstrings[glyph_name]
        cs.program = program
        cs.bytecode = None
        pixel_count += 1

    print(f"  Pixelated: {pixel_count}, Empty: {empty_count}")
    print(f"  Shape-corrected: {corrected_count} glyphs")

    private.Subrs.items = []
    if 'Subrs' in private.rawDict:
        del private.rawDict['Subrs']
    cff.GlobalSubrs.items = []

    update_font_names(font, weight)

    otf_path = os.path.join(OUT_DIR, f"OpenRundePixel-{weight}.otf")
    font.flavor = None
    font.save(otf_path)
    print(f"  Saved: {otf_path}")

    woff_path = os.path.join(OUT_DIR, f"OpenRundePixel-{weight}.woff")
    font.flavor = 'woff'
    font.save(woff_path)
    print(f"  Saved: {woff_path}")

    woff2_path = os.path.join(OUT_DIR, f"OpenRundePixel-{weight}.woff2")
    font.flavor = 'woff2'
    font.save(woff2_path)
    print(f"  Saved: {woff2_path}")

    font.close()


def main():
    print("Open Runde Pixel — Font Generator")
    print(f"Grid: {GRID} font units ({2048 // GRID}px cap height)")
    print(f"Supersampling: {SUPERSAMPLE}x")
    print(f"Threshold: {THRESHOLD}")
    print(f"Corrections: symmetry (V+H), border smoothing (counter-aware)")

    for weight in WEIGHTS:
        process_weight(weight)

    print(f"\n{'='*60}")
    print("Done! All weights generated.")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
