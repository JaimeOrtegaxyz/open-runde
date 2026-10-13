from __future__ import annotations

from pathlib import Path

import glyphsLib
from ufo2ft import compileOTF


def workspace_dir() -> Path:
    return Path(__file__).resolve().parent


def source_glyphs() -> Path:
    return workspace_dir() / "OpenRunde-Regular.pixel-prototype.glyphs"


def build_dir() -> Path:
    return workspace_dir() / "build"


def output_otf() -> Path:
    return build_dir() / "OpenRunde-PixelPrototype-Regular.otf"


def main() -> None:
    build_dir().mkdir(parents=True, exist_ok=True)

    ufos = glyphsLib.load_to_ufos(str(source_glyphs()))
    if not ufos:
        raise RuntimeError("No UFOs were produced from the prototype Glyphs source")

    ufo = ufos[0]
    ufo.info.familyName = "Open Runde Pixel Prototype"
    ufo.info.styleName = "Regular"
    ufo.info.styleMapFamilyName = "Open Runde Pixel Prototype"
    ufo.info.openTypeNamePreferredFamilyName = "Open Runde Pixel Prototype"
    ufo.info.openTypeNamePreferredSubfamilyName = "Regular"
    ufo.info.postscriptFontName = "OpenRundePixelPrototype-Regular"

    font = compileOTF(ufo)
    font.save(output_otf())

    print(f"Wrote {output_otf()}")


if __name__ == "__main__":
    main()
