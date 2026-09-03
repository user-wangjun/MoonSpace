"""存档管理测试。"""

import json
from pathlib import Path

import pytest

from core.save_manager import CorruptSaveError, SaveManager, default_save_dir
import config


def test_save_manager_lists_empty_slots(tmp_path):
    manager = SaveManager(tmp_path)

    slots = manager.list_slots()

    assert len(slots) == 3
    assert slots[0]["exists"] is False
    assert slots[0]["label"] == "新游戏"


def test_default_source_save_dir_is_project_root_saves(monkeypatch):
    monkeypatch.delattr("core.save_manager.sys.frozen", raising=False)

    path = default_save_dir()

    assert path == Path(config.__file__).resolve().parent / "saves"


def test_frozen_save_dir_is_next_to_executable(monkeypatch, tmp_path):
    executable = tmp_path / "MoonSpace.exe"
    monkeypatch.setattr("core.save_manager.sys.frozen", True, raising=False)
    monkeypatch.setattr("core.save_manager.sys.executable", str(executable))

    assert default_save_dir() == tmp_path / "saves"


def test_save_and_load_slot(tmp_path):
    manager = SaveManager(tmp_path)

    saved = manager.save(1, {"opening_seen": True, "violation_count": 2})
    loaded = manager.load(1)

    assert saved["slot_id"] == 1
    assert loaded["opening_seen"] is True
    assert loaded["violation_count"] == 2
    assert loaded["saved_at"]


def test_default_save_uses_large_map_spawn(tmp_path):
    manager = SaveManager(tmp_path)

    data = manager.default_save(1)

    assert data["player"]["x"] == config.PLAYER_START_X
    assert data["player"]["y"] == config.PLAYER_START_Y


def test_default_save_starts_before_home_tutorial(tmp_path):
    manager = SaveManager(tmp_path)

    data = manager.default_save(1)

    assert data["home_tutorial_done"] is False
    assert data["home_tutorial"] == {
        "sign_read": False,
        "practice_done": False,
        "rules_briefing_complete": False,
    }


def test_default_save_starts_before_full_mainline(tmp_path):
    manager = SaveManager(tmp_path)

    data = manager.default_save(1)

    assert data["mainline"] == {
        "wugang_checked": False,
        "yutu_checked": False,
        "wugang_polluted": False,
        "yutu_polluted": False,
        "report_completed": False,
        "handoff_completed": False,
        "return_countdown_active": False,
        "return_countdown_remaining": 0.0,
        "return_departed_on_time": False,
        "pending_pool_ending": "",
        "ending": "",
        "broken_jade_obtained": False,
    }

def test_slot_summary_for_existing_save(tmp_path):
    manager = SaveManager(tmp_path)
    manager.save(2, {"known_rules": {"a": "rule"}, "violation_count": 1})

    summary = manager.get_slot_summary(2)

    assert summary["exists"] is True
    assert summary["known_rule_count"] == 1
    assert summary["violation_count"] == 1
    assert summary["home_tutorial_done"] is False


def test_delete_slot(tmp_path):
    manager = SaveManager(tmp_path)
    manager.save(1, {"opening_seen": True})
    manager.delete(1)

    assert manager.load(1) is None


@pytest.mark.parametrize(
    "content",
    (
        "{\"opening_seen\": true",
        "[]",
        json.dumps({"mainline": []}),
        json.dumps({"player": {"x": "bad"}}),
        json.dumps({"violation_count": "3"}),
        json.dumps({"wugang": {"chop_count": "bad"}}),
        json.dumps({"home_tutorial": {"practice_done": 1}}),
        json.dumps({"laurel_tree": {"bleeding": "yes"}}),
        json.dumps({"yutu": {"is_pounding": 1}}),
        json.dumps({"envoy_register": {"name": "超过四个汉字", "registered": True}}),
    ),
)
def test_corrupt_save_is_reported_without_breaking_slot_listing(tmp_path, content):
    (tmp_path / "slot_1.json").write_text(content, encoding="utf-8")
    manager = SaveManager(tmp_path)

    slots = manager.list_slots()

    assert slots[0]["exists"] is True
    assert slots[0]["corrupted"] is True
    assert slots[1]["exists"] is False
    with pytest.raises(CorruptSaveError):
        manager.load(1)


def test_save_atomically_replaces_corrupt_slot(tmp_path):
    (tmp_path / "slot_1.json").write_text("broken", encoding="utf-8")
    manager = SaveManager(tmp_path)

    manager.save(1, {"opening_seen": True})

    assert manager.load(1)["opening_seen"] is True
    assert not (tmp_path / "slot_1.json.tmp").exists()


def test_legacy_flat_envoy_and_countdown_fields_migrate_on_load(tmp_path):
    manager = SaveManager(tmp_path)
    legacy = {
        "slot_id": 1,
        "saved_at": "",
        "opening_seen": True,
        "home_tutorial_done": True,
        "scene": "guanghan",
        "envoy_registered": True,
        "envoy_name": "凌霄来使姓名",
        "report_completed": True,
        "return_countdown": 12.5,
        "player": {"x": 480, "y": 456, "facing": "up"},
        "violation_count": 0,
        "known_rules": {},
    }
    (tmp_path / "slot_1.json").write_text(json.dumps(legacy), encoding="utf-8")

    migrated = manager.load(1)

    assert migrated["envoy_register"] == {"registered": True, "name": "凌霄来使"}
    assert migrated["mainline"]["report_completed"] is True
    assert migrated["mainline"]["return_countdown_active"] is True
    assert migrated["mainline"]["return_countdown_remaining"] == 12.5
    assert migrated["mainline"]["return_departed_on_time"] is False


def test_legacy_countdown_in_courtyard_keeps_running_until_courtyard_exit(tmp_path):
    manager = SaveManager(tmp_path)
    legacy = manager.default_save(1)
    legacy["scene"] = "playing"
    legacy["mainline"].update(
        {
            "report_completed": True,
            "return_countdown_active": True,
            "return_countdown_remaining": 12.5,
        }
    )
    (tmp_path / "slot_1.json").write_text(json.dumps(legacy), encoding="utf-8")

    migrated = manager.load(1)

    assert migrated["mainline"]["return_departed_on_time"] is False
    assert migrated["mainline"]["return_countdown_active"] is True
    assert migrated["mainline"]["return_countdown_remaining"] == 12.5


def test_legacy_double_pollution_id_is_migrated_to_be_double(tmp_path):
    manager = SaveManager(tmp_path)
    legacy = manager.default_save(1)
    legacy["scene"] = "playing"
    legacy["mainline"].update(
        {
            "pending_pool_ending": "be_laurel_mixed",
            "ending": "be_laurel_mixed",
        }
    )
    (tmp_path / "slot_1.json").write_text(json.dumps(legacy), encoding="utf-8")

    migrated = manager.load(1)

    assert migrated["mainline"]["pending_pool_ending"] == "be_double"
    assert migrated["mainline"]["ending"] == "be_double"
