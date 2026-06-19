# tests/unit/test_player_controller.gd
extends GutTest

# 预加载 Player 场景
const PlayerScene = preload("res://scenes/player.tscn")

var player: CharacterBody2D

# 每个测试前创建 Player 实例并添加到场景树
func before_each():
	player = PlayerScene.instantiate()
	add_child(player)

# 每个测试后释放 Player
func after_each():
	player.free()

# 测试 Player 场景可实例化
func test_player_scene_instantiates():
	assert_not_null(player, "Player 场景应可实例化")

# 测试 Player 在 player 组中
func test_player_in_player_group():
	assert_true(player.is_in_group("player"), "Player 应在 player 组中")

# 测试初始速度为 0
func test_player_initial_velocity_zero():
	assert_eq(player.velocity, Vector2.ZERO, "Player 初始速度应为 0")

# 测试 is_moving 初始返回 false
func test_player_is_moving_initial_false():
	assert_false(player.is_moving(), "初始状态下 is_moving 应返回 false")

# 测试设置速度后 is_moving 返回 true
func test_player_is_moving_true_when_velocity_set():
	player.velocity = Vector2(10, 0)
	assert_true(player.is_moving(), "有速度时 is_moving 应返回 true")

# 测试朝向判定——右
func test_player_facing_right():
	player.velocity = Vector2(10, 0)
	assert_eq(player.get_facing_direction(), "right", "向右移动应朝向 right")

# 测试朝向判定——左
func test_player_facing_left():
	player.velocity = Vector2(-10, 0)
	assert_eq(player.get_facing_direction(), "left", "向左移动应朝向 left")

# 测试朝向判定——下
func test_player_facing_down():
	player.velocity = Vector2(0, 10)
	assert_eq(player.get_facing_direction(), "down", "向下移动应朝向 down")

# 测试朝向判定——上
func test_player_facing_up():
	player.velocity = Vector2(0, -10)
	assert_eq(player.get_facing_direction(), "up", "向上移动应朝向 up")

# 测试速度常量
func test_player_speed_constants():
	assert_eq(player.SPEED_WALK, 80.0, "走路速度应为 80")
	assert_eq(player.SPEED_RUN, 140.0, "跑步速度应为 140")
