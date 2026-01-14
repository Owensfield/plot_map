# Owensfield Map (tube-style)

This repo renders a clean, editable SVG map from a small YAML file.

## Files
- `map.yaml` – the editable source of roads, plots, and labels (JSON is valid YAML 1.2)
- `render.py` – renders `map.yaml` to `output.svg`
- `output.svg` – generated SVG (London tube–style lines)

## Quick start
```bash
python3 render.py
```

Open `output.svg` in a browser or vector editor.

## Editing
- Edit or add roads in `map.yaml` under `roads` (each road is a list of points).
- Add plots/houses under `plots` (number + name + position).
- Adjust labels under `labels`.

Coordinates are in pixels; keep angles to 0/45/90 degrees for the tube look.
