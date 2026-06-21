# scripts/effects/death_effect.gd
extends CanvasLayer

## 死亡特效——玩家死亡时显示死亡画面
## 包含淡入黑屏、死亡文字和重启提示

# 淡入持续时间（秒）
const FADE_DURATION: float = 1.5

# 死亡标题文本
const DEATH_TITLE: String = "你已陨落于月宫"

# 重启提示文本
const RESTART_PROMPT: String = "按 R 键重新开始"

# 黑屏 ColorRect
var _fade_rect: ColorRect

# 死亡标题 Label
var _title_label: Label

# 重启提示 Label
var _prompt_label: Label

# 是否正在淡入
var _fading: bool = false

# 淡入计时器
var _fade_timer: float = 0.0

# 是否已显示完成
var _fully_shown: bool = false

## 初始化
func _ready() -> void:
	layer = 100
	_create_ui_elements()
	visible = false
	EventBus.player_died.connect(_on_player_died)

## 创建 UI 元素
func _create_ui_elements() -> void:
	# 黑屏
	_fade_rect = ColorRect.new()
	_fade_rect.color = Color(0, 0, 0, 0)
	_fade_rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(_fade_rect)

	# 死亡标题
	_title_label = Label.new()
	_title_label.text = DEATH_TITLE
	_title_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_title_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_title_label.set_anchors_preset(Control.PRESET_FULL_RECT)
	_title_label.add_theme_font_size_override("font_size", 24)
	_title_label.add_theme_color_override("font_color", Color(0.8, 0.2, 0.2))
	_title_label.modulate.a = 0
	add_child(_title_label)

	# 重启提示
	_prompt_label = Label.new()
	_prompt_label.text = RESTART_PROMPT
	_prompt_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_prompt_label.vertical_alignment = VERTICAL_ALIGNMENT_BOTTOM
	_prompt_label.set_anchors_preset(Control.PRESET_FULL_RECT)
	_prompt_label.add_theme_font_size_override("font_size", 14)
	_prompt_label.add_theme_color_override("font_color", Color(0.7, 0.7, 0.7))
	_prompt_label.modulate.a = 0
	add_child(_prompt_label)

## 每帧处理淡入
func _process(delta: float) -> void:
	if not _fading:
		return
	_fade_timer += delta
	var progress = _fade_timer / FADE_DURATION
	if progress >= 1.0:
		progress = 1.0
		_fading = false
		_fully_shown = true
	_fade_rect.color.a = progress
	_title_label.modulate.a = progress
	if progress >= 0.7:
		_prompt_label.modulate.a = (progress - 0.7) / 0.3

## 处理输入
func _input(event: InputEvent) -> void:
	if not _fully_shown:
		return
	if event is InputEventKey and event.pressed and event.keycode == KEY_R:
		_restart_game()

## 触发死亡特效
func trigger_death() -> void:
	visible = true
	_fading = true
	_fade_timer = 0.0
	_fully_shown = false

## 重启游戏
func _restart_game() -> void:
	GameState.reset()
	get_tree().reload_current_scene()

## 玩家死亡信号回调
func _on_player_died() -> void:
	trigger_death()

## 检查是否正在淡入
func is_fading() -> bool:
	return _fading

## 检查是否已完全显示
func is_fully_shown() -> bool:
	return _fully_shown

## 获取当前淡入进度（0-1）
func get_fade_progress() -> float:
	if FADE_DURATION <= 0:
		return 1.0
	return clamp(_fade_timer / FADE_DURATION, 0.0, 1.0)

## 隐藏特效（用于测试）
func hide_effect() -> void:
	visible = false
	_fading = false
	_fully_shown = false
	_fade_timer = 0.0
	_fade_rect.color.a = 0
	_title_label.modulate.a = 0
	_prompt_label.modulate.a = 0
