# MoonSpace Visual Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the current playable Python + Pygame demo with PRD-aligned code-drawn pixel characters, scene objects, and UI, then verify the visuals are integrated into the game.

**Architecture:** Keep the existing `draw(surface, camera_offset)` architecture and event/gameplay flow. Add only small reusable pixel-art helpers where they reduce duplication, then replace rectangle placeholder visuals in entity, world, and UI modules.

**Tech Stack:** Python 3.12, Pygame 2.x, pytest, existing code-drawn pixel art utilities.

---

## Current Baseline

Run from `D:\CodeWorkspace\MoonSpace`:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Expected baseline before edits:

```text
72 passed
```

## Task 1: Pixel-Art Helper Coverage

**Files:**
- Modify: `utils/pixel_art.py`
- Modify: `tests/test_pixel_art.py`

- [ ] **Step 1: Write failing helper tests**

Add tests that require a double border helper and a small glyph/row helper:

```python
def test_draw_double_rect_draws_outer_and_inner_borders():
    surface = pygame.Surface((12, 12))
    draw_double_rect(surface, pygame.Rect(1, 1, 10, 10), (255, 255, 255), (0, 255, 0))
    assert surface.get_at((1, 1))[:3] == (255, 255, 255)
    assert surface.get_at((3, 3))[:3] == (0, 255, 0)


def test_draw_marker_pixels_draws_relative_points():
    surface = pygame.Surface((8, 8))
    draw_marker_pixels(surface, 2, 2, [(0, 0), (2, 1)], (255, 0, 0))
    assert surface.get_at((2, 2))[:3] == (255, 0, 0)
    assert surface.get_at((4, 3))[:3] == (255, 0, 0)
```

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_pixel_art.py
```

Expected: fails because helpers do not exist.

- [ ] **Step 2: Implement helpers**

Add:

```python
def draw_double_rect(surface, rect, outer_color, inner_color):
    rect = pygame.Rect(rect)
    draw_rect(surface, rect.x, rect.y, rect.width, rect.height, outer_color)
    if rect.width > 4 and rect.height > 4:
        draw_rect(surface, rect.x + 2, rect.y + 2, rect.width - 4, rect.height - 4, inner_color)


def draw_marker_pixels(surface, x, y, points, color):
    for px, py in points:
        draw_pixel(surface, x + px, y + py, color)
```

- [ ] **Step 3: Verify**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_pixel_art.py
```

Expected: passes.

## Task 2: Player Sprite Frames

**Files:**
- Modify: `entities/player.py`
- Modify: `tests/test_player.py`

- [ ] **Step 1: Write failing tests**

Add tests for the 16x24 frame and required palette symbols:

```python
def test_player_pixel_frame_is_16_by_24_and_uses_envoy_symbols():
    player = Player()
    frame = player._pixel_frame()
    assert len(frame) == 24
    assert all(len(row) == 16 for row in frame)
    used = set("".join(frame)) - {" "}
    assert {"H", "R", "D", "M", "G", "K"}.issubset(used)


def test_player_direction_changes_face_pixels():
    player = Player()
    player.facing = "down"
    down = player._pixel_frame()
    player.facing = "up"
    up = player._pixel_frame()
    assert down != up
```

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_player.py
```

Expected: fails because the current frame lacks the full envoy symbol set.

- [ ] **Step 2: Replace player frame drawing**

Update `Player.draw()` color map to include:

```python
"G": palette.PALE_MOON,
"K": palette.BLACK,
```

Replace `_pixel_frame()` with a 16x24 robed envoy frame that varies face/hem/feet by `facing`, `anim_state`, and `current_frame`.

- [ ] **Step 3: Verify player tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_player.py
```

Expected: passes.

## Task 3: NPC Visual Upgrade

**Files:**
- Modify: `entities/wugang.py`
- Modify: `entities/yutu.py`
- Modify: `tests/test_wugang.py`
- Modify: `tests/test_yutu.py`

- [ ] **Step 1: Write non-regression visual tests**

Add tests that draw each NPC and assert multiple meaningful colors are present:

