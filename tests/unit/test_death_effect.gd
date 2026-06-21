# tests/unit/test_death_effect.gd
extends GutTest

var _death_effect: CanvasLayer

func before_each() -> void:
	_death_effect = load("res://scripts/effects/death_effect.gd").new()
	add_child(_death_effect)

func after_each() -> void:
	if _death_effect != null and is_instance_valid(_death_effect):
		_death_effect.queue_free()

func test_initial_state_hidden() -> void:
	assert_false(_death_effect.visible, "初始应不可见")
	assert_false(_death_effect.is_fading(), "初始不应在淡入")
	assert_false(_death_effect.is_fully_shown(), "初始不应完全显示")

func test_initial_fade_progress_zero() -> void:
	assert_eq(_death_effect.get_fade_progress(), 0.0, "初始淡入进度应为 0")

func test_trigger_death_starts_fading() -> void:
	_death_effect.trigger_death()
	assert_true(_death_effect.visible, "触发后应可见")
	assert_true(_death_effect.is_fading(), "触发后应在淡入")
	assert_false(_death_effect.is_fully_shown(), "触发后不应立即完全显示")

func test_process_increases_fade_progress() -> void:
	_death_effect.trigger_death()
	_death_effect._process(0.5)
	assert_gt(_death_effect.get_fade_progress(), 0.0, "处理后进度应增加")

func test_process_completes_fade() -> void:
	_death_effect.trigger_death()
	# 模拟超过持续时间
	_death_effect._process(2.0)
	assert_eq(_death_effect.get_fade_progress(), 1.0, "进度应达到 1")
	assert_false(_death_effect.is_fading(), "完成后不应在淡入")
	assert_true(_death_effect.is_fully_shown(), "应标记为完全显示")

func test_hide_effect_resets_state() -> void:
	_death_effect.trigger_death()
	_death_effect._process(1.0)
	_death_effect.hide_effect()
	assert_false(_death_effect.visible, "隐藏后应不可见")
	assert_false(_death_effect.is_fading(), "隐藏后不应在淡入")
	assert_false(_death_effect.is_fully_shown(), "隐藏后不应完全显示")
	assert_eq(_death_effect.get_fade_progress(), 0.0, "隐藏后进度应归零")

func test_player_died_signal_triggers_death() -> void:
	_death_effect._on_player_died()
	assert_true(_death_effect.is_fading(), "玩家死亡信号应触发死亡特效")

func test_fade_progress_capped_at_one() -> void:
	_death_effect.trigger_death()
	_death_effect._process(100.0)
	assert_lte(_death_effect.get_fade_progress(), 1.0, "进度不应超过 1")
