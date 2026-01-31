import json

class Geoviz:
    """
    A Python wrapper for the geoviz JavaScript library.
    Allows creating maps by chaining commands and rendering them to an HTML file.
    """
    def __init__(self, **kwargs):
        """
        Initialize the Geoviz object.
        
        Args:
            width (int): Width of the SVG.
            height (int): Height of the SVG.
            margin (list): Margins [top, right, bottom, left].
            domain (object): GeoJSON to define the domain.
            projection (string): Projection name (e.g., "mercator", "EqualEarth").
            zoomable (bool): If True, the map is zoomable.
            background (string): Background color.
        """
        self.commands = []
        self.commands.append({"name": "create", "args": kwargs})

    def _add_command(self, name, args):
        """Add a command to the list of commands to be executed."""
        self.commands.append({"name": name, "args": args})
        return self

    # Marks
    def outline(self, **kwargs):
        """
        Add an outline to the map (graticule sphere).
        
        Args:
            fill (string): Fill color.
            stroke (string): Stroke color.
            strokeWidth (number): Stroke width.
        """
        return self._add_command("outline", kwargs)

    def graticule(self, **kwargs):
        """
        Add a graticule to the map.
        
        Args:
            stroke (string): Stroke color.
            strokeWidth (number): Stroke width.
            step (list): Step [x, y] in degrees.
        """
        return self._add_command("graticule", kwargs)

    def path(self, **kwargs):
        """
        Draw a path (geometry) on the map.
        
        Args:
            datum (object): GeoJSON Feature or FeatureCollection.
            fill (string): Fill color.
            stroke (string): Stroke color.
            strokeWidth (number): Stroke width.
        """
        return self._add_command("path", kwargs)

    def header(self, **kwargs):
        """
        Add a header (title) to the map.
        
        Args:
            text (string): Title text.
            fontSize (number): Font size.
            fontFamily (string): Font family.
            fill (string): Text color.
            anchor (string): Text anchor ("start", "middle", "end").
        """
        return self._add_command("header", kwargs)

    def footer(self, **kwargs):
        """
        Add a footer (source, author) to the map.
        
        Args:
            text (string): Footer text.
            fontSize (number): Font size.
            fill (string): Text color.
            anchor (string): Text anchor.
        """
        return self._add_command("footer", kwargs)

    def circle(self, **kwargs):
        """
        Draw circles on the map (low-level mark).
        For proportional circles with legend, use prop().
        
        Args:
            data (object): GeoJSON FeatureCollection.
            r (string|number): Radius value or property name.
            fill (string): Fill color.
            stroke (string): Stroke color.
            tip (string|bool): Tooltip content.
        """
        return self._add_command("circle", kwargs)

    def square(self, **kwargs):
        """
        Draw squares on the map (low-level mark).
        For proportional squares with legend, use prop(symbol="square").
        
        Args:
            data (object): GeoJSON FeatureCollection.
            side (string|number): Side length or property name.
            fill (string): Fill color.
        """
        return self._add_command("square", kwargs)

    def spike(self, **kwargs):
        """
        Draw spikes on the map (low-level mark).
        
        Args:
            data (object): GeoJSON FeatureCollection.
            height (string|number): Height value or property name.
            width (number): Width of the spike.
            fill (string): Fill color.
        """
        return self._add_command("spike", kwargs)

    def text(self, **kwargs):
        """
        Add text labels to the map.
        
        Args:
            data (object): GeoJSON FeatureCollection.
            text (string): Property name for the text.
            fontSize (number): Font size.
            fill (string): Text color.
        """
        return self._add_command("text", kwargs)

    def tile(self, **kwargs):
        """
        Add a tile layer (basemap).
        
        Args:
            url (string): URL template or keyword (e.g., "worldStreet", "openstreetmap").
            opacity (number): Opacity (0 to 1).
        """
        return self._add_command("tile", kwargs)

    def scalebar(self, **kwargs):
        """
        Add a scale bar.
        
        Args:
            x (number): X position.
            y (number): Y position.
            units (string): "km" or "mi".
        """
        return self._add_command("scalebar", kwargs)

    def north(self, **kwargs):
        """
        Add a north arrow.
        
        Args:
            x (number): X position.
            y (number): Y position.
            width (number): Width of the arrow.
        """
        return self._add_command("north", kwargs)

    def plot(self, **kwargs):
        """
        Generic plot function.
        
        Args:
            type (string): Type of plot ("choro", "prop", "typo", etc.).
            data (object): GeoJSON data.
            var (string): Variable to map.
        """
        return self._add_command("plot", kwargs)

    def tissot(self, **kwargs):
        """Draw Tissot's indicatrix to visualize distortion."""
        return self._add_command("tissot", kwargs)

    def rhumbs(self, **kwargs):
        """Draw rhumb lines."""
        return self._add_command("rhumbs", kwargs)

    def earth(self, **kwargs):
        """Draw the earth (background)."""
        return self._add_command("earth", kwargs)

    def empty(self, **kwargs):
        """Create an empty layer."""
        return self._add_command("empty", kwargs)

    def halfcircle(self, **kwargs):
        """Draw half-circles."""
        return self._add_command("halfcircle", kwargs)

    def symbol(self, **kwargs):
        """Draw symbols."""
        return self._add_command("symbol", kwargs)

    def grid(self, **kwargs):
        """Draw a grid."""
        return self._add_command("grid", kwargs)

    # Plot shortcuts (sugar syntax for plot({type: ...}))
    def choro(self, **kwargs):
        """
        Draw a choropleth map.
        
        Args:
            data (object): GeoJSON FeatureCollection.
            var (string): Variable name containing numeric values.
            method (string): Classification method ('quantile', 'jenks', 'equal', etc.).
            nb (int): Number of classes.
            colors (string|list): Color palette name or list of colors.
            legend (bool): Whether to show the legend (default: True).
            leg_pos (list): Legend position [x, y].
            leg_title (string): Legend title.
        """
        return self._add_command("plot", {"type": "choro", **kwargs})

    def typo(self, **kwargs):
        """
        Draw a typology map (categorical data).
        
        Args:
            data (object): GeoJSON FeatureCollection.
            var (string): Variable name containing categories.
            colors (string|list): Color palette or list.
            legend (bool): Show legend.
        """
        return self._add_command("plot", {"type": "typo", **kwargs})

    def prop(self, **kwargs):
        """
        Draw a proportional symbol map.
        
        Args:
            data (object): GeoJSON FeatureCollection.
            var (string): Variable name containing numeric values.
            symbol (string): Symbol type ("circle", "square", "spike").
            k (number): Size of the largest symbol.
            fill (string): Fill color.
            legend (bool): Show legend.
            leg_type (string): Legend style ("nested", "separate").
        """
        return self._add_command("plot", {"type": "prop", **kwargs})

    def propchoro(self, **kwargs):
        """
        Draw proportional symbols colored by a choropleth variable.
        
        Args:
            data (object): GeoJSON FeatureCollection.
            var (string): Variable for symbol size.
            var2 (string): Variable for color.
            method (string): Classification method for color.
            colors (string|list): Color palette.
        """
        return self._add_command("plot", {"type": "propchoro", **kwargs})

    def proptypo(self, **kwargs):
        """
        Draw proportional symbols colored by categories.
        
        Args:
            data (object): GeoJSON FeatureCollection.
            var (string): Variable for symbol size.
            var2 (string): Variable for category color.
        """
        return self._add_command("plot", {"type": "proptypo", **kwargs})

    def picto(self, **kwargs):
        """Draw a pictogram map."""
        return self._add_command("plot", {"type": "picto", **kwargs})

    def bertin(self, **kwargs):
        """
        Draw a Bertin map (dots).
        
        Args:
            data (object): GeoJSON FeatureCollection.
            var (string): Variable name.
            n (int): Number of dots per unit.
        """
        return self._add_command("plot", {"type": "bertin", **kwargs})

    # Legends
    def legend_circles_nested(self, **kwargs):
        """Draw a nested circles legend."""
        return self._add_command("legend.circles_nested", kwargs)

    def legend_circles(self, **kwargs):
        """Draw a circles legend."""
        return self._add_command("legend.circles", kwargs)

    def legend_squares(self, **kwargs):
        """Draw a squares legend."""
        return self._add_command("legend.squares", kwargs)

    def legend_squares_nested(self, **kwargs):
        """Draw a nested squares legend."""
        return self._add_command("legend.squares_nested", kwargs)

    def legend_circles_half(self, **kwargs):
        """Draw a half-circles legend."""
        return self._add_command("legend.circles_half", kwargs)

    def legend_spikes(self, **kwargs):
        """Draw a spikes legend."""
        return self._add_command("legend.spikes", kwargs)

    def legend_mushrooms(self, **kwargs):
        """Draw a mushrooms legend."""
        return self._add_command("legend.mushrooms", kwargs)

    def legend_choro_vertical(self, **kwargs):
        """Draw a vertical choropleth legend."""
        return self._add_command("legend.choro_vertical", kwargs)

    def legend_choro_horizontal(self, **kwargs):
        """Draw a horizontal choropleth legend."""
        return self._add_command("legend.choro_horizontal", kwargs)

    def legend_typo_vertical(self, **kwargs):
        """Draw a vertical typology legend."""
        return self._add_command("legend.typo_vertical", kwargs)

    def legend_typo_horizontal(self, **kwargs):
        """Draw a horizontal typology legend."""
        return self._add_command("legend.typo_horizontal", kwargs)

    def legend_symbol_vertical(self, **kwargs):
        """Draw a vertical symbol legend."""
        return self._add_command("legend.symbol_vertical", kwargs)

    def legend_symbol_horizontal(self, **kwargs):
        """Draw a horizontal symbol legend."""
        return self._add_command("legend.symbol_horizontal", kwargs)

    def legend_box(self, **kwargs):
        """Draw a box legend."""
        return self._add_command("legend.box", kwargs)

    # Effects
    def effect_blur(self, **kwargs):
        """Apply a blur effect."""
        return self._add_command("effect.blur", kwargs)

    def effect_shadow(self, **kwargs):
        """Apply a shadow effect."""
        return self._add_command("effect.shadow", kwargs)

    def effect_radialGradient(self, **kwargs):
        """Apply a radial gradient effect."""
        return self._add_command("effect.radialGradient", kwargs)

    def effect_clipPath(self, **kwargs):
        """Apply a clip path effect."""
        return self._add_command("effect.clipPath", kwargs)

    def get_config(self):
        """Return the configuration as a JSON-compatible list of commands."""
        def process_args(args):
            new_args = {}
            for k, v in args.items():
                if v is None:
                    continue # Skip None values
                if isinstance(v, str) and (v.strip().startswith("(") or v.strip().startswith("function") or "=>" in v):
                     new_args[k] = {"__js_func__": v}
                elif isinstance(v, dict):
                    new_args[k] = process_args(v)
                else:
                    new_args[k] = v
            return new_args

        processed_commands = []
        for cmd in self.commands:
            processed_commands.append({"name": cmd["name"], "args": process_args(cmd["args"])})
        
        return processed_commands

    def to_json(self):
        """Return the configuration as a JSON string."""
        return json.dumps(self.get_config())

    def render_html(self, filename="map.html"):
        """Render the map to an HTML file."""
        json_commands = self.to_json()
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Tangerine"/>
  <script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
  <script src="https://cdn.jsdelivr.net/npm/geoviz@0.9.8"></script>
