# tests/unit/test_game_state.gd
extends GutTest

# 每个测试前重置状态，确保测试隔离
func before_each():
	GameState.reset()

# 测试初始状态值
func test_game_state_initial_values():
	assert_eq(GameState.violation_count, 0, "初始违规次数应为 0")
	assert_eq(GameState.known_rules.size(), 0, "初始已知规则为空")

# 测试增加违规次数
func test_game_state_add_violation():
	GameState.add_violation()
	assert_eq(GameState.violation_count, 1, "违规一次后计数应为 1")

# 测试添加已知规则
func test_game_state_add_known_rule():
	GameState.add_known_rule("rule_1", "见树需稽首")
	assert_eq(GameState.known_rules.size(), 1, "添加一条规则后应为 1")
	assert_eq(GameState.known_rules["rule_1"], "见树需稽首", "规则文本应匹配")

# 测试违规 3 次判定死亡
func test_game_state_is_dead_at_3_violations():
	GameState.violation_count = 3
	assert_true(GameState.is_dead(), "违规 3 次应判定死亡")

# 测试违规不足 3 次未死亡
func test_game_state_not_dead_below_3():
	GameState.violation_count = 2
	assert_false(GameState.is_dead(), "违规 2 次不应判定死亡")

# 测试状态重置
func test_game_state_reset():
	GameState.violation_count = 2
	GameState.add_known_rule("r1", "test")
	GameState.reset()
	assert_eq(GameState.violation_count, 0, "重置后违规次数应为 0")
	assert_eq(GameState.known_rules.size(), 0, "重置后规则列表应为空")
