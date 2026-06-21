# tests/unit/test_wugang_npc.gd
extends GutTest

const WuGangScene = preload("res://scenes/wugang_npc.tscn")
const PlayerScene = preload("res://scenes/player.tscn")

var wugang: Area2D
var player: CharacterBody2D

func before_each():
	wugang = WuGangScene.instantiate()
	add_child(wugang)
	player = PlayerScene.instantiate()
	add_child(player)

func after_each():
	wugang.free()
	player.free()

# 测试吴刚场景可实例化
func test_wugang_instantiates():
	assert_not_null(wugang, "吴刚场景应可实例化")

# 测试默认属性
func test_wugang_default_properties():
	assert_eq(wugang.npc_id, "wugang", "默认 npc_id 应为 wugang")
	assert_eq(wugang.chop_count, 0, "初始砍伐次数应为 0")
	assert_false(wugang.is_bleeding(), "初始状态不应流血")

# 测试砍伐增加计数
func test_wugang_chop_increases_count():
	wugang.chop()
	assert_eq(wugang.get_chop_count(), 1, "砍一次后计数应为 1")

# 测试第 5 刀触发流血信号
func test_wugang_bleed_at_5th_chop():
	var state = {"bled": false}
	EventBus.tree_bleeding.connect(func(): state["bled"] = true)
	# 砍 4 刀不应流血
	for i in range(4):
		wugang.chop()
	assert_false(state["bled"], "砍 4 刀不应触发流血")
	assert_false(wugang.is_bleeding(), "砍 4 刀不应处于流血状态")
	# 第 5 刀应触发流血
	wugang.chop()
	assert_true(state["bled"], "第 5 刀应触发流血信号")
	assert_true(wugang.is_bleeding(), "第 5 刀后应处于流血状态")

# 测试玩家进入范围
func test_wugang_player_enter_range():
	wugang._on_body_entered(player)
	assert_true(wugang.is_player_in_range(), "玩家进入后应在范围内")

# 测试玩家离开范围
func test_wugang_player_exit_range():
	wugang._on_body_entered(player)
	wugang._on_body_exited(player)
	assert_false(wugang.is_player_in_range(), "玩家离开后不应在范围内")

# 测试对话内容
func test_wugang_has_dialogs():
	var dlgs = wugang.get_dialogs()
	assert_gt(dlgs.size(), 0, "吴刚应有对话内容")

# 测试对话触发
func test_wugang_start_dialog():
	var state = {"id": "", "count": 0}
	EventBus.show_dialog.connect(func(id: String, dlgs: Array):
		state["id"] = id
		state["count"] = dlgs.size()
	)
	wugang._start_dialog()
	assert_eq(state["id"], "wugang", "应发送 wugang 作为 NPC ID")
	assert_gt(state["count"], 0, "应发送对话内容")

# 测试重置状态
func test_wugang_reset():
	wugang.chop()
	wugang.chop()
	wugang.reset()
	assert_eq(wugang.get_chop_count(), 0, "重置后砍伐次数应为 0")

# 测试砍伐常量
func test_wugang_constants():
	assert_eq(wugang.BLEED_THRESHOLD, 5, "流血阈值应为 5")
	assert_eq(wugang.CHOP_INTERVAL, 2.0, "砍伐间隔应为 2 秒")
