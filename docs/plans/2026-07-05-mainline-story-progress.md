# MoonSpace 主线剧情当前进度

日期：2026-07-10

## 最新复查：2026-07-10

本轮依据用户提供的五份视觉参考完成了资源复核、无损入库、运行时接入和视觉回看：

- 玉兔污染线 BE CG 已替换为用户提供的第一张图，正式资源为 `assets/sprites/moonspace/cg/be_yutu_pollution.png`。
- 广寒宫广场已接入“检查未完成时关门、吴刚与玉兔均检查完成后开门”的两态背景；宫门状态与主线检查状态实时同步。
- 宫门交互区已从旧临时位置下移到实际台阶处，旧十字形入口标记已移除，不再遮挡门体。
- 用户补充的电视框 24 帧图已接入月谷进入月宫的转场；画面在电视屏幕内按加载进度播放，最后两帧进入“找到你了”状态。
- 水池建模参考图已原样归档到 `assets/source/user_references/2026-07-10/moon_pool_model_reference.png`；经用户授权后，使用内置 imagegen 生成纯绿抠图底版本，再通过本地色键移除、边缘收缩和缩放生成正式透明资源 `assets/sprites/moonspace/moon_pool_large.png`。
- 正式月池已放大为 `144×144` 并移到广场正中轴，世界中心坐标为 `(480, 360)`；碰撞为 `112×112`，倒影触发区同步扩展，原有“静止并面对倒影才违规”的规则没有改变。
- 新游戏出生点已移到中央水池正下方；旧存档若保存位置落入新水池碰撞区，加载时会自动迁移到池子下方。
- 月池已改为实时玩家倒影：复用玩家当前动画帧，垂直翻转、压暗后在圆形水面遮罩内分条错位；玩家离开倒影区或没有面对月池时不显示。
- 倒影按玩家相对水池的四个方向使用反向角色帧，上下左右均面向观察者，并放到观察者远侧的水面位置；违规后加强横向扭曲并短暂亮起红眼。
- 五份用户原图均原样归档到 `assets/source/user_references/2026-07-10/`；已经入库的四份正式资源与归档原图逐字节一致，没有重绘、改色或覆盖式后处理。
- 已完成关门、开门、水池正常/异常状态、实际游戏视角及电视转场首帧/中间帧/发现帧视觉回看，结果符合当前 480×270 游戏画面。
- 最新完整测试结果：`212 passed`。
- 已重新打包并同步 `release/MoonSpace.exe` 和 `release/MoonSpace-20260710-151629-centered-pool-reflection.exe`；两份文件与 `dist/MoonSpace.exe` 的 SHA-256 一致，并通过隐藏启动冒烟检查。

### 本轮预览方法

- 直接打开 `tmp/preview/pool-center-directions/center-pool-normal-2x.png` 查看中央大水池与正常倒影。
- 打开 `tmp/preview/pool-center-directions/center-pool-anomaly-2x.png` 查看违规红眼状态。
- 打开 `tmp/preview/pool-center-directions/direction-contact-sheet-2x.png` 查看上下左右四个方向的倒影对照。
- 透明资源本体预览位于 `tmp/imagegen/moon-pool/pool-112-preview.png`，棋盘格区域代表透明背景。
- 运行完整游戏预览：在项目目录执行 `.\.venv\Scripts\python.exe main.py`。

## 最新复查：2026-07-06

本次重新核对了当前代码、资源目录、release 文件夹和完整测试结果。结论如下：

- 主线剧情闭环仍然完整：吴刚检查、玉兔检查、广寒宫复命、候月倒计时、HE 返回地球和四个主线 BE 都在代码中。
- 吴刚/玉兔污染已经是正式对话选项，不再是“按住奔跑键”的临时触发方式。
- 复命 staging CG 已经接入，进入广寒宫后会先播放 `report_staging.png` 短过场，再进入嫦娥对话。
- 广寒宫内殿已接入背景图，并用现有角色资源绘制嫦娥、吴刚、玉兔的轻量站位。
- 月池违规判定、玉兔背后安全检查、月桂 10 秒自修复窗口、吴刚休息状态等玩法修正仍在当前代码中。
- 宫门/水池 v3 到 v9 候选仍是审看候选，没有固化到正式 `assets/`，也没有接入运行时代码。
- 当前前院入殿入口使用的是临时低干扰标记，不是最终宫门美术。
- 最新完整测试结果：`199 passed`。
- 当前 release 最新同步版本是 `release/MoonSpace.exe` 和 `release/MoonSpace-20260705-162538-yutu-back-fix.exe`，时间为 2026-07-05 16:25；7月6日凌晨的 v3-v9 候选仍未打入 release。
## 最新更新：2026-07-05 17:15

