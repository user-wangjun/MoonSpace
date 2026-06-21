# tests/unit/test_yutu_npc.gd
extends GutTest

const YuTuScene = preload("res://scenes/yutu_npc.tscn")
const PlayerScene = preload("res://scenes/player.tscn")

var yutu: Area2D
var player: CharacterBody2D

func before_each():
	yutu = YuTuScene.instantiate()
	add_child(yutu)
	player = PlayerScene.instantiate()
	add_child(player)

func after_each():
	yutu.free()
	player.free()

# 测试玉兔场景可实例化
func test_yutu_instantiates():
	assert_not_null(yutu, "玉兔场景应可实例化")

# 测试默认属性
func test_yutu_default_properties():
	assert_eq(yutu.npc_id, "yutu", "默认 npc_id 应为 yutu")
	assert_true(yutu.is_currently_pounding(), "初始状态应正在捣药")

# 测试玩家进入时停止捣药
func test_yutu_stops_pounding_on_enter():
	yutu._on_body_entered(player)
	assert_false(yutu.is_currently_pounding(), "玩家进入后应停止捣药")

# 测试玩家离开时恢复捣药
func test_yutu_resumes_pounding_on_exit():
	yutu._on_body_entered(player)
	yutu._on_body_exited(player)
	assert_true(yutu.is_currently_pounding(), "玩家离开后应恢复捣药")

# 测试捣药状态变化触发 EventBus 信号
func test_yutu_pounding_changed_signal():
	var state = {"pounding": true}
	EventBus.yutu_pounding_changed.connect(func(p: bool): state["pounding"] = p)
	yutu._on_body_entered(player)
	assert_false(state["pounding"], "进入时应发送 false 信号")
	yutu._on_body_exited(player)
	assert_true(state["pounding"], "离开时应发送 true 信号")

# 测试对话内容
func test_yutu_has_dialogs():
	var dlgs = yutu.get_dialogs()
	assert_gt(dlgs.size(), 0, "玉兔应有对话内容")

# 测试对话触发
func test_yutu_start_dialog():
	var state = {"id": "", "count": 0}
	EventBus.show_dialog.connect(func(id: String, dlgs: Array):
		state["id"] = id
		state["count"] = dlgs.size()
	)
	yutu._start_dialog()
	assert_eq(state["id"], "yutu", "应发送 yutu 作为 NPC ID")
	assert_gt(state["count"], 0, "应发送对话内容")

# 测试 set_pounding 幂等性
func test_yutu_set_pounding_idempotent():
	var call_count = {"count": 0}
	EventBus.yutu_pounding_changed.connect(func(_p): call_count["count"] += 1)
	# 已经在捣药，再设 true 不应触发信号
	yutu.set_pounding(true)
	assert_eq(call_count["count"], 0, "状态未变不应触发信号")
	# 设 false 应触发
	yutu.set_pounding(false)
	assert_eq(call_count["count"], 1, "状态变化应触发信号")

# 测试重置
func test_yutu_reset():
	yutu._on_body_entered(player)
	yutu.reset()
	assert_true(yutu.is_currently_pounding(), "重置后应恢复捣药状态")
	assert_false(yutu.is_player_in_range(), "重置后玩家不应在范围内")
