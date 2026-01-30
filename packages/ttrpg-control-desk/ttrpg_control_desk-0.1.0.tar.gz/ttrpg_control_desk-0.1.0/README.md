# TTRPG Control Desk

A desktop application for tabletop RPG game masters to display backgrounds, character portraits, and fog of war to players on an external screen.

## Features

- **Dual-window system** - Control panel for GM, separate display for players
- **Background images** - Select and display scene backgrounds
- **Character portraits** - Multi-select characters, displayed at bottom of screen
- **Fog of war** - Paint to reveal areas, per-image fog masks
- **Zoom and pan** - Navigate large images with mouse
- **Pointer** - Hold P to show pointer on player display, move mouse to position
- **Fast loading** - Async loading, thumbnail caching, image preloading

## Installation

Requires Python 3 and PyQt5:

```bash
pip install PyQt5
```

## Usage

```bash
python3 main.py                      # Start empty, select folders manually
python3 main.py /path/to/project     # Auto-detect subfolders
```

When providing a project path, the app looks for:
- `Backgrounds/` or `Fonds/` - Background images
- `Characters/` or `Personnages/` - Character portraits

## Controls

### Keyboard
- **Esc** - Quit
- **F** - Toggle fullscreen
- **P** (hold) - Show pointer on player display
- **Left/Right** - Previous/next background

### Mouse (on preview)
- **Left click + drag** - Paint fog (reveal areas)
- **Right click + drag** - Pan when zoomed
- **Zoom slider** - Zoom in/out

### Docks
- **Backgrounds** - Click to select, folder button to change directory
- **Characters** - Click to toggle selection (multi-select), size slider adjusts portrait size
- **Fog of War** - Enable/disable fog, brush size, clear/fill buttons

## Supported Formats

PNG, JPG, JPEG, BMP, GIF, WebP

## License

MIT