本轮针对月池、广寒宫入口、月桂流血窗口做了玩法与视觉对齐修正：

- 月池违规触发已改为“静止、面对月池、站在倒影区”才累计停留触发；路过、背对或未真正照影不会消耗冷却。
- 月池触发逻辑已修复；v2 小水池候选已被否定并从运行时代码拆除。当前视觉暂保留原月池加深反馈，新的 v3 方向改为从 BE CG 提取“大块暗水地面/倒影污染区”等待确认。
- 广寒宫广场入口交互逻辑已补齐；v2 小宫门候选已被否定并从运行时代码拆除。新的 v3 方向改为从 `guanghan_hall.png` / `report_staging.png` 提取“宽宫殿门面/纵深入口”等待确认。
- 正式广寒宫广场不再挂告示牌；告示牌对象和规则读取仍保留在月谷教程场景。
- 月桂流血改为约 10 秒自修复窗口：大面积血痕会随时间收束，期间不再触发“靠近流血树”伤害/违规。
- 吴刚在月桂 10 秒自修复窗口中进入休息状态，停斧并使用休息帧；窗口结束后恢复伐桂计时。
- 玉兔背后检查已继续锁定为安全路径，背后不会触发正面对视违规。
- v2 候选已废弃；已生成源 CG 参考图与 v3 大场景候选供确认：`tmp/cg-inspection/cg_gate_pool_source_context_map.png`、`tmp/cg-inspection/cg_gate_pool_source_inspection.png`、`tmp/art-approval-v3/contact_sheet_art_candidates_v3.png`。
- 最新完整测试结果：`199 passed`。
- 说明：本轮没有新增独立生成美术文件到正式资源；v2 候选因不符合 CG 原貌已废弃并从运行时代码拆除。v3 候选只保存在 `tmp/art-approval-v3/`，确认后再决定是否固化为正式 PNG 资源或继续调整。

### 2026-07-06 00:10 视觉方向修正

- 用户确认 v2 的小水池、小宫门方向不符合现有 CG；v2 已作为废稿处理，不入库。
- 运行时代码中已拆除 v2 的 CG 小贴片裁切逻辑，保留月池违规触发、月桂自修复、吴刚休息等玩法修复。
- 已生成源 CG 宫门/池子参考图：`tmp/cg-inspection/cg_gate_pool_source_context_map.png`、`tmp/cg-inspection/cg_gate_pool_source_inspection.png`。
- 已生成 v3 大场景候选：`tmp/art-approval-v3/contact_sheet_art_candidates_v3.png`。
- v3 方向：宫门改为宽宫殿门面/纵深入口；月池改为大块暗水地面/倒影污染区，不再做椭圆小水池或孤立小门。
- v3 仍是候选预览，未移入正式 `assets/`，等待确认或继续调整。

### 2026-07-06 00:25 v4 源 CG 直裁对照

- 在 v3 之后继续生成了 v4 直裁候选：`tmp/art-approval-v4-source-direct/contact_sheet_direct_source_candidates_v4.png`。
- v4 不混图、不发明新形状，只把单一 CG 的宽宫门/暗水地面区域直接裁切并放入游戏视角预览。
- v4 包含 4 个宫门源区：`gate_hall_broad`、`gate_hall_center_deep`、`gate_report_right_facade`、`gate_report_center_approach`。
- v4 包含 4 个池/地面源区：`pool_wugang_broad_ground`、`pool_yutu_broad_ground`、`pool_double_broad_root_ground`、`pool_wait_broad_floor`。
- v4 仍然是候选预览，未被代码引用、未入正式资源。当前代码只保留玩法修复和临时视觉反馈。
- 为便于审看，另生成 v4 分拆大图：`tmp/art-approval-v4-source-direct/contact_sheet_gate_direct_source_candidates_v4_zoom.png`、`tmp/art-approval-v4-source-direct/contact_sheet_pool_direct_source_candidates_v4_zoom.png`。
- 目标测试结果：64 passed。

### 2026-07-06 00:20 v5 推荐组合

