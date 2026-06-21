# tests/unit/test_dialog_box.gd
extends GutTest

const DialogBoxScene = preload("res://scenes/dialog_box.tscn")

var dialog_box: Control

func before_each():
	dialog_box = DialogBoxScene.instantiate()
	add_child(dialog_box)

func after_each():
	dialog_box.free()

# 测试对话框场景可实例化
func test_dialog_box_instantiates():
	assert_not_null(dialog_box, "对话框场景应可实例化")

# 测试初始状态隐藏
func test_dialog_box_initially_hidden():
	assert_false(dialog_box.is_dialog_visible(), "对话框初始应隐藏")

# 测试显示对话
func test_dialog_box_show_dialog():
	var dlgs = ["第一句", "第二句", "第三句"]
	EventBus.show_dialog.emit("test_npc", dlgs)
	assert_true(dialog_box.is_dialog_visible(), "收到信号后应显示")
	assert_eq(dialog_box.get_dialog_count(), 3, "应有 3 条对话")
	assert_eq(dialog_box.get_current_index(), 0, "初始索引应为 0")

# 测试空对话不显示
func test_dialog_box_empty_dialogs_not_shown():
	EventBus.show_dialog.emit("empty_npc", [])
	assert_false(dialog_box.is_dialog_visible(), "空对话不应显示")

# 测试推进对话
func test_dialog_box_advance():
	var dlgs = ["A", "B", "C"]
	EventBus.show_dialog.emit("test", dlgs)
	# 手动推进
	dialog_box._advance_dialog()
	assert_eq(dialog_box.get_current_index(), 1, "推进后索引应为 1")
	dialog_box._advance_dialog()
	assert_eq(dialog_box.get_current_index(), 2, "推进后索引应为 2")

# 测试对话结束自动隐藏
func test_dialog_box_end_after_last():
	var dlgs = ["A", "B"]
	EventBus.show_dialog.emit("test", dlgs)
	dialog_box._advance_dialog()
	dialog_box._advance_dialog()
	assert_false(dialog_box.is_dialog_visible(), "最后一条推进后应隐藏")
	assert_eq(dialog_box.get_dialog_count(), 0, "结束后对话应清空")

# 测试重新显示对话重置索引
func test_dialog_box_reshow_resets_index():
	var dlgs = ["A", "B", "C"]
	EventBus.show_dialog.emit("test", dlgs)
	dialog_box._advance_dialog()
	# 再次显示新对话
	EventBus.show_dialog.emit("test2", ["X"])
	assert_eq(dialog_box.get_current_index(), 0, "新对话应从索引 0 开始")
