# scripts/effects/root_spread.gd
extends Node2D

## 根须蔓延特效——月桂树流血时从树根位置向外蔓延根须
## 使用 Line2D 绘制分形根须，逐渐生长覆盖屏幕

# 根须生长速度（像素/秒）
const GROW_SPEED: float = 60.0

# 最大根须长度
const MAX_LENGTH: float = 200.0

# 根须分支数量
const BRANCH_COUNT: int = 5

# 根须颜色
const ROOT_COLOR: Color = Color(0.2, 0.1, 0.05, 0.9)

# 是否正在蔓延
var _spreading: bool = false

# 当前生长长度
var _current_length: float = 0.0

# 根须线段数组
var _root_lines: Array[Line2D] = []

## 初始化时连接信号
func _ready() -> void:
	visible = false
	EventBus.tree_bleeding.connect(_on_tree_bleeding)
	_create_root_lines()

## 每帧处理根须生长
func _process(delta: float) -> void:
	if not _spreading:
		return
	_current_length += GROW_SPEED * delta
	if _current_length >= MAX_LENGTH:
		_current_length = MAX_LENGTH
		_spreading = false
	_update_root_lines()

## 创建根须线段
func _create_root_lines() -> void:
	for i in range(BRANCH_COUNT):
		var line = Line2D.new()
		line.width = 2.0
		line.default_color = ROOT_COLOR
		line.joint_mode = Line2D.LINE_JOINT_ROUND
		# 初始点在原点
		line.add_point(Vector2.ZERO)
		# 随机方向
		var angle = (i / float(BRANCH_COUNT)) * TAU + randf_range(-0.3, 0.3)
		var end_point = Vector2(cos(angle), sin(angle)) * MAX_LENGTH
		line.add_point(Vector2.ZERO)  # 临时终点，会被更新
		add_child(line)
		_root_lines.append(line)

## 更新根须线段终点
func _update_root_lines() -> void:
	for i in range(_root_lines.size()):
		var line = _root_lines[i]
		var angle = (i / float(_root_lines.size())) * TAU + randf_range(-0.3, 0.3)
		var end_point = Vector2(cos(angle), sin(angle)) * _current_length
		line.set_point_position(1, end_point)

## 开始蔓延
func start_spread() -> void:
	visible = true
	_spreading = true
	_current_length = 0.0

## 停止蔓延并隐藏
func stop_spread() -> void:
	_spreading = false
	_current_length = 0.0
	visible = false
	for line in _root_lines:
		line.set_point_position(1, Vector2.ZERO)

## 月桂树流血时触发蔓延
func _on_tree_bleeding() -> void:
	start_spread()

## 检查是否正在蔓延
func is_spreading() -> bool:
	return _spreading

## 获取当前生长长度
func get_current_length() -> float:
	return _current_length

## 获取根须分支数量
func get_branch_count() -> int:
	return _root_lines.size()
