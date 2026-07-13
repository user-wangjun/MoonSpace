"""存档菜单测试。"""

import pygame

from core.save_manager import SaveManager
from ui.save_menu import SAVE_MODE_DELETE, SAVE_MODE_LOAD, SAVE_MODE_NEW, SaveMenu


class NumberOneInput:
    def was_pressed(self, action):
        _ = action
        return False

    def was_key_pressed(self, key):
        return key == pygame.K_1


def test_save_menu_refreshes_slots(tmp_path):
    manager = SaveManager(tmp_path)
    menu = SaveMenu(manager)
    manager.save(1, {"opening_seen": True})

    menu.refresh()

    assert menu.slots[0]["exists"] is True


def test_save_menu_open_sets_mode(tmp_path):
    manager = SaveManager(tmp_path)
    menu = SaveMenu(manager)

    menu.open(SAVE_MODE_NEW)

    assert menu.mode == SAVE_MODE_NEW
    assert menu.back_requested is False


def test_delete_slot_removes_save(tmp_path):
    manager = SaveManager(tmp_path)
    menu = SaveMenu(manager)
    manager.save(1, {"opening_seen": True})

    menu.open(SAVE_MODE_DELETE)
    menu._delete_slot(1)

    assert manager.load(1) is None
    assert "已删除" in menu.message


def test_load_mode_refuses_corrupt_slot_without_overwriting_it(tmp_path):
    corrupt_path = tmp_path / "slot_1.json"
    corrupt_path.write_text("broken", encoding="utf-8")
    menu = SaveMenu(SaveManager(tmp_path))
    menu.open(SAVE_MODE_LOAD)

    selected = menu.update(0.016, NumberOneInput())

    assert selected is None
    assert "存档损坏" in menu.message
    assert corrupt_path.read_text(encoding="utf-8") == "broken"


def test_delete_mode_can_remove_corrupt_slot(tmp_path):
    corrupt_path = tmp_path / "slot_1.json"
    corrupt_path.write_text("broken", encoding="utf-8")
    menu = SaveMenu(SaveManager(tmp_path))
    menu.open(SAVE_MODE_DELETE)

    menu.update(0.016, NumberOneInput())

    assert not corrupt_path.exists()


def test_new_mode_can_explicitly_replace_corrupt_slot(tmp_path):
    (tmp_path / "slot_1.json").write_text("broken", encoding="utf-8")
    menu = SaveMenu(SaveManager(tmp_path))
    menu.open(SAVE_MODE_NEW)

    selected = menu.update(0.016, NumberOneInput())

    assert selected == 1
