# tests/unit/test_distortion_manager.gd
extends GutTest

var manager: Node

func before_each():
	manager = preload("res://scripts/world/distortion_manager.gd").new()
	add_child(manager)

func after_each():
	manager.free()

# 测试管理器可实例化
func test_manager_instantiates():
	assert_not_null(manager, "扭曲管理器应可实例化")

# 测试初始状态
func test_manager_initial_state():
	assert_eq(manager.get_distortion_level(), 0, "初始扭曲等级应为 0")
	assert_false(manager.is_shaking(), "初始不应震动")

# 测试违规 1 级触发震动
func test_manager_violation_1_triggers_shake():
	manager._on_violation_changed(1)
	assert_eq(manager.get_distortion_level(), 1, "扭曲等级应为 1")
	assert_true(manager.is_shaking(), "应开始震动")
	assert_eq(manager.get_shake_intensity(), manager.SHAKE_LEVEL_1, "震动强度应为等级 1")

# 测试违规 2 级更强震动
func test_manager_violation_2_stronger_shake():
	manager._on_violation_changed(2)
	assert_eq(manager.get_distortion_level(), 2, "扭曲等级应为 2")
	assert_eq(manager.get_shake_intensity(), manager.SHAKE_LEVEL_2, "震动强度应为等级 2")

# 测试违规 3 级最强震动
func test_manager_violation_3_max_shake():
	manager._on_violation_changed(3)
	assert_eq(manager.get_distortion_level(), 3, "扭曲等级应为 3")
	assert_eq(manager.get_shake_intensity(), manager.SHAKE_LEVEL_3, "震动强度应为等级 3")

# 测试月桂树流血触发震动
func test_manager_tree_bleeding_triggers_shake():
	manager._on_tree_bleeding()
	assert_true(manager.is_shaking(), "流血应触发震动")
	assert_eq(manager.get_shake_intensity(), manager.SHAKE_LEVEL_3, "流血震动应为最强")

# 测试玩家死亡停止震动
func test_manager_player_died_stops_shake():
	manager._on_violation_changed(2)
	assert_true(manager.is_shaking(), "应正在震动")
	manager._on_player_died()
	assert_false(manager.is_shaking(), "死亡后应停止震动")

# 测试震动持续时间内保持震动
func test_manager_shake_duration():
	manager._on_violation_changed(1)
	# 处理小于持续时间的帧
	manager._process(0.3)
	assert_true(manager.is_shaking(), "持续时间内应保持震动")

# 测试震动超时后停止
func test_manager_shake_timeout():
	manager._on_violation_changed(1)
	# 处理超过持续时间的帧
	manager._process(0.6)
	assert_false(manager.is_shaking(), "超时后应停止震动")

# 测试重置
func test_manager_reset():
	manager._on_violation_changed(2)
	manager.reset()
	assert_eq(manager.get_distortion_level(), 0, "重置后等级应为 0")
	assert_false(manager.is_shaking(), "重置后不应震动")

# 测试震动常量
func test_manager_constants():
	assert_eq(manager.SHAKE_LEVEL_1, 1.0, "等级 1 强度应为 1.0")
	assert_eq(manager.SHAKE_LEVEL_2, 3.0, "等级 2 强度应为 3.0")
	assert_eq(manager.SHAKE_LEVEL_3, 6.0, "等级 3 强度应为 6.0")
	assert_eq(manager.SHAKE_DURATION, 0.5, "震动持续应为 0.5 秒")
