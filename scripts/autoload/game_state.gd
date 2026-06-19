# scripts/autoload/game_state.gd
extends Node

## 管理游戏全局状态——违规次数、已收集规则
## 作为 autoload 单例全局访问，所有系统共享同一份状态

# 当前违规次数（达到 3 次判定死亡）
var violation_count: int = 0

# 已发现的规则字典——键为规则 ID，值为规则文本
var known_rules: Dictionary = {}

## 增加一次违规记录，触发对应等级的世界扭曲事件
## 违规满 3 次时触发玩家死亡信号
func add_violation() -> void:
	violation_count += 1
	EventBus.violation_changed.emit(violation_count)
	if is_dead():
		EventBus.player_died.emit()

## 添加一条新发现的规则到规则手册
## 同时通过事件总线通知 UI 层更新显示
func add_known_rule(rule_id: String, rule_text: String) -> void:
	known_rules[rule_id] = rule_text
	EventBus.rule_discovered.emit(rule_id, rule_text)

## 判断玩家是否已死亡（违规 3 次）
func is_dead() -> bool:
	return violation_count >= 3

## 重置所有状态（用于重新开始游戏或测试隔离）
func reset() -> void:
	violation_count = 0
	known_rules.clear()
