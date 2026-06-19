# tests/unit/test_event_bus.gd
extends GutTest

# 预加载 EventBus 脚本，用于在测试中创建实例
const EventBusScript = preload("res://scripts/autoload/event_bus.gd")

# 测试事件总线应可被实例化
func test_event_bus_exists():
	var bus = EventBusScript.new()
	assert_not_null(bus, "事件总线应可被实例化")
	bus.free()

# 测试事件总线信号的发送和接收
func test_event_bus_emit_and_receive():
	var bus = EventBusScript.new()
	# 使用字典持有状态，避免 lambda 捕获基本类型的潜在问题
	var result = {"count": -1}
	bus.violation_changed.connect(func(count: int): result["count"] = count)
	bus.violation_changed.emit(2)
	assert_eq(result["count"], 2, "发送信号后接收方应收到信号及参数")
	bus.free()

# 测试事件总线可连接多个接收者
func test_event_bus_multiple_receivers():
	var bus = EventBusScript.new()
	var state = {"r1": false, "r2": false}
	bus.player_died.connect(func(): state["r1"] = true)
	bus.player_died.connect(func(): state["r2"] = true)
	bus.player_died.emit()
	assert_true(state["r1"], "第一个接收者应被调用")
	assert_true(state["r2"], "第二个接收者应被调用")
	bus.free()
