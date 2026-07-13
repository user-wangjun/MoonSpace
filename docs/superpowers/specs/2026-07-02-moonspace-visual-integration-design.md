# MoonSpace Visual Integration Design

## Goal

Improve the current Python + Pygame demo so the player, NPCs, moon palace courtyard objects, and game UI match the PRD and composition documents more closely while staying inside the existing code-drawn pixel art pipeline.

## Source Documents

- `docs/plans/2026-06-19-moonspace-design.md`
- `docs/plans/moonspace-character-scene-composition.md`
- `.trae/specs/pygame-rewrite/spec.md`
- `.trae/rules/project_rules.md`

## Scope

This design upgrades the visuals that are already in the playable Pygame game:

- Player envoy sprite
- Wugang sprite and chopping silhouette
- Yutu sprite and pounding silhouette
- Laurel tree, moon pool, pound table, sign board, and Guanghan Palace wall
- Main menu, dialog box, rule book, status strip, and interaction prompt
- Integration into the current draw order in `core/game.py`

This does not add combat, audio, new endings, a new asset loading pipeline, or external image dependencies.

## Approach

Use code-drawn pixel art rather than PNG sprites. The current repo rule says core pixel art should prefer code drawing, and the existing game already draws through `draw(surface, camera_offset)` methods. The visual upgrade should replace rectangle placeholders with small reusable shape helpers and denser pixel silhouettes.

The `imagegen` concept reference created during design is only a mood and composition reference. It is not a project asset and should not be loaded by the game.

## Characters

### Player

The player remains a 16x24 entity with the same collision rectangle and movement logic. The visual frame should become a robed false envoy:

- dark blue robe body with vertical robe folds
- pale moon trim at collar, sleeve, and hem
- small pale face and dark hair
- directional face treatment for up, down, left, and right
- walking frame foot alternation and a subtle idle breathing frame
- interaction frame that raises one sleeve without changing collision

Implementation should keep `Player.update()` behavior intact and replace only drawing/frame data.

### Wugang

Wugang remains a 16x24 NPC at the current position. His sprite should read as a cursed chopping figure:

- wide shoulders and gray-pale skin
- asymmetric torso lines to imply distorted muscles
- moon-white axe head and dark wood handle
- four chopping frames with the axe moving from raised to impact
- after violation level 2, current game behavior already makes rule consequences visible elsewhere; the sprite should still be readable in normal and horror states

The fifth chop still emits `TREE_BLEEDING`.

### Yutu

Yutu remains a 16x16 NPC with an interaction area. It should stop looking like a white block and become an uncanny crouched humanoid rabbit:

- low crouched body
- long uneven ears
- one or two red eye pixels
- bent limb pixels that look slightly wrong
- three pounding frames while `is_pounding` is true
- stopped posture when the player enters interaction range

The current `YUTU_POUNDING_CHANGED` event behavior remains unchanged.

## Scene Objects

### Laurel Tree

The laurel tree remains the main visual anchor and rule executor.

- draw layered dark-green crown clusters instead of one rectangle
- draw twisted trunk with roots reaching into nearby tiles
- add multiple faint face marks in the trunk
- keep breathing pulse via `_time`
- when bleeding, draw restrained vertical dark-red streaks and root highlights

Collision rectangle remains unchanged.

### Moon Pool

The moon pool keeps its current rectangle and reflection zone.

- draw a beveled dark-blue basin and mirror-like inner water
- add moving pale line highlights
- when time phase changes, show a faint humanoid reflection/noise mark in the water
- do not make the water look like a generic blue block

### Guanghan Palace Wall

The wall remains top collision/background.

- add roof/flying-eave silhouette along the top band
- add a central gate signal and cold window marks
- add a faint Chang'e light silhouette behind the gate/window area
- keep it as background, not a detailed foreground object

### Sign Board And Pound Table

The sign board should read as the starting rule board with legs, top plank, and carved rule strokes. The pound table should read as a mortar/pestle station with a small bowl, support pixels, and scattered medicine dust.

## UI

### Main Menu

Keep the current keyboard shortcuts, but make the screen feel like MoonSpace rather than a plain menu:

- blood moon remains as first-viewport anchor
- palace/courtyard silhouette behind the options
- stronger title framing using moon-white and blood-red accents
- menu options stay readable and fit the 480x270 canvas

### Dialog Box

Keep the bottom panel behavior and text wrapping.

- use a double-line moon-white frame with deep-blue inner rule
- add speaker nameplate and small corner ticks
- use the same colors as rule book for consistency
- do not obscure the player or core scene more than the current panel does

### Rule Book

Keep Tab open/close and current rule data.

- draw as a worn moon palace rule register
- add title line, numbered entries, and subtle divider marks
- preserve the existing wrapped text fallback

### Interaction And Status UI

The current `E` hint and bottom status strip stay small. Improve readability with icon-like pixel marks and avoid bulky panels.

## Architecture

No new runtime dependency is needed.

Expected code changes:

- `utils/pixel_art.py`: add small helpers only if they reduce duplication, such as `draw_outline_rect`, `draw_pixel_data_rows`, or small line/marker helpers.
- `entities/player.py`: replace frame rows and palette map.
- `entities/wugang.py`: replace rectangle drawing with frame-aware code drawing.
- `entities/yutu.py`: replace rectangle drawing with frame-aware code drawing.
- `world/laurel_tree.py`: upgrade tree drawing.
- `world/moon_pool.py`: upgrade pool drawing.
- `world/palace_wall.py`: upgrade wall/Chang'e far silhouette.
- `world/pound_table.py`: upgrade mortar table drawing.
- `world/sign_board.py`: upgrade board drawing.
- `ui/main_menu.py`, `ui/dialog_box.py`, `ui/rule_book.py`, and `core/game.py`: upgrade UI drawing only.

Game flow, save data, rules, collision, input mappings, and event names should remain stable.

## Testing And Verification

Automated tests should cover behavior that can be asserted without screenshot comparison:

- player frame output includes all required palette keys and remains 16x24
- Wugang fifth chop event still fires
- Yutu pounding state still changes around player range
- scene object collision rectangles remain unchanged and nonzero
- UI components still open/close/advance as before

Manual/runtime verification should cover visual quality:

- run `python -m pytest`
- run `python main.py`
- verify the main menu appears
- start or load a game and confirm upgraded player, Wugang, Yutu, laurel tree, moon pool, sign board, pound table, palace wall, dialog box, rule book, status strip, and interaction hint are visible in the game
- verify no text overlaps its panel at 960x540
- verify pixel edges remain sharp after scale

## Acceptance Criteria

- Player, Wugang, Yutu, laurel tree, moon pool, sign board, pound table, and palace wall are no longer plain rectangle placeholders.
- Character and scene silhouettes match the PRD roles and the composition document.
- Main menu, dialog box, and rule book share a coherent moon palace horror UI style.
- The upgraded visuals are integrated into the existing game loop.
- Existing gameplay behavior remains intact.
- `python -m pytest` passes.
- `python main.py` launches successfully for visual inspection.
