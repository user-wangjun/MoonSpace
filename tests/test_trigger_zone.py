"""触发区域测试。"""

import pygame

from world.trigger_zone import CircularTriggerZone, TriggerZone


def test_enter_trigger_fires_once_when_entering():
    zone = TriggerZone((10, 10, 20, 20), "rule", "enter", cooldown=1.0)
    target = pygame.Rect(12, 12, 4, 4)

    assert zone.update(0.1, target)
    assert not zone.update(0.1, target)


def test_stay_trigger_requires_time():
    zone = TriggerZone((10, 10, 20, 20), "rule", "stay", cooldown=1.0, required_stay=0.5)
    target = pygame.Rect(12, 12, 4, 4)

    assert not zone.update(0.2, target)
    assert not zone.update(0.2, target)
    assert zone.update(0.1, target)


def test_cooldown_prevents_repeated_inside_trigger():
    zone = TriggerZone((10, 10, 20, 20), "rule", "inside", cooldown=1.0)
    target = pygame.Rect(12, 12, 4, 4)

    assert zone.update(0.1, target)
    assert not zone.update(0.1, target)
    assert zone.update(1.0, target)


def test_reset_clears_state():
    zone = TriggerZone((10, 10, 20, 20), "rule", "enter", cooldown=1.0)
    target = pygame.Rect(12, 12, 4, 4)

    assert zone.update(0.1, target)
    zone.reset()
    assert zone.update(0.1, target)


def test_circular_trigger_zone_uses_circle_not_bounding_box_corners():
    zone = CircularTriggerZone((100, 100), 50, "tree", trigger_type="enter")

    assert zone.update(0.1, pygame.Rect(145, 95, 10, 10)) is True
    zone.reset()
    assert zone.update(0.1, pygame.Rect(145, 145, 10, 10)) is False