- 基于 v4 直裁对照，生成了一个明确推荐组合：`tmp/art-approval-v5-recommended/contact_sheet_recommended_pairing_v5.png`。
- 推荐宫门：`gate_hall_center_deep`，理由是来自广寒宫背景中轴，保留内殿纵深和入口识别度。
- 推荐池/暗水地面：`pool_double_broad_root_ground`，理由是最接近 BE 中暗水、根系污染、地面一体化的叙事中心。
- v5 仍未入正式 `assets/`，也未被运行时代码引用；等待确认后再固化资源。

### 2026-07-06 00:30 v6 宫门低突兀度方案

- 用户反馈 v5 宫门仍然太突兀；v5 不作为宫门入库方向。
- 生成 v6 宫门候选：`tmp/art-approval-v6-gate-integrated/contact_sheet_gate_integrated_candidates_v6.png`。
- v6 方向从“宫殿门面贴片”改为“嵌入现有宫墙的低对比内殿暗门/门洞”。
- v6 仍是候选预览，未入正式 `assets/`，也未被代码引用。

### 2026-07-06 00:32 v7 墙面暗口式宫门

- 继续降低宫门突兀感，生成 v7：`tmp/art-approval-v7-gate-subtle/contact_sheet_gate_subtle_candidates_v7.png`。
- v7 不再使用大面积 CG 宫殿门面，而是做成融入前院墙体的暗口/门缝/低亮门槛。
- v7 仍是候选预览，未入正式 `assets/`，也未被代码引用。

### 2026-07-06 00:55 v9 CG 对齐入口/水池候选

- 用户反馈 v7/v8 仍“不像宫门/位置不对”；v7/v8 不作为入库方向。
- 新增 v9 临时候选：`tmp/art-approval-v9-cg-aligned/contact_sheet_cg_aligned_candidates_v9.png`。
- v9 只使用现有 CG 直裁候选和当前大地图背景合成，不改正式 `assets/`，不被运行时代码引用。
- 入口候选按真实交互框 `palace_entry_rect=(432,168,96,28)` 对齐，门槛贴合宫墙脚线；contact sheet 里的绿色框仅是实际交互区参考线，不是游戏内美术。
- 水池候选按当前月池视觉中心 `(628,368)` 对齐，方向改为 BE CG 式的大块暗水/倒影污染地面，而不是小椭圆水池。
- 本轮验证：`py_compile` 通过；目标测试 `tests/test_world_objects.py tests/test_wugang.py tests/test_home_tutorial_game_flow.py` 结果为 `64 passed`；随后完整测试 `python -m pytest` 结果为 `199 passed`。
- v9 已进一步导出每个候选的透明 overlay PNG、世界预览、`candidate_manifest_v9.json` 和审看页 `tmp/art-approval-v9-cg-aligned/index.html`。
- 所有门/池/门槛 overlay 四角透明度已验证为 0，具备确认后复制到正式资源目录并按 manifest 坐标接入的条件。
- 为便于最终确认，新增放大审看图：`tmp/art-approval-v9-cg-aligned/contact_sheet_gate_zoom_v9.png`、`tmp/art-approval-v9-cg-aligned/contact_sheet_pool_zoom_v9.png`。
- 追加推荐组合预览：`tmp/art-approval-v9-cg-aligned/contact_sheet_recommended_pairing_v9.png`，当前建议优先确认 `A + P1`；理由写入 `tmp/art-approval-v9-cg-aligned/recommendation_v9.md`。
- v9 等待用户确认候选编号后，才能把选定入口/水池固化为正式 PNG 资源并更新运行时代码。
## 历史更新：2026-07-05 16:03

本轮已补齐主线叙事演出版的关键缺口：

- 吴刚、玉兔检查已经从“按住奔跑键触发污染”改为正式对话选项。
- 吴刚选项：`只记录，不执斧。` / `替斧声续记一响。`
- 玉兔选项：`只记录药色/杵声。` / `近闻药香，确认药成。`
- 广寒宫前院新增可见的“广寒宫内殿”入口宫门，玩家需要在门前按 E 复命；未验齐时仍提示“验职未齐”。
- 进入广寒宫后，复命会先播放 `report_staging.png` 短过场，再进入嫦娥对话。
- 广寒宫内殿已使用现有资源绘制轻量人物站位：嫦娥居中，吴刚、玉兔分列两侧。
- 当时测试结果：`191 passed`。
- 已重新打包并同步到：`release/MoonSpace.exe`、`release/MoonSpace-20260705-160327-mainline-dialogue.exe`。

## 结论

