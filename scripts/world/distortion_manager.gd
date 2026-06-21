# scripts/world/distortion_manager.gd
extends Node

## 世界扭曲管理器——根据违规等级和特殊事件应用视觉扭曲效果
## 违规 1 级：轻微色调偏移；2 级：屏幕震动 + 色调加重；3 级：重度扭曲 + 死亡
## 月桂树流血时触发特殊扭曲脉冲

# 当前扭曲等级（0-3）
var distortion_level: int = 0

# 是否正在震动屏幕
var _shaking: bool = false

# 震动强度
var _shake_intensity: float = 0.0

# 震动计时器
var _shake_timer: float = 0.0

# 震动持续时间
const SHAKE_DURATION: float = 0.5

# 各等级震动强度
const SHAKE_LEVEL_1: float = 1.0
const SHAKE_LEVEL_2: float = 3.0
const SHAKE_LEVEL_3: float = 6.0

# 目标相机引用（由主场景设置）
var _camera: Camera2D = null

## 初始化时连接信号
func _ready() -> void:
	EventBus.violation_changed.connect(_on_violation_changed)
	EventBus.tree_bleeding.connect(_on_tree_bleeding)
	EventBus.player_died.connect(_on_player_died)

## 每帧处理震动效果
func _process(delta: float) -> void:
	if not _shaking:
		return
	_shake_timer += delta
	if _shake_timer >= SHAKE_DURATION:
		_stop_shake()
		return
	# 仅当相机存在时应用偏移
	if _camera != null:
		var offset = Vector2(
			randf_range(-_shake_intensity, _shake_intensity),
			randf_range(-_shake_intensity, _shake_intensity)
		)
		_camera.offset = offset

## 设置目标相机
func set_camera(camera: Camera2D) -> void:
	_camera = camera

## 违规变化时更新扭曲等级
func _on_violation_changed(count: int) -> void:
	distortion_level = count
	match count:
		1:
			_start_shake(SHAKE_LEVEL_1)
		2:
			_start_shake(SHAKE_LEVEL_2)
		3:
			_start_shake(SHAKE_LEVEL_3)

## 月桂树流血时触发特殊扭曲
func _on_tree_bleeding() -> void:
	_start_shake(SHAKE_LEVEL_3)

## 玩家死亡时停止所有效果
func _on_player_died() -> void:
	_stop_shake()

## 开始屏幕震动
func _start_shake(intensity: float) -> void:
	_shaking = true
	_shake_intensity = intensity
	_shake_timer = 0.0

## 停止屏幕震动
func _stop_shake() -> void:
	_shaking = false
	_shake_intensity = 0.0
	_shake_timer = 0.0
	if _camera != null:
		_camera.offset = Vector2.ZERO

## 获取当前扭曲等级
func get_distortion_level() -> int:
	return distortion_level

## 检查是否正在震动
func is_shaking() -> bool:
	return _shaking

## 获取当前震动强度
func get_shake_intensity() -> float:
	return _shake_intensity

## 重置状态（用于测试隔离）
func reset() -> void:
	distortion_level = 0
	_stop_shake()
