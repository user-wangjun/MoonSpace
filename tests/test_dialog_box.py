"""对话框 UI 测试。"""

import pygame

from core.event_bus import DIALOG_ACTIVE_CHANGED, DIALOG_CHOICE_SELECTED, EventBus, SHOW_DIALOG
from ui.dialog_box import DialogBox
from utils import palette


class FakeInput:
    def __init__(self, pressed=False):
        self.pressed = pressed

    def was_pressed(self, action):
        return self.pressed and action == "interact"


def test_dialog_box_opens_on_show_dialog():
    bus = EventBus()
    dialog = DialogBox(bus)

    bus.emit(SHOW_DIALOG, speaker_id="npc", lines=["a", "b"])

    assert dialog.active
    assert dialog.current_line == "a"


def test_dialog_box_advances_and_closes():
    bus = EventBus()
    dialog = DialogBox(bus)
    bus.emit(SHOW_DIALOG, speaker_id="npc", lines=["a", "b"])

    dialog.update(0.1, FakeInput(True))
    assert dialog.current_line == "b"
    dialog.update(0.1, FakeInput(True))
    assert not dialog.active


def test_dialog_box_emits_active_changed_events():
    bus = EventBus()
    received = []
    bus.subscribe(DIALOG_ACTIVE_CHANGED, lambda **payload: received.append(payload))
    dialog = DialogBox(bus)

    bus.emit(SHOW_DIALOG, speaker_id="npc", lines=["a"])
    dialog.advance()

    assert received == [
        {"active": True, "speaker_id": "npc"},
        {"active": False, "speaker_id": "npc"},
    ]


def test_dialog_box_selects_choice_on_final_line():
    bus = EventBus()
    received = []
    bus.subscribe(DIALOG_CHOICE_SELECTED, lambda **payload: received.append(payload))
    dialog = DialogBox(bus)

    bus.emit(
        SHOW_DIALOG,
        speaker_id="wugang",
        lines=["先看。", "再记。"],
        choices=[{"id": "record", "text": "只记录"}, {"id": "overstep", "text": "替一响"}],
        choice_context="test_check",
    )
    dialog.advance()
    dialog.selected_choice_index = 1
    dialog.advance()

    assert dialog.active is False
    assert received == [
        {
            "speaker_id": "wugang",
            "choice_id": "overstep",
            "choice_text": "替一响",
            "context": "test_check",
        }
    ]


def test_dialog_box_draw_uses_moonspace_frame_colors():
    bus = EventBus()
    dialog = DialogBox(bus)
    surface = pygame.Surface((480, 270))
    bus.emit(SHOW_DIALOG, speaker_id="wugang", lines=["我是吴刚。"])

    dialog.draw(surface)

    colors = {surface.get_at((x, y))[:3] for x in range(18, 462) for y in range(194, 254)}
    assert palette.MOON_WHITE in colors
    assert palette.DEEP_BLUE in colors
    assert palette.DARK_BLOOD in colors


def test_dialog_box_draws_confirmed_portrait_for_mainline_speakers():
    bus = EventBus()
    dialog = DialogBox(bus)
    surface = pygame.Surface((480, 270))
    bus.emit(SHOW_DIALOG, speaker_id="change", lines=["留下来等。"])

    dialog.draw(surface)

    portrait_colors = {
        surface.get_at((x, y))[:3]
        for x in range(12, 104, 8)
        for y in range(32, 244, 12)
    }
    assert len(portrait_colors) > 3


def test_dialog_box_uses_large_portrait_layout_for_all_four_story_characters():
    bus = EventBus()
    dialog = DialogBox(bus)
    surface = pygame.Surface((480, 270))

    for speaker_id in ("player", "change", "wugang", "yutu"):
        surface.fill(palette.BLACK)
        bus.emit(SHOW_DIALOG, speaker_id=speaker_id, lines=["复命。"])
        dialog.draw(surface)

        if speaker_id == "player":
            assert surface.get_at((8, 30))[:3] != palette.BLACK
            assert surface.get_at((112, 194))[:3] == palette.MOON_WHITE
        else:
            assert surface.get_at((468, 30))[:3] != palette.BLACK
            assert surface.get_at((18, 194))[:3] == palette.MOON_WHITE
