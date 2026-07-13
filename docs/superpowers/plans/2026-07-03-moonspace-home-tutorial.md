# MoonSpace Home Tutorial Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a playable home/tutorial scene between the opening CG and the current Moon Palace courtyard.

**Architecture:** Introduce a focused `HomeTutorialScene` world object/controller that owns the home map draw/update rules and exposes simple status flags to `Game`. `Game` remains responsible for top-level mode transitions, saving `home_tutorial_done`, and resetting the player into the existing courtyard when the gate is entered.

**Tech Stack:** Python, Pygame, pytest, existing image asset loader and event bus.

---

## File Structure

- Create `world/home_tutorial_scene.py`: home scene background, sign interaction, facing-practice rule, gate trigger, collision rectangles, and draw routine.
- Modify `core/game.py`: add `MODE_HOME`, transition from opening/load into home when needed, route update/draw to home, persist tutorial completion, and enter existing courtyard after the gate.
- Modify `core/save_manager.py`: add `home_tutorial_done` to new saves and slot summaries.
- Modify `ui/dialog_box.py`: add readable speaker labels for home tutorial objects.
- Add `tests/test_home_tutorial_scene.py`: focused behavior tests for reading the sign, completing facing practice, gate lock/unlock, and drawing.
- Modify `tests/test_save_manager.py`: assert default and summary include home tutorial state.
- Add `assets/sprites/moonspace/home_tutorial_bg.png`: resized preview-derived background for the home scene.

## Tasks

### Task 1: Save Data Contract

**Files:**
- Modify: `core/save_manager.py`
- Modify: `tests/test_save_manager.py`

- [ ] Add a failing test that `default_save()` includes `home_tutorial_done: False`.
- [ ] Add a failing test that slot summaries expose `home_tutorial_done`.
- [ ] Run `python -m pytest tests/test_save_manager.py -q` and confirm failure.
- [ ] Add the field in `SaveManager.default_save()` and `get_slot_summary()`.
- [ ] Re-run the save manager tests.

### Task 2: Home Tutorial Scene Unit

**Files:**
- Create: `world/home_tutorial_scene.py`
- Add: `tests/test_home_tutorial_scene.py`

- [ ] Add failing tests for initial locked gate, sign-read rule disclosure, facing practice completion, locked gate before requirements, open gate after requirements, collision rectangles, and draw output.
- [ ] Run `python -m pytest tests/test_home_tutorial_scene.py -q` and confirm failure.
- [ ] Implement `HomeTutorialScene` with `update()`, `draw()`, `read_sign()`, `is_gate_entered()`, `get_collision_rects()`, `apply_save_data()`, and `collect_save_data()`.
- [ ] Re-run the home scene tests.

### Task 3: Game Flow Integration

**Files:**
- Modify: `core/game.py`
- Modify: `ui/dialog_box.py`
- Add/modify tests as needed.

- [ ] Add failing tests that new games enter `MODE_HOME` after opening, completed home saves enter `MODE_PLAYING`, and gate entry saves completion.
- [ ] Run the targeted game-flow tests and confirm failure.
- [ ] Add `MODE_HOME`, instantiate `HomeTutorialScene`, route update/draw, transition opening/load to home when `home_tutorial_done` is false, and transition gate entry to existing courtyard.
- [ ] Add dialog labels for home sign and tutorial shadow.
- [ ] Re-run targeted tests.

### Task 4: Preview Asset

**Files:**
- Add: `assets/sprites/moonspace/home_tutorial_bg.png`

- [ ] Resize/crop the approved preview to `960x540`.
- [ ] Save it under the project asset path without replacing existing assets.
- [ ] Add a test or asset assertion that it exists and has expected dimensions.

### Task 5: Verification

**Files:** all touched files.

- [ ] Run `python -m pytest`.
- [ ] Launch a lightweight Pygame draw/update smoke check for `HomeTutorialScene`.
- [ ] Report exact verification status and any manual follow-up needed.
