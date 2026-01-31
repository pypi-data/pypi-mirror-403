# geovizpy

A Python wrapper for the [geoviz](https://github.com/neocarto/geoviz) JavaScript library.
It allows you to create thematic maps using a simple Python API and render them to HTML.

## Installation

```bash
pip install git+https://github.com/fbxyz/geovizpy.git
```

## Usage

```python
from geovizpy import Geoviz
import json

# Load your GeoJSON data
with open("examples/world.json") as f:
    world_data = json.load(f)

# Create a map
viz = Geoviz(projection="EqualEarth")
viz.outline()
viz.choro(data=world_data, var="gdppc")
viz.render_html("map.html")
```
