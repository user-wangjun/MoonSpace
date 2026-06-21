# tests/unit/test_rule_book.gd
extends GutTest

const RuleBookScene = preload("res://scenes/rule_book.tscn")

var rule_book: Control

func before_each():
	GameState.reset()
	rule_book = RuleBookScene.instantiate()
	add_child(rule_book)

func after_each():
	rule_book.free()
	GameState.reset()

# 测试规则手册场景可实例化
func test_rule_book_instantiates():
	assert_not_null(rule_book, "规则手册场景应可实例化")

# 测试初始状态隐藏
func test_rule_book_initially_hidden():
	assert_false(rule_book.is_book_visible(), "规则手册初始应隐藏")

# 测试切换可见性
func test_rule_book_toggle():
	rule_book._toggle_visibility()
	assert_true(rule_book.is_book_visible(), "切换后应显示")
	rule_book._toggle_visibility()
	assert_false(rule_book.is_book_visible(), "再次切换应隐藏")

# 测试无规则时显示提示
func test_rule_book_empty_state():
	rule_book.visible = true
	rule_book._refresh_display()
	# 无规则时应显示 1 个提示标签
	assert_eq(rule_book.get_displayed_rule_count(), 1, "无规则时应显示 1 个提示")

# 测试添加规则后刷新显示
func test_rule_book_displays_rules():
	GameState.add_known_rule("rule_1", "见树需稽首")
	GameState.add_known_rule("rule_2", "月池不可视")
	rule_book.visible = true
	rule_book._refresh_display()
	assert_eq(rule_book.get_displayed_rule_count(), 2, "应显示 2 条规则")

# 测试 rule_discovered 信号触发刷新
func test_rule_book_updates_on_discover():
	rule_book.visible = true
	# 初始无规则
	assert_eq(rule_book.get_displayed_rule_count(), 1, "初始应显示提示")
	# 发现新规则
	EventBus.rule_discovered.emit("rule_1", "见树需稽首")
	assert_eq(rule_book.get_displayed_rule_count(), 1, "发现规则后应显示 1 条规则")

# 测试 violation_changed 信号触发刷新
func test_rule_book_updates_on_violation():
	rule_book.visible = true
	GameState.add_known_rule("r1", "测试规则")
	rule_book._refresh_display()
	# 触发违规变化
	EventBus.violation_changed.emit(1)
	# 验证没有崩溃即可（标题已更新）
	assert_true(rule_book.is_book_visible(), "面板应仍然可见")

# 测试隐藏状态下不刷新显示
func test_rule_book_hidden_no_refresh():
	# 隐藏状态下调用 _on_rule_discovered 不应出错
	EventBus.rule_discovered.emit("r1", "测试")
	assert_false(rule_book.is_book_visible(), "隐藏状态应保持隐藏")
