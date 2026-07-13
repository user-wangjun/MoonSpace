"""输入管理：将 Pygame 键盘状态映射为游戏动作。"""

from __future__ import annotations

import pygame

from config import (
    ACTION_INTERACT,
    ACTION_MOVE_DOWN,
    ACTION_MOVE_LEFT,
    ACTION_MOVE_RIGHT,
    ACTION_MOVE_UP,
    ACTION_OPEN_RULE_BOOK,
    ACTION_QUIT,
    ACTION_RESTART,
    ACTION_RUN,
)


class InputManager:
    """区分持续按键和单次触发，避免 UI 交互每帧重复执行。"""

    HOLD_KEY_MAP = {
        ACTION_MOVE_UP: (pygame.K_w, pygame.K_UP),
        ACTION_MOVE_DOWN: (pygame.K_s, pygame.K_DOWN),
        ACTION_MOVE_LEFT: (pygame.K_a, pygame.K_LEFT),
        ACTION_MOVE_RIGHT: (pygame.K_d, pygame.K_RIGHT),
        ACTION_RUN: (pygame.K_LSHIFT, pygame.K_RSHIFT),
    }

    PRESS_KEY_MAP = {
        ACTION_INTERACT: (pygame.K_e, pygame.K_SPACE),
        ACTION_OPEN_RULE_BOOK: (pygame.K_TAB,),
        ACTION_RESTART: (pygame.K_r,),
        ACTION_QUIT: (pygame.K_ESCAPE,),
    }

    def __init__(self) -> None:
        self._pressed_once: set[str] = set()
        self._keys_pressed_once: set[int] = set()
        self.text_input = ""
        self.scroll_y = 0
        self.fullscreen_toggle_requested = False
        self.quit_requested = False

    def begin_frame(self) -> None:
        """每帧开始时清空单次触发缓存。"""
        self._pressed_once.clear()
        self._keys_pressed_once.clear()
        self.text_input = ""
        self.scroll_y = 0
        self.fullscreen_toggle_requested = False
        self.quit_requested = False

    def process_event(self, event: pygame.event.Event) -> None:
        """处理 Pygame 事件并记录单次动作。"""
        if event.type == pygame.QUIT:
            self.quit_requested = True
            self._pressed_once.add(ACTION_QUIT)
            return

        if event.type == pygame.TEXTINPUT:
            self.text_input += event.text
            return

        if event.type == pygame.MOUSEWHEEL:
            self.scroll_y += event.y
            return

        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_F11 or (
            event.key in (pygame.K_RETURN, pygame.K_KP_ENTER)
            and getattr(event, "mod", 0) & pygame.KMOD_ALT
        ):
            self.fullscreen_toggle_requested = True
            return

        self._keys_pressed_once.add(event.key)

        for action, keys in self.PRESS_KEY_MAP.items():
            if event.key in keys:
                self._pressed_once.add(action)

    def is_pressed(self, action: str) -> bool:
        """查询持续动作，例如移动和跑步。"""
        keys = self.HOLD_KEY_MAP.get(action, ())
        pressed = pygame.key.get_pressed()
        return any(pressed[key] for key in keys)

    def was_pressed(self, action: str) -> bool:
        """查询本帧单次触发动作，例如交互、Tab 和 ESC。"""
        return action in self._pressed_once

    def was_key_pressed(self, key: int) -> bool:
        """查询某个物理按键是否在本帧刚按下，用于菜单快捷键。"""
        return key in self._keys_pressed_once
