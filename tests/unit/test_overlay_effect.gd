# tests/unit/test_overlay_effect.gd
extends GutTest

const OverlayScene = preload("res://scenes/overlay_effect.tscn")

var overlay: ColorRect

func before_each():
	overlay = OverlayScene.instantiate()
	add_child(overlay)

func after_each():
	overlay.free()

# 测试覆盖层场景可实例化
func test_overlay_instantiates():
	assert_not_null(overlay, "覆盖层场景应可实例化")

# 测试初始状态透明
func test_overlay_initially_transparent():
	assert_eq(overlay.get_alpha(), 0.0, "初始不透明度应为 0")
	assert_eq(overlay.get_effect_type(), "none", "初始效果类型应为 none")

# 测试红色闪烁触发
func test_overlay_flash_red():
	overlay.flash_red()
	assert_eq(overlay.get_effect_type(), "flash", "闪烁后效果类型应为 flash")
	assert_gt(overlay.get_alpha(), 0.0, "闪烁后不透明度应大于 0")

# 测试闪烁完成后恢复
func test_overlay_flash_completes():
	overlay.flash_red()
	# 模拟足够时间过去
	overlay._process(0.4)
	assert_eq(overlay.get_effect_type(), "none", "闪烁完成后效果类型应恢复 none")
	assert_eq(overlay.get_alpha(), 0.0, "闪烁完成后不透明度应恢复 0")

# 测试黑屏渐隐触发
func test_overlay_fade_to_black():
	overlay.fade_to_black()
	assert_eq(overlay.get_effect_type(), "fade", "渐隐后效果类型应为 fade")

# 测试渐隐完成
func test_overlay_fade_completes():
	overlay.fade_to_black()
	overlay._process(2.0)
	assert_eq(overlay.get_alpha(), 1.0, "渐隐完成后不透明度应为 1")

# 测试脉冲效果
func test_overlay_pulse():
	overlay.start_pulse()
	assert_true(overlay.is_pulsing(), "脉冲应正在运行")
	assert_eq(overlay.get_effect_type(), "pulse", "效果类型应为 pulse")
	overlay.stop_pulse()
	assert_false(overlay.is_pulsing(), "停止后不应脉冲")
	assert_eq(overlay.get_effect_type(), "none", "停止后效果类型应为 none")

# 测试违规信号触发闪烁
func test_overlay_violation_triggers_flash():
	EventBus.violation_changed.emit(1)
	assert_eq(overlay.get_effect_type(), "flash", "违规信号应触发闪烁")

# 测试死亡信号触发渐隐
func test_overlay_death_triggers_fade():
	EventBus.player_died.emit()
	assert_eq(overlay.get_effect_type(), "fade", "死亡信号应触发渐隐")

# 测试脉冲不透明度在范围内
func test_overlay_pulse_alpha_range():
	overlay.start_pulse()
	# 处理几帧
	for i in range(10):
		overlay._process(0.1)
	var alpha = overlay.get_alpha()
	assert_true(alpha >= 0.0 and alpha <= 0.3, "脉冲不透明度应在 0-0.3 范围内")
