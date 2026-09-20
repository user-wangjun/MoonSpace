"""Visual obstacle and depth regressions for the polished maps."""

import pygame

from core.game import Game
from entities.player import Player
from tests.test_player import FakeInput
from utils.assets import load_image
from world.scenery import HALL_LANTERNS, draw_scenery_foreground
import config


def test_hall_blocks_lamp_bases_but_keeps_floor_below_dais_walkable():
    game = Game()
    obstacles = game._guanghan_collision_rects()
    assert any(rect.collidepoint(210, 272) for rect in obstacles)
    assert not any(rect.collidepoint(480, 220) for rect in obstacles)
    assert any(rect.collidepoint(480, 165) for rect in obstacles)
    player = Player(202, 300)
    player.update(1, FakeInput({config.ACTION_MOVE_UP}), obstacles, (960, 720))
    assert player.get_collision_rect().top == 279


def test_hall_lantern_occlusion_tracks_camera_and_ground_depth():
    background = load_image("sprites/moonspace/backgrounds/guanghan_hall_curtain.png")
    surface = pygame.Surface((480, 270))
    surface.fill((255, 0, 255))
    draw_scenery_foreground(surface, background, HALL_LANTERNS, (-100, -100), 260)
    assert surface.get_at((110, 140)) == background.get_at((210, 240))
    assert surface.get_at((155, 140))[:3] == (255, 0, 255)
    surface.fill((255, 0, 255))
    draw_scenery_foreground(surface, background, HALL_LANTERNS, (-100, -100), 300)
    assert surface.get_at((110, 140))[:3] == (255, 0, 255)
