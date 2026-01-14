#!/usr/bin/env python3
import json
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
        parts.append(
            f"<rect x='{x - 12}' y='{y - 12}' width='24' height='24' rx='4' "
            f"fill='{fill}' stroke='{style['plot_stroke']}' stroke-width='2'/>"
        )
        parts.append(
            f"<text x='{x}' y='{y + 6}' text-anchor='middle' "
            f"font-family='{style['label_font']}' font-size='12' fill='{text_color}'>{label}</text>"
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
        text = escape(label["text"])
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
        parts.append("<g>")
        for idx, item in enumerate(key["items"]):
            text = escape(item.get("text", ""))
            if not text:
                continue
            color = item.get("color", style["label_text"])
            y = ky + idx * line_height
            rect_w = max(40, len(text) * char_width) + pad_x * 2
            rect_h = font_size + pad_y * 2
            rect_y = y - rect_h / 2
            parts.append(
                f"<rect x='{kx}' y='{rect_y}' width='{rect_w}' height='{rect_h}' rx='4' "
                f"fill='{color}'/>"
            )
            parts.append(
                f"<text x='{kx + rect_w / 2}' y='{y}' text-anchor='middle' dominant-baseline='middle' "
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


if __name__ == "__main__":
    main()
