# scripts/npc/wugang_npc.gd
extends Area2D

## 吴刚 NPC——伐桂者，每 2 秒砍一刀
## 第 5 刀时月桂树流血，触发恐怖事件
## 玩家可通过交互获取规则提示

# NPC 唯一标识符
@export var npc_id: String = "wugang"

# 交互提示文本
@export var interaction_prompt: String = "按 E 与吴刚交谈"

# 对话内容
@export var dialogs: Array = [
	"我是吴刚，被罚伐桂千年。",
	"记住：见树需稽首，否则树会记住你。",
	"第五千斧落下时，你会看到不该看的东西。"
]

# 当前砍伐次数
var chop_count: int = 0

# 砍伐间隔（秒）
const CHOP_INTERVAL: float = 2.0

# 流血触发的砍伐次数阈值
const BLEED_THRESHOLD: int = 5

# 砍伐计时器
var _chop_timer: float = 0.0

# 玩家是否在交互范围内
var _player_in_range: bool = false

## 初始化时连接信号
func _ready() -> void:
	body_entered.connect(_on_body_entered)
	body_exited.connect(_on_body_exited)

## 每帧处理砍伐计时和交互输入
func _physics_process(delta: float) -> void:
	_process_chopping(delta)
	if _player_in_range and Input.is_action_just_pressed("interact"):
		_start_dialog()

## 处理砍伐逻辑——定时增加砍伐次数
func _process_chopping(delta: float) -> void:
	_chop_timer += delta
	if _chop_timer >= CHOP_INTERVAL:
		_chop_timer = 0.0
		chop()

## 执行一次砍伐——增加计数，达到阈值时触发流血
func chop() -> void:
	chop_count += 1
	if chop_count == BLEED_THRESHOLD:
		EventBus.tree_bleeding.emit()

## 玩家进入交互范围
func _on_body_entered(body: Node2D) -> void:
	if body.is_in_group("player"):
		_player_in_range = true

## 玩家离开交互范围
func _on_body_exited(body: Node2D) -> void:
	if body.is_in_group("player"):
		_player_in_range = false

## 启动对话——通过 EventBus 发送对话信号
func _start_dialog() -> void:
	if dialogs.is_empty():
		return
	EventBus.show_dialog.emit(npc_id, dialogs)

## 获取当前砍伐次数
func get_chop_count() -> int:
	return chop_count

## 检查是否已触发流血
func is_bleeding() -> bool:
	return chop_count >= BLEED_THRESHOLD

## 检查玩家是否在交互范围内
func is_player_in_range() -> bool:
	return _player_in_range

## 获取对话内容
func get_dialogs() -> Array:
	return dialogs

## 重置状态（用于测试隔离）
func reset() -> void:
	chop_count = 0
	_chop_timer = 0.0
