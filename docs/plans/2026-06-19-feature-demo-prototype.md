# MoonSpace Demo 原型实施计划

> **For Claude:** 使用 superpowers:executing-plans 按任务逐步实施此计划。

**目标：** 构建 MoonSpace 规则怪谈游戏 Demo 原型——月宫前院探索场景，包含移动、规则引擎、NPC 交互、世界扭曲效果。

**架构：** Godot 4.x 2D 俯视角，规则引擎 + 事件总线作为 autoload 单例，CharacterBody2D 控制玩家，NPC 继承基类，UI 层独立管理。

**技术栈：** Godot 4.x, GDScript, GUT（测试框架）

---

## 阶段 1：基础设施（3 个任务）

### 任务 1：安装 GUT 测试框架并创建首个测试

**文件：**
- 创建：`addons/gut/`（通过 AssetLib 安装）
- 创建：`tests/unit/test_event_bus.gd`

**Step 1：在 Godot 编辑器中安装 GUT**

在 Godot AssetLib 中搜索 "GUT" 并安装，或将 GUT 插件复制到 `addons/gut/` 目录。

**Step 2：编写事件总线的失败测试**

```gdscript
# tests/unit/test_event_bus.gd
extends GutTest

func test_event_bus_exists():
    var bus = EventBus.new()
    assert_not_null(bus, "事件总线应可被实例化")

func test_event_bus_emit_and_receive():
    var bus = EventBus.new()
    var received = false
    bus.connect("test_signal", func(): received = true)
    bus.emit_signal("test_signal")
    assert_true(received, "发送信号后接收方应收到信号")
```

**Step 3：运行测试验证失败**

在 Godot 编辑器底部打开 GUT 面板，运行测试。

**Step 4：创建 EventBus 最小实现**

```gdscript
# scripts/autoload/event_bus.gd
extends Node

## 全局事件总线，用于解耦各个游戏系统之间的通信
```

将 EventBus 添加到 Project Settings → Autoload，名称为 `EventBus`。

**Step 5：运行测试验证通过**

**Step 6：提交**

```bash
git add tests/ scripts/autoload/ project.godot
git commit -m "test: 添加 GUT 测试框架和 EventBus 基础测试"
```

---

### 任务 2：创建 GameState 全局状态管理

**文件：**
- 创建：`tests/unit/test_game_state.gd`
- 创建：`scripts/autoload/game_state.gd`

**Step 1：编写失败测试**

```gdscript
# tests/unit/test_game_state.gd
extends GutTest

func test_game_state_initial_values():
    var state = auto_load("res://scripts/autoload/game_state.gd")
    assert_eq(state.violation_count, 0, "初始违规次数应为 0")
    assert_eq(state.known_rules.size(), 0, "初始已知规则为空")

func test_game_state_add_violation():
    var state = auto_load("res://scripts/autoload/game_state.gd")
    state.violation_count = 0
    state.add_violation()
    assert_eq(state.violation_count, 1, "违规一次后计数应为 1")

func test_game_state_add_known_rule():
    var state = auto_load("res://scripts/autoload/game_state.gd")
    state.known_rules.clear()
    state.add_known_rule("rule_1", "见树需稽首")
    assert_eq(state.known_rules.size(), 1, "添加一条规则后应为 1")
    assert_eq(state.known_rules["rule_1"], "见树需稽首")

func test_game_state_is_dead_at_3_violations():
    var state = auto_load("res://scripts/autoload/game_state.gd")
    state.violation_count = 3
    assert_true(state.is_dead(), "违规 3 次应判定死亡")

func test_game_state_reset():
    var state = auto_load("res://scripts/autoload/game_state.gd")
    state.violation_count = 2
    state.add_known_rule("r1", "test")
    state.reset()
    assert_eq(state.violation_count, 0, "重置后违规次数应为 0")
    assert_eq(state.known_rules.size(), 0, "重置后规则列表应为空")
```

**Step 2：运行测试验证失败**

