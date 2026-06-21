# scripts/main.gd
extends Node2D

## 主入口脚本——组装游戏场景并初始化所有规则
## 负责将各个子系统（世界、玩家、NPC、UI、特效）组合到一起
## 并向 RuleEngine 注册所有真规则和伪规则（陷阱）

# 子场景节点引用
@onready var _game_world: Node2D = $GameWorld
@onready var _player: CharacterBody2D = $Player
@onready var _wugang: Area2D = $WugangNPC
@onready var _yutu: Area2D = $YutuNPC
@onready var _dialog_box: Control = $UI/DialogBox
@onready var _rule_book: Control = $UI/RuleBook
@onready var _overlay: ColorRect = $UI/OverlayEffect
@onready var _distortion: Node = $DistortionManager
@onready var _root_spread: Node2D = $RootSpread
@onready var _death_effect: CanvasLayer = $DeathEffect

# 玩家相机
var _camera: Camera2D

## 初始化
func _ready() -> void:
	_setup_camera()
	_register_rules()
	_discover_initial_rules()
	_position_entities()

## 设置玩家相机
func _setup_camera() -> void:
	_camera = Camera2D.new()
	_camera.zoom = Vector2(2, 2)  # 像素风放大
	_player.add_child(_camera)

## 注册所有规则到 RuleEngine
func _register_rules() -> void:
	# === 真规则 ===
	# 规则一：不可直面月桂树（进入树周围即违规）
	RuleEngine.register_rule("rule_bow_to_tree", {
		"description": "月桂乃神木，凡人不可直面。须绕行，勿近其身。",
		"check": func(_context: Dictionary) -> bool:
			return false  # 进入树区域即视为违规
	})

	# 规则二：不可凝视水池倒影（停留水池即违规）
	RuleEngine.register_rule("rule_pool_reflection", {
		"description": "池中倒影非汝之影，久视必失本心。勿驻足，勿凝望。",
		"check": func(_context: Dictionary) -> bool:
			return false  # 停留水池即视为违规
	})

	# === 伪规则（陷阱）===
	# 陷阱规则：玉兔捣药时必须靠近观看
	# 实际上靠近玉兔会打断其捣药，反而违规
	RuleEngine.register_pseudo_rule("pseudo_rule_yutu_watch", {
		"description": "玉兔捣药为月宫要务，凡人当近前观摩以示敬意。",
		"check": func(_context: Dictionary) -> bool:
			# 如果玩家遵守此"规则"（靠近玉兔），返回 true 表示上当了
			return true
	})

## 发现初始规则（开场即告知玩家的规则）
func _discover_initial_rules() -> void:
	GameState.add_known_rule("rule_bow_to_tree", "月桂乃神木，凡人不可直面。须绕行，勿近其身。")
	GameState.add_known_rule("rule_pool_reflection", "池中倒影非汝之影，久视必失本心。勿驻足，勿凝望。")
	GameState.add_known_rule("pseudo_rule_yutu_watch", "玉兔捣药为月宫要务，凡人当近前观摩以示敬意。")

## 定位实体到场景中的初始位置
func _position_entities() -> void:
	# 玩家初始位置（左下角空地）
	_player.position = Vector2(48, 200)

	# 吴刚位于月桂树旁（树在 48,48，吴刚在右侧）
	_wugang.position = Vector2(96, 48)

	# 玉兔位于水池旁（水池在 152,184，玉兔在左侧）
	_yutu.position = Vector2(112, 184)

	# 根须蔓延特效定位到月桂树位置
	_root_spread.position = Vector2(48, 48)

## 处理输入
func _input(event: InputEvent) -> void:
	# ESC 退出
	if event is InputEventKey and event.pressed and event.keycode == KEY_ESCAPE:
		get_tree().quit()

## 获取玩家节点（用于测试）
func get_player() -> CharacterBody2D:
	return _player

## 获取世界节点（用于测试）
func get_game_world() -> Node2D:
	return _game_world

## 获取吴刚节点（用于测试）
func get_wugang() -> Area2D:
	return _wugang

## 获取玉兔节点（用于测试）
func get_yutu() -> Area2D:
	return _yutu

## 检查所有规则是否已注册
func are_all_rules_registered() -> bool:
	return RuleEngine.has_rule("rule_bow_to_tree") \
		and RuleEngine.has_rule("rule_pool_reflection") \
		and RuleEngine.has_pseudo_rule("pseudo_rule_yutu_watch")
