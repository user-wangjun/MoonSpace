# scripts/world/trigger_zone.gd
extends Area2D

## 规则触发区域——当玩家进入/离开/停留在区域内时检测规则
## 通过 @export 配置规则 ID、触发类型和上下文数据

# 要检测的规则 ID（对应 RuleEngine 中注册的规则）
@export var rule_id: String = ""

# 触发类型：enter（进入时）、exit（离开时）、stay（停留时）
@export var trigger_type: String = "enter"

# 传递给规则检测的上下文数据
@export var context_data: Dictionary = {}

## 初始化时连接信号
func _ready() -> void:
	body_entered.connect(_on_body_entered)
	body_exited.connect(_on_body_exited)

## 玩家进入区域时检测 enter 类型规则
func _on_body_entered(body: Node2D) -> void:
	if body.is_in_group("player") and trigger_type == "enter":
		_fire_rule_check()

## 玩家离开区域时检测 exit 类型规则
func _on_body_exited(body: Node2D) -> void:
	if body.is_in_group("player") and trigger_type == "exit":
		_fire_rule_check()

## 玩家停留在区域内时检测 stay 类型规则（每帧调用）
func _physics_process(_delta: float) -> void:
	if trigger_type != "stay":
		return
	if rule_id == "":
		return
	# 检查是否有玩家在区域内
	for body in get_overlapping_bodies():
		if body.is_in_group("player"):
			RuleEngine.check_rule(rule_id, context_data)
			return

## 触发规则检测
func _fire_rule_check() -> void:
	if rule_id != "":
		RuleEngine.check_rule(rule_id, context_data)
