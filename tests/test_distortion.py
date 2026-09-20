"""世界扭曲特效测试。"""

from core.event_bus import EventBus, PLAYER_DIED, RULE_DISCOVERED, TREE_BLEEDING, VIOLATION_CHANGED
from effects.distortion import DistortionEffect


def test_violation_triggers_shake_and_flash():
    bus = EventBus()
    effect = DistortionEffect(bus)

    bus.emit(VIOLATION_CHANGED, count=2, rule_id="rule")

    assert effect.shake_timer > 0
    assert effect.flash_timer > 0
    assert effect.horror_intensity >= 0.4


def test_tree_bleeding_triggers_blood_pulse():
    bus = EventBus()
    effect = DistortionEffect(bus)

    bus.emit(TREE_BLEEDING, source="wugang")

    assert effect.blood_pulse_timer == 1.2
    assert effect.shake_timer > 0


def test_rule_discovery_and_death_have_desktop_screen_feedback():
    bus = EventBus()
    effect = DistortionEffect(bus)

    bus.emit(RULE_DISCOVERED, rule_id="rule", rule_text="text")
    assert effect.shake_timer == 0.14
    assert effect.shake_intensity == 1.5

    bus.emit(PLAYER_DIED, count=3, rule_id="rule")
    assert effect.shake_timer == 0.55
    assert effect.shake_intensity == 8.0


def test_screen_shake_toggle_leaves_visual_horror_feedback_enabled():
    bus = EventBus()
    effect = DistortionEffect(bus)
    effect.set_shake_enabled(False)

    bus.emit(VIOLATION_CHANGED, count=2, rule_id="rule")

    assert effect.shake_timer == 0.0
    assert effect.flash_timer > 0.0
    assert effect.horror_intensity >= 0.4


def test_update_resets_camera_offset_after_shake():
    bus = EventBus()
    effect = DistortionEffect(bus)
    effect.start_shake(3.0, 0.1)

    effect.update(0.2)

    assert effect.shake_timer == 0.0
    assert effect.camera_offset.xy == (0, 0)


def test_reset_clears_effect_state():
    bus = EventBus()
    effect = DistortionEffect(bus)
    bus.emit(VIOLATION_CHANGED, count=3, rule_id="rule")

    effect.reset()

    assert effect.shake_timer == 0.0
    assert effect.horror_intensity == 0.0
    assert effect.flash_timer == 0.0


def test_restore_violation_count_restores_only_persistent_horror():
    effect = DistortionEffect(EventBus())

    effect.restore_violation_count(2)

    assert effect.horror_intensity == 0.4
    assert effect.shake_timer == 0.0
    assert effect.flash_timer == 0.0
