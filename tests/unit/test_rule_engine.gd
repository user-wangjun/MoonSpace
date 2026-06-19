# tests/unit/test_rule_engine.gd
extends GutTest

# 每个测试前重置 GameState 和 RuleEngine 状态
func before_each():
	GameState.reset()
	RuleEngine.clear()

# 测试注册并查找规则
func test_register_and_check_rule():
	RuleEngine.register_rule("rule_bow_to_tree", {
		"description": "见树需稽首",
		"check": func(_ctx): return true
	})
	assert_true(RuleEngine.has_rule("rule_bow_to_tree"), "应能找到已注册的规则")

# 测试规则检测返回 true（合规）
func test_check_rule_returns_true():
	RuleEngine.register_rule("always_true", {
		"description": "总是真",
		"check": func(_ctx): return true
	})
	var result = RuleEngine.check_rule("always_true", {})
	assert_true(result, "规则检测应返回 true")

# 测试规则检测返回 false 时触发违规
func test_check_rule_returns_false_triggers_violation():
	RuleEngine.register_rule("always_false", {
		"description": "总是假",
		"check": func(_ctx): return false
	})
	var result = RuleEngine.check_rule("always_false", {})
	assert_false(result, "规则检测应返回 false")
	assert_eq(GameState.violation_count, 1, "违规次数应增加 1")

# 测试未知规则默认放过
func test_check_unknown_rule_passes():
	var result = RuleEngine.check_rule("nonexistent_rule", {})
	assert_true(result, "未知规则应默认放过")

# 测试伪规则——遵守反而违规
func test_register_pseudo_rule():
	RuleEngine.register_pseudo_rule("run_is_respect", {
		"description": "广寒宫前疾走以示敬意",
		"check": func(_ctx): return true
	})
	assert_true(RuleEngine.has_pseudo_rule("run_is_respect"), "应能找到已注册的伪规则")

# 测试遵守伪规则增加违规次数
func test_check_pseudo_rule_followed_triggers_violation():
	RuleEngine.register_pseudo_rule("run_is_respect", {
		"description": "广寒宫前疾走以示敬意",
		"check": func(_ctx): return true  # 玩家遵守了陷阱
	})
	var result = RuleEngine.check_pseudo_rule("run_is_respect", {})
	assert_false(result, "遵守伪规则应返回 false（上当了）")
	assert_eq(GameState.violation_count, 1, "遵守伪规则应增加违规次数")

# 测试未遵守伪规则不增加违规
func test_check_pseudo_rule_not_followed_no_violation():
	RuleEngine.register_pseudo_rule("run_is_respect", {
		"description": "广寒宫前疾走以示敬意",
		"check": func(_ctx): return false  # 玩家没遵守陷阱
	})
	var result = RuleEngine.check_pseudo_rule("run_is_respect", {})
	assert_true(result, "未遵守伪规则应返回 true（没上当）")
	assert_eq(GameState.violation_count, 0, "未遵守伪规则不应增加违规次数")

# 测试获取所有规则描述
func test_get_all_rules():
	RuleEngine.register_rule("rule_1", {
		"description": "规则一",
		"check": func(_ctx): return true
	})
	RuleEngine.register_rule("rule_2", {
		"description": "规则二",
		"check": func(_ctx): return true
	})
	var all = RuleEngine.get_all_rules()
	assert_eq(all.size(), 2, "应有 2 条规则")
	assert_eq(all["rule_1"], "规则一", "规则一描述应匹配")
	assert_eq(all["rule_2"], "规则二", "规则二描述应匹配")