**Step 3：编写 GameState 实现**

```gdscript
# scripts/autoload/game_state.gd
extends Node

## 管理游戏全局状态——违规次数、已收集规则

var violation_count: int = 0
var known_rules: Dictionary = {}

## 增加一次违规记录，触发对应等级的世界扭曲事件
func add_violation() -> void:
    violation_count += 1
    EventBus.emit_signal("violation_changed", violation_count)
    if is_dead():
        EventBus.emit_signal("player_died")

## 添加一条新发现的规则到规则手册
func add_known_rule(rule_id: String, rule_text: String) -> void:
    known_rules[rule_id] = rule_text
    EventBus.emit_signal("rule_discovered", rule_id, rule_text)

## 判断玩家是否已死亡（违规 3 次）
func is_dead() -> bool:
    return violation_count >= 3

## 重置所有状态（用于重新开始）
func reset() -> void:
    violation_count = 0
    known_rules.clear()
```

将 GameState 添加到 Autoload，名称为 `GameState`。

**Step 4：运行测试验证通过**

**Step 5：提交**

```bash
git add tests/ scripts/autoload/ project.godot
git commit -m "feat: 添加 GameState 全局状态管理"
```

---

### 任务 3：创建 RuleEngine 规则引擎

**文件：**
- 创建：`tests/unit/test_rule_engine.gd`
- 创建：`scripts/autoload/rule_engine.gd`

**Step 1：编写失败测试**

```gdscript
# tests/unit/test_rule_engine.gd
extends GutTest

var rule_engine: Node

func before_each():
    # 因依赖 GameState，需先重置
    GameState.reset()
    rule_engine = auto_load("res://scripts/autoload/rule_engine.gd")

func test_register_and_check_rule():
    rule_engine.register_rule("rule_bow_to_tree", {
        "description": "见树需稽首",
        "check": func(_ctx): return true
    })
    assert_true(rule_engine.has_rule("rule_bow_to_tree"), "应能找到已注册的规则")

func test_check_rule_returns_true():
    # 注册一个总返回 true 的规则
    rule_engine.register_rule("always_true", {
        "description": "总是真",
        "check": func(_ctx): return true
    })
    var result = rule_engine.check_rule("always_true", {})
    assert_true(result, "规则检测应返回 true")

func test_check_rule_returns_false_triggers_violation():
    rule_engine.register_rule("always_false", {
        "description": "总是假",
        "check": func(_ctx): return false
    })
    GameState.violation_count = 0
    var result = rule_engine.check_rule("always_false", {})
    assert_false(result, "规则检测应返回 false")
    assert_eq(GameState.violation_count, 1, "违规次数应增加 1")

func test_register_pseudo_rule():
    rule_engine.register_pseudo_rule("run_is_respect", {
        "description": "广寒宫前疾走以示敬意",
        "check": func(_ctx): return true
    })
    # 伪规则逻辑上反转——遵守反而是违规
    GameState.violation_count = 0
    rule_engine.check_pseudo_rule("run_is_respect", {})
    assert_eq(GameState.violation_count, 1, "遵守伪规则应增加违规次数")
```

**Step 2：运行测试验证失败**

**Step 3：编写 RuleEngine 实现**

```gdscript
# scripts/autoload/rule_engine.gd
extends Node

## 规则引擎——注册、检测、执行规则判定
## 规则通过环境叙事呈现，玩家需要自行发现和遵守

var _rules: Dictionary = {}
var _pseudo_rules: Dictionary = {}

## 注册一条真规则
func register_rule(rule_id: String, rule_data: Dictionary) -> void:
    _rules[rule_id] = rule_data

## 注册一条伪规则（遵守反而违规）
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

## 获取所有已注册的规则描述
func get_all_rules() -> Dictionary:
    var all := {}
    for id in _rules:
        all[id] = _rules[id]["description"]
    return all
```

将 RuleEngine 添加到 Autoload，名称为 `RuleEngine`。

