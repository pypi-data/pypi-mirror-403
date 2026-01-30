# Preset Background Images

This directory contains built-in background image presets for the poster-design library.

## Adding New Presets

1. Place image files in this directory
2. Register the preset in `src/poster_design/core/backgrounds.py`:
   ```python
   PRESET_BACKGROUNDS: Dict[str, str] = {
       # ... existing presets
       "your_preset_name": "assets/backgrounds/your_file.png",
   }
   ```

## Guidelines

- **File Size**: Keep images between 100-500 KB
- **Formats**: Use PNG or JPG for compatibility
- **Dimensions**: Minimum 1920x1080 for quality scaling
- **Naming**: Use lowercase with underscores (e.g., `paper_texture.png`)
- **License**: Use only public domain or freely licensed images

## Available Presets

| Preset Name | File | Description |
|-------------|------|-------------|
| paper_texture | paper_texture.png | Subtle paper texture |
| wood_grain | wood_grain.jpg | Wood grain pattern |
| fabric_linen | fabric_linen.jpg | Linen fabric texture |
| marble | marble_pattern.jpg | Marble pattern |
| geometric | geometric_pattern.png | Geometric pattern |

## Custom Presets

Users can register custom backgrounds at runtime:

```python
from poster_design.core.backgrounds import register_preset_background

register_preset_background("my_custom", "/path/to/image.jpg")
canvas.set_background(preset="my_custom")
```
