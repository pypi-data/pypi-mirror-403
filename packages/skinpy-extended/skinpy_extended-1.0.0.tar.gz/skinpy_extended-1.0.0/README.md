# Skinpy Extended

<p align="center">
  <img src="https://raw.githubusercontent.com/Bonenk/skinpy-extended/refs/heads/master/docs/steve-render.png" alt="isometric render" height=300>
</p>

A Python library for Minecraft skins, focusing on high-fidelity rendering, texture reconstruction, and bi-directional mapping.

## Motivation

This project is a fork and extension of the archived [skinpy](https://github.com/t-mart/skinpy/) library. We aim to revitalize the project with advanced features inspired by modern high-performance renderers like [nmsr-rs](https://github.com/Bonenk/nmsr-rs/).

Our core goal is to provide a simple, Pythonic way to bridge the gap between 2D skin textures and 3D renders, enabling seamless mapping in both directions.

## Features

- **2D to 3D Mapping:** Render high-quality isometric views of any Minecraft skin.
- **3D to 2D Reconstruction:** Reconstruct original 64x64 skin textures from rendered images.
- **Granular Control:** Access and modify pixels at the skin, body part, or individual face level using 3D coordinates.
- **Dataset Preparation:** Perfect for generating large-scale, consistent datasets of skin renders and their corresponding textures.
- **CLI & API:** Use the built-in command-line tool or integrate the flexible Python API into your own projects.

## Installation

```shell
pip install skinpy-extended
```

## Quickstart

### Loading and Saving

```python
from skinpy import Skin

# Load a skin from a file
skin = Skin.from_path("steve.png")

# Save the skin texture back to a file
skin.to_image().save("steve_copy.png")
```

### Rendering a Perspective View

```python
from skinpy import Skin, Perspective

skin = Skin.from_path("steve.png")

# Create a perspective (Front-Right-Up)
perspective = Perspective.new(
    x="right",
    y="front",
    z="up",
    scaling_factor=20
)

# Render and save
skin.to_isometric_image(perspective).save("render.png")
```

### Reconstructing a Skin from a Render

```python
from PIL import Image
from skinpy import Skin

# Load a combined render (e.g. front and back views)
render_img = Image.open("render.png").convert("RGBA")

# Map the render back to a 3D Skin object
skin = Skin.from_combined_render(render_img, scale=20)

# Extract the original 2D texture
skin.to_image().save("reconstructed.png")
```

## Coordinate System

Skinpy uses a coordinate system with the origin at the left-down-front of the skin from the perspective of an observer looking at the skin.

![coordinate system](https://github.com/Bonenk/skinpy-extended/raw/master/docs/coordsys.png)

## Development & Contributing

We welcome contributions to expand the library's capabilities! Areas of interest include:
- Support for Slim (Alex-style) models.
- Support for secondary layers (overlays/hats).
- Improved rendering performance.

Feel free to open issues or submit pull requests.

## Credits

- Originally created by [Tim Martin](https://github.com/t-mart) and [Steven Van Ingelgem](https://github.com/svaningelgem).
- Maintained and extended by [Bonenk](https://github.com/Bonenk).
- Logic inspired by [nmsr-rs](https://github.com/NickAcPT/nmsr-rs).

## License

MIT
