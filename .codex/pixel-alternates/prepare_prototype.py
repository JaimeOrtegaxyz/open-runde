from __future__ import annotations

import json
import re
from pathlib import Path


PROTOTYPE_GLYPHS = ["o", "e", "r", "d", "p", "n", "u"]

FEATURE_ORDER = [
    ("ss01", ["d", "e", "n", "o", "p", "r", "u"]),
    ("cv01", ["o"]),
    ("cv02", ["p"]),
    ("cv03", ["e"]),
    ("cv04", ["n"]),
    ("cv05", ["r"]),
    ("cv06", ["u"]),
    ("cv07", ["d"]),
    ("salt", ["d", "e", "n", "o", "p", "r", "u"]),
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def feature_file_path() -> Path:
    return Path(__file__).resolve().with_name("prototype_features.fea")


def source_path() -> Path:
    return repo_root() / "src" / "glyphs" / "OpenRunde-Regular.glyphs"


def output_path() -> Path:
    return Path(__file__).resolve().with_name("OpenRunde-Regular.pixel-prototype.glyphs")


def metrics_path() -> Path:
    return Path(__file__).resolve().with_name("prototype_metrics.json")


def find_matching_delimiter(text: str, start: int, opening: str, closing: str) -> int:
    depth = 0
    in_string = False
    escape = False

    for index in range(start, len(text)):
        char = text[index]

        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == "\"":
                in_string = False
            continue

        if char == "\"":
            in_string = True
            continue

        if char == opening:
            depth += 1
        elif char == closing:
            depth -= 1
            if depth == 0:
                return index

    raise ValueError(f"Unmatched delimiter for {opening} at index {start}")


def section_bounds(text: str, marker: str) -> tuple[int, int]:
    marker_index = text.index(marker)
    open_index = marker_index + len(marker) - 1
    close_index = find_matching_delimiter(text, open_index, "(", ")")
    return open_index, close_index


def top_level_objects(section_text: str) -> list[str]:
    objects: list[str] = []
    index = 0

    while index < len(section_text):
        if section_text[index] == "{":
            close_index = find_matching_delimiter(section_text, index, "{", "}")
            objects.append(section_text[index : close_index + 1])
            index = close_index + 1
            continue
        index += 1

    return objects


def glyph_name(glyph_object: str) -> str:
    match = re.search(r"\bglyphname = ([^;]+);", glyph_object)
    if not match:
        raise ValueError("Glyph object is missing glyphname")
    return match.group(1).strip()


def glyph_metric(glyph_object: str, field: str) -> str | None:
    match = re.search(rf"\b{re.escape(field)} = ([^;]+);", glyph_object)
    if not match:
        return None
    return match.group(1).strip()


def duplicate_glyph_object(glyph_object: str, base_name: str) -> str:
    pixel_name = f"{base_name}.pixel"
    duplicated = glyph_object
    duplicated = re.sub(
        rf"\bglyphname = {re.escape(base_name)};",
        f"glyphname = {pixel_name};",
        duplicated,
        count=1,
    )
    duplicated = re.sub(r"(?m)^[ \t]*unicode = [^;]+;\n", "", duplicated)
    duplicated = re.sub(
        rf"\bnote = {re.escape(base_name)};",
        f"note = {pixel_name};",
        duplicated,
        count=1,
    )
    return duplicated


def encode_feature_code(feature_code: str) -> str:
    code = feature_code.strip().replace("\\", "\\\\").replace("\"", "\\\"")
    return code.replace("\n", "\\012") + "\\012"


def build_feature_block(name: str, glyph_names: list[str]) -> str:
    if name == "ss01":
        lines = [f"sub {glyph} by {glyph}.pixel;" for glyph in glyph_names]
    elif name == "salt":
        lines = [f"sub {glyph} from [{glyph}.pixel];" for glyph in glyph_names]
    else:
        glyph = glyph_names[0]
        lines = [f"sub {glyph} by {glyph}.pixel;"]

    encoded = encode_feature_code("\n".join(lines))
    return "{\ncode = \"" + encoded + "\";\nname = " + name + ";\n}"


def build_feature_objects() -> str:
    return ",\n".join(build_feature_block(name, glyphs) for name, glyphs in FEATURE_ORDER)


def append_manual_features(text: str) -> str:
    open_index, close_index = section_bounds(text, "features = (")
    inner = text[open_index + 1 : close_index]
    updated_inner = inner.rstrip() + ",\n" + build_feature_objects() + "\n"
    return text[: open_index + 1] + updated_inner + text[close_index:]


def append_pixel_glyphs(text: str) -> tuple[str, list[dict[str, str | None]]]:
    open_index, close_index = section_bounds(text, "glyphs = (")
    inner = text[open_index + 1 : close_index]
    objects = top_level_objects(inner)
    glyphs = {glyph_name(obj): obj for obj in objects}

    missing = [name for name in PROTOTYPE_GLYPHS if name not in glyphs]
    if missing:
        raise ValueError(f"Missing glyphs in source: {', '.join(missing)}")

    metrics = []
    duplicates = []
    for name in PROTOTYPE_GLYPHS:
        glyph_object = glyphs[name]
        metrics.append(
            {
                "glyph": name,
                "width": glyph_metric(glyph_object, "width"),
                "leftKerningGroup": glyph_metric(glyph_object, "leftKerningGroup"),
                "rightKerningGroup": glyph_metric(glyph_object, "rightKerningGroup"),
            }
        )
        duplicates.append(duplicate_glyph_object(glyph_object, name))

    updated_inner = inner.rstrip() + ",\n" + ",\n".join(duplicates) + "\n"
    updated_text = text[: open_index + 1] + updated_inner + text[close_index:]
    return updated_text, metrics


def main() -> None:
    source_text = source_path().read_text(encoding="utf-8")
    with_features = append_manual_features(source_text)
    with_pixel_glyphs, metrics = append_pixel_glyphs(with_features)

    output_path().write_text(with_pixel_glyphs, encoding="utf-8")
    metrics_path().write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote {output_path().relative_to(repo_root())}")
    print(f"Wrote {metrics_path().relative_to(repo_root())}")


if __name__ == "__main__":
    main()