**Step 4：运行测试验证通过**

**Step 5：提交**

```bash
git add tests/ scripts/autoload/ project.godot
git commit -m "feat: 添加 RuleEngine 规则引擎核心"
```

---

## 阶段 2：玩家系统（1 个任务）

### 任务 4：创建玩家角色与移动控制

**文件：**
- 创建：`scenes/player.tscn`
- 创建：`scripts/player/player_controller.gd`

**Step 1：创建 Player 场景**

在 Godot 编辑器中：
1. 创建新场景，根节点为 `CharacterBody2D`，命名为 `Player`
2. 添加子节点：
   - `CollisionShape2D`（矩形，16×24 像素碰撞）
   - `Sprite2D`（先用占位纹理：32×32 白色方块）
3. 将脚本 `player_controller.gd` 挂载到根节点

**Step 2：编写 PlayerController 脚本**

```gdscript
# scripts/player/player_controller.gd
extends CharacterBody2D

## 玩家控制器——处理移动、跑步和交互

const SPEED_WALK: float = 80.0
const SPEED_RUN: float = 140.0

## 每帧处理输入和移动
func _physics_process(_delta: float) -> void:
    var input_dir = Input.get_vector("move_left", "move_right", "move_up", "move_down")
    var speed = SPEED_RUN if Input.is_action_pressed("run") else SPEED_WALK
    velocity = input_dir * speed
    move_and_slide()

## 检测玩家是否在移动
func is_moving() -> bool:
    return velocity.length() > 0.0

## 获取当前朝向（4 方向）
func get_facing_direction() -> String:
    if abs(velocity.x) > abs(velocity.y):
        return "right" if velocity.x > 0 else "left"
    else:
        return "down" if velocity.y > 0 else "up"
```

**Step 3：在编辑器中验证**

创建临时测试场景，放入 Player，运行查看 WASD 移动和 Shift 跑步是否正常。

**Step 4：提交**

```bash
git add scenes/player.tscn scripts/player/player_controller.gd
git commit -m "feat: 添加玩家角色移动控制"
```

---

## 阶段 3：地图与触发区域（2 个任务）

### 任务 5：创建月宫前院瓦片地图

**文件：**
- 创建：`assets/tilesets/moon_palace_floor.png`（程序生成占位图，16×16 灰色像素）
- 创建：`assets/tilesets/moon_tiles.tres`
- 创建：`scenes/game_world.tscn`

**Step 1：在编辑器中创建瓦片集**

1. 在 Godot 文件系统中右键 `assets/tilesets/` → 新建资源 → TileSet
2. 命名为 `moon_tiles.tres`
3. 暂时使用纯色矩形作为地面砖块（后续替换为美术资源）

**Step 2：创建 GameWorld 场景**

1. 根节点 `Node2D`，命名为 `GameWorld`
2. 添加 `TileMapLayer` 节点，挂载 moon_tiles.tres
3. 绘制月宫前院地图：
   - 主区域 20×15 瓦片（320×240 像素）
   - 左上角：月桂树位置标记
   - 右上角：捣药台
   - 下方：月池（3×2 蓝色区域）
   - 顶部：广寒宫轮廓（装饰墙体）

**Step 3：添加世界边界**

添加 `StaticBody2D` + `CollisionShape2D` 作为地图边界。

**Step 4：提交**

```bash
git add assets/tilesets/ scenes/game_world.tscn
git commit -m "feat: 创建月宫前院瓦片地图"
```

---

### 任务 6：创建规则触发区域（TriggerZone）

**文件：**
- 创建：`scripts/world/trigger_zone.gd`
- 创建：`scenes/trigger_zone.tscn`

**Step 1：编写 TriggerZone 脚本**

