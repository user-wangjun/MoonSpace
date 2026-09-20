"""场景物体测试。"""

import pygame
import pytest

import config
from core.event_bus import EventBus
from core.game_state import GameState
from utils import palette
from utils.assets import load_image
from world.laurel_tree import LaurelTree
from world.moon_pool import MoonPool
from world.palace_wall import PalaceWall
from world.pound_table import PoundTable
from world.sign_board import BASIC_RULES, SignBoard


def test_world_objects_have_collision_rects():
    objects = [LaurelTree(), MoonPool(), PoundTable(), PalaceWall(), SignBoard()]

    for obj in objects:
        rect = obj.get_collision_rect()
        assert isinstance(rect, pygame.Rect)
        assert rect.width > 0
        assert rect.height > 0
        assert rect.right <= config.MAP_WIDTH
        assert rect.bottom <= config.MAP_HEIGHT


def test_palace_wall_collision_blocks_visual_wall_body():
    wall = PalaceWall()

    rect = wall.get_collision_rect()

    assert rect.top == 0
    assert rect.height >= 150


def test_palace_entry_rect_is_aligned_below_wall_collision():
    wall = PalaceWall()

    assert wall.get_entry_rect().top > wall.get_collision_rect().bottom
    assert wall.get_entry_rect().centerx == config.MAP_WIDTH // 2


def test_laurel_tree_bleeding_state_can_change():
    tree = LaurelTree()

    tree.set_bleeding(True)

    assert tree.bleeding is True


def test_laurel_tree_rule_rect_covers_visible_trunk_sides():
    tree = LaurelTree()

    assert tree.get_rule_rect().contains(tree.get_collision_rect())
    center, radius = tree.get_rule_circle()
    assert center == (tree.rect.centerx, tree.rect.centery + 4)
    assert radius == 176
    assert tree.get_rule_rect().size == (352, 352)
    assert tree.get_rule_rect().center == center


def test_laurel_tree_bleed_time_advances_only_while_bleeding():
    tree = LaurelTree()

    tree.update(0.5)
    assert tree.bleed_time == 0.0

    tree.set_bleeding(True)
    tree.update(0.5)

    assert tree.bleed_time == 0.5


def test_moon_pool_reflection_flash_timer_counts_down():
    pool = MoonPool()

    pool.flash_reflection()
    assert pool.reflection_flash_timer > 0

    pool.update(pool.reflection_flash_timer + 0.1)

    assert pool.reflection_flash_timer == 0.0


def test_palace_wall_horror_level_can_change():
    wall = PalaceWall()

    wall.set_horror_level(2)

    assert wall.horror_level == 2


def test_sign_board_interaction_range():
    sign = SignBoard(50, 50)
    near_player = pygame.Rect(45, 45, 16, 24)
    far_player = pygame.Rect(200, 200, 16, 24)

    assert sign.can_interact(near_player)
    assert not sign.can_interact(far_player)


def test_sign_board_adds_basic_rules_to_game_state():
    state = GameState(EventBus())
    sign = SignBoard()

    first_read = sign.interact(state)

    assert first_read is True
    assert sign.has_been_read
    assert state.known_rules == BASIC_RULES
    assert len(state.known_rules) >= 4
    assert any("十息" in text and "不可代职" in text for text in state.known_rules.values())


def test_sign_board_discloses_full_mainline_flow():
    state = GameState(EventBus())
    sign = SignBoard()

    sign.interact(state)
    rules_text = "\n".join(state.known_rules.values())

    assert "凌霄来使入宫" in rules_text
    assert "验明三职" in rules_text
    assert "命毕方可返月谷" in rules_text
    assert "不得代职" in rules_text
    assert "不得候宫" in rules_text

def test_sign_board_second_interact_is_not_first_read_but_rules_remain():
    state = GameState(EventBus())
    sign = SignBoard()

    sign.interact(state)
    second_read = sign.interact(state)

    assert second_read is False
    assert state.known_rules == BASIC_RULES


def test_laurel_tree_draw_adds_bleeding_pixels_on_large_background():
    tree = LaurelTree()
    tree.set_bleeding(True)
    surface = pygame.Surface((config.MAP_WIDTH, config.MAP_HEIGHT))

    tree.draw(surface)

    sample = tree.rect.inflate(40, 40).clip(surface.get_rect())
    colors = {
        surface.get_at((x, y))[:3]
        for x in range(sample.left, sample.right)
        for y in range(sample.top, sample.bottom)
    }
    assert palette.BLOOD_RED in colors


