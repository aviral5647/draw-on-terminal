# Terminal Whiteboard (draw.py)

A small terminal-based drawing tool written in Python using the curses library, where you can draw using your keyboard alone.

## Requirements

- Python 3 (tested on Linux and Windows) 
- A terminal supporting curses (ncurses). On most Linux systems Python's builtin curses works out of the box.

## Run

Open a terminal with at least 80×24 characters and run:

```bash
python3 draw.py
```

### Terminal Compatibility
If you experience issues with input not working (spacebar not drawing, etc.), try:

```bash
# With debug mode to see what's happening
WHITEBOARD_DEBUG=true python3 draw.py

# Or with specific terminal type
TERM=xterm-256color python3 draw.py
```

**Note**: The program has been enhanced for better terminal compatibility. See `TERMINAL_FIX.md` for detailed troubleshooting if you encounter issues in different terminal environments.

## Quick controls (overview)

- Movement: Arrow keys or WASD
- Use tool: SPACE
- Tool menu: TAB
- Brush menu: B
- Pattern menu: P
- Layer menu: L
- Color menu: K
- Shapes menu: N
- Toggle grid: G
- Toggle grid snap: F
- Zoom in/out: = / -  (reset: 0)
- Toggle help: H
- Save: S (saves to `drawing.json`)
- Open: O (loads `drawing.json` if present)
- Undo: U
- Redo: R
- Clear canvas: x
- Clear all (settings/history): SHIFT+X
- Quit: Q

## Tools

The program exposes a number of tools (see the on-screen tool list). Examples include:

- pen: freehand brush
- ers: eraser
- line: draw straight lines
- box: rectangle (filled or outline)
- circ: circle
- fill: flood fill
- spray: spray paint
- text: enter text at cursor
- sel: select rectangular region
- move / copy / paste: clipboard operations
- pat: place pre-defined patterns
- arrow / star / tri / hex: shape tools

Use TAB to open the tools menu and choose a tool by arrow keys, Enter, or number keys.

## Brushes & Patterns

- Press `B` for brush menu (select size/character)
- Press `P` to cycle or pick pattern presets
- Brush sizes 1-5 are mapped to keys 1..5 for quick selection

## Layers

- Add/delete layers with `+` and `-` keys
- Open layer menu with `L` to toggle visibility `v` or lock `l` a layer
- Layers are composited top-to-bottom when rendered

## Colors

- Quick cycle foreground: `C` (or `c` in the code)
- Quick cycle background: `V` (or `v` in the code)
- Full color menu: `K`
