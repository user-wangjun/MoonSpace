# tests/unit/test_main.gd
extends GutTest

var _main: Node2D

func before_each() -> void:
	# 清除 RuleEngine 中已有规则，确保测试隔离
	RuleEngine.clear()
	GameState.reset()
	# 加载主场景
	var scene = load("res://scenes/main.tscn")
	_main = scene.instantiate()
	add_child(_main)

func after_each() -> void:
	if _main != null and is_instance_valid(_main):
		_main.queue_free()
	RuleEngine.clear()
	GameState.reset()

func test_main_instantiates() -> void:
	assert_not_null(_main, "主场景应能实例化")
	assert_true(is_instance_valid(_main), "主场景应有效")

func test_main_has_player() -> void:
	var player = _main.get_player()
	assert_not_null(player, "应能获取玩家节点")
	assert_true(player.is_in_group("player"), "玩家应在 player 组中")

func test_main_has_game_world() -> void:
	var world = _main.get_game_world()
	assert_not_null(world, "应能获取游戏世界节点")

func test_main_has_wugang() -> void:
	var wugang = _main.get_wugang()
	assert_not_null(wugang, "应能获取吴刚 NPC 节点")

func test_main_has_yutu() -> void:
	var yutu = _main.get_yutu()
	assert_not_null(yutu, "应能获取玉兔 NPC 节点")

func test_all_rules_registered() -> void:
	assert_true(_main.are_all_rules_registered(), "所有规则应已注册")
	assert_true(RuleEngine.has_rule("rule_bow_to_tree"), "月桂树规则应已注册")
	assert_true(RuleEngine.has_rule("rule_pool_reflection"), "水池规则应已注册")
	assert_true(RuleEngine.has_pseudo_rule("pseudo_rule_yutu_watch"), "玉兔伪规则应已注册")

func test_initial_rules_discovered() -> void:
	# 开场应已发现 3 条规则
	assert_eq(GameState.known_rules.size(), 3, "应已发现 3 条规则")
	assert_true(GameState.known_rules.has("rule_bow_to_tree"), "应包含月桂树规则")
	assert_true(GameState.known_rules.has("rule_pool_reflection"), "应包含水池规则")
	assert_true(GameState.known_rules.has("pseudo_rule_yutu_watch"), "应包含玉兔伪规则")

func test_player_initial_position() -> void:
	var player = _main.get_player()
	assert_eq(player.position, Vector2(48, 200), "玩家初始位置应为 (48, 200)")

func test_wugang_initial_position() -> void:
	var wugang = _main.get_wugang()
	assert_eq(wugang.position, Vector2(96, 48), "吴刚初始位置应为 (96, 48)")

func test_yutu_initial_position() -> void:
	var yutu = _main.get_yutu()
	assert_eq(yutu.position, Vector2(112, 184), "玉兔初始位置应为 (112, 184)")

func test_rule_descriptions_not_empty() -> void:
	var rules = RuleEngine.get_all_rules()
	for rule_id in rules:
		assert_gt(len(rules[rule_id]), 0, "规则 %s 的描述不应为空" % rule_id)
