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
    assert register.mode == register.MODE_VERIFY


def test_identity_verification_needs_no_personal_name():
    register = EnvoyRegister()
    inputs = InputManager()
    register.open_register()

    assert register.update(inputs) is False
    inputs._pressed_once.add(config.ACTION_INTERACT)

    assert register.update(inputs) is True
    assert register.name == ""
    assert register.registered is True
    assert register.mode == register.MODE_COMPLETE


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
