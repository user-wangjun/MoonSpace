# MoonSpace PNG Asset Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the visible code-rectangle character and scene placeholders with project-local PNG sprites, sprite sheets, and scene backgrounds loaded by the Pygame game.

**Architecture:** Keep the existing entity and UI draw order in `core/game.py`, but add a small asset-loading layer that returns cached `pygame.Surface` objects from `assets/sprites/moonspace/`. Entities and scene objects should draw PNG frames first and keep their current code-drawn fallback only for missing assets or broken files. A deterministic asset-generation script creates the first production-ready pixel PNGs so the game has real files in the repo instead of runtime-only drawings.

**Tech Stack:** Python 3.12, Pygame, pytest, PyInstaller.

---

## File Structure

- Create `tools/generate_moonspace_assets.py`: deterministic PNG asset generator using Pygame surfaces. It writes character sheets, object sprites, main-menu background, and opening CG backgrounds.
- Create `utils/assets.py`: cached Pygame asset loader with `load_image()` and `load_sprite_sheet()`.
- Create `tests/test_assets.py`: verifies generated files exist, load correctly, and expose expected frame dimensions.
- Modify `entities/player.py`: load `player_envoy.png` frames for four directions and animation states; fallback to existing code pixel frame if unavailable.
- Modify `entities/wugang.py`: load `wugang_chop.png` four-frame sheet; fallback to current drawing.
- Modify `entities/yutu.py`: load `yutu_pounding.png` pounding/stopped frames; fallback to current drawing.
- Modify `world/laurel_tree.py`, `world/moon_pool.py`, `world/pound_table.py`, `world/sign_board.py`, `world/palace_wall.py`: draw PNG object/background assets first and preserve state overlays such as bleeding, reflection flash, and horror accents.
- Modify `ui/main_menu.py`: use `main_menu_bg.png` as the base scene and keep interactive menu text/buttons on top.
- Modify `ui/opening_cg.py`: use opening CG background images per act while keeping caption timing and skip behavior.
- Modify `build.py` only if asset packaging misses the new directory; current `assets` packaging should already include it.

## Task 1: Asset Loader And Failing Tests

**Files:**
- Create: `tests/test_assets.py`
- Create: `utils/assets.py`

- [ ] **Step 1: Write failing tests**

Add tests that assert `utils.assets.load_image()` and `load_sprite_sheet()` exist, load from `assets/sprites/moonspace/`, preserve alpha, cache repeated loads, and slice frames by size.

