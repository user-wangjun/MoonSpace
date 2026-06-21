# tests/integration/test_main_scene_integration.gd
extends GutTest

## 主场景集成测试——验证所有子系统协同工作
## 此测试在 GUT 框架内运行，autoload 单例可用

var _main: Node2D

func before_each() -> void:
	RuleEngine.clear()
	GameState.reset()
	var scene = load("res://scenes/main.tscn")
	_main = scene.instantiate()
	add_child(_main)
	# 等待一帧让所有 @onready 和 _ready 执行
	await wait_physics_frames(1)

func after_each() -> void:
	if _main != null and is_instance_valid(_main):
		_main.queue_free()
	RuleEngine.clear()
	GameState.reset()

func test_main_scene_loads_with_all_subsystems() -> void:
	assert_not_null(_main, "主场景应能加载")
	assert_true(is_instance_valid(_main), "主场景应有效")

func test_all_subsystem_nodes_present() -> void:
	var expected_nodes = [
		"GameWorld", "Player", "WugangNPC", "YutuNPC",
		"RootSpread", "DistortionManager", "DeathEffect",
		"UI/DialogBox", "UI/RuleBook", "UI/OverlayEffect"
	]
	for path in expected_nodes:
		assert_true(_main.has_node(path), "应存在子节点: %s" % path)

func test_all_rules_registered_on_load() -> void:
	assert_true(_main.are_all_rules_registered(), "所有规则应在加载时注册")
	assert_true(RuleEngine.has_rule("rule_bow_to_tree"), "月桂树规则应已注册")
	assert_true(RuleEngine.has_rule("rule_pool_reflection"), "水池规则应已注册")
	assert_true(RuleEngine.has_pseudo_rule("pseudo_rule_yutu_watch"), "玉兔伪规则应已注册")

func test_initial_state_correct() -> void:
	assert_eq(GameState.violation_count, 0, "初始违规次数应为 0")
	assert_eq(GameState.known_rules.size(), 3, "应已发现 3 条规则")
	assert_false(GameState.is_dead(), "玩家初始不应死亡")

func test_player_exists_and_in_group() -> void:
	var player = _main.get_player()
	assert_not_null(player, "玩家节点不应为空")
	assert_true(player.is_in_group("player"), "玩家应在 player 组中")

func test_npc_positions_correct() -> void:
	# NPC 是 Area2D，不受物理碰撞影响，位置应保持
	assert_eq(_main.get_wugang().position, Vector2(96, 48), "吴刚应在树旁")
	assert_eq(_main.get_yutu().position, Vector2(112, 184), "玉兔应在水池旁")

func test_rule_violation_triggers_state_change() -> void:
	# 模拟违反月桂树规则
	RuleEngine.check_rule("rule_bow_to_tree", {})
	assert_eq(GameState.violation_count, 1, "违规后次数应为 1")

func test_three_violations_trigger_death() -> void:
	RuleEngine.check_rule("rule_bow_to_tree", {})
	RuleEngine.check_rule("rule_pool_reflection", {})
	RuleEngine.check_rule("rule_bow_to_tree", {})
	assert_eq(GameState.violation_count, 3, "三次违规后次数应为 3")
	assert_true(GameState.is_dead(), "三次违规后玩家应死亡")

func test_pseudo_rule_violation_when_followed() -> void:
	# 遵守伪规则（靠近玉兔）应导致违规
	RuleEngine.check_pseudo_rule("pseudo_rule_yutu_watch", {})
	assert_eq(GameState.violation_count, 1, "遵守伪规则应导致 1 次违规")

func test_rule_descriptions_are_meaningful() -> void:
	var rules = RuleEngine.get_all_rules()
	for rule_id in rules:
		var desc = rules[rule_id]
		assert_gt(len(desc), 10, "规则 %s 描述应足够详细" % rule_id)

func test_violation_and_death_flow() -> void:
	# 完整流程：3 次违规 → 死亡
	assert_false(GameState.is_dead(), "初始不应死亡")
	RuleEngine.check_rule("rule_bow_to_tree", {})
	assert_false(GameState.is_dead(), "1 次违规后不应死亡")
	RuleEngine.check_rule("rule_pool_reflection", {})
	assert_false(GameState.is_dead(), "2 次违规后不应死亡")
	RuleEngine.check_rule("rule_bow_to_tree", {})
	assert_true(GameState.is_dead(), "3 次违规后应死亡")
