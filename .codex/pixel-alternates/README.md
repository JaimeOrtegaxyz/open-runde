# Pixel Alternates Prototype Workspace

This folder is the Codex-owned workspace for the Open Runde pixel-alternate prototype.

It does not modify the primary source in `src/glyphs/`.

## Contents

- `prepare_prototype.py`: generates a working `.glyphs` copy with pixel alternate scaffolding
- `prototype_features.fea`: OpenType feature code for the prototype glyph set
- `OpenRunde-Regular.pixel-prototype.glyphs`: generated working copy for Glyphs
- `prototype_metrics.json`: generated metrics snapshot for the prototype glyphs

## Prototype Scope

The scaffold targets this lowercase subset:

- `o`
- `e`
- `r`
- `d`
- `p`
- `n`
- `u`

Each duplicate is named with a `.pixel` suffix and keeps the base glyph's width and kerning groups.

## Usage

Run:

```sh
python3 .codex/pixel-alternates/prepare_prototype.py
```

Then open:

```text
.codex/pixel-alternates/OpenRunde-Regular.pixel-prototype.glyphs
```

## Expected Manual Work In Glyphs

The generated `.pixel` glyphs start as duplicated outlines from the base glyphs.

You still need to:

1. Redraw each `.pixel` glyph on the chosen grid.
2. Keep the copied widths and kerning groups unchanged.
3. Test `ss01` and `cv01` through `cv07` in words like `open runde`, `round`, and `under`.
