# scripts/player/player_controller.gd
extends CharacterBody2D

## 玩家控制器——处理移动、跑步和交互
## 通过 WASD/方向键控制移动，Shift 跑步，E/空格交互

# 走路速度（像素/秒）
const SPEED_WALK: float = 80.0

# 跑步速度（像素/秒）
const SPEED_RUN: float = 140.0

## 每帧处理输入和移动
func _physics_process(_delta: float) -> void:
	var input_dir = Input.get_vector("move_left", "move_right", "move_up", "move_down")
	var speed = SPEED_RUN if Input.is_action_pressed("run") else SPEED_WALK
	velocity = input_dir * speed
	move_and_slide()

## 检测玩家是否在移动
func is_moving() -> bool:
	return velocity.length() > 0.0

## 获取当前朝向（4 方向）
## 返回 "up"、"down"、"left"、"right" 之一
func get_facing_direction() -> String:
	if abs(velocity.x) > abs(velocity.y):
		return "right" if velocity.x > 0 else "left"
	else:
		return "down" if velocity.y > 0 else "up"