```gdscript
# scripts/world/trigger_zone.gd
extends Area2D

## 规则触发区域——当玩家进入/离开/停留在区域内时检测规则

@export var rule_id: String = ""
@export var trigger_type: String = "enter"  # enter, exit, stay
@export var context_data: Dictionary = {}

## 玩家进入区域时检测 enter 类型规则
func _on_body_entered(body: Node2D) -> void:
    if body.is_in_group("player") and trigger_type == "enter":
        _fire_rule_check()

## 玩家离开区域时检测 exit 类型规则
func _on_body_exited(body: Node2D) -> void:
    if body.is_in_group("player") and trigger_type == "exit":
        _fire_rule_check()

func _fire_rule_check() -> void:
    if rule_id != "":
        RuleEngine.check_rule(rule_id, context_data)
```

**Step 2：创建 TriggerZone 场景**

1. 根节点 `Area2D`，命名为 `TriggerZone`
2. 添加 `CollisionShape2D`（矩形，大小可调）
3. 挂载上述脚本

**Step 3：在 GameWorld 中放置触发区域**

- 在月桂树周围放置 `rule_bow_to_tree` 进入触发区
- 在月池旁放置 `rule_pool_reflection` 停留触发区

**Step 4：提交**

```bash
git add scripts/world/trigger_zone.gd scenes/trigger_zone.tscn scenes/game_world.tscn
git commit -m "feat: 添加规则触发区域系统"
```

---

## 阶段 4：NPC 系统（3 个任务）

### 任务 7：创建 NPC 基类

**文件：**
- 创建：`scripts/npc/npc_base.gd`
- 创建：`scenes/npc_base.tscn`

**Step 1：编写 NPC 基类**

```gdscript
# scripts/npc/npc_base.gd
extends CharacterBody2D

## NPC 基类——提供交互、对话等公共功能

@export var npc_id: String = ""
@export var interaction_distance: float = 32.0
@export var dialogs: Array[String] = []

var _player_nearby: bool = false
var _player_ref: Node2D = null

## 检测玩家是否在交互范围内
func _process(_delta: float) -> void:
    if _player_ref and _player_nearby:
        var dist = global_position.distance_to(_player_ref.global_position)
        if dist <= interaction_distance and Input.is_action_just_pressed("interact"):
            _on_interact()

## 当玩家进入检测范围
func _on_player_entered(body: Node2D) -> void:
    if body.is_in_group("player"):
        _player_nearby = true
        _player_ref = body

## 当玩家离开检测范围
func _on_player_exited(body: Node2D) -> void:
    if body.is_in_group("player"):
        _player_nearby = false
        _player_ref = null

## 子类重写此方法实现具体交互逻辑
func _on_interact() -> void:
    if dialogs.size() > 0:
        EventBus.emit_signal("show_dialog", npc_id, dialogs)
```

**Step 2：创建 NPC 基础场景**

1. 根节点 `CharacterBody2D`，添加 `CollisionShape2D` + `Sprite2D`（占位）
2. 添加子节点 `Area2D`（检测玩家靠近），命名为 `DetectionZone`
3. 连接 `DetectionZone` 的 `body_entered` / `body_exited` 信号到脚本
4. 挂载上述脚本

**Step 3：提交**

```bash
git add scripts/npc/npc_base.gd scenes/npc_base.tscn
git commit -m "feat: 添加 NPC 基类"
```

---

### 任务 8：创建吴刚 NPC

**文件：**
- 创建：`scripts/npc/wugang_npc.gd`
- 创建：`scenes/wugang.tscn`

**Step 1：编写吴刚脚本**