主线剧情骨架已经完善并接入游戏：玩家以“凌霄来使”的伪装身份进入月宫，完成吴刚、玉兔两项职司检查，进入广寒宫复命；无污染且在倒计时结束前返回月谷祭坛触发 HE，其他路线进入 BE。

当前版本已经不是单纯 Demo，已经具备完整主线闭环、多个结局触发、结局 CG 资源、广寒宫内殿背景和三名主线人物对话头像。

当前已经补齐正式对话选项、前院两态宫门、入殿交互、复命 staging 过场和内殿轻量站位。剩余打磨主要在水池正式资源适配、普通违规 3 次专属 CG、内殿角色待机动画细节，以及更完整的复命分镜。

## 已完善的主线流程

### 1. 月谷祭坛起点

状态：已实现

- 玩家从月谷/祭坛区域开始。
- 初始阶段通过告示牌获得来使规条。
- 月谷祭坛同时作为 HE 的返回点。
- 复命完成前，玩家不能直接以 HE 离开。

当前告示牌已经包含主线目标：

- 凌霄来使入宫，须依次验明三职。
- 一验吴刚伐桂。
- 二验玉兔捣药。
- 三入广寒宫复命。
- 命毕方可返月谷。
- 来使只验、只记、只复命；不得代职，不得候宫。

### 2. 吴刚伐桂检查

状态：已实现主逻辑

正确流程：

- 必须等到月桂树流血。
- 月桂流血时靠近吴刚。
- 与吴刚交互后完成“伐桂职司仍续”的检查记录。
- 正确完成后写入 `wugang_checked = true`。

污染流程：

- 玩家在检查中越权“替斧声续记一响”会触发吴刚污染。
- 当前实现里，这个污染行为已经接入正式对话选项。
- 污染后不会立刻失败，而是进入后续复命结算。
- 状态写入 `wugang_polluted = true`。

已接入文案方向：

- 正确检查强调“只需记下，不必替我”。
- 污染检查强调“替斧声续记一响”“记录边缘渗出木色”。

### 3. 玉兔捣药检查

状态：已实现主逻辑

正确流程：

- 玉兔正面接触属于违规。
- 玩家需要绕到玉兔身后或侧后方。
- 从正确位置交互后完成“捣药职司仍续”的检查记录。
- 正确完成后写入 `yutu_checked = true`。

污染流程：

- 玩家越权“近闻药香/替玉兔确认药成”会触发玉兔污染。
- 当前实现里，这个污染行为已经接入正式对话选项。
- 污染后不会立刻失败，而是进入后续复命结算。
- 状态写入 `yutu_polluted = true`。

已接入文案方向：

- 正确检查强调“药未由来使试验”。
- 污染检查强调“药雾先在影子的眼眶里沉下去”“药簿记录边缘泛白”。

### 4. 广寒宫内殿复命

状态：已实现主逻辑和场景背景

进入条件：

- `wugang_checked = true`
- `yutu_checked = true`

如果检查未齐：

- 广寒宫门不会放行。
- 对话提示“验职未齐，广寒宫不受复命”。

如果检查完成：

- 进入广寒宫内殿。
- 已接入正式广寒宫内殿背景图。
- 嫦娥对话头像已经接入对话框。

### 5. 无污染复命

状态：已实现

条件：

- 吴刚检查完成。
- 玉兔检查完成。
- 没有吴刚污染。
- 没有玉兔污染。

结果：

- 嫦娥正常收下记录。
- 启动“候月”倒计时，当前为 60 秒。
- 倒计时文案故意具有误导性，提示玩家“候月”，但真实 HE 要求玩家不要留下来等。

当前复命文案核心：

- “吴刚斧声未绝，玉兔杵声未停。”
- “来使的记录，月宫收下了。”
- “复命既毕，使者可候月落。”

## 已实现的结局

### HE：返回地球

状态：已实现，已接入 CG

触发条件：

- 完成吴刚检查。
- 完成玉兔检查。
- 无吴刚污染。
- 无玉兔污染。
- 完成广寒宫复命。
- 候月倒计时结束前离开广寒宫。
- 返回月谷祭坛。

结果：

- 触发 `he_return_earth`。
- 播放返回地球 CG。
- CG 图中远方对象已经按要求使用地球，不使用月亮。

### BE：留下来等 / 嫦娥结局

状态：已实现，已接入 CG

触发条件：

- 无污染复命完成。
- 候月倒计时归零前没有回到月谷祭坛。

结果：

