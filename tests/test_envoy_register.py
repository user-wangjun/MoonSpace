import pygame

import config
from core.input_manager import InputManager
from ui.envoy_register import EnvoyRegister


def test_register_can_read_all_three_scrolls_before_writing_name():
    register = EnvoyRegister()
    inputs = InputManager()
    register.open_records()
    inputs._keys_pressed_once.add(pygame.K_RIGHT)
    register.update(inputs)
    register.update(inputs)

    assert register.mode == register.MODE_READ
    assert register.page == 2
    assert "勿留姓名" in register.RECORDS[2]
    assert register.RECORDS[0][1] == "甲子七二"
    assert register.RECORDS[2][1] == "甲子六九"


def test_records_and_registration_open_as_separate_interactions():
    register = EnvoyRegister()

    register.open_records()
    assert register.mode == register.MODE_READ
    register.close()

    register.open_register()
    assert register.mode == register.MODE_REGISTER
    assert not hasattr(register, "MODE_MENU")
    assert not hasattr(register, "MODE_VERIFY")
    assert not hasattr(register, "MODE_WRITE")


def test_registration_page_accepts_name_and_submits_with_enter():
    register = EnvoyRegister()
    inputs = InputManager()
    register.open_register()

    assert register.update(inputs) is False
    inputs.text_input = "玄"
    inputs._keys_pressed_once.add(pygame.K_RETURN)

    assert register.update(inputs) is True
    assert register.name == "玄"
    assert register.registered is True
    assert register.mode == register.MODE_COMPLETE


def test_registration_page_submits_unnamed_envoy_on_enter():
    register = EnvoyRegister()
    inputs = InputManager()
    register.open_register()
    inputs._keys_pressed_once.add(pygame.K_RETURN)

    assert register.update(inputs) is True
    assert register.registered is True
    assert register.mode == register.MODE_COMPLETE
    assert register.collect_save_data() == {"name": "无名", "registered": True}


def test_registration_page_allows_enter_button_without_typing(monkeypatch):
    register = EnvoyRegister()
    register.open_register()
    buttons = []
    monkeypatch.setattr(
        register,
        "_draw_button",
        lambda surface, rect, label, *, active: buttons.append((label, active)),
    )

    register._draw_name_input(pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT)))

    assert ("Enter 登记", True) in buttons


def test_registration_can_finish_and_close_using_keypad_enter():
    register = EnvoyRegister()
    inputs = InputManager()
    register.open_register()

    for expected_mode in (register.MODE_COMPLETE, register.MODE_SEALED):
        inputs.begin_frame()
        inputs.process_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_KP_ENTER, mod=0))
        register.update(inputs)
        assert register.mode == expected_mode

    inputs.begin_frame()
    inputs.process_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0))
    assert register.update(inputs) is False
    assert register.active is False
    assert register.collect_save_data() == {"name": "无名", "registered": True}


def test_registration_page_uses_confirmed_unsubmitted_columns():
    register = EnvoyRegister()

    assert register._registration_columns(False) == (
        "来使登记", "凌霄来使", "来使姓名", "待书",
        "职司已验", "月桂已查", "玉兔已查", "入宫登记",
        "复命未毕", "候月未定", "返程未定", "神志清明", "形貌如初",
        "尚未归档", "广寒宫录",
    )


def test_registration_page_restores_finalized_status_columns():
    register = EnvoyRegister()

    columns = register._registration_columns(True)

    assert columns[11:13] == ("神志清明", "形貌如初")


def test_registration_page_accepts_real_textinput_events():
    register = EnvoyRegister()
    inputs = InputManager()
    register.open_register()
    inputs.begin_frame()
    inputs.process_event(pygame.event.Event(pygame.TEXTINPUT, {"text": "玄"}))
    inputs.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN, "mod": 0}))

    assert register.update(inputs) is True
    assert register.name == "玄"
    assert register.registered is True


def test_leaving_write_mode_does_not_keep_unsubmitted_name():
    register = EnvoyRegister()
    inputs = InputManager()
    register.open_register()
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


def test_legacy_name_data_remains_bounded_when_loaded():
    register = EnvoyRegister()
    register.apply_save_data({"name": "凌霄来使甲", "registered": True})

    assert register.name == "凌霄来使"
    assert register.registered is True


def test_all_record_columns_fit_the_fifteen_slip_format():
    register = EnvoyRegister()

    assert len(register._slip_safe_rects()) == 15
    assert all(len(columns) == 15 for columns in register.RECORD_COLUMNS)
    assert all(len(column) <= 4 for columns in register.RECORD_COLUMNS for column in columns)