```gdscript
# scripts/npc/wugang_npc.gd
extends "res://scripts/npc/npc_base.gd"

## 吴刚——永远在月桂树下伐桂，循环动画

@export var chop_interval: float = 2.0
@export var chop_count_max: int = 5000

var _chop_count: int = 0
var _chop_timer: float = 0.0
var _is_staring: bool = false  # 违规 2 次后变为盯着玩家

## 初始化
func _ready() -> void:
    npc_id = "wugang"
    dialogs = [
        "吴刚没有看你，只是继续挥斧。",
        "斧刃入木的声音带着某种规律……像是某种计数。"
    ]
    EventBus.connect("violation_changed", _on_violation_changed)

## 伐桂循环
func _process(delta: float) -> void:
    if _is_staring:
        _stare_at_player(delta)
        return
    _chop_timer += delta
    if _chop_timer >= chop_interval:
        _chop_timer = 0.0
        _chop_count += 1
        _do_chop_animation()
        if _chop_count == 5000:
            EventBus.emit_signal("tree_bleeding")  # 月桂树流泪事件

## 执行砍伐动画（目前为占位——缩放弹跳模拟）
func _do_chop_animation() -> void:
    var tween = create_tween()
    tween.tween_property(self, "scale", Vector2(1.1, 0.9), 0.1)
    tween.tween_property(self, "scale", Vector2(1.0, 1.0), 0.3)

## 违规后盯着玩家
func _stare_at_player(_delta: float) -> void:
    if _player_ref:
        look_at(_player_ref.global_position)

func _on_violation_changed(count: int) -> void:
    if count >= 2:
        _is_staring = true
```

**Step 2：创建 WuGang 场景**

1. 继承 `npc_base.tscn`，替换脚本为 `wugang_npc.gd`
2. 放置在月桂树旁边（map 坐标约 6, 4）

**Step 3：提交**

```bash
git add scripts/npc/wugang_npc.gd scenes/wugang.tscn scenes/game_world.tscn
git commit -m "feat: 添加吴刚 NPC 和伐桂循环"
```

---

### 任务 9：创建玉兔 NPC 和对话系统

**文件：**
- 创建：`scripts/npc/yutu_npc.gd`
- 创建：`scenes/yutu.tscn`
- 创建：`scripts/ui/dialog_ui.gd`
- 创建：`scenes/ui/dialog_box.tscn`

**Step 1：编写玉兔脚本**

```gdscript
# scripts/npc/yutu_npc.gd
extends "res://scripts/npc/npc_base.gd"

## 玉兔——捣药 NPC，会给出伪规则陷阱

@export var pound_interval: float = 1.5

var _pound_timer: float = 0.0
var _is_pounding: bool = true
var _spoken_pseudo_rule: bool = false

func _ready() -> void:
    npc_id = "yutu"
    dialogs = [
        "玉兔没有抬头，捣药声规律而沉闷。",
        "「使者大人……广寒宫前，疾走以示敬意。」",
        "说完这句话，它继续捣药，仿佛什么都没发生过。"
    ]

func _process(delta: float) -> void:
    _pound_timer += delta
    if _pound_timer >= pound_interval:
        _pound_timer = 0.0
        _is_pounding = not _is_pounding
        EventBus.emit_signal("yutu_pounding_changed", _is_pounding)

## 交互时触发伪规则
func _on_interact() -> void:
    super._on_interact()
    if not _spoken_pseudo_rule:
        _spoken_pseudo_rule = true
        RuleEngine.register_pseudo_rule("run_is_respect", {
            "description": "广寒宫前疾走以示敬意",
            "check": func(_ctx): return Input.is_action_pressed("run")
        })
```

**Step 2：编写对话 UI**

```gdscript
# scripts/ui/dialog_ui.gd
extends CanvasLayer

## 对话面板——显示 NPC 对话内容

@onready var label: Label = $Panel/Label
@onready var panel: Panel = $Panel

var _dialog_queue: Array[String] = []
var _current_index: int = 0

func _ready() -> void:
    panel.visible = false
    EventBus.connect("show_dialog", _on_show_dialog)

func _input(event: InputEvent) -> void:
    if panel.visible and event.is_action_pressed("interact"):
        _advance_dialog()

func _on_show_dialog(_npc_id: String, dialogs: Array) -> void:
    _dialog_queue = dialogs
    _current_index = 0
    _show_current()

func _show_current() -> void:
    if _current_index < _dialog_queue.size():
        panel.visible = true
        label.text = _dialog_queue[_current_index]
    else:
        panel.visible = false

func _advance_dialog() -> void:
    _current_index += 1
    _show_current()
```