@pytest.mark.parametrize("elapsed", [0.0, 0.7, 5.0, 9.8])
def test_laurel_bleeding_stays_attached_to_tree_during_breathing(elapsed):
    tree = LaurelTree(0, 0)
    tree.update(elapsed)
    idle = pygame.Surface((176, 220), pygame.SRCALPHA)
    tree.draw(idle)
    tree.set_bleeding(True)
    tree.bleed_time = elapsed
    bleeding = pygame.Surface((176, 220), pygame.SRCALPHA)
    tree.draw(bleeding)

    # Independently render the breathing silhouette from the actual asset.
    sprite = load_image("sprites/moonspace/laurel_tree.png")
    silhouette = pygame.Surface((176, 220), pygame.SRCALPHA)
    if elapsed in (0.7, 5.0, 9.8):
        sprite = pygame.transform.smoothscale(sprite, (178, 222))
        silhouette.blit(sprite, (-1, -2))
    else:
        silhouette.blit(sprite, (0, 0))
    changed = []
    for x in range(176):
        for y in range(220):
            if idle.get_at((x, y)) != bleeding.get_at((x, y)):
                changed.append((x, y))
                assert silhouette.get_at((x, y)).a > 0, (elapsed, x, y)
                assert bleeding.get_at((x, y))[:3] not in (palette.PALE_MOON, palette.HORROR_CYAN_GRAY)
    assert changed


def test_laurel_tree_large_background_mode_draws_complete_foreground_tree_when_idle():
    tree = LaurelTree()
    surface = pygame.Surface((config.MAP_WIDTH, config.MAP_HEIGHT), pygame.SRCALPHA)

    tree.draw(surface)

    drawn = surface.get_bounding_rect()
    assert drawn.width >= 45
    assert drawn.height >= 72
    assert drawn.top >= 0
    assert drawn.bottom <= config.MAP_HEIGHT


def test_laurel_tree_idle_animation_changes_drawn_pixels_over_time():
    tree = LaurelTree()
    before = pygame.Surface((config.MAP_WIDTH, config.MAP_HEIGHT), pygame.SRCALPHA)
    after = pygame.Surface((config.MAP_WIDTH, config.MAP_HEIGHT), pygame.SRCALPHA)

    tree.draw(before)
    tree.update(0.7)
    tree.draw(after)

    sample = tree.sprite_rect.inflate(8, 8).clip(before.get_rect())
    changed = 0
    for x in range(sample.left, sample.right, 6):
        for y in range(sample.top, sample.bottom, 6):
            if before.get_at((x, y)) != after.get_at((x, y)):
                changed += 1

    assert changed > 0


def test_moon_pool_table_and_sign_use_png_assets():
    surface = pygame.Surface((config.MAP_WIDTH, config.MAP_HEIGHT), pygame.SRCALPHA)
    pool = MoonPool()
    table = PoundTable()
    sign = SignBoard()

    pool.draw(surface)
    table.draw(surface)
    sign.draw(surface)

    colors = {
        surface.get_at((x, y))[:4]
        for x in range(config.MAP_WIDTH)
        for y in range(config.MAP_HEIGHT)
        if surface.get_at((x, y)).a > 0
    }
    assert len(colors) > 50


def test_pound_table_keeps_collision_anchor_but_draws_split_mortar_layers():
    table = PoundTable(740, 302)
    surface = pygame.Surface((config.MAP_WIDTH, config.MAP_HEIGHT), pygame.SRCALPHA)

    table.draw_back(surface)
    surface.fill((255, 0, 0, 255), pygame.Rect(table.rect.centerx - 20, table.rect.centery + 2, 40, 16))
    before_front = surface.copy()
    table.draw_front(surface)

    assert table.get_collision_rect().topleft == (740, 302)
    changed = sum(
        before_front.get_at((x, y)) != surface.get_at((x, y))
        for x in range(table.rect.centerx - 24, table.rect.centerx + 24)
        for y in range(table.rect.centery + 2, table.rect.centery + 18)
        if 0 <= x < surface.get_width() and 0 <= y < surface.get_height()
    )
    assert changed > 0


def test_palace_wall_draw_contains_moonlight_and_blood_moon_accents():
    wall = PalaceWall()
    wall.set_horror_level(3)
    surface = pygame.Surface((config.MAP_WIDTH, 80))

    wall.draw(surface)

    colors = {
        surface.get_at((x, y))[:3]
        for x in range(config.MAP_WIDTH)
        for y in range(0, 40)
    }
    assert palette.BLOOD_RED in colors


