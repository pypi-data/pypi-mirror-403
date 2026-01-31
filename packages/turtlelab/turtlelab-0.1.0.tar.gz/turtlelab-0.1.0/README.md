# ✨Interactive Turtle Lab 🐢🔬

A simple Graphical Interface for executing Python turtle graphics from external files interactively, to make turtle programming easier & better.

## Features
- Browse and load `.py` files with turtle code
- A small built-in integrated code editor inside
- Embedded turtle canvas (no external windows)
- Built-in sandboxed execution environment

## Usage

```cli
turtlelab  # Execute from CLI
```

1. Click **Browse...** to select a Python file
2. Review the code from the editor
3. Click **Run** to execute (Ctrl+Enter). It will automatically sync from the file loaded as well before running. So you can edit the file in your personal Editor and just click 'Run' and it will auto-fetch code from the file.
4. Click **Clear** to reset the canvas

## Important Rules

- Use provided `t` (turtle) and `screen` objects directly
- Do NOT use `import turtle` in your code

## Example Files

Check the `examples/` folder (inside ..Python/Lib/site-packages/turtlelab ) for sample scripts:

- `square.py` - Draw a square
- `star.py` - Draw a star
- `spiral.py` - Draw a spiral

## API

Your code has access to:
- `t` - RawTurtle object with full turtle graphics API
- `screen` - TurtleScreen for the canvas

**More features will be coming soon!**