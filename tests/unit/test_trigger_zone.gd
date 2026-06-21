# tests/unit/test_trigger_zone.gd
extends GutTest

const TriggerZoneScene = preload("res://scenes/trigger_zone.tscn")
const PlayerScene = preload("res://scenes/player.tscn")

var trigger: Area2D
var player: CharacterBody2D

func before_each():
	GameState.reset()
	RuleEngine.clear()
	trigger = TriggerZoneScene.instantiate()
	add_child(trigger)
	player = PlayerScene.instantiate()
	add_child(player)

func after_each():
	trigger.free()
	player.free()

# 测试 TriggerZone 场景可实例化
func test_trigger_zone_instantiates():
	assert_not_null(trigger, "TriggerZone 场景应可实例化")

# 测试默认导出属性
func test_trigger_zone_default_properties():
	assert_eq(trigger.rule_id, "", "默认 rule_id 应为空字符串")
	assert_eq(trigger.trigger_type, "enter", "默认 trigger_type 应为 enter")

# 测试设置规则 ID 和触发类型
func test_trigger_zone_set_properties():
	trigger.rule_id = "test_rule"
	trigger.trigger_type = "exit"
	assert_eq(trigger.rule_id, "test_rule", "rule_id 应可设置")
	assert_eq(trigger.trigger_type, "exit", "trigger_type 应可设置")

# 测试 enter 触发——注册一个返回 false 的规则，玩家进入应触发违规
func test_trigger_zone_enter_triggers_violation():
	RuleEngine.register_rule("enter_rule", {
		"description": "进入即违规",
		"check": func(_ctx): return false
	})
	trigger.rule_id = "enter_rule"
	trigger.trigger_type = "enter"
	# 手动调用 _on_body_entered 模拟玩家进入
	trigger._on_body_entered(player)
	assert_eq(GameState.violation_count, 1, "玩家进入应触发违规")

# 测试 exit 触发——离开时才检测
func test_trigger_zone_exit_triggers_violation():
	RuleEngine.register_rule("exit_rule", {
		"description": "离开即违规",
		"check": func(_ctx): return false
	})
	trigger.rule_id = "exit_rule"
	trigger.trigger_type = "exit"
	# 玩家进入不应触发
	trigger._on_body_entered(player)
	assert_eq(GameState.violation_count, 0, "玩家进入 exit 类型区域不应触发违规")
	# 玩家离开应触发
	trigger._on_body_exited(player)
	assert_eq(GameState.violation_count, 1, "玩家离开应触发违规")

# 测试空 rule_id 不触发检测
func test_trigger_zone_empty_rule_id_no_check():
	trigger.rule_id = ""
	trigger._on_body_entered(player)
	assert_eq(GameState.violation_count, 0, "空 rule_id 不应触发任何检测")

# 测试 enter 类型不响应 exit 事件
func test_trigger_zone_enter_type_ignores_exit():
	RuleEngine.register_rule("enter_only", {
		"description": "仅进入检测",
		"check": func(_ctx): return false
	})
	trigger.rule_id = "enter_only"
	trigger.trigger_type = "enter"
	trigger._on_body_exited(player)
	assert_eq(GameState.violation_count, 0, "enter 类型不应响应 exit 事件")
