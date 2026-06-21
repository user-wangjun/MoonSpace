# scripts/npc/yutu_npc.gd
extends Area2D

## 玉兔 NPC——捣药者
## 玩家靠近时停止捣药，远离时恢复捣药
## 伪规则：玉兔捣药时不应被注视（注视反而违规）

# NPC 唯一标识符
@export var npc_id: String = "yutu"

# 交互提示文本
@export var interaction_prompt: String = "按 E 与玉兔交谈"

# 对话内容
@export var dialogs: Array = [
	"我是玉兔，在此捣药千年。",
	"切记：我捣药时，你不该看。",
	"月池中的倒影，不是你的。"
]

# 是否正在捣药
var is_pounding: bool = true

# 玩家是否在交互范围内
var _player_in_range: bool = false

## 初始化时连接信号
func _ready() -> void:
	body_entered.connect(_on_body_entered)
	body_exited.connect(_on_body_exited)
	# 初始状态通知捣药中
	EventBus.yutu_pounding_changed.emit(is_pounding)

## 每帧处理交互输入
func _physics_process(_delta: float) -> void:
	if _player_in_range and Input.is_action_just_pressed("interact"):
		_start_dialog()

## 玩家进入交互范围——停止捣药
func _on_body_entered(body: Node2D) -> void:
	if body.is_in_group("player"):
		_player_in_range = true
		set_pounding(false)

## 玩家离开交互范围——恢复捣药
func _on_body_exited(body: Node2D) -> void:
	if body.is_in_group("player"):
		_player_in_range = false
		set_pounding(true)

## 设置捣药状态并通知事件总线
func set_pounding(pounding: bool) -> void:
	if is_pounding == pounding:
		return
	is_pounding = pounding
	EventBus.yutu_pounding_changed.emit(is_pounding)

## 启动对话——通过 EventBus 发送对话信号
func _start_dialog() -> void:
	if dialogs.is_empty():
		return
	EventBus.show_dialog.emit(npc_id, dialogs)

## 获取对话内容
func get_dialogs() -> Array:
	return dialogs

## 检查玩家是否在交互范围内
func is_player_in_range() -> bool:
	return _player_in_range

## 检查是否正在捣药
func is_currently_pounding() -> bool:
	return is_pounding

## 重置状态（用于测试隔离）
func reset() -> void:
	is_pounding = true
	_player_in_range = false
