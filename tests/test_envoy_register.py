import pygame

import config
from core.input_manager import InputManager
from ui.envoy_register import EnvoyRegister


def test_register_can_read_all_three_scrolls_before_writing_name():
    register = EnvoyRegister()
    inputs = InputManager()
    register.open()
    register.menu_index = 1
    inputs._pressed_once.add(config.ACTION_INTERACT)

    register.update(inputs)
    inputs._pressed_once.clear()
    inputs._keys_pressed_once.add(pygame.K_RIGHT)
    register.update(inputs)
    register.update(inputs)

    assert register.mode == register.MODE_READ
    assert register.page == 2
    assert "不要留下姓名" not in register.RECORDS[2]


def test_typing_name_and_enter_irreversibly_seals_register():
    register = EnvoyRegister()
    inputs = InputManager()
    register.open()
    register.mode = register.MODE_WRITE
    inputs.text_input = "林月"

    assert register.update(inputs) is False
    inputs.text_input = ""
    inputs._keys_pressed_once.add(pygame.K_RETURN)

    assert register.update(inputs) is True
    assert register.name == "林月"
    assert register.registered is True
    assert register.mode == register.MODE_COMPLETE


def test_leaving_write_mode_does_not_keep_unsubmitted_name():
    register = EnvoyRegister()
    inputs = InputManager()
    register.open()
    register.mode = register.MODE_WRITE
    inputs.text_input = "未提交"
    register.update(inputs)
    inputs.text_input = ""
    inputs._pressed_once.add(config.ACTION_QUIT)

    register.update(inputs)

    assert register.active is False
    assert register.name == ""
    assert register.collect_save_data() == {"name": "", "registered": False}


def test_register_save_data_restores_sealed_state():
    register = EnvoyRegister()
    register.apply_save_data({"name": "无名", "registered": True})

    register.open()

    assert register.mode == register.MODE_SEALED
    assert register.collect_save_data() == {"name": "无名", "registered": True}
