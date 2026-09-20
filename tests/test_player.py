"""玩家实体测试。"""

import pygame
import pytest

import config
from entities.player import Player


class FakeInput:
    def __init__(self, pressed=None):
        self.pressed = set(pressed or [])

    def is_pressed(self, action):
        return action in self.pressed


def test_player_initial_state():
    player = Player(10, 20)

    assert player.rect.topleft == (10, 20)
    assert player.facing == "down"
    assert player.anim_state == "idle"


def test_player_moves_right():
    player = Player(10, 20)

    player.update(1.0, FakeInput({config.ACTION_MOVE_RIGHT}), [])

    assert player.rect.x == 10 + config.PLAYER_WALK_SPEED
    assert player.facing == "right"
    assert player.anim_state == "walk"


def test_player_run_speed_is_faster():
    player = Player(10, 20)

    player.update(1.0, FakeInput({config.ACTION_MOVE_RIGHT, config.ACTION_RUN}), [])

    assert player.rect.x == 10 + config.PLAYER_RUN_SPEED


def test_player_does_not_cross_obstacle():
    player = Player(10, 20)
    obstacle = pygame.Rect(40, 20, 16, 24)

    player.update(1.0, FakeInput({config.ACTION_MOVE_RIGHT}), [obstacle])

    assert player.rect.right == obstacle.left


def test_player_is_clamped_to_world_bounds():
    player = Player(0, 0)

    player.update(1.0, FakeInput({config.ACTION_MOVE_LEFT, config.ACTION_MOVE_UP}), [])

    assert player.rect.left == 0
    assert player.rect.top == 0


def test_player_can_use_scene_specific_world_bounds():
    player = Player(940, 700)

    player.update(1.0, FakeInput({config.ACTION_MOVE_RIGHT, config.ACTION_MOVE_DOWN}), [], (960, 720))

    assert player.rect.right == 960
    assert player.rect.bottom == 720


def test_interact_animation_can_be_triggered():
    player = Player()

    player.trigger_interact_animation()

    assert player.anim_state == "interact"


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


def test_player_draw_uses_png_envoy_sprite():
    player = Player(10, 10)
    surface = pygame.Surface((64, 64), pygame.SRCALPHA)

    player.draw(surface)

    colors = {
        surface.get_at((x, y))[:4]
        for x in range(player.rect.left, player.rect.right)
        for y in range(player.rect.top, player.rect.bottom)
        if surface.get_at((x, y)).a > 0
    }
    assert len(colors) > 20


def test_player_sprite_facing_override_does_not_change_player_state():
    player = Player()
    player.facing = "up"

    normal = player.get_current_sprite()
    turned = player.get_current_sprite("down")

    assert player.facing == "up"
    assert normal.get_size() == turned.get_size()
    assert pygame.image.tobytes(normal, "RGBA") != pygame.image.tobytes(turned, "RGBA")


def test_player_reflection_sprite_uses_opposite_facing_for_all_directions():
    player = Player()

    for facing, reflected_facing in player.REFLECTION_FACING.items():
        player.facing = facing
        reflected = player.get_reflection_sprite()
        expected = player.get_current_sprite(reflected_facing)
        assert pygame.image.tobytes(reflected, "RGBA") == pygame.image.tobytes(expected, "RGBA")


def test_player_walk_frames_keep_visible_size_and_foot_anchor_stable():
    player = Player()
    player.anim_state = "walk"

    for facing in player.VALID_FACINGS:
        player.facing = facing
        bounds_by_frame = []
        for frame in range(4):
            player.current_frame = frame
            bounds_by_frame.append(player.get_current_sprite().get_bounding_rect(min_alpha=1))

        assert {bounds.height for bounds in bounds_by_frame} == {60}
        assert {bounds.bottom for bounds in bounds_by_frame} == {62}


@pytest.mark.parametrize("fps", [30, 60, 144, 240])
@pytest.mark.parametrize("running", [False, True])
def test_movement_preserves_subpixels_across_frame_rates(fps, running):
    player = Player(100, 100)
    actions = {config.ACTION_MOVE_RIGHT}
    if running:
        actions.add(config.ACTION_RUN)
    for _ in range(fps):
        player.update(1 / fps, FakeInput(actions), [])
    speed = config.PLAYER_RUN_SPEED if running else config.PLAYER_WALK_SPEED
    assert player.position.x == pytest.approx(100 + speed)
    assert player.rect.x == 100 + speed


def test_head_can_overlap_scenery_while_feet_pass_below_it():
    player = Player(10, 20)
    obstacle = pygame.Rect(40, 10, 16, 20)
    player.update(0.5, FakeInput({config.ACTION_MOVE_RIGHT}), [obstacle])
    assert player.rect.x == 50


@pytest.mark.parametrize("dt", [0.1, 1 / 240])
def test_pushing_wall_is_not_actual_movement(dt):
    player = Player(24, 20)
    player.update(dt, FakeInput({config.ACTION_MOVE_RIGHT}), [pygame.Rect(40, 0, 16, 100)])
    assert not player.is_moving()
    assert player.anim_state == "idle"


def test_subpixel_movement_cannot_accumulate_outside_world_boundary():
    player = Player(944, 20)
    player.update(1 / 240, FakeInput({config.ACTION_MOVE_RIGHT}), [])
    assert player.position.x == 944
    assert not player.is_moving()


@pytest.mark.parametrize("reverse", [False, True])
def test_sweep_stops_at_nearest_thin_wall_regardless_of_order(reverse):
    player = Player(10, 20)
    walls = [pygame.Rect(80, 0, 1, 100), pygame.Rect(40, 0, 1, 100)]
    player.update(2.0, FakeInput({config.ACTION_MOVE_RIGHT}), walls[::-1] if reverse else walls)
    assert player.rect.right == 40


def test_upward_collision_uses_feet_and_slides_along_wall():
    player = Player(50, 40)
    wall = pygame.Rect(0, 10, 200, 20)
    player.update(1.0, FakeInput({config.ACTION_MOVE_UP, config.ACTION_MOVE_RIGHT}), [wall])
    assert player.get_collision_rect().top == wall.bottom
    assert player.rect.x > 50
    assert player.is_moving()
