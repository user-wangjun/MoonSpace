"""事件总线测试。"""

from core.event_bus import EventBus, VIOLATION_CHANGED


def test_emit_calls_subscribers_with_payload():
    bus = EventBus()
    received = []

    bus.subscribe(VIOLATION_CHANGED, lambda **payload: received.append(payload))
    bus.emit(VIOLATION_CHANGED, count=1)

    assert received == [{"count": 1}]


def test_emit_supports_multiple_subscribers():
    bus = EventBus()
    received = []

    bus.subscribe("event", lambda **payload: received.append(("a", payload)))
    bus.subscribe("event", lambda **payload: received.append(("b", payload)))
    bus.emit("event", value=42)

    assert received == [("a", {"value": 42}), ("b", {"value": 42})]


def test_unsubscribe_removes_callback():
    bus = EventBus()
    received = []

    def callback(**payload):
        received.append(payload)

    bus.subscribe("event", callback)
    bus.unsubscribe("event", callback)
    bus.emit("event", value=1)

    assert received == []


def test_emit_without_subscribers_does_not_crash():
    bus = EventBus()
    bus.emit("missing", value=1)


def test_clear_removes_all_subscribers():
    bus = EventBus()
    received = []

    bus.subscribe("event", lambda **payload: received.append(payload))
    bus.clear()
    bus.emit("event", value=1)

    assert received == []