**Step 3：创建 DialogBox 场景**

1. 根节点 `CanvasLayer`，挂载 `dialog_ui.gd`
2. 子节点 `Panel` → `Label`
3. 面板位置：底部居中，半透明黑色背景

**Step 4：创建 Yutu 场景**

1. 继承 `npc_base.tscn`，替换脚本
2. 放置在捣药台旁

**Step 5：提交**

```bash
git add scripts/npc/yutu_npc.gd scenes/yutu.tscn scripts/ui/dialog_ui.gd scenes/ui/dialog_box.tscn scenes/game_world.tscn
git commit -m "feat: 添加玉兔 NPC 和对话系统"
```

---

## 阶段 5：UI 系统（2 个任务）

### 任务 10：创建规则手册面板

**文件：**
- 创建：`scripts/ui/rule_panel_ui.gd`
- 创建：`scenes/ui/rule_panel.tscn`

**Step 1：编写规则手册 UI**

```gdscript
# scripts/ui/rule_panel_ui.gd
extends CanvasLayer

## 规则手册——显示已收集的规则，颜色标识状态

@onready var rule_list: VBoxContainer = $Panel/ScrollContainer/RuleList
@onready var panel: Panel = $Panel

var _is_open: bool = false

func _ready() -> void:
    panel.visible = false
    EventBus.connect("rule_discovered", _on_rule_discovered)

func _input(event: InputEvent) -> void:
    if event.is_action_pressed("open_rule_book"):
        _toggle()

func _toggle() -> void:
    _is_open = not _is_open
    panel.visible = _is_open
    if _is_open:
        _refresh_list()

func _refresh_list() -> void:
    # 清除旧条目
    for child in rule_list.get_children():
        child.queue_free()
    # 添加已知规则
    for rule_id in GameState.known_rules:
        var label = Label.new()
        label.text = "· " + GameState.known_rules[rule_id]
        label.add_theme_color_override("font_color", Color.GREEN)
        rule_list.add_child(label)

func _on_rule_discovered(_rule_id: String, _rule_text: String) -> void:
    if _is_open:
        _refresh_list()
```

**Step 2：创建 RulePanel 场景**

1. 根节点 `CanvasLayer`，挂载 `rule_panel_ui.gd`
2. 子节点 `Panel` → `ScrollContainer` → `VBoxContainer`（RuleList）
3. 面板位置：左侧，半透明背景

**Step 3：提交**

```bash
git add scripts/ui/rule_panel_ui.gd scenes/ui/rule_panel.tscn
git commit -m "feat: 添加规则手册 UI"
```

---

### 任务 11：创建全屏覆盖层效果

**文件：**
- 创建：`scripts/ui/screen_overlay.gd`
- 创建：`scenes/ui/screen_overlay.tscn`

**Step 1：编写全屏特效脚本**

```gdscript
# scripts/ui/screen_overlay.gd
extends CanvasLayer

## 屏幕覆盖层——违规时的视觉扭曲效果

@onready var color_rect: ColorRect = $ColorRect

func _ready() -> void:
    color_rect.visible = false
    EventBus.connect("violation_changed", _on_violation_changed)

func _on_violation_changed(count: int) -> void:
    match count:
        1:
            _flash_red()
        2:
            _show_vignette()
        3:
            _death_sequence()

## 红色闪烁效果
func _flash_red() -> void:
    color_rect.color = Color(0.8, 0.1, 0.1, 0.3)
    color_rect.visible = true
    var tween = create_tween()
    tween.tween_property(color_rect, "visible", false, 0.5)

## 暗角效果（月桂根须包围感）
func _show_vignette() -> void:
    color_rect.color = Color(0.05, 0.0, 0.0, 0.4)
    color_rect.visible = true

## 死亡序列
func _death_sequence() -> void:
    color_rect.color = Color.BLACK
    color_rect.visible = true
    var tween = create_tween()
    tween.tween_property(color_rect, "color:a", 1.0, 2.0)
```