- 触发 `be_change`。
- 播放“留下来等”的 BE CG。
- 叙事含义：玩家接受了“候宫/候月”的陷阱，被月宫流程收编。

### BE：吴刚污染

状态：已实现，已接入 CG

触发条件：

- 吴刚检查时发生越权污染。
- 完成玉兔检查。
- 进入广寒宫复命。
- 污染复命对话结束后出殿。

结果：

- 触发 `be_wugang`。
- 出殿后直接进入月池异常 CG。
- 叙事含义：玩家被月池照出已经归入吴刚职司，成为新的伐桂人。

### BE：玉兔污染

状态：已实现，已接入 CG

触发条件：

- 玉兔检查时发生越权污染。
- 完成吴刚检查。
- 进入广寒宫复命。
- 污染复命对话结束后出殿。

结果：

- 触发 `be_yutu`。
- 出殿后直接进入月池异常 CG。
- 叙事含义：玩家被月池照出已经归入玉兔职司，成为新的捣药人。

### BE：双重污染 / 月桂养料

状态：已实现，已接入 CG

触发条件：

- 吴刚污染和玉兔污染同时存在。
- 进入广寒宫复命。
- 污染复命对话结束后出殿。

结果：

- 触发 `be_laurel_mixed`。
- 出殿后直接进入异常 CG。
- 叙事含义：玩家半属吴刚、半属玉兔，被玉桂树判定为多余记录，拖走吞噬，树上多出流血面孔。

### BE：普通违规 3 次

状态：沿用已有死亡系统

触发条件：

- 普通规则违规累计达到 3 次。

当前普通违规包括：

- 月桂前未按规则稽首。
- 玉兔捣药时正面接触/对视。
- 月池前凝视倒影。
- 广寒宫前疾走伪规则导致的违规链。
- 月桂流血阶段现在是 10 秒自修复窗口，不再造成普通违规。

结果：

- 进入已有死亡界面/死亡结算。
- 这个 BE 还没有单独接入新的主线 CG，后续可以决定是否补一张“身份败露/月桂养料”专属 CG。

## 已接入的视觉资源

### 正式游戏资源

- `assets/sprites/moonspace/backgrounds/guanghan_hall.png`
- `assets/sprites/moonspace/portraits/chang_e_dialog.png`
- `assets/sprites/moonspace/portraits/wugang_dialog.png`
- `assets/sprites/moonspace/portraits/yutu_dialog.png`
- `assets/sprites/moonspace/sheets/chang_e_16frames.png`
- `assets/sprites/moonspace/cg/he_earth_return.png`
- `assets/sprites/moonspace/cg/be_wugang_pollution.png`
- `assets/sprites/moonspace/cg/be_yutu_pollution.png`
- `assets/sprites/moonspace/cg/be_double_pollution.png`
- `assets/sprites/moonspace/cg/be_wait_trap.png`
- `assets/sprites/moonspace/cg/report_staging.png`

### 已实际接入游戏显示

- 广寒宫内殿背景：已接入内殿模式。
- 嫦娥、吴刚、玉兔：已在内殿完成轻量站位。
- 复命 staging：已接入 `report_staging.png` 短过场。
- 嫦娥/吴刚/玉兔对话头像：已接入对话框。
- HE 和四个主线 BE CG：已接入结局播放器。

### 已保留来源归档

确认过的生成图已同步保存到：

- `assets/source/imagegen/candidates/`

用途：

- 后续返修。
- 重新裁切。
- 做正式立绘/动画版本时作为源图参考。

## 当前版本的剩余打磨

### 1. 污染选项已经改为正式对话选项

当前吴刚污染、玉兔污染已经不再依赖隐藏跑步键，而是在检查对话最后显示正式选项：

吴刚：

- 只记录，不执斧。正确
- 替斧声续记一响。污染

玉兔：

- 只记录药色/杵声。正确
- 近闻药香，确认药成。污染

### 2. 广寒宫前院入口交互已经补齐，美术仍是临时标记

广寒宫前院现在有可见的“广寒宫内殿”入口提示，玩家需要站到门前按 E 复命：

- 验职未齐时，宫门提示“验职未齐”。
- 验职完成时，进入广寒宫内殿。
- 当前运行时代码使用的是低干扰临时标记，不是最终宫门美术。
- v9 宫门候选仍在 `tmp/art-approval-v9-cg-aligned/` 等待确认，未入正式资源。

### 3. 复命 staging CG 已接入

`report_staging.png` 已经作为复命短过场接入：

