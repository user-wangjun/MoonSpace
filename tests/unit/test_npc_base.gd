# tests/unit/test_npc_base.gd
extends GutTest

const NPCBaseScene = preload("res://scenes/npc_base.tscn")
const PlayerScene = preload("res://scenes/player.tscn")

var npc: Area2D
var player: CharacterBody2D

func before_each():
	npc = NPCBaseScene.instantiate()
	add_child(npc)
	player = PlayerScene.instantiate()
	add_child(player)

func after_each():
	npc.free()
	player.free()

# 测试 NPC 场景可实例化
func test_npc_base_instantiates():
	assert_not_null(npc, "NPCBase 场景应可实例化")

# 测试默认属性
func test_npc_base_default_properties():
	assert_eq(npc.npc_id, "", "默认 npc_id 应为空")
	assert_eq(npc.interaction_prompt, "按 E 交互", "默认交互提示应正确")
	assert_false(npc.is_player_in_range(), "初始状态玩家不应在范围内")

# 测试设置 NPC 属性
func test_npc_base_set_properties():
	npc.npc_id = "wugang"
	npc.dialogs = ["你好", "我是吴刚"]
	assert_eq(npc.npc_id, "wugang", "npc_id 应可设置")
	assert_eq(npc.dialogs.size(), 2, "对话数组应有 2 条")

# 测试玩家进入范围
func test_npc_base_player_enter_range():
	npc._on_body_entered(player)
	assert_true(npc.is_player_in_range(), "玩家进入后应在范围内")

# 测试玩家离开范围
func test_npc_base_player_exit_range():
	npc._on_body_entered(player)
	npc._on_body_exited(player)
	assert_false(npc.is_player_in_range(), "玩家离开后不应在范围内")

# 测试非玩家进入不触发
func test_npc_base_non_player_ignored():
	var other = Node2D.new()
	add_child(other)
	npc._on_body_entered(other)
	assert_false(npc.is_player_in_range(), "非玩家进入不应触发")
	other.free()

# 测试对话触发——通过 EventBus 信号验证
func test_npc_base_start_dialog():
	npc.npc_id = "test_npc"
	npc.dialogs = ["第一句", "第二句"]
	var state = {"id": "", "count": 0}
	EventBus.show_dialog.connect(func(id: String, dlgs: Array):
		state["id"] = id
		state["count"] = dlgs.size()
	)
	npc._start_dialog()
	assert_eq(state["id"], "test_npc", "应通过 EventBus 发送 NPC ID")
	assert_eq(state["count"], 2, "应发送 2 条对话")

# 测试空对话不触发
func test_npc_base_empty_dialogs_no_emit():
	npc.npc_id = "empty_npc"
	npc.dialogs = []
	var state = {"emitted": false}
	EventBus.show_dialog.connect(func(_id, _dlgs): state["emitted"] = true)
	npc._start_dialog()
	assert_false(state["emitted"], "空对话不应触发 EventBus 信号")

# 测试获取对话内容
func test_npc_base_get_dialogs():
	npc.dialogs = ["A", "B", "C"]
	var dlgs = npc.get_dialogs()
	assert_eq(dlgs.size(), 3, "get_dialogs 应返回 3 条对话")
