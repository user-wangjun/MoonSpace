"""全局设置管理；设置文件与具体游戏存档槽位完全分离。"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from core.save_manager import default_save_dir


class SettingsManager:
    """使用独立 JSON 文件保存音量倍率和震动开关。"""

    DEFAULTS = {
        "bgm_volume": 1.0,
        "sfx_volume": 1.0,
        "vibration_enabled": True,
    }
    MIN_VOLUME = 0.0
    MAX_VOLUME = 1.0

    def __init__(self, settings_path: str | Path | None = None) -> None:
        path = Path(settings_path) if settings_path is not None else default_save_dir() / "settings.json"
        # Accept a directory in tests and in small integrations for parity with
        # SaveManager's directory-oriented constructor.
        if path.exists() and path.is_dir():
            path = path / "settings.json"
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.values = self.load()

    def load(self) -> dict[str, float | bool]:
        """读取并规范化设置；损坏或缺失的值回退为默认值。"""
        raw: Any = {}
        if self.path.exists():
            try:
                with self.path.open("r", encoding="utf-8") as file:
                    raw = json.load(file)
            except (OSError, json.JSONDecodeError, UnicodeError):
                raw = {}
        if not isinstance(raw, dict):
            raw = {}

        self.values = {
            "bgm_volume": self._normalize_volume(raw.get("bgm_volume", self.DEFAULTS["bgm_volume"])),
            "sfx_volume": self._normalize_volume(raw.get("sfx_volume", self.DEFAULTS["sfx_volume"])),
            "vibration_enabled": self._normalize_bool(
                raw.get("vibration_enabled", self.DEFAULTS["vibration_enabled"]),
                default=bool(self.DEFAULTS["vibration_enabled"]),
            ),
        }
        return dict(self.values)

    def set_volume(self, key: str, value: float) -> dict[str, float | bool]:
        """设置一个音量倍率并立即持久化。"""
        if key not in ("bgm_volume", "sfx_volume"):
            raise KeyError(key)
        self.values[key] = self._normalize_volume(value)
        self.save()
        return dict(self.values)

    def set_volumes(
        self,
        *,
        bgm_volume: float | None = None,
        sfx_volume: float | None = None,
    ) -> dict[str, float | bool]:
        """批量设置音量倍率并只写入一次文件。"""
        if bgm_volume is not None:
            self.values["bgm_volume"] = self._normalize_volume(bgm_volume)
        if sfx_volume is not None:
            self.values["sfx_volume"] = self._normalize_volume(sfx_volume)
        self.save()
        return dict(self.values)

    def set_vibration_enabled(self, enabled: bool) -> dict[str, float | bool]:
        """设置全局震动开关并立即持久化。"""
        self.values["vibration_enabled"] = bool(enabled)
        self.save()
        return dict(self.values)

    def mute(self) -> dict[str, float | bool]:
        """静音 BGM 与音效，但保留独立的震动开关。"""
        self.values["bgm_volume"] = 0.0
        self.values["sfx_volume"] = 0.0
        self.save()
        return dict(self.values)

    def restore_defaults(self) -> dict[str, float | bool]:
        """恢复默认音量倍率和震动开关。"""
        self.values = dict(self.DEFAULTS)
        self.save()
        return dict(self.values)

    def save(self) -> dict[str, float | bool]:
        """以临时文件替换方式保存设置，避免留下半个 JSON。"""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "bgm_volume": self._normalize_volume(self.values.get("bgm_volume", self.DEFAULTS["bgm_volume"])),
            "sfx_volume": self._normalize_volume(self.values.get("sfx_volume", self.DEFAULTS["sfx_volume"])),
            "vibration_enabled": self._normalize_bool(
                self.values.get("vibration_enabled", self.DEFAULTS["vibration_enabled"]),
                default=bool(self.DEFAULTS["vibration_enabled"]),
            ),
        }
        self.values = payload
        temp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        try:
            with temp_path.open("w", encoding="utf-8") as file:
                json.dump(payload, file, ensure_ascii=False, indent=2)
                file.flush()
            temp_path.replace(self.path)
        finally:
            temp_path.unlink(missing_ok=True)
        return dict(self.values)

    @classmethod
    def _normalize_volume(cls, value: Any) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            return 1.0
        return max(cls.MIN_VOLUME, min(cls.MAX_VOLUME, float(value)))

    @staticmethod
    def _normalize_bool(value: Any, *, default: bool) -> bool:
        """读取旧配置时只接受明确的布尔值或 0/1 数字。"""
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)) and math.isfinite(float(value)):
            return bool(value)
        return default