- 进入广寒宫后先显示 2.8 秒复命 CG，也可以按 E 跳过。
- 然后进入嫦娥对话。
- 污染和无污染复用同一张 staging 图，字幕按分支变化。

### 4. 广寒宫内殿已完成轻量人物站位

当前内殿已使用现有资源绘制轻量站位：

- 嫦娥居中。
- 吴刚、玉兔分列两侧。
- 暂未扩展为完整可探索地图。

### 5. 嫦娥 16 帧图已入库，后续可增强为待机动画

当前已入库：

- `assets/sprites/moonspace/sheets/chang_e_16frames.png`

后续还可增强：

- 嫦娥 NPC 待机动画。
- 与复命对话同步的待机帧。

### 6. 前院水池/宫门正式美术已接入

当前状态：

- v2 小水池/小宫门方案已经废弃并从运行时代码拆除。
- v3-v9 保留为历史候选，不再作为正式入库方向。
- 用户提供的关门/开门场景图已直接接入宫门两态，旧临时入口标记已移除。
- 用户提供的水池图已完成透明化和 `144×144` 游戏尺寸适配，正式资源为 `moon_pool_large.png`，并放置在广场世界坐标 `(480, 360)`。
- 月池碰撞、倒影范围和异常反馈已按新尺寸同步调整。

### 7. 普通违规 3 次结局还没有专属新 CG

当前普通违规 3 次沿用死亡系统。

如果要统一主线表现，建议补一张：

- `be_identity_exposed_laurel_feed.png`

内容方向：

- 主角身份被月宫识破。
- 月桂根须从地面伸出。
- 不是污染变形，而是“非来使”的直接清除。

## 当前测试和打包状态

### 测试

最新完整测试结果：

- `212 passed`

覆盖范围包括：

- 主线流程。
- 广寒宫复命。
- HE 触发。
- 各污染 BE 触发。
- 结局 CG 资源。
- 对话头像资源。
- 广寒宫内殿背景。
- 存档、规则、场景切换等基础系统。

### 打包

当前 release 文件夹最新同步版本：

- `release/MoonSpace.exe`
- `release/MoonSpace-20260710-151629-centered-pool-reflection.exe`

历史版本仍保留：

- `release/MoonSpace-20260705-160327-mainline-dialogue.exe`
- `release/MoonSpace-20260705-145925-mainline-assets.exe`

说明：

- `release/MoonSpace.exe`、版本化文件和 `dist/MoonSpace.exe` 大小均为 `123775847` 字节，SHA-256 均为 `2A7746610C8811997E44A0CDD35F02528A62F47FD5045AD0E6F2099EB16FF0AD`。
- 新包已包含宫门两态、中央大水池、四方向实时倒影、玉兔 BE 和电视多帧转场。
- 可执行文件已通过隐藏启动 8 秒冒烟检查。

## 下一步建议

优先级 1：补普通违规 3 次专属主线 CG。

原因：

- 当前 HE 和主要主线 BE 都已有专属图，普通三次违规死亡仍偏系统化。

优先级 2：继续增强广寒宫内殿人物待机/复命分镜。

原因：

- 当前已有静态轻量站位，后续可以使用嫦娥 16 帧资源增强待机表现。

优先级 3：继续做演出细节复查。

原因：

- 当前主线资源已形成完整组合，后续重点是人物待机和普通违规结局的表现统一。

优先级 4：后续改动完成后再更新 release。

原因：

- 当前 release 已同步本轮最终版本，无需再次打包。

## 总体进度判断

以“完整版主线通关”为标准：

- 主线设计：已完成。
- 主线可玩闭环：已完成。
- 多结局触发：已完成。
- 已确认视觉资源入库：已完成。
- 关键 CG 接入：已完成。
- release 包同步：已完成到 `MoonSpace-20260710-151629-centered-pool-reflection.exe`。
- 正式对话选项玩法：已完成。
- 复命过场演出：已接入 staging CG。
- 内殿人物演出：已完成轻量静态站位，待继续增强动画。
- 前院宫门正式美术：关门/开门两态已入库并接入。
- 前院水池正式美术：已完成透明化、尺寸适配、碰撞与倒影区域接入。
- 普通违规 3 次专属 CG：未完成。

当前可以称为：

> 主线叙事演出版的关键流程、宫门两态、中央大水池、四方向实时倒影、玉兔 BE、电视多帧转场和 release 更新均已完成；后续工作集中在普通违规 BE CG 和演出精修。















