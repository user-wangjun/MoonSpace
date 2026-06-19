# tests/unit/test_game_world.gd
extends GutTest

const GameWorldScene = preload("res://scenes/game_world.tscn")

var world: Node2D

func before_each():
	world = GameWorldScene.instantiate()
	add_child(world)

func after_each():
	world.free()

# 测试 GameWorld 场景可实例化
func test_game_world_instantiates():
	assert_not_null(world, "GameWorld 场景应可实例化")

# 测试 FloorLayer 节点存在
func test_game_world_has_floor_layer():
	var floor_layer = world.get_node("FloorLayer")
	assert_not_null(floor_layer, "应存在 FloorLayer 节点")
	assert_true(floor_layer is TileMapLayer, "FloorLayer 应为 TileMapLayer 类型")

# 测试 WorldBoundaries 节点存在
func test_game_world_has_boundaries():
	var boundaries = world.get_node("WorldBoundaries")
	assert_not_null(boundaries, "应存在 WorldBoundaries 节点")
	assert_true(boundaries is StaticBody2D, "WorldBoundaries 应为 StaticBody2D 类型")

# 测试地图常量
func test_game_world_map_dimensions():
	assert_eq(world.MAP_WIDTH, 20, "地图宽度应为 20 瓦片")
	assert_eq(world.MAP_HEIGHT, 15, "地图高度应为 15 瓦片")

# 测试关键位置常量
func test_game_world_key_positions():
	assert_eq(world.TREE_POS, Vector2i(3, 3), "月桂树位置应为 (3,3)")
	assert_eq(world.POUND_POS, Vector2i(16, 3), "捣药台位置应为 (16,3)")
	assert_eq(world.POOL_POS, Vector2i(8, 11), "月池位置应为 (8,11)")

# 测试瓦片绘制——检查角落瓦片是否已设置
func test_game_world_tiles_drawn():
	# 等待一帧让 _ready 执行
	await get_tree().process_frame
	var floor_layer = world.get_node("FloorLayer") as TileMapLayer
	# 检查四个角的瓦片
	assert_true(floor_layer.get_cell_source_id(Vector2i(0, 0)) >= 0, "左上角瓦片应已绘制")
	assert_true(floor_layer.get_cell_source_id(Vector2i(19, 0)) >= 0, "右上角瓦片应已绘制")
	assert_true(floor_layer.get_cell_source_id(Vector2i(0, 14)) >= 0, "左下角瓦片应已绘制")
	assert_true(floor_layer.get_cell_source_id(Vector2i(19, 14)) >= 0, "右下角瓦片应已绘制")
