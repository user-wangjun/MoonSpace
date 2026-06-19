# scripts/autoload/rule_engine.gd
extends Node

## 规则引擎——注册、检测、执行规则判定
## 规则通过环境叙事呈现，玩家需要自行发现和遵守
## 真规则：违反则计入违规；伪规则：遵守反而计入违规（陷阱）

# 已注册的真规则字典——键为规则 ID，值为规则数据（含 description 和 check 回调）
var _rules: Dictionary = {}

# 已注册的伪规则字典——结构与真规则相同，但判定逻辑相反
var _pseudo_rules: Dictionary = {}

## 注册一条真规则
## rule_data 包含 description（描述文本）和 check（检测回调，返回 true 表示合规）
func register_rule(rule_id: String, rule_data: Dictionary) -> void:
	_rules[rule_id] = rule_data

## 注册一条伪规则（遵守反而违规）
## 数据结构与真规则相同，但 check 返回 true 表示玩家遵守了陷阱
func register_pseudo_rule(rule_id: String, rule_data: Dictionary) -> void:
	_pseudo_rules[rule_id] = rule_data

## 检测指定规则是否被遵守
## 返回 true 表示合规，false 表示违规（并计入 GameState）
func check_rule(rule_id: String, context: Dictionary) -> bool:
	if not _rules.has(rule_id):
		return true  # 未知规则默认放过
	var rule = _rules[rule_id]
	var passed = rule["check"].call(context)
	if not passed:
		GameState.add_violation()
	return passed

## 检测伪规则——遵守伪规则反而违规
## 返回 true 表示"没上当"（未遵守陷阱），false 表示上当了
func check_pseudo_rule(rule_id: String, context: Dictionary) -> bool:
	if not _pseudo_rules.has(rule_id):
		return true
	var rule = _pseudo_rules[rule_id]
	var followed = rule["check"].call(context)
	if followed:
		GameState.add_violation()
	return not followed  # 返回 true 表示"没上当"

## 检查规则是否已注册
func has_rule(rule_id: String) -> bool:
	return _rules.has(rule_id)

## 检查伪规则是否已注册
func has_pseudo_rule(rule_id: String) -> bool:
	return _pseudo_rules.has(rule_id)

## 获取所有已注册的真规则描述
func get_all_rules() -> Dictionary:
	var all := {}
	for id in _rules:
		all[id] = _rules[id]["description"]
	return all

## 清除所有已注册规则（用于重置或测试隔离）
func clear() -> void:
	_rules.clear()
	_pseudo_rules.clear()
