# msui (vittud-msui)

A tiny, modular **MS-style UI** framework prototype meant to render “pedal / multi-effect” style screens on small embedded displays, while staying easy to test on desktop (via pygame).

The long-term goal is **to translate this UI to real hardware** (framebuffer/SPI TFT), keeping the core logic and rendering code as backend-agnostic as possible.

Target hardware (planned):
- **1.69" TFT LCD IPS**
- **240×280**
- **SPI**
- **Driver: ST7789**

---

## What’s in this repo

### 1) Clear separation: core / render / controls / backends

- **`msui/core/`**
  - Pure UI state machine and logic (no pygame):
    - `model.py`: `Effect`, `Page`, control protocol, params, selection state
    - `events.py`: UI events (nav, page, delta, bypass, quit)
    - `controller.py`: applies events to the model, returns a **dirty mask**
    - `dirty.py`: dirty bit flags for incremental redraws
    - `profiler.py`: small per-second perf counters for demos

- **`msui/controls/`**
  - UI “tiles” (encoders drive them via `adjust(delta, effect)`):
    - `DialControl`: numeric dial with arbitrary ranges (supports negative + 0 marker)
    - `EnumControl`: icon-based enum selector
    - `SwitchControl`: 2–3 way switch visualization
    - `ButtonControl`: LED-style boolean control
    - `TextControl`: large centered text selector (good for “DIV” / ratio selections)
  - Shared behavior lives in `controls/base.py`:
    - `Control` base (tile layout helpers, clamp flag)
    - `BoolControl`, `IndexedControl` helpers to reduce duplication

- **`msui/render/`**
  - Backend-agnostic rendering on a “Canvas” API:
    - `screen_effect.py`: renders the whole effect editor screen
    - `layout.py`: layout math (header, badge, tiles, page slots)
    - `draw.py`: dial rendering primitives (ticks, needle, 0 marker)
    - `icon/`: icons split by topic (badge/wave/filter), plus mirror/primitives

- **`msui/backends/`**
  - Pluggable backends:
    - `canvas.py`: `Canvas` protocol (fill, lines, text, etc.)
    - `input.py`: `InputSource` protocol
    - `canvas_pygame.py`: pygame implementation (+ bounded LRU text caches)
    - `input_pygame.py`: dt-based key repeat/accel mapped to UI events

- **`msui/demos/`**
  - Example “effect” setup to exercise controls and rendering:
    - `chorus_demo.py`

- **`msui/__main__.py`**
  - Lets you run: `python -m msui`  
    This resolves and launches the demo entrypoint.

---

## Core ideas / design goals

### Backend-agnostic drawing
Rendering code talks only to the **`Canvas` protocol**, not pygame directly.  
This makes it feasible to later write a `canvas_st7789.py` (SPI TFT) without rewriting UI logic.

### Deterministic input behavior
The pygame input repeater is **dt-based** (not wall-clock), so it behaves consistently across different FPS and machines.

### Incremental rendering (“dirty rectangles”)
The controller returns a **dirty mask** describing what changed:
- Header only (e.g., bypass toggle)
- Page slots only (page change)
- One tile only (value change)
- Full tiles row, etc.

This reduces work on small hardware where pushing pixels is expensive.

---

## How to run (desktop)

```bash
python -m msui
```

Optional: enable debug logging
```bash
MSUI_LOG_LEVEL=DEBUG python -m msui
```

---

## How the UI is driven

### Events
Input produces `UIEvent`s:
- `NAV_LEFT / NAV_RIGHT`: move focus across tiles
- `PAGE_PREV / PAGE_NEXT`: switch page
- `VALUE_DELTA`: encoder-like delta (+/-)
- `TOGGLE_BYPASS`: toggle ACTIVE/BYPASS

### Model
An `Effect` contains:
- `pages`: list of `Page(title, controls)`
- `params`: shared parameter dict (values are stored here)
- `page_index`, `control_index`, `enabled`

Controls read/write `effect.params[control.key]`.

---

## Notes for the future hardware port

The intended “translation” path:
1. Keep **`core/`**, **`controls/`**, **`render/`** as-is.
2. Replace pygame backend with:
   - A `Canvas` implementation that draws to an ST7789 buffer
   - An `InputSource` implementation for real encoders/buttons
3. Keep the same `UIEvent` stream and `controller.apply_event()`.

The current screen size in `Theme` is already set to:
- **W=240, H=280** (matches the target TFT)

---

## Status

This is a prototype focused on:
- visual language (MS-style tiles + icons)
- performance strategy (dirty masks + caching)
- clean architecture for backend portability

It is **not** yet a complete embedded UI stack (no real SPI backend yet).