def test_palace_wall_draw_uses_png_background_asset():
    wall = PalaceWall()
    wall.set_horror_level(2)
    surface = pygame.Surface((config.MAP_WIDTH, 80), pygame.SRCALPHA)

    wall.draw(surface)

    colors = {
        surface.get_at((x, y))[:3]
        for x in range(config.MAP_WIDTH)
        for y in range(0, 80)
    }
    assert palette.DARK_BLOOD in colors


def test_palace_wall_switches_between_closed_and_open_gate_backgrounds():
    wall = PalaceWall()
    surface = pygame.Surface((config.MAP_WIDTH, config.MAP_HEIGHT), pygame.SRCALPHA)

    wall.set_gate_open(False)
    wall.draw(surface)
    closed = surface.copy()

    surface.fill((0, 0, 0, 0))
    wall.set_gate_open(True)
    wall.draw(surface)

    gate_sample = pygame.Rect(config.MAP_WIDTH // 2 - 64, 120, 128, 120)
    changed_pixels = sum(
        closed.get_at((x, y)) != surface.get_at((x, y))
        for x in range(gate_sample.left, gate_sample.right)
        for y in range(gate_sample.top, gate_sample.bottom)
    )
    assert changed_pixels > 500


def test_laurel_tree_bleeding_auto_repairs_after_duration():
    tree = LaurelTree()
    tree.set_bleeding(True)

    tree.update(tree.BLEED_DURATION - 0.1)
    assert tree.bleeding is True

    tree.update(0.11)

    assert tree.bleeding is False
    assert tree.bleed_time == 0.0


def test_moon_pool_collision_and_reflection_area_match_confirmed_large_model():
    pool = MoonPool()

    assert pool.visual_rect.size == (144, 144)
    assert pool.get_collision_rect().size == (112, 112)
    assert pool.visual_rect.center == (config.MAP_WIDTH // 2, 360)
    assert pool.visual_rect.center == pool.get_collision_rect().center
    assert pool.reflection_rect.width > pool.visual_rect.width
    assert pool.reflection_rect.height > pool.visual_rect.height
    assert pool.reflection_rect.contains(pool.visual_rect)


def test_moon_pool_draws_real_sprite_reflection_without_touching_stone_rim():
    pool = MoonPool()
    before = pygame.Surface((config.MAP_WIDTH, config.MAP_HEIGHT), pygame.SRCALPHA)
    after = pygame.Surface((config.MAP_WIDTH, config.MAP_HEIGHT), pygame.SRCALPHA)
    reflection = pygame.Surface((18, 28), pygame.SRCALPHA)
    reflection.fill((*palette.PALE_MOON, 255))

    pool.draw(before)
    pool.draw(
        after,
        reflection_sprite=reflection,
        observer_center=(pool.rect.centerx, pool.visual_rect.bottom + 8),
        show_reflection=True,
    )

    water_sample = pool.visual_rect.inflate(-34, -34)
    changed = sum(
        before.get_at((x, y)) != after.get_at((x, y))
        for x in range(water_sample.left, water_sample.right)
        for y in range(water_sample.top, water_sample.bottom)
    )
    assert changed > 50

    rim_points = [
        (pool.visual_rect.centerx, pool.visual_rect.top + 5),
        (pool.visual_rect.centerx, pool.visual_rect.bottom - 6),
        (pool.visual_rect.left + 5, pool.visual_rect.centery),
        (pool.visual_rect.right - 6, pool.visual_rect.centery),
    ]
    assert all(before.get_at(point) == after.get_at(point) for point in rim_points)


def test_moon_pool_pollution_is_an_inner_overlay_without_changing_geometry():
    pool = MoonPool()
    normal = pygame.Surface((config.MAP_WIDTH, config.MAP_HEIGHT), pygame.SRCALPHA)
    polluted = pygame.Surface((config.MAP_WIDTH, config.MAP_HEIGHT), pygame.SRCALPHA)

    pool.draw(normal)
    pool.draw(polluted, show_pollution=True)

    assert pool.visual_rect.center == pool.rect.center
    changed = sum(
        normal.get_at((x, y)) != polluted.get_at((x, y))
        for y in range(pool.visual_rect.top + 12, pool.visual_rect.bottom - 12)
        for x in range(pool.visual_rect.left + 12, pool.visual_rect.right - 12)
    )
    assert changed > 100

    rim_points = (
        (pool.visual_rect.centerx, pool.visual_rect.top + 5),
        (pool.visual_rect.centerx, pool.visual_rect.bottom - 6),
        (pool.visual_rect.left + 5, pool.visual_rect.centery),
        (pool.visual_rect.right - 6, pool.visual_rect.centery),
    )
    assert all(normal.get_at(point) == polluted.get_at(point) for point in rim_points)


def test_pool_premonition_changes_water_but_not_rim_or_violation_timer():
    pool = MoonPool()
    normal = pygame.Surface((18, 28), pygame.SRCALPHA)
    normal.fill((180, 190, 220, 255))
    turned = normal.copy()
    turned.fill((20, 30, 50, 255), pygame.Rect(4, 2, 10, 10))
    frames = []
    for progress in (0.0, 0.75):
        pool.gaze_progress = progress
        frame = pygame.Surface((960, 540), pygame.SRCALPHA)
        pool.draw(frame, reflection_sprite=normal, anomaly_sprite=turned, show_reflection=True)
        frames.append(frame)
    assert pygame.image.tobytes(frames[0], "RGBA") != pygame.image.tobytes(frames[1], "RGBA")
    rim = pygame.Rect(pool.visual_rect.left, pool.visual_rect.top, pool.visual_rect.width, pool.WATER_INSET)
    assert pygame.image.tobytes(frames[0].subsurface(rim), "RGBA") == pygame.image.tobytes(frames[1].subsurface(rim), "RGBA")
    assert pool.reflection_flash_timer == 0


def test_moon_pool_violation_reflection_adds_red_eyes():
    pool = MoonPool()
    surface = pygame.Surface((config.MAP_WIDTH, config.MAP_HEIGHT), pygame.SRCALPHA)
    reflection = pygame.Surface((18, 28), pygame.SRCALPHA)
    reflection.fill((*palette.PALE_MOON, 255))

    pool.flash_reflection()
    pool.draw(
        surface,
        reflection_sprite=reflection,
        anomaly_sprite=reflection,
        observer_center=(pool.rect.centerx, pool.visual_rect.bottom + 8),
        show_reflection=True,
    )

    sample = pool.visual_rect.inflate(-34, -34)
    colors = {
        surface.get_at((x, y))[:3]
        for x in range(sample.left, sample.right)
        for y in range(sample.top, sample.bottom)
        if surface.get_at((x, y)).a > 0
    }
    assert any(r > 100 and r > g * 1.8 and r > b * 1.5 for r, g, b in colors)


def test_moon_pool_reflection_tracks_observer_to_near_shore():
    pool = MoonPool()
    reflection = pygame.Surface((18, 28), pygame.SRCALPHA)
    reflection.fill((*palette.PALE_MOON, 255))

    def changed_centroid(observer):
        base = pygame.Surface((config.MAP_WIDTH, config.MAP_HEIGHT), pygame.SRCALPHA)
        shown = pygame.Surface((config.MAP_WIDTH, config.MAP_HEIGHT), pygame.SRCALPHA)
        pool.draw(base)
        pool.draw(shown, reflection_sprite=reflection, observer_center=observer, show_reflection=True)
        points = [
            (x, y)
            for y in range(pool.visual_rect.top, pool.visual_rect.bottom)
            for x in range(pool.visual_rect.left, pool.visual_rect.right)
            if base.get_at((x, y)) != shown.get_at((x, y))
        ]
        return sum(x for x, _ in points) / len(points), sum(y for _, y in points) / len(points)

    _x_bottom, y_bottom = changed_centroid((pool.rect.centerx, pool.visual_rect.bottom + 20))
    _x_top, y_top = changed_centroid((pool.rect.centerx, pool.visual_rect.top - 20))

    assert y_bottom > y_top


def test_moon_pool_reflection_keeps_feet_near_observer_shore():
    pool = MoonPool()
    reflection = pygame.Surface((18, 28), pygame.SRCALPHA)
    reflection.fill((220, 40, 40, 255), pygame.Rect(0, 0, 18, 10))  # head
    reflection.fill((40, 80, 220, 255), pygame.Rect(0, 18, 18, 10))  # feet
    surface = pygame.Surface((config.MAP_WIDTH, config.MAP_HEIGHT), pygame.SRCALPHA)

    pool.draw(
        surface,
        reflection_sprite=reflection,
        observer_center=(pool.rect.centerx, pool.visual_rect.bottom + 20),
        show_reflection=True,
    )

    sample = pool.visual_rect.inflate(-34, -34)
    red_y = []
    blue_y = []
    for y in range(sample.top, sample.bottom):
        for x in range(sample.left, sample.right):
            r, g, b, a = surface.get_at((x, y))
            if a and r > b * 1.25:
                red_y.append(y)
            if a and b > r * 1.25:
                blue_y.append(y)
    assert red_y and blue_y
    assert sum(blue_y) / len(blue_y) > sum(red_y) / len(red_y)




