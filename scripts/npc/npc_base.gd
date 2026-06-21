# scripts/npc/npc_base.gd
extends Area2D

## NPC 基类——所有 NPC 的父类，处理玩家交互和对话触发
## 子类通过重写 get_dialogs() 提供对话内容

# NPC 唯一标识符
@export var npc_id: String = ""

# 交互提示文本（玩家进入范围时显示）
@export var interaction_prompt: String = "按 E 交互"

# 对话内容数组——子类应重写此方法
@export var dialogs: Array = []

# 玩家是否在交互范围内
var _player_in_range: bool = false

# 交互按键状态跟踪（防止按住时重复触发）
var _interact_pressed: bool = false

## 初始化时连接信号
func _ready() -> void:
	body_entered.connect(_on_body_entered)
	body_exited.connect(_on_body_exited)

## 每帧检测交互输入
func _physics_process(_delta: float) -> void:
	if _player_in_range and Input.is_action_just_pressed("interact"):
		_start_dialog()

## 玩家进入交互范围
func _on_body_entered(body: Node2D) -> void:
	if body.is_in_group("player"):
		_player_in_range = true
		_show_prompt()

## 玩家离开交互范围
func _on_body_exited(body: Node2D) -> void:
	if body.is_in_group("player"):
		_player_in_range = false
		_hide_prompt()

## 显示交互提示（子类可重写以自定义 UI）
func _show_prompt() -> void:
	# 基类仅打印日志，子类可重写为显示 Label
	pass

## 隐藏交互提示
func _hide_prompt() -> void:
	pass

## 启动对话——通过 EventBus 发送对话信号
func _start_dialog() -> void:
	if dialogs.is_empty():
		return
	EventBus.show_dialog.emit(npc_id, dialogs)

## 获取 NPC 对话内容
func get_dialogs() -> Array:
	return dialogs

## 检查玩家是否在交互范围内
func is_player_in_range() -> bool:
	return _player_in_range
