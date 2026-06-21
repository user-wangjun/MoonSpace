# scripts/ui/rule_book.gd
extends Control

## 规则手册面板——按 Tab 切换显示/隐藏
## 实时显示已发现的规则和当前违规次数
## 监听 EventBus.rule_discovered 信号自动更新

# 规则列表容器
@onready var _rule_list: VBoxContainer = $Panel/ScrollContainer/RuleList

# 标题标签（显示规则数和违规数）
@onready var _title_label: Label = $Panel/TitleLabel

## 初始化时隐藏面板并连接信号
func _ready() -> void:
	visible = false
	EventBus.rule_discovered.connect(_on_rule_discovered)
	EventBus.violation_changed.connect(_on_violation_changed)
	_refresh_display()

## 每帧检测 Tab 键切换
func _unhandled_input(_event: InputEvent) -> void:
	if Input.is_action_just_pressed("toggle_rulebook"):
		_toggle_visibility()

## 切换面板显示状态
func _toggle_visibility() -> void:
	visible = not visible
	if visible:
		_refresh_display()

## 发现新规则时刷新显示
func _on_rule_discovered(_rule_id: String, _rule_text: String) -> void:
	_refresh_display()

## 违规次数变化时刷新显示
func _on_violation_changed(_count: int) -> void:
	_refresh_display()

## 刷新面板内容——清空并重新填充规则列表
func _refresh_display() -> void:
	# 更新标题
	var rule_count = GameState.known_rules.size()
	var violation = GameState.violation_count
	_title_label.text = "规则手册  |  已知规则: %d  |  违规: %d/3" % [rule_count, violation]

	# 清空旧列表（使用 free 立即移除，避免 queue_free 延迟导致重复）
	for child in _rule_list.get_children():
		child.free()

	# 填充规则
	var rule_index = 1
	for rule_id in GameState.known_rules:
		var label = Label.new()
		label.text = "%d. %s" % [rule_index, GameState.known_rules[rule_id]]
		_rule_list.add_child(label)
		rule_index += 1

	# 如果没有规则，显示提示
	if GameState.known_rules.is_empty():
		var empty_label = Label.new()
		empty_label.text = "尚未发现任何规则..."
		empty_label.modulate = Color(0.5, 0.5, 0.5)
		_rule_list.add_child(empty_label)

## 获取当前显示的规则数量（用于测试）
func get_displayed_rule_count() -> int:
	return _rule_list.get_child_count()

## 检查面板是否可见
func is_book_visible() -> bool:
	return visible
