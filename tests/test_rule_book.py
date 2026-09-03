"""规则手册 UI 测试。"""

import pygame

from core.event_bus import EventBus
from core.game_state import GameState
from ui.rule_book import RuleBook
from utils import palette


class FakeInput:
    def __init__(self, pressed=False):
        self.pressed = pressed

    def was_pressed(self, action):
        return self.pressed and action == "open_rule_book"

    def was_key_pressed(self, key):
        return False

    scroll_y = 0


def test_rule_book_toggles_with_tab_action():
    state = GameState(EventBus())
    rule_book = RuleBook(state.event_bus, state)

    rule_book.update(0.1, FakeInput(True))
    assert rule_book.is_open
    rule_book.update(0.1, FakeInput(True))
    assert not rule_book.is_open


def test_rule_book_updates_when_rule_discovered():
    state = GameState(EventBus())
    rule_book = RuleBook(state.event_bus, state)

    state.add_known_rule("rule", "见树需稽首")

    assert rule_book.rules == {"rule": "见树需稽首"}
    assert rule_book._rule_lines() == ["1. 见树需稽首"]


def test_rule_book_appends_broken_jade_clue_after_it_is_obtained():
    state = GameState(EventBus())
    rule_book = RuleBook(state.event_bus, state)
    state.add_known_rule("rule", "月池不可久视。")

    rule_book.set_broken_jade_obtained(True)

    assert rule_book._rule_lines()[-2:] == [
        "2. 留名者，名归月籍。",
        "3. 命既毕，速离月宫。",
    ]


def test_rule_book_draw_uses_register_frame_colors():
    state = GameState(EventBus())
    rule_book = RuleBook(state.event_bus, state)
    state.add_known_rule("rule", "见树需稽首")
    rule_book.toggle()
    surface = pygame.Surface((480, 270))

    rule_book.draw(surface)

    colors = {surface.get_at((x, y))[:3] for x in range(58, 422) for y in range(28, 240)}
    assert palette.MOON_WHITE in colors
    assert palette.WOOD_DARK in colors
    assert palette.DARK_BLOOD in colors


def test_rule_book_clips_long_content_and_draws_scrollbar():
    state = GameState(EventBus())
    rule_book = RuleBook(state.event_bus, state)
    for index in range(12):
        state.add_known_rule(str(index), "这是一条会自动换行的月宫规条，用于验证正文不会穿过底边。")
    rule_book.toggle()
    surface = pygame.Surface((480, 270))
    surface.fill((3, 5, 7))

    rule_book.draw(surface)

    assert surface.get_at((404, 90))[:3] in (palette.NIGHT_BLACK, palette.DARK_BLOOD)
    assert surface.get_at((200, 244))[:3] == (3, 5, 7)
    assert rule_book._max_scroll() > 0


def test_rule_book_scrolls_with_mouse_wheel_and_clamps():
    state = GameState(EventBus())
    rule_book = RuleBook(state.event_bus, state)
    for index in range(12):
        state.add_known_rule(str(index), "长规则内容，需要滚动查看。")
    rule_book.toggle()
    inputs = FakeInput()
    inputs.scroll_y = -3

    rule_book.update(0.1, inputs)

    assert rule_book.scroll_line == min(3, rule_book._max_scroll())
