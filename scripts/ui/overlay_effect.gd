# scripts/ui/overlay_effect.gd
extends ColorRect

## 全屏覆盖层效果——用于恐怖氛围渲染
## 违规时红色闪烁、死亡时黑屏渐隐、紧张时脉冲效果

# 默认透明
const DEFAULT_ALPHA: float = 0.0

# 红色闪烁持续时间（秒）
const FLASH_DURATION: float = 0.3

# 红色闪烁最大不透明度
const FLASH_MAX_ALPHA: float = 0.6

# 黑屏渐隐持续时间（秒）
const FADE_DURATION: float = 1.5

# 脉冲效果最小不透明度
const PULSE_MIN_ALPHA: float = 0.0

# 脉冲效果最大不透明度
const PULSE_MAX_ALPHA: float = 0.3

# 脉冲速度
const PULSE_SPEED: float = 2.0

# 当前效果类型：none、flash、fade、pulse
var _effect_type: String = "none"

# 效果计时器
var _effect_timer: float = 0.0

# 是否正在脉冲
var _pulsing: bool = false

## 初始化时设置为全屏透明
func _ready() -> void:
	color = Color(0, 0, 0, DEFAULT_ALPHA)
	# 连接 EventBus 信号
	EventBus.violation_changed.connect(_on_violation_changed)
	EventBus.player_died.connect(_on_player_died)

## 每帧处理效果动画
func _process(delta: float) -> void:
	match _effect_type:
		"flash":
			_process_flash(delta)
		"fade":
			_process_fade(delta)
		"pulse":
			_process_pulse(delta)

## 触发红色闪烁效果
func flash_red() -> void:
	_effect_type = "flash"
	_effect_timer = 0.0
	color = Color(1, 0, 0, FLASH_MAX_ALPHA)

## 触发黑屏渐隐效果
func fade_to_black() -> void:
	_effect_type = "fade"
	_effect_timer = 0.0

## 开始脉冲效果
func start_pulse() -> void:
	_effect_type = "pulse"
	_pulsing = true

## 停止脉冲效果
func stop_pulse() -> void:
	_pulsing = false
	_effect_type = "none"
	color.a = DEFAULT_ALPHA

## 处理闪烁效果——快速淡出
func _process_flash(delta: float) -> void:
	_effect_timer += delta
	var progress = _effect_timer / FLASH_DURATION
	if progress >= 1.0:
		_effect_type = "none"
		color.a = DEFAULT_ALPHA
	else:
		color.a = FLASH_MAX_ALPHA * (1.0 - progress)

## 处理渐隐效果——缓慢变黑
func _process_fade(delta: float) -> void:
	_effect_timer += delta
	var progress = _effect_timer / FADE_DURATION
	if progress >= 1.0:
		color.a = 1.0
		_effect_type = "none"
	else:
		color.a = progress

## 处理脉冲效果——正弦波呼吸
func _process_pulse(delta: float) -> void:
	_effect_timer += delta
	var sine_val = sin(_effect_timer * PULSE_SPEED) * 0.5 + 0.5
	color.a = lerp(PULSE_MIN_ALPHA, PULSE_MAX_ALPHA, sine_val)

## 违规变化时触发红色闪烁
func _on_violation_changed(_count: int) -> void:
	flash_red()

## 玩家死亡时触发黑屏渐隐
func _on_player_died() -> void:
	fade_to_black()

## 获取当前效果类型（用于测试）
func get_effect_type() -> String:
	return _effect_type

## 检查是否正在脉冲
func is_pulsing() -> bool:
	return _pulsing

## 获取当前不透明度（用于测试）
func get_alpha() -> float:
	return color.a
