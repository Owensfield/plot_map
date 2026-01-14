# Owensfield Map (tube-style)

![Rendered map](output.png?raw=1)

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

## PNG output (local)
If you want `output.png` locally, install `rsvg-convert`:
```bash
sudo apt-get update
sudo apt-get install -y librsvg2-bin
```
Then rerun:
```bash
python3 render.py
```

## Editing
- Edit or add roads in `map.yaml` under `roads` (each road is a list of points).
- Add plots/houses under `plots` (number + name + position).
- Adjust labels under `labels`.

Coordinates are in pixels; keep angles to 0/45/90 degrees for the tube look.