**Step 2：创建场景**

1. 根节点 `CanvasLayer`，挂载脚本
2. 添加子节点 `ColorRect`（全屏拉伸，初始隐藏）

**Step 3：提交**

```bash
git add scripts/ui/screen_overlay.gd scenes/ui/screen_overlay.tscn
git commit -m "feat: 添加全屏扭曲效果 UI"
```

---

## 阶段 6：世界扭曲系统（2 个任务）

### 任务 12：创建世界扭曲管理器

**文件：**
- 创建：`scripts/world/world_distortion.gd`

**Step 1：编写世界扭曲管理器**

```gdscript
# scripts/world/world_distortion.gd
extends Node

## 世界扭曲管理器——根据违规次数改变场景表现

@export var vine_scene: PackedScene  # 根须特效预制

var _current_level: int = 0

func _ready() -> void:
    EventBus.connect("violation_changed", _on_violation_changed)

func _on_violation_changed(count: int) -> void:
    _current_level = count
    match count:
        1:
            _spawn_vines_following_player()
        2:
            _distort_world()
        3:
            _trigger_death()

## 在玩家身后生成根须
func _spawn_vines_following_player() -> void:
    if vine_scene:
        var vine = vine_scene.instantiate()
        vine.position = _get_player_position()
        get_tree().current_scene.add_child(vine)

func _distort_world() -> void:
    # 场景布局变化——随机微调某些元素位置
    var rng = RandomNumberGenerator.new()
    for node in get_tree().get_nodes_in_group("distortable"):
        var offset = Vector2(rng.randf_range(-8, 8), rng.randf_range(-4, 4))
        node.position += offset

func _trigger_death() -> void:
    EventBus.emit_signal("player_died")

func _get_player_position() -> Vector2:
    var players = get_tree().get_nodes_in_group("player")
    if players.size() > 0:
        return players[0].global_position
    return Vector2.ZERO
```

**Step 2：提交**

```bash
git add scripts/world/world_distortion.gd
git commit -m "feat: 添加世界扭曲管理器"
```

---

### 任务 13：创建根须蔓延和死亡特效场景

**文件：**
- 创建：`scenes/effects/vine_creep.tscn`
- 创建：`scenes/effects/death_transition.tscn`

**Step 1：创建根须特效**

在 Godot 中：
1. 根节点 `Node2D`，添加 `Sprite2D`（用简单的深红线条做占位）
2. 添加脚本让根须在出现后 3 秒淡出消失

**Step 2：创建死亡转场**

1. 根节点 `CanvasLayer`
2. `ColorRect` 从透明渐变为全黑（2 秒）
3. 渐变完成后发出信号通知主场景重启

**Step 3：在 game_world.tscn 中挂载 WorldDistortion**

将 `world_distortion.gd` 脚本挂载到 GameWorld 场景的根节点。

**Step 4：提交**

```bash
git add scenes/effects/ scenes/game_world.tscn scripts/world/
git commit -m "feat: 添加根须蔓延和死亡特效"
```

---

## 阶段 7：场景组装与规则配置（2 个任务）

### 任务 14：创建主入口场景和规则初始化

**文件：**
- 创建：`scenes/main.tscn`
- 创建：`scripts/autoload/game_initializer.gd`（或直接在 main 场景脚本中）

**Step 1：创建 Main 场景**

1. 根节点 `Node2D`，挂载初始化脚本
2. 添加 GameWorld 作为子场景
3. 添加 UI 层：RulePanel、DialogBox、ScreenOverlay

**Step 2：编写初始化脚本**

