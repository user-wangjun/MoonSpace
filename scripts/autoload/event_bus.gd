# scripts/autoload/event_bus.gd
extends Node

## 全局事件总线，用于解耦各个游戏系统之间的通信
## 各系统通过连接/发送信号来交互，避免相互直接引用

# 违规次数变化信号——参数为当前违规次数
signal violation_changed(count: int)

# 玩家死亡信号——违规满 3 次或战斗失败时触发
signal player_died

# 发现新规则信号——参数为规则 ID 和规则文本
signal rule_discovered(rule_id: String, rule_text: String)

# 显示对话信号——参数为 NPC ID 和对话内容数组
signal show_dialog(npc_id: String, dialogs: Array)

# 月桂树流血信号——吴刚伐桂第五千下时触发
signal tree_bleeding

# 玉兔捣药状态变化信号——参数为是否正在捣药
signal yutu_pounding_changed(is_pounding: bool)
