# scripts/world/game_world.gd
extends Node2D

## 月宫前院场景——管理瓦片地图绘制和场景元素布局
## 地图尺寸 20x15 瓦片（320x240 像素）

# 瓦片地图图层节点引用
@onready var floor_layer: TileMapLayer = $FloorLayer

# 地图尺寸（瓦片数）
const MAP_WIDTH: int = 20
const MAP_HEIGHT: int = 15

# 月桂树位置（瓦片坐标）
const TREE_POS := Vector2i(3, 3)
# 捣药台位置（瓦片坐标）
const POUND_POS := Vector2i(16, 3)
# 月池位置（瓦片坐标，左上角）
const POOL_POS := Vector2i(8, 11)
# 月池尺寸
const POOL_SIZE := Vector2i(3, 2)

func _ready() -> void:
	_draw_floor()

## 绘制地面瓦片——全图铺设灰色地砖
func _draw_floor() -> void:
	var source_id = 0  # TileSet 中第一个图集源
	var atlas_coords := Vector2i(0, 0)  # 瓦片在图集中的坐标
	for x in range(MAP_WIDTH):
		for y in range(MAP_HEIGHT):
			floor_layer.set_cell(Vector2i(x, y), source_id, atlas_coords)