```gdscript
# scenes/main.gd（挂载到 main.tscn 根节点）
extends Node2D

## 主场景——初始化游戏系统、注册规则

func _ready() -> void:
    _setup_rules()
    GameState.reset()
    _connect_death_handler()

## 注册 Demo 中的所有规则
func _setup_rules() -> void:
    # 告示牌规则 1：见树需稽首
    RuleEngine.register_rule("rule_bow_to_tree", {
        "description": "凌霄来使，见树需稽首",
        "check": func(ctx): return ctx.get("bowed", false)
    })
    # 告示牌规则 2：玉兔捣药时不可对视
    RuleEngine.register_rule("rule_dont_stare_yutu", {
        "description": "玉兔捣药时，不可与之对视",
        "check": func(ctx):
            return not ctx.get("yutu_pounding", false) or not ctx.get("facing_yutu", false)
    })
    # 告示牌规则 3：月池不可见影
    RuleEngine.register_rule("rule_pool_reflection", {
        "description": "月池之水面，不可见使者的影子",
        "check": func(ctx): return not ctx.get("looking_at_pool", false)
    })
    # 环境规则 4：吴刚伐桂五千下时树会流泪（逻辑反转）
    RuleEngine.register_rule("rule_tree_bleeding", {
        "description": "吴刚伐桂第五千下，树会流泪——靠近才安全",
        "check": func(ctx): return ctx.get("near_tree", false)
    })

func _connect_death_handler() -> void:
    EventBus.connect("player_died", _on_player_died)

func _on_player_died() -> void:
    # 2 秒后重启场景
    await get_tree().create_timer(2.0).timeout
    get_tree().reload_current_scene()
```

**Step 3：配置项目启动场景**

在 `project.godot` 中设置 `application/run/main_scene` 为 `res://scenes/main.tscn`。

**Step 4：提交**

```bash
git add scenes/main.tscn scenes/main.gd project.godot
git commit -m "feat: 添加主场景和规则初始化"
```

---

### 任务 15：最终集成测试与调试

**文件：**
- 创建：`tests/integration/test_full_flow.gd`

**Step 1：编写集成测试**

```gdscript
# tests/integration/test_full_flow.gd
extends GutTest

func test_game_flow_rule_violation_chain():
    GameState.reset()
    # 模拟三次违规
    GameState.add_violation()
    assert_eq(GameState.violation_count, 1)
    GameState.add_violation()
    assert_eq(GameState.violation_count, 2)
    GameState.add_violation()
    assert_true(GameState.is_dead())

func test_rule_discovery():
    GameState.reset()
    GameState.add_known_rule("rule_test", "测试规则")
    assert_eq(GameState.known_rules.size(), 1)
    assert_eq(GameState.known_rules["rule_test"], "测试规则")

func test_pseudo_rule_trap():
    GameState.reset()
    RuleEngine.register_pseudo_rule("trap_rule", {
        "description": "陷阱规则",
        "check": func(_ctx): return true  # 玩家遵守了
    })
    RuleEngine.check_pseudo_rule("trap_rule", {})
    assert_eq(GameState.violation_count, 1, "遵守伪规则应计入违规")
```

**Step 2：运行全套测试**

在 Godot 编辑器中打开 GUT 面板，运行全部测试。确保所有 15+ 测试通过。

**Step 3：提交**

```bash
git add tests/
git commit -m "test: 添加完整流程集成测试"
```

---

## 总结

| 阶段 | 任务数 | 产出 |
|------|--------|------|
| 阶段 1：基础设施 | 3 | EventBus, GameState, RuleEngine + 测试 |
| 阶段 2：玩家系统 | 1 | 角色移动（走/跑） |
| 阶段 3：地图 | 2 | TileMap 地图 + TriggerZone |
| 阶段 4：NPC | 3 | NPC 基类, 吴刚, 玉兔 + 对话 |
| 阶段 5：UI | 2 | 规则手册, 全屏特效 |
| 阶段 6：世界扭曲 | 2 | 扭曲管理器, 根须/死亡特效 |
| 阶段 7：组装 | 2 | 主场景, 规则初始化, 集成测试 |
| **合计** | **15** | |

所有脚本采用 TDD 方式开发，核心逻辑（RuleEngine、GameState）有完整单元测试覆盖。
