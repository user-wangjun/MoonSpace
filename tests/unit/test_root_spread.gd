# tests/unit/test_root_spread.gd
extends GutTest

var _root_spread: Node2D

func before_each() -> void:
	_root_spread = load("res://scripts/effects/root_spread.gd").new()
	add_child(_root_spread)

func after_each() -> void:
	if _root_spread != null and is_instance_valid(_root_spread):
		_root_spread.queue_free()

func test_initial_state_not_spreading() -> void:
	assert_false(_root_spread.is_spreading(), "初始状态不应在蔓延")
	assert_false(_root_spread.visible, "初始应不可见")

func test_initial_length_zero() -> void:
	assert_eq(_root_spread.get_current_length(), 0.0, "初始长度应为 0")

func test_initial_branch_count() -> void:
	assert_eq(_root_spread.get_branch_count(), 5, "应有 5 条根须分支")

func test_start_spread_sets_spreading() -> void:
	_root_spread.start_spread()
	assert_true(_root_spread.is_spreading(), "开始蔓延后应处于蔓延状态")
	assert_true(_root_spread.visible, "开始蔓延后应可见")

func test_stop_spread_clears_state() -> void:
	_root_spread.start_spread()
	_root_spread.stop_spread()
	assert_false(_root_spread.is_spreading(), "停止后不应在蔓延")
	assert_false(_root_spread.visible, "停止后应不可见")
	assert_eq(_root_spread.get_current_length(), 0.0, "停止后长度应归零")

func test_process_grows_length() -> void:
	_root_spread.start_spread()
	_root_spread._process(0.5)
	assert_gt(_root_spread.get_current_length(), 0.0, "处理后长度应增加")

func test_process_caps_at_max_length() -> void:
	_root_spread.start_spread()
	# 模拟大量时间流逝
	_root_spread._process(10.0)
	assert_eq(_root_spread.get_current_length(), 200.0, "长度不应超过最大值")
	assert_false(_root_spread.is_spreading(), "达到最大长度后应停止蔓延")

func test_tree_bleeding_signal_triggers_spread() -> void:
	# 模拟 EventBus 信号
	_root_spread._on_tree_bleeding()
	assert_true(_root_spread.is_spreading(), "月桂树流血信号应触发蔓延")