- [ ] **Step 2: Run tests and confirm RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_assets.py
```

Expected: fails because `utils.assets` and asset PNG files do not exist yet.

- [ ] **Step 3: Implement minimal loader**

Create `utils/assets.py` with:

- `asset_path(relative_path: str) -> Path`
- `load_image(relative_path: str, *, convert_alpha: bool = True) -> pygame.Surface`
- `load_sprite_sheet(relative_path: str, frame_width: int, frame_height: int) -> list[pygame.Surface]`
- `clear_asset_cache() -> None`

Use `sys._MEIPASS` support for PyInstaller and an in-memory cache keyed by relative path.

- [ ] **Step 4: Run tests and confirm GREEN after assets are generated**

The loader tests pass once Task 2 writes the first PNG assets.

## Task 2: Generate Real PNG Assets

**Files:**
- Create: `tools/generate_moonspace_assets.py`
- Create: `assets/sprites/moonspace/*.png`

- [ ] **Step 1: Write deterministic generator**

Use Pygame surfaces to generate hard-edged pixel art PNGs with alpha. Output:

- `player_envoy.png`: 8 frames, 16x24 each, four directional idle frames and four walking frames.
- `wugang_chop.png`: 4 frames, 32x32 each, raised/mid/impact/recover axe poses.
- `yutu_pounding.png`: 4 frames, 24x24 each, three pounding frames and one stopped frame.
- `laurel_tree.png`: 64x80 transparent object sprite.
- `moon_pool.png`: 64x40 transparent object sprite.
- `pound_table.png`: 24x24 transparent object sprite.
- `sign_board.png`: 24x32 transparent object sprite.
- `palace_wall_bg.png`: 480x80 background band.
- `main_menu_bg.png`: 480x270 title scene background.
- `opening_cg_*.png`: 480x270 backgrounds for download room, moon reveal, moonlight pullback, and blackout.

- [ ] **Step 2: Generate assets**

Run:

```powershell
.\.venv\Scripts\python.exe tools\generate_moonspace_assets.py
```

Expected: files are created under `assets/sprites/moonspace/`.

- [ ] **Step 3: Inspect generated dimensions**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_assets.py
```

Expected: loader and asset dimension tests pass.

## Task 3: Character Sprite Integration

**Files:**
- Modify: `entities/player.py`
- Modify: `entities/wugang.py`
- Modify: `entities/yutu.py`
- Modify: `tests/test_player.py`
- Modify: `tests/test_wugang.py`
- Modify: `tests/test_yutu.py`

- [ ] **Step 1: Add failing draw tests**

Tests should verify that each character draw includes alpha PNG asset colors and does not depend only on rectangle fallback.

- [ ] **Step 2: Implement sprite drawing**

Load sheets lazily. Choose frame indices from current direction and animation state without changing collision rectangles, interaction ranges, timers, or events.

- [ ] **Step 3: Run character tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_player.py tests\test_wugang.py tests\test_yutu.py
```

Expected: all pass.

## Task 4: Scene Object And Background Integration

**Files:**
- Modify: `world/laurel_tree.py`
- Modify: `world/moon_pool.py`
- Modify: `world/pound_table.py`
- Modify: `world/sign_board.py`
- Modify: `world/palace_wall.py`
- Modify: `tests/test_world_objects.py`

- [ ] **Step 1: Add failing scene asset tests**

Tests should verify object sprites draw expected asset-only colors and that collision rectangles stay unchanged.

- [ ] **Step 2: Implement object image draws**

Blit PNG sprites at object rects. Keep dynamic overlays:

- laurel bleeding drips and pulse
- moon pool reflection flash
- palace horror level accents
- sign board read-state border

- [ ] **Step 3: Run scene tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_world_objects.py tests\test_tile_map.py
```

Expected: all pass.

## Task 5: Main Menu And Opening CG Asset Integration

**Files:**
- Modify: `ui/main_menu.py`
- Modify: `ui/opening_cg.py`
- Modify: `tests/test_main_menu.py`
- Modify: `tests/test_opening_cg.py`

- [ ] **Step 1: Add failing UI asset tests**

Tests should verify menu and opening CG render asset background colors while preserving option selection and skip behavior.

- [ ] **Step 2: Blit scene backgrounds**

Use `main_menu_bg.png` and `opening_cg_*.png` as base layers. Keep text, selection marker, captions, and keyboard handling in code.

- [ ] **Step 3: Run UI tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_main_menu.py tests\test_opening_cg.py
```

Expected: all pass.

## Task 6: Full Verification And Build

**Files:**
- Runtime artifact: `dist/MoonSpace.exe`

- [ ] **Step 1: Run full tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Expected: every test passes.

- [ ] **Step 2: Render a gameplay screenshot**

Run a dummy SDL script that instantiates `Game`, switches to playing mode, draws `game.game_surface`, and saves a screenshot under `tmp/asset-check/gameplay.png`. Inspect it visually.

- [ ] **Step 3: Build exe**

Run:

```powershell
.\.venv\Scripts\python.exe build.py
```

Expected: `dist/MoonSpace.exe` is rebuilt and includes `assets/sprites/moonspace/`.

- [ ] **Step 4: Launch smoke test**

Start `dist/MoonSpace.exe` for three seconds and confirm it does not exit early.

## Self-Review

- Spec coverage: This plan covers game-scene sprites, main menu scene, and opening CG scene as requested by the user.
- Placeholder scan: No TBD/TODO placeholders are present.
- Scope control: The plan does not add new gameplay, combat, endings, or new dependencies.
