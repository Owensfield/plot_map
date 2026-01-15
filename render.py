#!/usr/bin/env python3
import json
import math
import shutil
import subprocess
from pathlib import Path

def svg_header(width, height):
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' "
        f"xmlns:xlink='http://www.w3.org/1999/xlink' "
        f"width='{width}' height='{height}' viewBox='0 0 {width} {height}'>"
    )

def escape(text):
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )

def render(data):
    meta = data["meta"]
    style = data["style"]
    width = meta["width"]
    height = meta["height"]
    groups = {g["id"]: g for g in data.get("groups", [])}

    parts = [svg_header(width, height)]
    parts.append(
        f"<rect width='{width}' height='{height}' fill='{meta['background']}'/>"
    )

    # Roads (tube-style straight polylines)
    parts.append(
        "<g fill='none' stroke-linecap='round' stroke-linejoin='round'>"
    )
    for road in data.get("roads", []):
        pts = " ".join(f"{x},{y}" for x, y in road["points"])
        color = road.get("color", style["road_stroke"])
        parts.append(
            f"<polyline points='{pts}' stroke='{color}' stroke-width='{style['road_width']}'/>"
        )
    parts.append("</g>")

    # Plot markers
    parts.append("<g>")
    for plot in data.get("plots", []):
        x, y = plot["x"], plot["y"]
        label = escape(plot["id"])
        group_id = plot.get("group")
        group = groups.get(group_id)
        fill = group["color"] if group else style["plot_fill"]
        text_color = group.get("text", "#ffffff") if group else style["plot_text"]
        plot_size = style.get("plot_size", 24)
        parts.append(
            f"<rect x='{x - plot_size / 2}' y='{y - plot_size / 2}' "
            f"width='{plot_size}' height='{plot_size}' rx='4' "
            f"fill='{fill}' stroke='{style['plot_stroke']}' stroke-width='2'/>"
        )
        parts.append(
            f"<text x='{x}' y='{y + 6}' text-anchor='middle' "
            f"font-family='{style['label_font']}' font-size='12' font-weight='700' "
            f"fill='{text_color}'>{label}</text>"
        )
        if plot.get("name"):
            name = escape(plot["name"])
            parts.append(
                f"<text x='{x + 18}' y='{y + 4}' font-family='{style['name_font']}' "
                f"font-size='14' fill='{style['label_text']}'>{name}</text>"
            )
    parts.append("</g>")

    # Decorations (thin lines, arrows, shapes)
    decorations = data.get("decorations", [])
    if decorations:
        parts.append("<g>")
        for deco in decorations:
            dtype = deco.get("type", "polyline")
            stroke = deco.get("stroke", "#111111")
            width = deco.get("width", 2)
            linecap = deco.get("linecap", "round")
            linejoin = deco.get("linejoin", "round")
            fill = deco.get("fill", "none")
            if dtype == "polyline":
                pts = " ".join(f"{x},{y}" for x, y in deco["points"])
                parts.append(
                    f"<polyline points='{pts}' stroke='{stroke}' stroke-width='{width}' "
                    f"fill='{fill}' stroke-linecap='{linecap}' stroke-linejoin='{linejoin}'/>"
                )
            elif dtype == "polygon":
                pts = " ".join(f"{x},{y}" for x, y in deco["points"])
                parts.append(
                    f"<polygon points='{pts}' stroke='{stroke}' stroke-width='{width}' fill='{fill}' "
                    f"stroke-linejoin='{linejoin}'/>"
                )
            elif dtype == "line":
                parts.append(
                    f"<line x1='{deco['x1']}' y1='{deco['y1']}' x2='{deco['x2']}' y2='{deco['y2']}' "
                    f"stroke='{stroke}' stroke-width='{width}' stroke-linecap='{linecap}'/>"
                )
            elif dtype == "circle":
                parts.append(
                    f"<circle cx='{deco['cx']}' cy='{deco['cy']}' r='{deco['r']}' "
                    f"stroke='{stroke}' stroke-width='{width}' fill='{fill}'/>"
                )
            elif dtype == "image":
                href = deco.get("href")
                if not href:
                    continue
                parts.append(
                    f"<image href='{href}' x='{deco['x']}' y='{deco['y']}' "
                    f"width='{deco['width']}' height='{deco['height']}' "
                    f"preserveAspectRatio='{deco.get('preserve', 'xMidYMid meet')}'/>"
                )
        parts.append("</g>")

    # Labels
    parts.append("<g>")
    for label in data.get("labels", []):
        size = label.get("size", 16)
        color = label.get("color", style["label_text"])
        font = label.get("font", style["label_font"])
        anchor = label.get("anchor")
        weight = label.get("weight", "700")
        rotate = label.get("rotate")
        attrs = [
            f"x='{label['x']}'",
            f"y='{label['y']}'",
            f"font-family='{font}'",
            f"font-size='{size}'",
            f"fill='{color}'",
        ]
        if anchor:
            attrs.append(f"text-anchor='{anchor}'")
        if weight:
            attrs.append(f"font-weight='{weight}'")
        if rotate:
            attrs.append(f"transform='rotate({rotate} {label['x']} {label['y']})'")
        spans = label.get("spans")
        if spans:
            parts.append(f"<text {' '.join(attrs)}>")
            for span in spans:
                span_x = span.get("x", label["x"])
                span_y = span.get("y", label["y"])
                parts.append(
                    f"<tspan x='{span_x}' y='{span_y}'>{escape(str(span.get('text', '')))}</tspan>"
                )
            parts.append("</text>")
        else:
            lines = label.get("lines")
            if lines:
                line_height = label.get("line_height", size + 4)
                parts.append(f"<text {' '.join(attrs)}>")
                for idx, line in enumerate(lines):
                    y = label["y"] + idx * line_height
                    parts.append(
                        f"<tspan x='{label['x']}' y='{y}'>{escape(str(line))}</tspan>"
                    )
                parts.append("</text>")
            else:
                text = escape(label["text"])
                parts.append(f"<text {' '.join(attrs)}>{text}</text>")
    parts.append("</g>")

    # Key (simple list of colored labels)
    key = data.get("key")
    if key and key.get("items"):
        kx = key.get("x", 900)
        ky = key.get("y", 70)
        line_height = key.get("line_height", 20)
        pad_x = key.get("pad_x", 8)
        pad_y = key.get("pad_y", 6)
        font_size = key.get("font_size", 14)
        char_width = key.get("char_width", 8)
        columns = key.get("columns", 1)
        column_gap = key.get("column_gap", 20)
        column_width = key.get("column_width")
        items = key["items"]
        rows_per_col = key.get("rows_per_col")
        if not rows_per_col:
            rows_per_col = math.ceil(len(items) / columns)

        col_widths = [0] * columns
        if column_width:
            for col in range(columns):
                col_widths[col] = column_width
        else:
            for idx, item in enumerate(items):
                col = idx // rows_per_col
                if col >= columns:
                    col = columns - 1
                text = escape(item.get("text", ""))
                rect_w = max(40, len(text) * char_width) + pad_x * 2
                if rect_w > col_widths[col]:
                    col_widths[col] = rect_w

        col_offsets = [0] * columns
        running = 0
        for col in range(columns):
            col_offsets[col] = running
            running += col_widths[col] + column_gap

        parts.append("<g>")
        for idx, item in enumerate(items):
            text = escape(item.get("text", ""))
            if not text:
                continue
            color = item.get("color", style["label_text"])
            col = idx // rows_per_col
            row = idx % rows_per_col
            if col >= columns:
                col = columns - 1
            x = kx + col_offsets[col]
            y = ky + row * line_height
            rect_w = max(40, len(text) * char_width) + pad_x * 2
            rect_h = font_size + pad_y * 2
            rect_y = y - rect_h / 2
            parts.append(
                f"<rect x='{x}' y='{rect_y}' width='{rect_w}' height='{rect_h}' rx='4' "
                f"fill='{color}'/>"
            )
            parts.append(
                f"<text x='{x + rect_w / 2}' y='{y}' text-anchor='middle' dominant-baseline='middle' "
                f"font-family='{style['label_font']}' font-size='{font_size}' font-weight='700' "
                f"fill='#111111'>{text}</text>"
            )
        parts.append("</g>")

    # Legend
    legend = data.get("legend")
    if legend:
        lx = legend["x"]
        ly = legend["y"]
        swatch = legend.get("swatch", 14)
        item_height = legend.get("item_height", 22)
        parts.append("<g>")
        parts.append(
            f"<text x='{lx}' y='{ly}' font-family='{style['legend_font']}' "
            f"font-size='18' fill='{style['label_text']}'>{escape(legend.get('title', 'Legend'))}</text>"
        )
        for idx, item in enumerate(legend.get("items", [])):
            group = groups.get(item.get("group"))
            if not group:
                continue
            y = ly + 12 + (idx + 1) * item_height
            parts.append(
                f"<rect x='{lx}' y='{y - swatch + 4}' width='{swatch}' height='{swatch}' rx='3' "
                f"fill='{group['color']}' stroke='{style['plot_stroke']}' stroke-width='1'/>"
            )
            label = escape(item.get("label", ""))
            parts.append(
                f"<text x='{lx + swatch + 8}' y='{y + 4}' font-family='{style['legend_font']}' "
                f"font-size='14' fill='{style['label_text']}'>{group['name']}: {label}</text>"
            )
        parts.append("</g>")

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main():
    map_path = Path("map.yaml")
    data = json.loads(map_path.read_text())
    svg = render(data)
    Path("output.svg").write_text(svg)
    print("Rendered output.svg from map.yaml")

    converter = shutil.which("rsvg-convert")
    if converter:
        png_zoom = data.get("meta", {}).get("png_zoom", 2)
        try:
            subprocess.run(
                [converter, "output.svg", "-o", "output.png", "--zoom", str(png_zoom)],
                check=True,
            )
            print("Rendered output.png from output.svg")
        except subprocess.CalledProcessError as exc:
            print(f"Failed to render output.png: {exc}")
    else:
        print("rsvg-convert not found; skipping output.png")


if __name__ == "__main__":
    main()