</head>
<body>
<script>
  const commands = {json_commands};
  let svg;

  // Helper to revive functions
  function revive(obj) {{
    if (typeof obj === 'object' && obj !== null) {{
      if (obj.hasOwnProperty('__js_func__')) {{
         try {{
            return eval(obj['__js_func__']);
         }} catch (e) {{
            console.error("Failed to eval function:", obj['__js_func__'], e);
            return null;
         }}
      }} else {{
         for (let key in obj) {{
            obj[key] = revive(obj[key]);
         }}
      }}
    }}
    return obj;
  }}

  const revivedCommands = revive(commands);

  revivedCommands.forEach(cmd => {{
    if (cmd.name === "create") {{
      svg = geoviz.create(cmd.args);
    }} else {{
      const parts = cmd.name.split(".");
      if (parts.length === 1) {{
         if (svg[parts[0]]) {{
            svg[parts[0]](cmd.args);
         }} else {{
            console.warn("Method " + parts[0] + " not found");
         }}
      }} else if (parts.length === 2) {{
         if (svg[parts[0]] && svg[parts[0]][parts[1]]) {{
            svg[parts[0]][parts[1]](cmd.args);
         }} else {{
            console.warn("Method " + cmd.name + " not found");
         }}
      }}
    }}
  }});

  if (svg) {{
    document.body.appendChild(svg.render());
  }}
</script>
</body>
</html>
"""
        with open(filename, "w") as f:
            f.write(html_content)
        print(f"Map saved to {filename}")