```python
def test_wugang_draw_uses_body_skin_and_axe_colors():
    bus = EventBus()
    wugang = Wugang(bus)
    surface = pygame.Surface((160, 160))
    wugang.draw(surface)
    colors = {surface.get_at((x, y))[:3] for x in range(90, 132) for y in range(70, 122)}
    assert palette.WUGANG_ROBE in colors
    assert palette.SKIN_PALE in colors
    assert palette.MOON_WHITE in colors


def test_yutu_draw_uses_body_eye_and_pestle_colors():
    bus = EventBus()
    yutu = Yutu(bus)
    surface = pygame.Surface((340, 180))
    yutu.draw(surface)
    colors = {surface.get_at((x, y))[:3] for x in range(260, 320) for y in range(90, 150)}
    assert palette.YUTU_WHITE in colors
    assert palette.BLOOD_RED in colors
    assert palette.MOON_WHITE in colors
```

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_wugang.py tests/test_yutu.py
```

Expected: Yutu test fails because current Yutu has no red eye pixels; Wugang may pass or be strengthened during implementation.

- [ ] **Step 2: Upgrade NPC draw methods**

Replace Wugang rectangle drawing with frame-aware body, head, torso lines, axe handle/head, and impact posture.

Replace Yutu rectangle drawing with crouched body, uneven ears, red eye pixels, limbs, and pounding/stopped posture.

- [ ] **Step 3: Verify NPC tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_wugang.py tests/test_yutu.py
```

Expected: passes.

## Task 4: Scene Object Visual Upgrade

**Files:**
- Modify: `world/laurel_tree.py`
- Modify: `world/moon_pool.py`
- Modify: `world/palace_wall.py`
- Modify: `world/pound_table.py`
- Modify: `world/sign_board.py`
- Modify: `tests/test_world_objects.py`

- [ ] **Step 1: Write visual non-regression tests**

Add tests that render world objects and assert PRD colors are present:

```python
def test_laurel_tree_draw_contains_faces_and_bleeding_pixels():
    tree = LaurelTree()
    tree.set_bleeding(True)
    surface = pygame.Surface((220, 160))
    tree.draw(surface)
    colors = {surface.get_at((x, y))[:3] for x in range(120, 190) for y in range(35, 125)}
    assert palette.LAUREL_GREEN in colors
    assert palette.ASH_GRAY in colors
    assert palette.BLOOD_RED in colors


def test_palace_wall_draw_contains_moonlight_and_blood_moon_accents():
    wall = PalaceWall()
    surface = pygame.Surface((config.MAP_WIDTH, 80))
    wall.draw(surface)
    colors = {surface.get_at((x, y))[:3] for x in range(config.MAP_WIDTH) for y in range(0, 40)}
    assert palette.PALE_MOON in colors
    assert palette.DARK_BLOOD in colors
```

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_world_objects.py
```

Expected: palace wall test fails before implementation.

- [ ] **Step 2: Upgrade object drawings**

Implement layered crown/trunk/roots/face marks in `LaurelTree`, mirror/basin/reflection marks in `MoonPool`, eaves/gate/Chang'e silhouette in `PalaceWall`, mortar/table details in `PoundTable`, and plank/legs/carved strokes in `SignBoard`.

Do not change collision rectangles.

- [ ] **Step 3: Verify scene tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_world_objects.py
```

Expected: passes.

## Task 5: UI Visual Upgrade

**Files:**
- Modify: `ui/main_menu.py`
- Modify: `ui/dialog_box.py`
- Modify: `ui/rule_book.py`
- Modify: `core/game.py`
- Modify: `tests/test_main_menu.py`
- Modify: `tests/test_dialog_box.py`
- Modify: `tests/test_rule_book.py`

- [ ] **Step 1: Write UI render tests**

Add tests that draw UI surfaces and assert style colors are present without changing behavior:

```python
def test_main_menu_draw_uses_moonspace_palette():
    menu = MainMenu()
    surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    menu.draw(surface)
    colors = {surface.get_at((x, y))[:3] for x in range(config.SCREEN_WIDTH) for y in range(config.SCREEN_HEIGHT)}
    assert palette.BLOOD_RED in colors
    assert palette.PALE_MOON in colors
    assert palette.PALACE_STONE in colors
```

For dialog/rule book, keep existing behavior tests and add a render color test only when the component is active/open.

- [ ] **Step 2: Upgrade UI drawing**

Use `draw_double_rect` where useful. Add moon palace silhouettes to main menu, speaker nameplate/corner ticks to dialog, and divider/title ornamentation to rule book. Improve the status strip and E hint in `core/game.py` without increasing panel bulk.

- [ ] **Step 3: Verify UI tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_main_menu.py tests/test_dialog_box.py tests/test_rule_book.py
```

Expected: passes.

## Task 6: Full Verification And Runtime Launch

**Files:**
- Inspect modified files only.

- [ ] **Step 1: Run all tests**

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Expected: all tests pass.

- [ ] **Step 2: Launch game for visual inspection**

```powershell
.\.venv\Scripts\python.exe main.py
```

Expected: game launches at 960x540 with sharp pixel scaling. Inspect main menu and enter/load a game if possible.

- [ ] **Step 3: Report remaining gaps**

If runtime inspection cannot be completed in this environment, report that clearly and include passing automated tests.
