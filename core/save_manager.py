"""多槽位存档管理。"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import config


SAVE_SLOT_COUNT = 3


class CorruptSaveError(ValueError):
    """存档内容无法安全读取或不符合基础结构。"""


class SaveManager:
    """使用 JSON 文件管理 3 个存档槽位。"""

    def __init__(self, save_dir: str | Path | None = None) -> None:
        self.save_dir = Path(save_dir) if save_dir is not None else default_save_dir()
        self.save_dir.mkdir(parents=True, exist_ok=True)

    def list_slots(self) -> list[dict[str, Any]]:
        """返回所有槽位摘要，用于存档菜单展示。"""
        return [self.get_slot_summary(slot_id) for slot_id in range(1, SAVE_SLOT_COUNT + 1)]

    def get_slot_summary(self, slot_id: int) -> dict[str, Any]:
        """返回单个槽位摘要。"""
        self._validate_slot(slot_id)
        try:
            data = self.load(slot_id)
        except (CorruptSaveError, OSError):
            return {
                "slot_id": slot_id,
                "exists": True,
                "corrupted": True,
                "label": "存档损坏",
            }
        if data is None:
            return {"slot_id": slot_id, "exists": False, "label": "新游戏"}
        return {
            "slot_id": slot_id,
            "exists": True,
            "label": "继续游戏",
            "saved_at": data.get("saved_at", "未知时间"),
            "violation_count": data.get("violation_count", 0),
            "known_rule_count": len(data.get("known_rules", {})),
            "opening_seen": data.get("opening_seen", False),
            "home_tutorial_done": data.get("home_tutorial_done", False),
        }

    def load(self, slot_id: int) -> dict[str, Any] | None:
        """读取槽位；空槽返回 None。"""
        self._validate_slot(slot_id)
        path = self._slot_path(slot_id)
        if not path.exists():
            return None
        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (json.JSONDecodeError, UnicodeError) as error:
            raise CorruptSaveError(f"corrupt save slot {slot_id}") from error

        if not isinstance(data, dict):
            raise CorruptSaveError(f"save slot {slot_id} must contain an object")
        for key in ("home_tutorial", "mainline", "player", "known_rules", "laurel_tree", "wugang", "yutu"):
            if key in data and not isinstance(data[key], dict):
                raise CorruptSaveError(f"save slot {slot_id} has invalid {key}")
        data = self._migrate_payload(data)
        self._validate_payload(slot_id, data)
        return data

    def save(self, slot_id: int, data: dict[str, Any]) -> dict[str, Any]:
        """写入槽位，并补齐保存时间和槽位编号。"""
        self._validate_slot(slot_id)
        payload = self.default_save(slot_id)
        payload.update(data)
        payload["slot_id"] = slot_id
        payload["saved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        path = self._slot_path(slot_id)
        temp_path = path.with_suffix(".json.tmp")
        try:
            with temp_path.open("w", encoding="utf-8") as file:
                json.dump(payload, file, ensure_ascii=False, indent=2)
                file.flush()
            temp_path.replace(path)
        finally:
            temp_path.unlink(missing_ok=True)
        return payload

    def delete(self, slot_id: int) -> None:
        """删除指定槽位。"""
        self._validate_slot(slot_id)
        path = self._slot_path(slot_id)
        if path.exists():
            path.unlink()

    def default_save(self, slot_id: int) -> dict[str, Any]:
        """创建新游戏默认存档结构。"""
        self._validate_slot(slot_id)
        return {
            "slot_id": slot_id,
            "saved_at": "",
            "opening_seen": False,
            "home_tutorial_done": False,
            "scene": "home",
            "home_tutorial": {
                "sign_read": False,
                "rules_briefing_complete": False,
                "practice_done": False,
            },
            "mainline": {
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
            },
            "envoy_register": {"name": "", "registered": False},
            "player": {"x": config.PLAYER_START_X, "y": config.PLAYER_START_Y, "facing": "down"},
            "violation_count": 0,
            "known_rules": {},
            "laurel_tree": {"bleeding": False},
            "wugang": {"chop_count": 0},
            "yutu": {"is_pounding": True},
        }

    def _slot_path(self, slot_id: int) -> Path:
        """返回槽位文件路径。"""
        return self.save_dir / f"slot_{slot_id}.json"

    @staticmethod
    def _validate_slot(slot_id: int) -> None:
        """限制槽位编号为 1 到 3。"""
        if slot_id < 1 or slot_id > SAVE_SLOT_COUNT:
            raise ValueError(f"invalid save slot: {slot_id}")

    @staticmethod
    def _validate_payload(slot_id: int, data: dict[str, Any]) -> None:
        """验证会直接参与状态恢复的字段，避免坏档在进入游戏后才崩溃。"""
        for key in ("opening_seen", "home_tutorial_done"):
            if key in data and not isinstance(data[key], bool):
                raise CorruptSaveError(f"save slot {slot_id} has invalid {key}")

        violation_count = data.get("violation_count", 0)
        if isinstance(violation_count, bool) or not isinstance(violation_count, int) or not 0 <= violation_count <= 3:
            raise CorruptSaveError(f"save slot {slot_id} has invalid violation_count")

        player = data.get("player", {})
        for key in ("x", "y"):
            value = player.get(key)
            if value is not None and (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
            ):
                raise CorruptSaveError(f"save slot {slot_id} has invalid player.{key}")
        if "facing" in player and player["facing"] not in ("up", "down", "left", "right"):
            raise CorruptSaveError(f"save slot {slot_id} has invalid player.facing")

        known_rules = data.get("known_rules", {})
        if any(not isinstance(key, str) or not isinstance(value, str) for key, value in known_rules.items()):
            raise CorruptSaveError(f"save slot {slot_id} has invalid known_rules")

        home_tutorial = data.get("home_tutorial", {})
        for key in ("sign_read", "rules_briefing_complete", "practice_done"):
            if key in home_tutorial and not isinstance(home_tutorial[key], bool):
                raise CorruptSaveError(f"save slot {slot_id} has invalid home_tutorial.{key}")

        mainline = data.get("mainline", {})
        for key in (
            "wugang_checked",
            "yutu_checked",
            "wugang_polluted",
            "yutu_polluted",
            "report_completed",
            "handoff_completed",
            "return_countdown_active",
            "return_departed_on_time",
            "broken_jade_obtained",
        ):
            if key in mainline and not isinstance(mainline[key], bool):
                raise CorruptSaveError(f"save slot {slot_id} has invalid mainline.{key}")
        envoy_register = data.get("envoy_register", {})
        if not isinstance(envoy_register, dict):
            raise CorruptSaveError(f"save slot {slot_id} has invalid envoy_register")
        if "registered" in envoy_register and not isinstance(envoy_register["registered"], bool):
            raise CorruptSaveError(f"save slot {slot_id} has invalid envoy_register.registered")
        if "name" in envoy_register and not isinstance(envoy_register["name"], str):
            raise CorruptSaveError(f"save slot {slot_id} has invalid envoy_register.name")
        name = envoy_register.get("name", "")
        if len(name) > 4:
            raise CorruptSaveError(f"save slot {slot_id} has inconsistent envoy_register")
        countdown = mainline.get("return_countdown_remaining", 0.0)
        if (
            isinstance(countdown, bool)
            or not isinstance(countdown, (int, float))
            or not math.isfinite(countdown)
            or countdown < 0
        ):
            raise CorruptSaveError(f"save slot {slot_id} has invalid mainline.return_countdown_remaining")
        for key in ("pending_pool_ending", "ending"):
            if key in mainline and not isinstance(mainline[key], str):
                raise CorruptSaveError(f"save slot {slot_id} has invalid mainline.{key}")

        laurel_tree = data.get("laurel_tree", {})
        if "bleeding" in laurel_tree and not isinstance(laurel_tree["bleeding"], bool):
            raise CorruptSaveError(f"save slot {slot_id} has invalid laurel_tree.bleeding")
        chop_count = data.get("wugang", {}).get("chop_count", 0)
        if isinstance(chop_count, bool) or not isinstance(chop_count, int) or chop_count < 0:
            raise CorruptSaveError(f"save slot {slot_id} has invalid wugang.chop_count")
        yutu = data.get("yutu", {})
        if "is_pounding" in yutu and not isinstance(yutu["is_pounding"], bool):
            raise CorruptSaveError(f"save slot {slot_id} has invalid yutu.is_pounding")

    @staticmethod
    def _migrate_payload(data: dict[str, Any]) -> dict[str, Any]:
        """把早期平铺来使字段和倒计时字段迁移到当前存档结构。"""
        migrated = dict(data)

        envoy_register = migrated.get("envoy_register")
        if not isinstance(envoy_register, dict):
            envoy_register = {}
        if "registered" not in envoy_register and "envoy_registered" in migrated:
            envoy_register["registered"] = migrated["envoy_registered"]
        if "name" not in envoy_register and "envoy_name" in migrated:
            legacy_name = migrated["envoy_name"]
            # 旧版允许更长的姓名；新流程不再收集姓名，但已有平铺值仍需可载入。
            envoy_register["name"] = legacy_name[:4] if isinstance(legacy_name, str) else legacy_name
        migrated["envoy_register"] = envoy_register

        mainline = migrated.get("mainline")
        if mainline is None:
            mainline = {}
        elif not isinstance(mainline, dict):
            return migrated
        for key in (
            "report_completed",
            "handoff_completed",
            "return_countdown_active",
            "return_departed_on_time",
            "pending_pool_ending",
            "ending",
        ):
            if key not in mainline and key in migrated:
                mainline[key] = migrated[key]
        if "handoff_completed" not in mainline:
            # Legacy saves cannot resume the transient Chang'e dialogue.
            mainline["handoff_completed"] = bool(
                mainline.get("report_completed")
                or mainline.get("pending_pool_ending")
                or mainline.get("ending")
            )
        if "return_countdown_remaining" not in mainline:
            if "return_countdown" in mainline:
                mainline["return_countdown_remaining"] = mainline["return_countdown"]
            elif "return_countdown" in migrated:
                mainline["return_countdown_remaining"] = migrated["return_countdown"]
        mainline.setdefault("return_countdown_remaining", 0.0)
        if "return_countdown_active" not in mainline:
            remaining = mainline["return_countdown_remaining"]
            mainline["return_countdown_active"] = bool(
                mainline.get("report_completed") and isinstance(remaining, (int, float)) and remaining > 0
            )
        if "return_departed_on_time" not in mainline:
            mainline["return_departed_on_time"] = bool(
                migrated.get("return_to_moon_valley_before_timer", False)
            )
        if (
            migrated.get("scene") == "home"
            and mainline.get("report_completed")
            and mainline.get("return_countdown_active")
            and not mainline.get("pending_pool_ending")
        ):
            mainline["return_departed_on_time"] = True
        if mainline.get("return_departed_on_time"):
            mainline["return_countdown_active"] = False
            mainline["return_countdown_remaining"] = 0.0

        # 旧版本双污染结局 ID 的兼容迁移；新存档统一使用 be_double。
        for key in ("pending_pool_ending", "ending"):
            if mainline.get(key) == "be_laurel_mixed":
                mainline[key] = "be_double"

        migrated["mainline"] = mainline
        return migrated


def default_save_dir() -> Path:
    """返回稳定存档目录，避免启动工作目录变化导致存档消失。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "saves"
    return Path(__file__).resolve().parents[1] / "saves"
