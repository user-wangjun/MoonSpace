# scripts/ui/dialog_box.gd
extends Control

## 对话框 UI——监听 EventBus.show_dialog 信号显示对话
## 玩家按 E/空格推进对话，对话结束后自动隐藏

# 当前对话内容数组
var _dialogs: Array = []

# 当前显示的对话索引
var _current_index: int = 0

# 对话文本标签
@onready var _label: Label = $Panel/Label

# 对话提示标签
@onready var _prompt: Label = $Panel/PromptLabel

## 初始化时隐藏并连接信号
func _ready() -> void:
	visible = false
	EventBus.show_dialog.connect(_on_show_dialog)

## 每帧检测推进对话输入
func _unhandled_input(_event: InputEvent) -> void:
	if not visible:
		return
	if Input.is_action_just_pressed("interact") or Input.is_action_just_pressed("ui_accept"):
		_advance_dialog()

## 显示对话——由 EventBus.show_dialog 信号触发
func _on_show_dialog(_npc_id: String, dialogs: Array) -> void:
	if dialogs.is_empty():
		return
	_dialogs = dialogs
	_current_index = 0
	_show_current_line()
	visible = true

## 显示当前对话行
func _show_current_line() -> void:
	if _current_index < _dialogs.size():
		_label.text = _dialogs[_current_index]
		_prompt.text = "(%d/%d) 按 E 继续" % [_current_index + 1, _dialogs.size()]

## 推进到下一行对话
func _advance_dialog() -> void:
	_current_index += 1
	if _current_index >= _dialogs.size():
		_end_dialog()
	else:
		_show_current_line()

## 结束对话——隐藏对话框
func _end_dialog() -> void:
	visible = false
	_dialogs = []
	_current_index = 0

## 获取当前对话索引（用于测试）
func get_current_index() -> int:
	return _current_index

## 获取当前对话总数（用于测试）
func get_dialog_count() -> int:
	return _dialogs.size()

## 检查对话框是否可见
func is_dialog_visible() -> bool:
	return visible
