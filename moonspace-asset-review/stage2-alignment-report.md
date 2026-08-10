# MoonSpace 第二阶段：美术资源对齐与生产清单

审查日期：2026-08-07（第二阶段基线修订 / 第三阶段 Batch A 入口）
仓库：`D:\CodeWorkspace\MoonSpace`
审查边界：保留第二阶段盘点结论；本次只修正运行时坐标、资源分类、评审页链接并记录 Batch A 基准板证据。用户本轮明确要求移除旧 `pound_table.png` / `sign_board.png` 位图；其碰撞锚点/兼容类实现仍保留，不修改剧情状态机、碰撞布局、计时规则、存档格式或正式结局 ID，不生成最终 CG，不重新打包发布版。

> 根目录未找到物理 `AGENTS.md`；本次按用户在任务中提供的同等约束执行。开始时 `git status --short --branch` 为 `main...origin/main`，已有用户改动和未跟踪目录均保留。

## 结论先行

第二阶段盘点完成。用户移除两张旧道具位图后，当前 `assets/sprites/moonspace` 实际包含 **45 张 PNG**：

- **31 张**在当前正常运行路径中会被实际绘制；
- **6 张**仍由代码保留为 fallback 或兼容回退，但正式资源存在时不会加载；
- **8 张**当前没有进入正常运行画面，其中 4 张是已被正式资源替代的废弃候选，4 张仍可作为未来表达或 CG 资源接入。

推荐采用 **方向 B：游戏内保持精细像素化恐怖，CG 保持电影绘景感，但所有角色设定、服装剪影、宫门、月池、帷幕、灯具和地面纹样必须共享锚点**。这能保留已有高细节 CG 的表现上限，也不必推翻第一阶段已经冻结的俯视地图和运行时流程；但需要先统一四名角色的比例/形态，再处理旧小图回退、玉兔/研钵重复、月池与宫门锚点。

当前最需要用户批准的五项决策是：

1. 最终视觉方向是否采用 B；
2. 玉兔是否正式定为“异化的类人兔妖/兔形生物”，并允许污染状态只改变身体和道具关系而不改成另一种角色；
3. 嫦娥是否按暂定基线收敛到主角高度约 1.5～1.6 倍；CG 特写可单独加强压迫感，但不能把游戏内比例继续当作约 2 倍；
4. 月池和宫门是否以当前俯视轮廓为游戏与 CG 的共同造型锚点；
5. CG 分镜是否按本报告的 33 个镜头覆盖范围推进，以及首批先做“视觉基准 + 复命/HE/普通违规”还是先做四个污染 BE。

本次只在已有评审目录内更新报告/页面/预览，并按用户明确反馈移除两张旧道具位图；未覆盖或回退其他仓库改动、未跟踪资源、`release/` 文件或旧审查素材。

## 0. 第三阶段入口修订（2026-08-07）

- **月池当前场景坐标以运行时构造为准：** `core/game.py:137` 明确调用 `MoonPool(480, 300)`。`world/moon_pool.py:19` 的 `DEFAULT_CENTER = (480, 360)` 只是类构造器的通用默认参数，不能作为当前月宫庭院场景的坐标依据；当前场景的视觉中心、碰撞中心和后续截图均以 `(480,300)` 为准。
- **HE 现有图重新分类：** `assets/sprites/moonspace/cg/he_earth_return.png` / 评审副本 `cg-he-earth-return.png` 现在标记为“月面返程/遥望地球过渡镜头”。画面仍停留在月面平台，地球位于远景；它不是已经抵达地球的最终画面。真正的 `earth_arrival` 必须在 Batch C 新增独立镜头。
- **stale 资产不再作为正式依据：** 旧绿幕嫦娥图集 `sheets/chang_e_16frames.png`、旧庭院/宫门候选 `courtyard_bg*.png` / `courtyard_gate_*.png`、旧矩形月池 `moon_pool.png` 以及 `gate-v9` / `pool-v9` 联系表均保留为历史问题证据，并显式标记为 `STALE`；它们不能升格为正式画面或继续用于基准板主图。
- **评审页链接已修正：** `pages/characters.html` 与 `pages/environments.html` 的 `overview.html`、`cg-and-endings.html` 已改为现有的 `asset-overview.html`、`cg-endings.html`；所有本地 `href` 均应能在 `pages` 目录内解析。

## 1. 证据基线与文档漂移

### 1.1 已核对的运行时事实

| 事实 | 代码证据 | 当前结论 |
|---|---|---|
| 逻辑画布 480×270，默认窗口 2 倍显示 | `config.py:4-10` | 固定，不在本阶段改变 |
| 广寒宫世界 960×720 | `config.py:18-22`、`core/game.py:530-542` | 固定；`guanghan_hall_curtain.png` 尺寸吻合 |
| 广寒宫唯一可行走背景 | `core/game.py:125`、`_draw_guanghan_background()` | 只用 `backgrounds/guanghan_hall_curtain.png` |
| 正面王座图不进入世界坐标 | `core/game.py:111-113, 530-542` | `backgrounds/guanghan_hall.png` 只作为 CG/构图候选 |
| 庭院宫门状态 | `world/palace_wall.py:16-18, 88-100` | 当前绘制的是 `courtyard_expanded_closed/open.png` 两态 |
| 月池正式路径 | `world/moon_pool.py:17-18, 51-60` | `moon_pool_large.png` 优先，`moon_pool.png` 仅 fallback |
| 角色大图与缺图回退 | `entities/player.py:278-283`、`entities/wugang.py:84-101`、`entities/yutu.py:60-75` | 大图优先；三份旧小图已清理，缺图时使用程序化安全回退 |
| 嫦娥世界动画 | `core/game.py:127, 564-588` | 只加载透明版 16 帧，并平滑缩放到 100×100；实际 Alpha 高度收敛到主角约 1.5～1.6 倍 |
| 对话头像 | `ui/dialog_box.py:30-31, 118-128` | 当前使用四列 `dialog_portraits_large.png`，不使用三张独立头像图 |
| 结局 ID | `ui/ending_cg.py:52-70` | 正式五个 ID 为 `he_return_earth`、`be_wugang`、`be_yutu`、`be_double`、`be_change` |
| 复命 staging | `core/game.py:675-687, 1288-1310` | `report_staging.png` 当前为 2.8 秒共享入殿镜头 |
| 登记台 | `core/game.py:596-617`、`ui/envoy_register.py:73-96, 187-193` | 当前是可选身份验牒；姓名输入方法仍是不可达兼容代码 |
| 开场色条 | `ui/opening_cg.py:141-157` | 程序绘制，不属于 45 张正式 PNG；第三阶段应替换为正式构图 |

验证命令：

```text
Get-ChildItem assets/sprites/moonspace -Recurse -Filter *.png
.\.venv\Scripts\python.exe -m pytest -q
```

当前测试结果：**319 passed**（本轮完整运行约 32.14s）。这比剧情简报和主线进度文档中记录的 199/212 passed 更新，不能继续引用旧数字。

### 1.2 文档漂移

- `docs/plans/moonspace-storyline-and-cg-brief.md` 仍把广寒宫写成“远景不可进入”，而当前代码已经有独立 960×720 可行走内殿、南门、登记台和复命区；按第一阶段约束标记为文档漂移。
- `docs/plans/moonspace-character-scene-composition.md` 仍把嫦娥定义成远景模糊光团；当前代码已经加载透明 16 帧并以 100×100 世界精灵绘制，必须以当前资源和代码为准。
- `docs/plans/2026-07-05-mainline-story-progress.md` 的“已接入视觉资源”仍列出非透明嫦娥图、三张独立头像和正面广寒宫图为正式接入；实际代码并非如此。
- 同一进度文档还写“内殿嫦娥居中、吴刚、玉兔分列两侧”。当前 `_draw_guanghan_actors()` 实际只绘制嫦娥、登记台和来使，未绘制吴刚/玉兔。`report_staging.png` 里出现他们不等于运行时内殿已经有他们。
- `moonspace-asset-review` 原有页面仍写“31 张资源”，并使用审查目录里的旧副本和旧文件名链接；本报告是第二阶段当前事实的准据，旧页面不能直接当作运行时事实。

## 2. 资源总数与分类统计

### 2.1 按目录统计

| 目录 | 数量 | 含 alpha 通道 | 当前正常运行可见 | fallback/兼容 | 当前未进入正常运行 |
|---|---:|---:|---:|---:|---:|
| `backgrounds/` | 6 | 3 | 3 | 0 | 3 |
| `cg/` | 6 | 0 | 6 | 0 | 0 |
| `portraits/` | 4 | 0 | 1 | 0 | 3 |
| `props/` | 2 | 2 | 2 | 0 | 0 |
| `sheets/` | 3 | 1 | 2 | 0 | 1 |
| `ui/` | 3 | 0 | 3 | 0 | 0 |
| 根目录 PNG | 23 | 22 | 15 | 6 | 2 |
| **合计** | **45** | **26** | **31** | **6** | **8** |

`RGBA*` 表示文件有 alpha 通道，但该图没有 alpha=0 的真正透明像素，基本应按不透明背景处理；不能把“有 alpha 通道”误报为“透明素材”。

### 2.2 按用途统计

| 用途 | 数量 | 说明 |
|---|---:|---|
| 角色动画与角色道具 | 10 | 玩家、吴刚、玉兔三组大小图，以及嫦娥 16 帧透明图 |
| 对话头像 | 4 | 1 张当前四列运行时头像表，3 张未接入的独立变体表 |
| 可行走场景与场景物体 | 13 | 庭院/教程/内殿背景、宫门状态、月桂、月池、登记台等；旧告示牌/独立捣药台位图已移除 |
| CG 与开场 | 10 | 6 张复命/结局 CG，4 张开场背景 |
| 系统 UI 与转场 | 8 | 菜单、转场电视、发现面孔、玉简 UI、残破玉简等 |
| **合计** | **45** | |

## 3. 45 张 PNG 完整盘点

状态说明：

- “正常运行”= 当前文件存在时会进入实际绘制路径；
- “fallback”= 代码有回退路径，但当前正式主资源存在，所以正常运行不会加载；
- “未接入”= 文件存在且可能有价值，但当前主流程没有实际绘制它；
- “废弃候选”只表示已被正式资源替代；本轮用户明确批准删除的两张旧道具位图不再列入盘点。

### 3.1 背景与 CG

| # | 资源（像素尺寸 / 通道） | 所属 / 原生视角 / 风格 | 代码引用、运行时缩放与实际状态 | 一致性判断 / 处理结论 |
|---:|---|---|---|---|
| 1 | `assets/sprites/moonspace/backgrounds/courtyard_expanded_closed.png`；960×640；RGBA* | 月宫庭院；俯视；高细节暗色 AI 绘景/像素化纹理 | `world/palace_wall.py:16-18, 88-100`；世界 1:1，视口再按 2 倍显示；当前关门状态实际绘制 | 当前正式庭院底图和北门锚点；保留。 |
| 2 | `assets/sprites/moonspace/backgrounds/courtyard_expanded_open.png`；960×640；RGBA* | 月宫庭院；俯视；与 #1 同一构图的开门/红光状态 | 同上；世界 1:1；两项职司检查完成后实际绘制 | 状态差异真实，不是字幕替换；保留。 |
| 3 | `assets/sprites/moonspace/backgrounds/courtyard_gate_closed.png`；1672×941；RGB | 宫门参考；正面/电影绘景；高细节 AI 绘景 | 无当前运行时加载；`tests/test_assets.py` 仅验证并保留用户参考 | 已由 #1 的 960×640 庭院两态替代；废弃候选。 |
| 4 | `assets/sprites/moonspace/backgrounds/courtyard_gate_open.png`；1672×941；RGB | 宫门参考；正面/电影绘景；高细节 AI 绘景 | 无当前运行时加载；只作为参考/测试资产 | 已由 #2 替代；废弃候选。 |
| 5 | `assets/sprites/moonspace/backgrounds/guanghan_hall_curtain.png`；960×720；RGBA* | 广寒宫内殿；俯视/半俯视；高细节暗色绘景 | `core/game.py:125, 530-542`；世界 1:1，摄像机裁切后 2 倍显示；当前唯一可行走内殿 | 帷幕、南门、台阶、地面纹样可成为 CG 锚点；保留。 |
| 6 | `assets/sprites/moonspace/backgrounds/guanghan_hall.png`；1672×941；RGB | 广寒宫王座/复命；正面；电影绘景 | `core/game.py:126` 仅保存为候选路径，当前没有加载/绘制；若接入需缩放到 480×270 | 与 #5 共享建筑、灯具、帷幕语言但不是地图；待接入。 |
| 7 | `assets/sprites/moonspace/cg/be_double_pollution.png`；1672×941；RGB | 双污染结局；正面/三分之四；电影恐怖绘景 | `ui/ending_cg.py:52-70, 120-128`；平滑缩放到 480×270，再按 2 倍显示；`be_double` 实际播放 | 月池、月桂根系、斧/药臼混合地标明确；当前可作最终归档帧；保留。 |
| 8 | `assets/sprites/moonspace/cg/be_wait_trap.png`；1672×941；RGB | 候宫/候月 BE；正面；电影绘景 | 同上；`be_change` 实际播放 | 王座、帷幕、灯具与 #5/#6 有可对齐空间，但“候宫”前置发现镜头缺失；保留。 |
| 9 | `assets/sprites/moonspace/cg/be_wugang_pollution.png`；1672×941；RGB | 吴刚污染 BE；正面池景；电影绘景 | 同上；`be_wugang` 实际播放 | 来使深蓝衣、池边宫门和倒影一致；吴刚的世界小图尺度过小；保留为最终帧，角色层需微调。 |
| 10 | `assets/sprites/moonspace/cg/be_yutu_pollution.png`；1672×941；RGB | 玉兔污染 BE；正面池景；电影绘景 | 同上；`be_yutu` 实际播放 | 长耳、灰白兔形、红眼和药臼明确；与世界大图一致；保留。 |
| 11 | `assets/sprites/moonspace/cg/he_earth_return.png`；1672×941；RGB | **月面返程/遥望地球过渡镜头**；正面/背面远景；电影绘景 | 同上；`he_return_earth` 当前把它作为共享单帧播放 | 只证明“地球在远处、返程已开始”，不是抵达地球最终画面；保留作过渡母版，必须另补祭坛启动、离开月宫和现实房间 `earth_arrival`。 |
| 12 | `assets/sprites/moonspace/cg/report_staging.png`；1672×941；RGB | 复命入殿；三分之四大厅；电影绘景 | `core/game.py:675-687`；2.8 秒共享 staging，平滑缩放到 480×270 | 可作为一次建立镜头；当前同时承载所有分支，污染细节不够；微调。 |
| 13 | `assets/sprites/moonspace/courtyard_bg.png`；480×270；RGBA* | 旧庭院；俯视；早期高细节背景 | 无当前代码引用；仅可作为旧版本对照 | 已被更大庭院构图取代；废弃候选。 |
| 14 | `assets/sprites/moonspace/courtyard_bg_large.png`；960×540；RGBA* | 旧庭院；俯视；高细节暗色绘景 | `world/tile_map.py:35`，`world/palace_wall.py:43` 只探测/备用；当前 `_draw_playing()` 不调用 `TileMap.draw()`，所以不进入当前可见画面 | 仍可作为旧地图回退，但不是当前正式底图；回退资源。 |
| 15 | `assets/sprites/moonspace/home_tutorial_bg_open.png`；960×540；RGBA 不透明 | 月谷教程/祭坛；俯视；高细节暗色绘景 | `world/home_tutorial_scene.py:102-105`；世界 1:1，摄像机裁切后 2 倍显示；读完规条后实际绘制 | 祭坛、告示牌、南北门和兔舍构成稳定入口锚点；保留。 |
| 16 | `assets/sprites/moonspace/home_tutorial_bg.png`；960×540；RGBA 不透明 | 月谷教程/祭坛；俯视；开门前状态 | 同上；初始实际绘制 | 与 #15 是真实状态对；保留。 |
| 17 | `assets/sprites/moonspace/laurel_tree.png`；176×220；RGBA 透明 | 月桂树；正面/半俯视透明精灵；高细节 AI 树体 | `world/laurel_tree.py:60-71`；世界 1:1，随大庭院绘制，代码另叠加伤口/流血 | 功能成立，但紫色枝叶、树体轮廓与 `be_double` 中黑色根系/树干人脸不是同一造型；重制。 |
| 18 | `assets/sprites/moonspace/main_menu_bg.png`；480×270；RGBA 不透明 | 主菜单；正面电影绘景；高细节暗色绘景 | `ui/main_menu.py:137-139`；逻辑 1:1，再按 2 倍显示 | 与开场房间和电视转场同一现实层；保留。 |

### 3.2 场景物体、角色与头像

| # | 资源（像素尺寸 / 通道） | 所属 / 原生视角 / 风格 | 代码引用、运行时缩放与实际状态 | 一致性判断 / 处理结论 |
|---:|---|---|---|---|
| 19 | `assets/sprites/moonspace/moon_pool_large.png`；144×144；RGBA 透明 | 月池；俯视圆形水面；高细节透明道具 | **`core/game.py:137` 的 `MoonPool(480,300)`；**世界 1:1，视觉 144×144，碰撞 112×112，显示 2 倍；当前实际绘制 | 运行时可读性好，且有倒影逻辑；`world/moon_pool.py` 的 `(480,360)` 只属于未传参实例的默认值，不能用于当前场景锚点；CG 共同轮廓仍待批准。 |
| 20 | `assets/sprites/moonspace/moon_pool.png`；64×40；RGBA 透明 | 旧月池；俯视矩形；粗糙旧像素/程序 fallback | `world/moon_pool.py:18, 55-60`；只有大图缺失时按 144×144 平滑放大 | 形状、边缘和 CG 差异大；仅保留兼容能力；回退资源。 |
| 21 | `assets/sprites/moonspace/opening_cg_blackout.png`；480×270；RGBA 不透明 | 开场；全屏黑场；高细节绘景/过渡 | `ui/opening_cg.py:155-157, 163-166`；逻辑 1:1，再按 2 倍显示；当前使用 | 黑场有明确叙事作用；保留。 |
| 22 | `assets/sprites/moonspace/opening_cg_blood_moon.png`；480×270；RGBA 不透明 | 开场；窗外/血月；高细节绘景 | `ui/opening_cg.py:116-119, 163-166`；逻辑 1:1；当前使用 | 与房间、月光镜头色彩连续；保留，后续拆出云层变化镜头。 |
| 23 | `assets/sprites/moonspace/opening_cg_moonlight.png`；480×270；RGBA 不透明 | 开场；房间被月光侵入；高细节绘景 | `ui/opening_cg.py:127-133, 163-166`；逻辑 1:1；当前使用 | 可承担“现实被月宫覆盖”建立镜头；保留。 |
| 24 | `assets/sprites/moonspace/opening_cg_room.png`；480×270；RGBA 不透明 | 开场；现实房间/电脑；高细节 AI 写实绘景 | `ui/opening_cg.py:92-104, 163-166`；逻辑 1:1；当前在 0～6 秒两个节拍重复使用 | 角色服装与游戏来使服装还未完全共享；可作为母版，需补独立转身/屏幕特写；微调。 |
| 25 | `assets/sprites/moonspace/palace_wall_bg.png`；480×80；RGBA 不透明 | 旧宫墙；俯视窄条；粗糙旧像素 | `world/palace_wall.py:53-58`；仅在扩展庭院资源缺失时 fallback，当前不会出现 | 只能当最后回退，不应作为正式审美基准；回退资源。 |
| 26 | `assets/sprites/moonspace/player_envoy_large.png`；168×248；RGBA 透明；4×4，每帧 42×62 | 凌霄来使；四向俯视/半俯视；CG 对齐的精细像素角色 | `entities/player.py:278-283`；每帧 42×62，世界 1:1；**2026-08-07 已接入正式主路径**，碰撞仍为 16×24 | 由已批准的年轻清瘦、无胡须、黑发髻、深靛交领长袍母版制作；保留原站位/碰撞，已在庭院与内殿真实绘制路径验证。 |
| 27 | `assets/sprites/moonspace/player_envoy.png`；128×24；RGBA 透明；8 帧 16×24 | **已清理：** 凌霄来使旧小图；四向俯视；粗糙旧像素 | 无当前运行时引用；文件已按用户确认删除，#26 缺失时使用程序化回退 | 不是 #26 的降采样版本，细节/比例完全不同；不再作为资源或视觉依据。 |
| 28 | `assets/sprites/moonspace/portraits/chang_e_dialog.png`；1254×1254；RGB；2×2 变体表 | 嫦娥头像；正面半身；高细节头像变体 | 无当前运行时引用；测试只确认文件存在 | 与 #29 的嫦娥身份相同但不是字节重复，含表情/束缚变体；待接入。 |
| 29 | `assets/sprites/moonspace/portraits/dialog_portraits_large.png`；1672×941；RGB；四列头像表 | 玩家/嫦娥/吴刚/玉兔；正面半身；高细节头像表 | `ui/dialog_box.py:30-31, 118-128`；每列裁成约 418×941，再平滑缩到高 224；当前唯一对话头像表 | 四名角色统一了边框和画面密度，是当前头像 canonical；保留。 |
| 30 | `assets/sprites/moonspace/portraits/wugang_dialog.png`；1254×1254；RGB；2×2 变体表 | 吴刚头像；正面/三分之四；高细节头像变体 | 无当前运行时引用；当前对话裁剪不使用此文件 | 身份和 #29 的吴刚一致，但不是重复文件；待接入。 |
| 31 | `assets/sprites/moonspace/portraits/yutu_dialog.png`；1254×1254；RGB；2×2 变体表 | 玉兔头像；正面/侧面；高细节头像变体 | 无当前运行时引用；当前对话裁剪不使用此文件 | 长耳、红眼、灰白身体与 #29 一致；待接入。 |
| 32 | `assets/sprites/moonspace/pound_table.png`；24×24；RGBA 透明 | **已移除：旧捣药台/小研钵；俯视；粗糙旧像素** | 位图已按用户反馈删除；`world/pound_table.py` 仍保留 16×16 碰撞锚点，但 `draw()` 不再绘制旧道具；玉兔大图承担药臼/杵视觉 | 用户确认游戏已有替代物；不再作为正式资源或视觉依据。 |
| 33 | `assets/sprites/moonspace/props/broken_jade_slip.png`；950×725；RGBA 透明 | 残破玉简；等距/俯视道具；高细节像素化绘景 | `ui/broken_jade.py:17, 47-57`；UI 中平滑缩到高 82；首次月池凝视后实际显示 | 作为“月池发现物”功能和风格都成立；保留。 |
| 34 | `assets/sprites/moonspace/props/registration_desk.png`；1672×941；RGBA 透明 | 广寒宫登记台；俯视/等距；高细节绘景道具 | `core/game.py:596-617`；平滑缩到世界 180×96；当前内殿实际绘制 | 玉简、砚台和黑色台面与内殿地面相容；当前不承载姓名输入；保留。 |
| 35 | `assets/sprites/moonspace/scene_transition_screen.png`；480×270；RGB | 电视转场；正面；电影绘景 | `ui/scene_transition.py:102-106`；逻辑 1:1，再按 2 倍显示；当前实际使用 | 与开场现实房间共享电脑/电视语法；保留。 |
| 36 | `assets/sprites/moonspace/sheets/chang_e_16frames_transparent.png`；1254×1254；RGBA 透明；4×4 | 嫦娥世界动画；正面站立；高细节透明角色 | `core/game.py:127, 564-588`；切成 16 帧，每帧平滑缩至 100×100；当前实际使用 | 服装、面纱、发饰与头像/CG可认作同一人；本轮已把运行时可见高度收敛到来使约 1.5～1.6 倍；不改站位、碰撞或剧情。 |
| 37 | `assets/sprites/moonspace/sheets/chang_e_16frames.png`；1254×1254；RGB 绿色背景；4×4 | **STALE：嫦娥世界动画旧版；正面站立；绿幕源图** | 无当前运行时引用；测试仅保留文件 | 与 #36 内容近似但绿幕不可直接进场；仅作历史问题证据，不能作为正式画面依据。 |
| 38 | `assets/sprites/moonspace/sheets/scene_transition_monitor_24frames.png`；1448×1086；RGB；6×4 | 电视寻找转场；正面；高细节动画图集 | `ui/scene_transition.py:26, 121-137`；每帧 362×181，裁 318×177 后平滑到 UI 251×126；当前实际使用 | 24 帧提供真实发现过程，替代旧程序占位；保留。 |
| 39 | `assets/sprites/moonspace/sign_board.png`；24×32；RGBA 透明 | **已移除：旧告示牌；俯视；粗糙旧像素** | 位图已按用户反馈删除；`core/game.py` 当前没有实例化 `SignBoard`，教程背景已把告示牌烘入大图；`world/sign_board.py` 仅保留兼容/测试类实现 | 用户确认已有背景替代物；不再作为正式资源或视觉依据。 |
| 40 | `assets/sprites/moonspace/transition_found_you_face.png`；92×112；RGBA 透明 | **已清理：** 电视发现面孔旧备用图；正面；透明恐怖精灵 | 无当前运行时引用；文件已按用户确认删除，24 帧监控转场保留 | 发现阶段由监控 24 帧主路径和程序化回退承担；不再作为资源或视觉依据。 |

### 3.3 UI 与角色回退

| # | 资源（像素尺寸 / 通道） | 所属 / 原生视角 / 风格 | 代码引用、运行时缩放与实际状态 | 一致性判断 / 处理结论 |
|---:|---|---|---|---|
| 41 | `assets/sprites/moonspace/ui/jade_register_volume_1.png`；480×270；RGB | 玉简验牒 UI；全屏；高细节内殿底图 + 玉简 | `ui/envoy_register.py:29-31, 187-193`；逻辑 1:1，再按 2 倍显示；当前实际使用；当前 Git 未跟踪 | 资源和当前“身份验牒”流程相容；保留。 |
| 42 | `assets/sprites/moonspace/ui/jade_register_volume_2.png`；480×270；RGB | 玉简旧卷 UI；全屏；同套底图/变体 | 同上；当前实际使用 | 当前可查阅旧卷，不等于收集姓名；保留。 |
| 43 | `assets/sprites/moonspace/ui/jade_register_volume_3.png`；480×270；RGB | 玉简警示 UI；全屏；同套底图/警示色 | 同上；当前实际使用 | “勿留姓名”是文案内容，不应引导继续制作姓名输入资源；保留。 |
| 44 | `assets/sprites/moonspace/wugang_chop_large.png`；304×368；RGBA 透明；4×4，每帧 76×92 | 吴刚；三分之四/侧面伐桂；高细节异化角色 | `entities/wugang.py:84-99`；世界 1:1，水平翻转；当前主路径，碰撞仍为 16×24 | 与头像/污染 CG 是同一强壮异化人物，但相对来使和庭院比例偏小；微调。 |
| 45 | `assets/sprites/moonspace/wugang_chop.png`；128×32；RGBA 透明；4 帧 32×32 | **已清理：** 吴刚旧小图；俯视；粗糙旧像素 | 无当前运行时引用；文件已按用户确认删除，大图缺失时使用程序绘制回退 | 与 #44 不是同一分辨率版本，不能作为视觉批准样本；不再作为资源或视觉依据。 |
| 46 | `assets/sprites/moonspace/yutu_pounding_large.png`；256×312；RGBA 透明；4×4，每帧 64×78 | 玉兔；蹲伏侧面；高细节异化类人兔妖 | `entities/yutu.py:60-75`；世界 1:1，当前主路径，碰撞仍为 16×24 | 与头像/玉兔 BE 的长耳、红眼、灰白身体相符；旧 #32 独立捣药台已移除；当前帧内本体与药臼/杵可分辨，独立图层仍为可选精修。 |
| 47 | `assets/sprites/moonspace/yutu_pounding.png`；96×24；RGBA 透明；4 帧 24×24 | **已清理：** 玉兔旧小图；俯视；粗糙旧像素 | 无当前运行时引用；文件已按用户确认删除，大图缺失时使用程序化本体回退 | 只保留动物剪影，无法承担当前类人兔妖设定；不再作为资源或视觉依据。 |

## 4. 重点重复关系与运行时映射

### 4.1 三组大图与程序化缺图回退

它们不是“同一图的高清/低清导出”，而是三套不同美术决策：

| 角色 | 主路径 | 每帧运行尺寸 | 缺图回退 | 关系结论 |
|---|---|---:|---|---|
| 来使 | `player_envoy_large.png` | 42×62 | 程序化玩家帧 | 大图保留深蓝长袍/暗金腰线；旧 16×24 小图已清理 |
| 吴刚 | `wugang_chop_large.png` | 76×92 | 程序化吴刚帧 | 大图保留高细节异化肌肉/斧头；旧 32×32 小图已清理 |
| 玉兔 | `yutu_pounding_large.png` / 透明分层图集 | 64×78 | 程序化本体与杵层 | 正常使用透明本体/杵覆盖层；旧 24×24 小图已清理 |

代码碰撞仍以 16×24 为主角/NPC 基准，而大图实际可见高度分别是 62、92、78 像素。这样做可以保留玩法碰撞，但不能在视觉设计上继续假设“角色都是 16×24”。

### 4.2 嫦娥透明版与绿幕版

`chang_e_16frames.png` 与 `chang_e_16frames_transparent.png` 都是 1254×1254、4×4 的 16 帧表，主体内容近似；区别是前者是 RGB 绿色背景，后者为 RGBA，alpha=0 区域约 70.9%，没有绿幕残留。当前代码明确使用透明版，绿幕版只应留在历史源/废弃候选区，不能继续制作围绕绿幕的资源。

### 4.3 三张独立头像与四列头像表

`chang_e_dialog.png`、`wugang_dialog.png`、`yutu_dialog.png` 各自是 1254×1254 的 2×2 头像变体表，分别包含同一角色的表情/异常状态；`dialog_portraits_large.png` 是 1672×941 的四列运行时表，第一至第四列依次为来使、嫦娥、吴刚、玉兔。它们不是字节重复，也不是当前代码会自动互换的 fallback：

- 当前对话框只裁剪四列表；
- 独立头像表可以作为未来“正常/异常/污染”表情库；
- 在用户批准复命分镜之前，不应同时把两套头像都当作正式运行时资源。

### 4.4 庭院背景和宫门状态

- `courtyard_bg.png`（480×270）与 `courtyard_bg_large.png`（960×540）是旧庭院背景对；当前正常主循环不调用 `TileMap.draw()`。
- `courtyard_expanded_closed/open.png`（960×640）是新的完整庭院状态对，包含北侧广寒宫门和南侧出口，当前由 `PalaceWall` 实际绘制。
- `courtyard_gate_closed/open.png`（1672×941）是正面宫门参考/用户参考保留文件，不是当前庭院状态图。
- 因此旧审查页把三组庭院图并列为“当前背景”是不准确的；当前运行时事实只有 expanded 状态对。

### 4.5 月池、研钵与宫墙

- `moon_pool_large.png` 是当前 144×144 圆形正式资源；`moon_pool.png` 是 64×40 的旧矩形 fallback，不能作为共同造型基准。
- `yutu_pounding_large.png` 帧内已经包含玉兔、药臼和药杵；用户已确认移除独立 `pound_table.png`。当前只保留 `PoundTable` 的原碰撞锚点，`draw()` 为空，不再绘制重复道具。
- `palace_wall_bg.png` 是 480×80 的旧窄宫墙；当前真正可见的是 960×640 expanded 全图，二者不应混称为同一宫门。

### 4.6 三张未跟踪玉简 UI

`assets/sprites/moonspace/ui/jade_register_volume_1/2/3.png` 在 Git 状态中仍显示为未跟踪目录，但 `EnvoyRegister.BACKGROUNDS` 已经直接加载它们。它们是当前运行时事实，不是“可能未接入的候选”。本阶段只记录这一事实，不替它们改名、移动或补姓名输入资源。

## 5. 当前最严重的十个视觉不一致

1. **高细节绘景、精细像素化角色和粗糙旧像素 fallback 并存。** 正常路径与缺失资源路径会出现完全不同的角色年龄、体型和轮廓，不能继续把 fallback 当成同一套正式美术。
2. **大图角色的可见尺寸远大于 16×24 碰撞基准。** 来使 42×62、吴刚 76×92、玉兔 64×78，在 480×270 逻辑画布里会改变玩家对“角色比例”的判断；当前代码功能正常，但视觉基准未写清。
3. **玉兔/药臼重复问题已按用户反馈收敛。** 旧 `pound_table.png` 位图已删除，场景保留碰撞锚点但不再绘制重复道具；当前玉兔大图内的本体与药臼/杵已能分辨，独立图层仍是可选精修。
4. **玉兔形态已按批准基线收敛。** 大图/头像/CG统一采用异化类人兔妖；旧小图接近动物剪影，现已清理，缺图时由程序化回退接管。
5. **嫦娥世界动画比例已收敛。** 当前透明 16 帧按 100×100 绘制，实际 Alpha 高度约为来使 1.5～1.6 倍；不再使用原先接近 2 倍的运行时比例。
6. **广寒宫俯视地图与正面王座/复命 CG 尚未完成空间锚点互译。** 帷幕、王座台阶、灯具和中央地面纹样能对应，但 `guanghan_hall.png` 未进运行时，`report_staging.png` 也只作为共享单图。
7. **月池的游戏形状与 CG 形状不同。** 当前是可碰撞的圆形 144×144 水面，污染 CG 是大块暗水/倒影地面；若不决定共同轮廓，玩家会把两个空间当成不同地点。
8. **宫门存在三代视觉来源。** 当前 expanded 庭院两态、未接入的正面 gate 参考、旧窄 `palace_wall_bg` 同时存在，旧审查页还把它们并列展示，容易误报正式资源。
9. **当前内殿运行时缺少旧文档声称的吴刚/玉兔站位。** staging CG 有四人，内殿实际绘制只有嫦娥、来使、登记台；复命七个镜头不能假设两名职司角色已经可用作实时前景。
10. **普通三次违规没有专属身份败露 CG，开场中段还由程序色条承载屏幕崩坏。** 主线五个 ending ID 已有单张图，但普通死亡和开场关键镜头的视觉完成度不齐，影响叙事层级。

## 6. 两套视觉方向比较与推荐

| 维度 | A：全面统一为精细像素恐怖 | B：游戏场景精细像素，CG 电影绘景但共享设定/锚点 |
|---|---|---|
| 制作成本 | 高：需把现有高细节 CG、头像、场景和角色统一降到同一像素密度，并重做多个源图 | 中：保留现有 CG/头像的暗色绘景表现，只修正游戏内角色、fallback、道具和锚点 |
| 与现有资产兼容度 | 低～中；大约 20～30 个视觉单元要重新像素化或重绘 | 高；32 张正常运行资源中约半数可以继续作为基准，现有 6 张 CG 可保留为最终帧 |
| 重制数量 | 高：角色四套、庭院/内殿、头像、CG 都要统一 | 中：先处理大/小角色体系、月桂、玉兔药台、宫门/月池锚点和缺失镜头 |
| 角色一致性 | 游戏内外最容易统一，但需要重新制作全部细节 | 依赖四名角色设定表和共享色板；做到后能同时保留游戏读图和 CG 细节 |
| CG 表现上限 | 中；像素化可读性高，但正面王座、池面反射和人物近景层次受限 | 高；可继续使用电影构图、反射、根系和环境纵深，只要求角色服装/地标不漂移 |
| 运行时清晰度 | 高；所有素材按 2 倍整数显示，边缘统一 | 高；游戏内仍按 480×270 和 2 倍整数显示，CG 只在播放时平滑缩放 |
| 风险 | 旧 CG 资产价值被大量丢弃，周期长 | 若没有 anchor sheet，CG 与游戏仍会出现“像另一个世界”的问题 |
| 结论 | 不作为当前阶段推荐 | **推荐**：成本、兼容度和表现上限平衡最好 |

推荐 B 的具体规则：游戏内统一逻辑像素密度、深蓝/冷白/暗红色板、1～2 像素冷色描边和明确可交互轮廓；CG 可以保留高精度绘景，但必须从同一角色设定、建筑中轴、帷幕/灯具、月池反射边界和祭坛圆环取锚点。当前阶段只完成选择依据，不生成高精度最终 CG。

## 7. 四名主要角色一致性结论

| 角色 | 当前跨资源关系 | 高度/体型与面部 | 发型/服装/标志道具 | 正常→异常规则 | 阶段结论 |
|---|---|---|---|---|---|
| 凌霄来使 | `player_envoy_large`、`dialog_portraits_large` 第一列、`report_staging`、HE/三张污染 CG、`candidate_player_envoy_cg_aligned.png` | 旧大图曾是戴冠帽/蓄须的成年男性；现正式大图已统一为年轻清瘦、无胡须、黑发髻男性；旧小图已清理 | 黑发髻、深靛交领长袍、暗金衣缘/腰线；记录册/来使身份是标志道具 | 正常始终保持同一来使剪影；污染只改变环境/身体异常，不另换基础身份 | 用户已确认 B01 主角候选；已用 imagegen 定向修复动作行、去色键、压制为 42×62 帧并接入正式大图，其他角色/CG仍按各自审批闸门处理 |
| 吴刚 | `wugang_chop_large`、`wugang_dialog`/四列头像、`report_staging`、`be_wugang`/`be_double` | 大图和头像都是强壮、灰肤、异化肌理的人；CG 中体型更接近巨型囚徒；旧小图已清理 | 长发束、暗红腰带、伐桂大斧；斧头角度和树伤是识别点 | 正常循环伐桂、灰暗皮肤；月桂流血时停斧；污染反馈用木色/反射/根系归档，不把吴刚变成普通恶鬼 | 大图/头像/CG 可认作同一人物；缺图时使用程序绘制回退，视觉批准以大图为准 |
| 玉兔 | `yutu_pounding_large`、透明本体/杵覆盖层、`yutu_dialog`/四列头像、`report_staging`、`be_yutu`/`be_double` | 大图与 CG 是苍白灰白、红眼、长耳、蹲伏的类人兔妖；旧小图已清理 | 长耳、红眼、红黑腰布、药臼和杵；旧独立 `pound_table` 已移除，当前帧内空间分离可读 | 正常是低头捣药、避视；污染是药雾进入身体/倒影，耳朵、眼色、杵声发生异常；不改成可爱兔子或普通人女性 | 用户已批准“异化类人兔妖”；透明分层已接入，缺图时使用程序化本体/杵层回退 |
| 嫦娥 | 透明 16 帧、旧绿幕 16 帧、四列头像、独立变体头像、`report_staging`、`be_wait` | 透明世界图按 100×100 绘制；头像/CG 是同一面纱、发饰、蓝灰衣裙；当前可见高度约为来使 1.5～1.6 倍 | 黑发高髻、银色发饰、面纱、冷白/靛蓝宽袖；帷幕和王座是她的场景道具 | 正常：静止、遮脸、收手、冷白光；异常/候宫：眼神/面纱/符纸/根影增加，不应突然换服装或年龄 | 用户已批准比例基线；旧绿幕版继续不接入 |

### 玉兔推荐 canonical

采用“**异化类人兔妖**”而不是“普通兔子”或“兔耳女性”：保留大图/头像/CG已经确立的长耳、红眼、灰白肌肉和低位蹲伏；正常状态只做低头捣药和避视，污染状态通过红眼、药雾、耳部错位和倒影变化表达。药臼是职司地标，可以保留在角色帧或独立道具中，但不能两者都以同样清晰度承担主体。

## 8. 九个关键场景视觉锚点

| 场景 | 世界视角 / 主光源 / 地面 | 建筑与交互轮廓 | CG 必须共享的锚点 | 当前保留资产 | 需要重制或批准 |
|---|---|---|---|---|---|
| 月谷祭坛 | 俯视；上方冷月、边缘少量红烛；深蓝石砖 | `home_tutorial_bg` 底部中央圆形祭坛，`altar_rect=(402,436,156,72)`；交互提示使用圆环/月印 | 祭坛圆环、中央月印、南北台阶和冷白反光；HE 第一镜头必须从这里启动 | `home_tutorial_bg.png`、`home_tutorial_bg_open.png` | 保留母版；需要 HE 启动/归返独立前景，避免只播放地球远景 |
| 月宫庭院 | 俯视；中央/上方冷月，侧边灯笼微红；深色石板 | 960×640 全图；北侧中央宫门、南侧中央出口、中央月池、左侧月桂、右侧玉兔区 | 宫门中轴、石板纹样、灯笼和月池反光边界；污染 CG 的池面必须可被识别为这里 | `courtyard_expanded_closed/open.png`、`moon_pool_large.png`、`laurel_tree.png` | 月池/宫门共同造型需批准；月桂需要重制以对齐根系风格 |
| 庭院南门 | 俯视；背向宫墙的冷白门槛光；石板 | `courtyard_south_exit_rect=(420,380,120,40)`；污染状态整段南墙封闭，不能回月谷 | HE 离院镜头共享南门门槛、两侧墙根和灯具；污染线不能把南门误作出口 | expanded 庭院两态、代码碰撞/交互 | 只做 CG 分镜和门槛前景，不改现有碰撞 |
| 广寒宫门 | 俯视；北侧门缝/宫墙冷光，开门态局部暗红 | `PalaceWall.ENTRY_RECT=(442,158,76,34)`；门状态由检查完成切换 | 宽屋檐、中央门洞、红光只在开门态出现；CG 中的入口要回指这个中轴 | expanded closed/open | 统一庭院门与 CG 门的轮廓；用户批准后再做第三阶段门前景 |
| 月池 | 俯视圆形水面；冷白倒影，异常时红眼/暗红水痕 | **运行时中心 `(480,300)`（`core/game.py:137`），**视觉 144×144，碰撞 112×112，倒影区扩大 56；静止面对才触发 | 水面形状、靠岸位置、倒影方向、暗色水纹必须与 `be_wugang/yutu/double` 对得上 | `moon_pool_large.png`、实时倒影代码、`broken_jade_slip.png` | 当前圆池 vs CG 大水面二选一锚点；用户批准；不得引用类默认 `(480,360)` |
| 吴刚/月桂区域 | 俯视；月光从上方，树伤/斧刃偏冷白，异常时暗红 | 月桂在左上 `(72,196)`，吴刚约 `(248,320)`；接近流血窗口才能交互 | 斧、树伤、根系、人脸纹理必须来自同一树体；污染 CG 的根系应能回指这里 | `laurel_tree.png`、`wugang_chop_large.png` | 月桂主体需重制；吴刚大图只做比例/描边校准 |
| 玉兔/药臼区域 | 俯视；冷月边光，药雾灰白/红眼 | 玉兔约 `(700,300)`，原药台碰撞锚点约 `(740,302)`；从背后/侧后交互，正面为违规区 | 长耳、杵声、独立药臼轮廓和红眼；BE 中池面药雾要能回指药臼 | `yutu_pounding_large.png`；旧 `pound_table.png` 已移除，碰撞锚点保留 | 视觉上由玉兔大图承载药臼/杵；正式分离方案仍需用户确认 |
| 广寒宫内殿 | 俯视；南北中轴冷光，灯具冷蓝；黑色反光砖 | 960×720；北侧帷幕/台阶，南侧门楼，中央地面纹样，登记台 `160,300,180×96` | 帷幕褶线、四组灯具、中央纹样、南门屋檐；正面 CG 需要给出可辨认对应 | `guanghan_hall_curtain.png`、`registration_desk.png`、透明嫦娥帧 | 当前实际运行只有嫦娥/来使/登记台；复命角色层和 CG 分层需补设计 |
| 王座与复命区 | 正面/三分之四；王座冷白边光、帷幕靛蓝、灯具对称 | `guanghan_hall.png` 是正面王座母版；`report_staging` 是侧向复命构图；对话区字幕底部安全 | 王座中轴、帷幕、灯具、地面中央纹样、嫦娥面纱；每个污染分支必须有真实前景差异 | `guanghan_hall.png`（CG候选）、`report_staging.png`、六张结局/复命图 | 需要 CG 分层和七个复命镜头，不把正面图接进可行走地图 |

## 9. CG 分镜生产清单（只设计，不制作最终成图）

### 9.1 统一制作规则

- 逻辑输出先按 480×270 设计；最终播放仍可保留现有 1672×941 源图的平滑缩放路线。
- 字幕安全区统一为底部 36～42 px；角色脸、池面倒影、王座中心和开场电脑进度条不得落入该区。
- 共享背景可以复用，但同一张图只能承担一次“没有真实视觉变化”的镜头；后续复用必须有明确前景、光源、角色位置或污染层变化。
- `ending_id` 只使用第一阶段固定的五个正式 ID。普通三次违规暂记为 `ending_id=none / death_state=violation_3`，建议文件名 `be_identity_exposed_laurel_feed`，不在用户批准前擅自新增正式 ID。

### 9.2 开场（当前 15 秒节拍的正式化方向）

| 镜头 | 状态 / ending_id | 构图与锚点 | 角色/资源 | 时长 / 共享背景 | 字幕安全区 | 动效与声音 | 优先级 |
|---|---|---|---|---:|---|---|---|
| O1 | `opening` / none | 现实房间背面中景；电脑、下载箭头、窗外血月同框 | `opening_cg_room.png` 保留；电脑进度前景需独立层 | 2.2s / 开场母版 | 底部 | 低频电脑风扇、进度条停顿声 | 高 |
| O2 | `opening` / none | 电脑屏幕特写；进度条停在最后一格，下载箭头反光 | 新屏幕特写；不重复 O1 全景 | 1.0s / 可共享房间墙面 | 底部 | 鼠标/硬盘声突然断掉 | 高 |
| O3 | `opening` / none | 主角肩后转向窗户；窗框成为后续月宫门框的形状伏笔 | 主角背影母版；窗框前景需独立 | 1.8s / 房间母版可共享 | 底部 | 椅子摩擦、无风但帘子动 | 中 |
| O4 | `opening` / none | 云层先裂出一条冷红缝，不直接满屏血月 | `opening_cg_blood_moon.png` 作为底；云层遮罩独立 | 1.6s / 血月底图 | 底部 | 云层低频轰鸣、单次心跳 | 高 |
| O5 | `opening` / none | 血月完整显现，月面像睁眼；窗口几何仍可辨 | 血月底图；月面眼裂/窗框 foreground | 1.8s / O4 可共享但需变化 | 底部 | 红光增强、远处金属摩擦 | 中 |
| O6 | `opening` / none | 月光从窗沿切入电脑和主角，现实桌面与来使深蓝服装颜色相连 | `opening_cg_moonlight.png` 保留；光束层 | 2.0s / 房间母版 | 底部 | 电流、布料吸光、呼吸声 | 高 |
| O7 | `opening` / none | 电脑屏幕反射出不属于房间的月宫门/眼；替换当前程序色条 | 新正式屏幕崩坏构图；不要使用 `_draw_screen_distortion()` 色条 | 1.4s / 可共享电视框 | 底部 | 数字噪声、反向人声、短促“找到你了”前奏 | 高 |
| O8 | `opening` / none | 白光/红光吞没房间，主角剪影被拉向屏幕，最终落入黑场 | `opening_cg_blackout.png` 保留；主角/门缝前景需独立 | 1.2s / 黑场底图 | 底部 | 低频吸入声、瞬时静音 | 高 |

开场当前问题：`OpeningCG` 在 0～6 秒两段都加载 `opening_cg_room.png`，12.6～14.0 秒由程序画色条，不能把 4 张现有开场 PNG 报成 8 个已完成镜头。O1/O4/O6/O8 可保留为母版，O2/O3/O5/O7 需第三阶段独立前景或新裁切。

### 9.3 广寒宫复命（七个镜头）

| 镜头 | 状态 / ending_id | 构图与锚点 | 角色/资源 | 时长 / 共享背景 | 字幕安全区 | 动效与声音 | 优先级 |
|---|---|---|---|---:|---|---|---|
| R1 | `report_enter` / none | 来使从南门进入中轴，先看到帷幕和四灯，停在复命区 | 来使大图/独立复命前景；`report_staging.png` 可作一次性建立镜头 | 2.8s / 当前 staging 可保留 | 底部 | 脚步、衣摆、殿内混响 | 高 |
| R2 | `report_receive` / none | 嫦娥从帷幕后伸手或以玉简光接记录，避免“只换字幕” | 嫦娥透明帧/头像、记录前景；王座/帷幕锚点 | 2.2s / R1 共享远景但角色位置变化 | 底部 | 玉简轻响、布帘摩擦 | 高 |
| R3 | `report_clean` / none | 清白反馈：吴刚斧声、玉兔杵声以两侧剪影/声纹回到画面，来使仍在中轴 | 来使、两侧职司剪影或声纹层；不假设当前内殿已有 NPC | 2.4s / R1 底图 | 底部 | 左右声道斧/杵回响，冷白灯亮 | 高 |
| R4 | `report_wugang` / none | 伐桂污染反馈：记录边缘木色渗出，来使倒影短暂出现斧影 | 来使、木色污染层、斧/树根前景；`be_wugang` 仅作最终帧 | 2.4s / R1 底图 | 底部 | 木裂、单次斧响、低沉池水声 | 高 |
| R5 | `report_yutu` / none | 玉兔污染反馈：药雾落入来使影子，耳/杵轮廓在地面反射中出现 | 来使、药雾、长耳倒影；`be_yutu` 作最终帧参考 | 2.4s / R1 底图 | 底部 | 杵声倒放、药瓶气泡、耳鸣 | 高 |
| R6 | `report_double` / none | 双污染：斧纹与药雾在中央地面纹样叠合，嫦娥不再称“来使” | 来使、根系/木色/药雾三层；`be_double` 作最终帧参考 | 2.6s / R1 底图 | 底部 | 斧声与杵声不同步叠加，根系摩擦 | 高 |
| R7 | `report_wait` / none | 清白线的“候月”诱导：王座/帷幕灯具亮度不变，出口反而变远 | 嫦娥、来使、南门远景；`be_wait_trap` 作后续归档参考 | 2.4s / R1 底图但光源/门距变化 | 底部 | 倒计时无数字，只用灯具间隔和远钟暗示 | 高 |

### 9.4 HE：`he_return_earth`（三镜头）

| 镜头 | 构图目的 | 角色/锚点 | 时长 / 共享背景 | 独立资源与动效 | 字幕/声音 | 优先级 |
|---|---|---|---:|---|---|---|
| H1 `altar_start` | 月谷祭坛启动合法归路；不是逃跑，是记录归档后门印熄灭 | 来使、祭坛圆环、月印；共享 `home_tutorial_bg_open` 锚点 | 2.5s / 祭坛母版 | 记录放回石面、月印逐一熄灭、冷白圆环扩张 | 底部；石鸣/风声 | 高 |
| H2 `moon_gate_exit` | 经过南门/月光通道，明确离开月宫 | 来使背影、庭院南门、`courtyard_south_exit_rect` 地标 | 2.5s / expanded 庭院 | 门槛月光、宫墙在身后合拢、脚步远去 | 底部；门轴/风声 | 高 |
| H3 `earth_arrival` | 真正抵达地球；不能继续站在月面看地球 | 现实房间、电脑、桌面和主角落地姿态；可借 `opening_cg_room` 母版但必须新构图 | 3.0s / 房间母版但不复用 O1 全景 | 电脑屏幕回到桌面、窗外无血月、主角手/呼吸恢复 | 底部；现实房间底噪、电脑待机声 | 高 |

### 9.5 四个专属 BE（每个三镜头）

| 结局 | 镜头 1：异常被发现 | 镜头 2：身份/身体变化 | 镜头 3：最终归档帧 | 共享锚点 / 时长 / 音效 | 优先级 |
|---|---|---|---|---|---|
| `be_wugang` | 月池倒影先显示斧刃和树皮，来使仍保持原衣 | 手指/衣袖出现木纹，斧声代替对话，池边宫门倒影弯曲 | 现有 `be_wugang_pollution.png`：新伐桂人被月桂收下 | 月池圆/水面、深蓝衣、庭院门；2.0s/2.4s/3.0s；水声→木裂→斧循环 | 高 |
| `be_yutu` | 月池倒影先出现长耳、红眼和药杵，身体尚未变形 | 药雾进入腕骨/喉部，耳朵与杵声不同步，药臼成为身体边界 | 现有 `be_yutu_pollution.png`：新捣药人归档 | 月池、水纹、药臼、红眼；2.0s/2.4s/3.0s；药瓶气泡→杵声→耳鸣 | 高 |
| `be_double` | 两份倒影在池面互相覆盖，记录无法归档到单一职司 | 一侧木纹、一侧兔耳/药雾，根系从二者之间生长 | 现有 `be_double_pollution.png`：月桂根系收下多余记录 | 月池、宫门、月桂根系；2.2s/2.8s/3.0s；双声道错位→根系摩擦 | 高 |
| `be_change` | 候月倒计时无数字归零，灯具仍亮，来使身后出现王座影 | 面部/服装被帷幕影替换，手势与嫦娥逐渐相同 | 现有 `be_wait_trap.png`：宫中留下一个等待者 | 帷幕、王座、灯具、地面纹样；2.0s/2.6s/3.0s；远钟→静音→帷幕声 | 中 |

### 9.6 普通三次违规死亡（专属分镜补齐）

当前状态：`violation_count=3` 进入既有死亡界面，暂无正式 ending ID 和专属 CG。建议美术命名 `be_identity_exposed_laurel_feed`，但不在本阶段修改状态机。

| 镜头 | 剧情状态 | 构图目的 / 角色 / 锚点 | 时长 / 背景共享 | 独立前景、字幕安全区、动效与声音 | 优先级 |
|---|---|---|---:|---|---|
| D1 | `violation_count=3` | 规则痕迹第三次亮起；来使在庭院中，月桂/池面/玉兔正面视线按触发来源选择 | 1.8s / 庭院可共享 | 红色规则刻痕、角色回头；底部字幕；规则纸张撕裂声 | 高 |
| D2 | `ending_id=none`, `death_state=identity_exposed` | 月宫认出“没有来处的外来者”；根须从地面向鞋底延伸 | 2.4s / 庭院或月桂局部 | 根须前景必须独立；字幕底部；地面挤压、木头低鸣 | 高 |
| D3 | `ending_id=none`, `death_state=laurel_feed` | 不是吴刚/玉兔污染，而是被月桂回收；最终只留下树干人脸/空地 | 3.0s / 月桂局部或新终帧 | 黑屏前保留一帧身份轮廓；底部安全区；树内呼吸声后静音 | 高 |

## 10. 第三阶段依赖顺序与生产批次

### 批次 A：视觉基准

- **前置依赖**：本报告通过；不需要改代码或替换 PNG。
- **目标资源数量**：4 份角色设定板（来使、吴刚、玉兔、嫦娥）+ 1 份正常/异常规则板 + 4 份空间锚点板（庭院/宫门、月池/南门、广寒宫俯视/正面、月谷祭坛）+ 1 份全局像素/色板/描边规范，共 **10 份审查板**。
- **内容**：统一服装、身高级差、面部识别、道具、污染色、主光源、地面材质、字幕安全区。
- **验收截图**：480×270 逻辑画布的四角色对比板、2 倍显示截图、俯视/正面锚点对照图；必须看不到绿幕、旧小图与重复研钵造成的歧义。
- **用户批准点**：最终视觉方向、玉兔形态、嫦娥比例、月池和宫门共同造型。
- **停止条件**：上述五项未批准，不进入批次 B 的正式重制。

### 批次 B：游戏内粗糙资源与比例修正

- **前置依赖**：批次 A 批准；第一阶段冻结的碰撞和剧情状态不动。
- **目标资源数量**：约 **11 个图像单元**：嫦娥世界帧 1、玉兔/药台组合 1、月桂主体 1、玩家/吴刚/玉兔 fallback 3、宫门闭/开 2、月池 1、登记台比例校准 1、必要的交互提示前景 1。
- **优先顺序**：先解决玉兔与研钵重复、月桂造型、角色大图与碰撞框的视觉比例，再处理旧小图 fallback；只有需要时才统一宫门/月池正式资源，不动当前代码状态。
- **验收截图**：庭院关门/开门、中央月池正常/异常、吴刚流血窗口、玉兔背后交互、广寒宫南门入口、内殿登记台六类 480×270/960×540 截图；同时跑“主图缺失时 fallback”测试，确认 fallback 不被误标正式。
- **用户批准点**：玉兔/研钵取舍、月池轮廓、宫门轮廓、嫦娥的最终游戏内高度。
- **停止条件**：角色设定板与运行时截图不能同时通过时，不进入 CG 批量制作。

### 批次 C：复命与主线 CG

- **前置依赖**：批次 A、B 视觉批准；不改 ending ID，不把正面王座图接入可行走地图。
- **目标覆盖**：**33 个镜头设计**：开场 8、复命 7、HE 3、四个专属 BE 各 3（12）、普通违规死亡 3；图像生产时允许共享背景母版，但每个镜头必须有独立差异记录。
- **首批建议顺序**：R1～R7 复命 → H1～H3 HE → D1～D3 普通身份败露 → `be_wugang`/`be_yutu`/`be_double`/`be_change` 的三段扩展；理由是复命和普通死亡目前最缺镜头行为，且能直接验证五个固定 ending ID 的分支空间。
- **验收截图**：一张完整 storyboard contact sheet、每个 ending 的三帧对照、字幕安全区叠加版、`guanghan_hall_curtain` 与 `guanghan_hall` 的地标连线图。
- **用户批准点**：CG 覆盖范围、分镜镜头数、首批顺序、普通违规是否采用独立身份败露视觉。
- **停止条件**：若污染分支只改变字幕/色调而没有角色或空间变化，退回批次 C 继续设计。

### 批次 D：声音与最终润色

- **前置依赖**：批次 C 的镜头和角色状态全部批准；代码只在用户批准后接入。
- **目标数量**：33 个镜头字幕时序 + 至少 8 类环境/动作声（电脑、血月/红光、宫门、斧、杵、月池、根系、祭坛/地球房间）+ 4 类简单动效（推拉、闪烁、遮罩、分层位移）。
- **验收截图/录屏**：480×270 逻辑画面、960×540 默认窗口、开场 15 秒、复命 2.8 秒 staging、清白返回、四污染分支、普通三次违规各一条完整演示；字幕不压角色脸和池面核心。
- **用户批准点**：字幕时长、音效强度、简单动效上限、最终运行时视觉 QA。
- **停止条件**：视觉 QA 通过后才允许未来的 release 计划；本阶段不打包。

## 11. 进入最终美术生产前的批准清单

必须由用户明确批准后，才能把候选变成第三阶段正式生产任务：

- [x] 方向 B：游戏内精细像素化恐怖 + CG 电影绘景共享设定/地标；
- [x] 玉兔 canonical 形态为异化类人兔妖，污染状态不另换物种；
- [x] 嫦娥与来使的最终身高级差：游戏内透明帧按 100×100 绘制，实际可见高度约 1.5～1.6 倍；
- [x] 月池的运行时轮廓：当前圆形池、中心 `(480,300)`，污染只通过池内附加层扩散；CG 共同轮廓在本轮冻结；
- [x] 宫门的运行时共同轮廓：当前庭院 expanded 门体闭/开两态；CG 共同锚点在本轮冻结；
- [x] 旧 `pound_table.png` 与 `sign_board.png` 位图移除；碰撞锚点/兼容类保留，不改变玩法规则；
- [ ] 玉兔正式大图与独立药臼/杵的最终分离方案；
- [ ] 复命七镜头、HE 三镜头、四个专属 BE 各三镜头、普通违规三镜头的覆盖范围；
- [ ] 批次 C 首批顺序是否按“复命 → HE → 普通违规 → 四个污染 BE”执行；
- [ ] 普通三次违规是否新增专属美术分镜；正式 ending ID 是否继续保持现有五个不变。

## 12. 本阶段完成边界

本报告完成的是“美术资源对齐与生产清单”，不是最终美术生产完成。当前仍未做以下事项：

- 没有制作或批量生成最终 CG；
- 未做全量替换；已接入并验证 B01 主角、B02 嫦娥比例和 B06 月池污染附加层，其他正式大图/背景保持当前主路径；
- 当时没有删除其他旧小图、绿幕图、宫门参考或旧审查素材；后续用户确认后，三份角色旧小图与发现面孔备用图已在 13.7 清理；`pound_table.png` / `sign_board.png` 仍按此前确认状态处于删除状态；
- 没有修改剧情状态机、ending ID 或碰撞布局；
- 没有重新打包 `release/MoonSpace.exe`；
- 没有把未接入素材误报为正式运行时资源。

## 13. 第三阶段 Batch A：视觉基准闸门（已完成，用户已批准）

本批次只从当前运行时资源、运行时渲染和既有代码锚点制作基准板；基准板作为用户审批闸门，不直接冒充运行时资源。用户已明确“批准全部候选”，因此本报告以下 Batch C/D 接入记录均以该审批为依据；新增/修正位图均按已读取的 `imagegen` 技能流程完成并落入项目。

### 13.1 十张基准板

每张板均在图内写明：当前游戏依据、目标效果、保留元素、需要重做元素、480×270 原生占比、960×540 整数 2×显示效果。文件放在既有 `moonspace-asset-review/assets/candidates/contact-sheets/`，使用语义化文件名，不代表最终资源。

| 编号 | 基准板 | 当前运行时依据 | 主要待批准/重做点 |
|---:|---|---|---|
| 01 | `baseline-board-01-protagonist.png` | CG/头像 canonical + 已接入 `player_envoy_large.png`；碰撞 16×24；imagegen 身份母版作来源 | 以年轻无须、黑发髻、深靛交领长袍统一 CG 与游戏内身份；保持原站位/碰撞盒；正式 42×62 图集已接入并在两处真实场景复核。 |
| 02 | `baseline-board-02-chang-e.png` | `chang_e_16frames_transparent.png`，运行时帧缩至 100×100 | 游戏内可见高度收敛到主角约 1.5～1.6 倍；保留面纱、发饰、冷白/靛蓝光；旧绿幕表 `chang_e_16frames.png` 为 STALE。 |
| 03 | `baseline-board-03-wugang.png` | `wugang_chop_large.png` 76×92、`laurel_tree.png` 176×220 | 保留宽肩、斧、树伤和灰暗皮肤；重做树体/根系与 CG 的统一锚点，不改交互规则。 |
| 04 | `baseline-board-04-yutu-mortar.png` | `yutu_pounding_large.png` 64×78；旧独立药台位图已移除 | 玉兔正式为异化类人兔妖；明确本体与药臼、杵的分离关系，保持旧碰撞锚点但不再绘制重复台。 |
| 05 | `baseline-board-05-palace-architecture.png` | `courtyard_expanded_closed/open.png`、`guanghan_hall_curtain.png` | 庭院/内殿共享中轴、灯具、帷幕和台阶语言；旧 Gate 候选只作 STALE 问题证据。 |
| 06 | `baseline-board-06-moon-pool.png` | `core/game.py:137` 的 `MoonPool(480,300)`、`moon_pool_large.png` 144×144 | 固定当前运行中心与碰撞比例；污染作为附加层向外扩散；旧 `(480,360)` 与 `moon_pool.png` 不得作当前依据。 |
| 07 | `baseline-board-07-gate-laurel-props.png` | expanded 宫门开/闭、`laurel_tree.png`、玉简 UI；旧独立药台位图已移除 | 保留门状态切换、月桂、供桌/册籍的功能识别；统一遮挡顺序与中央门轮廓，药臼视觉回归玉兔正式方案。 |
| 08 | `baseline-board-08-moon-wilds.png` | `home_tutorial_bg*`、庭院、吴刚/玉兔大图和环境层 | 保留月面荒野、冷月石板、普通敌对/异化层次；不得把旧小图或纯色回退当成正式效果。 |
| 09 | `baseline-board-09-cg-language.png` | `report_staging.png`、四张 BE、`he_earth_return.png` | CG 为电影感绘制、16:9；HE 现有图只作“月面返程/遥望地球”过渡，必须另补真正 `earth_arrival`。 |
| 10 | `baseline-board-10-ui-safe-area.png` | 主菜单、开场/转场、对话/结局字幕与 DeathScreen | 保留底部字幕安全区和 480→960 等比显示；重做开场色条占位，避免标题、字幕裁切和纯色块。 |

### 13.2 Batch A 输出与审批边界

- 基准板联系表：`assets/candidates/contact-sheets/baseline-boards-contact-sheet.png`。
- 中文接入预览：`integration-preview-cn-runtime.png`（Batch B 资源）、`integration-preview-cn-cg.png`（33 镜槽位）及 `report-sequence-preview-cn.png`、`he-sequence-preview-cn.png`、`bad-endings-sequence-preview-cn.png`、`death-sequence-preview-cn.png`、`opening-sequence-preview-cn.png` 五张中文标注板。用户已批准全部候选；历史绿幕、旧 Gate/Pool 和纯色占位仍只作问题证据。
- 运行时截图证据均存放在既有 `moonspace-asset-review/assets/candidates/contact-sheets/`，本轮正式 CG 证据命名为 `runtime-cg-*`，共 **66 张**（33 镜 × 480×270/960×540）；另有完整内殿复命证据 `runtime-guanghan-report-sequence-r6-480/960.png`。本轮新增 Batch B 证据 12 张；连同此前主菜单、月谷、庭院、宫门、月池、开门离场和结局场景证据，`runtime-*.png` 共 **132 张**，尺寸为 66 张 480×270 + 66 张 960×540。
- 目录中原有的 4 张 `*_v9` 联系表继续保留作历史问题发现材料，均为 **stale**，不计入 10 张基准板或正式 CG 资源，也不作为正式画面依据。
- 本轮实际验证结果：`pytest -q` 为 **319 passed**；`git diff --check` 通过；全量 `assets/sprites` + `assets/tilesets` PNG 扫描 **81** 个（RGBA 30、RGB 51；Alpha 通道 30、含真实透明像素 19），尺寸/读取错误 **0**。绿幕检测只命中已标记为 **STALE** 的 `assets/sprites/moonspace/sheets/chang_e_16frames.png`（约 71.2% 色键绿）；透明版 `chang_e_16frames_transparent.png` 才是当前运行路径。三张纯色图 `placeholder_npc.png`、`placeholder_player.png`、`tilesets/moon_palace_floor.png` 均无代码运行时引用，继续标记为 stale，未进入正式画面。
- 33 张正式 CG 帧位于 `assets/sprites/moonspace/cg/`：32 张为 480×270、6 张兼容/既有高分辨率图为 1672×941；正式 CG 无绿幕、无纯色块、无读取错误，且每组序列的帧哈希均不重复。评审页本地链接 **126 个、错误 0**；`tools/cg_preview.html` 内嵌 JavaScript 解析通过，33 个正式 CG 文件字面量全部存在。
- 用户批准后已完成此前的 Batch C/D 接入；Batch B 已保留并验证 B01 主角、B03 吴刚、B04 玉兔、B05 建筑、B07 小道具和 B08 UI 的正式主路径。本轮新增 B02 嫦娥比例与 B06 月池污染附加层；旧 Gate/Pool、绿幕或小图 fallback 仍未升格。

### 13.3 本轮用户反馈落地（2026-08-07）

- 用户明确要求移除两张过于粗糙且已有替代物的位图：`assets/sprites/moonspace/pound_table.png`、`assets/sprites/moonspace/sign_board.png`，以及评审页中的对应副本；删除已验证，未删除碰撞/兼容类。
- `world/pound_table.py` 现在只保留原 16×16 碰撞锚点，`draw()` 为空；真实运行截图已确认玉兔大图自带药臼/杵且不再出现独立旧台。
- 用户指出主角与 CG 形象差异过大。已用 imagegen 生成并去除色键的 `assets/candidates/imagegen/candidate_player_envoy_cg_aligned.png`（1254×1254 RGBA、4×4 预览），其身份为年轻清瘦、无胡须、黑发髻、深靛长袍；B01 中文基准板和角色页已据此更新。
- 用户随后确认接入。已用 imagegen 对候选第三行动行做定向修复，去色键后以预乘 Alpha 方式压制为 `assets/sprites/moonspace/player_envoy_large.png`（168×248 RGBA、4×4、每帧 42×62）；没有改动站位、16×24 碰撞盒、剧情或计时规则。评审副本 `moonspace-asset-review/assets/player-envoy-large.png` 已同步。
- 已新增真实运行时证据：`runtime-player-cg-aligned-courtyard-480/960.png` 与 `runtime-player-cg-aligned-guanghan-480/960.png`；两处均由 `Game.draw()` 实际绘制，覆盖 480×270 逻辑画布与 960×540 整数 2×显示。

- 主角接入后重新用当前工作区资源取证并覆盖更新了既有 `runtime-main-menu`、`runtime-home-tutorial`、`runtime-courtyard-*`、`runtime-guanghan-report`、5 条 `runtime-ending-*`、`runtime-death-violation-3` 及 `runtime-opening-01..08` 的 480/960 图；这组 52 张图证明当前分支画面可被实际绘制，不代表 33 镜 CG 已完成或通过视觉验收。
- 为避免把现有过渡图误读为抵达结局，`assets/sprites/moonspace/cg/he_earth_return.png` 仍标注为 H1“月面返程/遥望地球”过渡镜头；`ui/ending_cg.py` 的 HE 末镜字幕已更新为“晨光落在地球的房间里，归路终于抵达”，不改变 `he_return_earth` ID、8 秒时长或分支逻辑。H2/H3 已正式接入，运行时证据为 `runtime-cg-ending-he_return_earth-01..03-480/960.png`。
- 用户批准 HE 候选后，H2/H3 已从 `candidate_he_depart_moon_palace.png` / `candidate_he_earth_arrival.png` 压制为语义化正式资源 `assets/sprites/moonspace/cg/he_02_depart_moon_palace.png` / `he_03_earth_arrival.png`；H3 是现实卧室与晨光窗口中的真正抵达画面，不再把 H1 当作终点。
- `ui/opening_cg.py` 的第 7 镜此前已移除红/青成排色条占位；本轮又将正式 O1～O8 逐镜接入，开场总时长 15 秒、原字幕分段、跳过输入和存档行为不变。正式资源为 `assets/sprites/moonspace/cg/opening_01_download_start.png` ～ `opening_08_blackout_crescent.png`，证据为 `runtime-cg-opening-01..08-480/960.png`。
- 普通违规 D1/D2/D3 已从候选三联落为 `assets/sprites/moonspace/cg/death_violation_01_reflection.png`、`death_violation_02_pool_spreads.png`、`death_violation_03_pool_pull.png`，接入 `DeathScreen.draw()` 的 1.5 秒淡入阶段；不创建新的正式结局 ID。证据为 `runtime-cg-death-violation-01..03-480/960.png`。
- 四个坏结局各三镜已落为语义化正式资源：`be_wugang_01..03`、`be_yutu_01..03`、`be_double_01..03`、`be_change_01..03`，并接入 `EndingCG.SHOT_ASSETS_BY_ENDING`；`be_laurel_mixed` 兼容键复用 `be_double` 三镜。五个固定正式 ID 未增加或改名。证据为 `runtime-cg-ending-{he_return_earth,be_wugang,be_yutu,be_double,be_change}-01..03-480/960.png`。
- 玉兔 BE 第 2 镜在 480×270 QA 中曾出现药臼边缘抢主体、根须与血丝纹理过密，以及“站在血月上却出现另一轮月亮”的设定错误；按用户已批准的身份基线再次用 imagegen 做低噪、无独立月体重制后替换为 `be_yutu_02_mortar_awakens.png`，现在长耳兔妖是明确焦点，药臼与杵独立位于右下，背景改为低处血色地表/大气辉光与湿地反射，未引入嫦娥、重复本体或色块占位。已同步刷新正式 33 镜联系表和该镜 480×270/960×540 真实运行截图。
- 复命 R1～R7 已落为 `assets/sprites/moonspace/cg/report_01_enter_hall.png`、`report_02_walk_forward.png`、`report_03_stop_before_chang_e.png`、`report_04_formal_bow.png`、`report_05_present_records.png`、`report_06_chang_e_receives_records.png`、`report_07_records_on_desk.png`；`Game._draw_report_staging()` 在原 2.8 秒时长内逐镜切换。证据为 `runtime-cg-report-01..07-480/960.png` 与完整内殿 `runtime-guanghan-report-sequence-r6-480/960.png`。
- 四个序列联系表已改为已批准/接入状态；`tools/cg_preview.html` 已改为读取正式 33 镜资源，支持 480、2×预览，不再引用失效的 `tmp/cg-preview-candidates` 路径。
- 正式 33 镜静态帧总览与中文标注联系表：`assets/candidates/contact-sheets/formal-cg-frame-qa.png`；该图只作视觉 QA 证据，不作为运行时资源。本轮按用户要求暂停 CG，不修改该组资源和接入代码。

### 13.4 本轮用户指令落地：暂停 CG，收敛 Batch B 运行时资源（2026-08-08）

- **CG 冻结：** 本轮不生成、不替换、不调整 CG 帧、分镜、结局 ID 或 CG 播放流程；已有 Batch C/D 结果只保留，不把它们作为本轮工作范围。
- **B02 嫦娥比例已接入：** `core/game.py` 使用 `CHANG_E_WORLD_FRAME_SIZE = (100, 100)` 绘制透明 16 帧图集，底部锚点仍为 `(480,184)`；实际运行画面中可见 Alpha 高度约为来使的 1.5～1.6 倍。证据为 `runtime-batch-b-chang-e-scale-480.png`、`runtime-batch-b-chang-e-scale-960.png`。
- **B06 月池污染层已接入：** `world/moon_pool.py` 增加独立 Alpha 污染扩散层，只在月池视觉内矩形绘制动态红色环线/径向痕迹；触发条件只读取 `pending_pool_ending`、`wugang_polluted`、`yutu_polluted`，不改 `(480,300)` 运行时中心、144×144 视觉尺寸、112×112 碰撞区、计时或结局状态。证据为 `runtime-batch-b-moon-pool-normal-480/960.png` 与 `runtime-batch-b-moon-pool-polluted-480/960.png`。
- **已复核的正式主路径：** B01 `player_envoy_large.png`、B03 `wugang_chop_large.png`、B04 `yutu_pounding_large.png`、B05 `courtyard_expanded_closed/open.png`、B07 `laurel_tree.png`/登记台/玉简、B08 UI 均在 `Game.draw()` 真实场景中可加载；宫门证据为 `runtime-batch-b-gate-closed-480/960.png`、`runtime-batch-b-gate-open-480/960.png`，登记台证据为 `runtime-batch-b-registration-desk-480/960.png`。
- **B04 当前边界：** 旧 `pound_table.png` 位图已移除，运行时不再额外绘制粗糙捣药台；玉兔正式 4×4 透明帧中保留本体与药臼/杵的可辨识空间关系，但暂未拆成独立运行时图层。该项不再有重复旧台问题，独立图层化仍列为后续可选精修，不影响当前碰撞锚点。
- **比例档位：** 上述证据同时覆盖 480×270 原生逻辑画布和 960×540 整数 2×窗口；没有引入绿色幕布、纯色块、不透明矩形透明替代或新的缺图回退。

### 13.5 当前已知风险

1. 广寒宫可行走地图仍只绘制嫦娥、来使和登记台；复命七镜使用电影感静态 CG 表达动作，不假设吴刚/玉兔已在内殿实时站位。
2. 旧 Gate/Pool 候选、绿幕图、三张纯色占位 PNG 和旧单图 CG 仍留在仓库供历史回溯；三份角色旧小图与发现面孔备用图已按 13.7 清理，代码主路径不会加载其余历史/兼容资源。
3. 正式 CG 帧为不透明 RGB 绘景，这是电影感背景的预期；像素角色/道具资源仍需继续保持真实 Alpha。全量扫描没有发现新的绿幕或纯色正式 CG。
4. `be_laurel_mixed` 是旧兼容键，视觉上复用 `be_double` 三镜；正式结局 ID 仍只有 `he_return_earth`、`be_wugang`、`be_yutu`、`be_double`、`be_change` 五个。
5. B04 目前是同一透明帧内的玉兔/药臼/杵组合，并非三个独立运行时图层；旧独立捣药台已删除且不再绘制，后续如需细粒度遮挡控制仍需另行拆层。
6. 本轮完成的是 B02 嫦娥比例和 B06 月池污染层的运行时接入与证据；B01、B03、B04、B05、B07、B08 以现有正式主路径复核为准，旧候选、绿幕以及月池/宫墙兼容 fallback 仍只作历史/兼容用途。

### 13.6 2026-08-10 收口复核（覆盖前述临时状态）

本节是当前工作区的最新验收结论；前面关于“复命 2.8 秒”“死亡 1.5 秒”“玉兔仍为合并图层”的临时记录不再代表当前实现。

- **复命 R1～R7：** `Game.REPORT_SHOT_DURATION = 1.2`、`Game.REPORT_STAGING_DURATION = 8.4`，七镜在 `0.0/1.2/2.4/3.6/4.8/6.0/7.2` 秒切换；`E` 可跳过，结束后才打开正式对话，缺图时使用安全回退，不改变剧情、碰撞或存档计时。
- **死亡 D1～D3：** `DeathScreen` 固定为 D1 `0.0–1.2`、D2 `1.2–2.4`、D3 `2.4` 秒后持久在线；独立黑幕在 `2.4` 秒后开始并在约 `4.0` 秒达到上限；`R` 清空序列、计时、音效 token 并重新开始。三镜缺失时不会抛出资源异常。
- **玉兔与药臼：** 当前运行时路径为透明 `yutu_body_4x4.png`、透明 `yutu_pestle_overlay_4x4.png`、静态 `props/yutu_mortar.png`；缺少透明层时使用程序化回退，不再加载旧小图杵层。`PoundTable` 仍保留原 16×16 碰撞矩形和世界锚点（游戏中 `(740,302)`），绘制顺序为药臼后层 → 玉兔本体 → 手/杵层 → 药臼前层。代码不再引用旧 `pound_table.png`，也不重复绘制粗糙捣药台。
- **资源安全：** 正式 33 镜 CG 均可读取；全量 PNG 解码错误为 0，正式 CG 与本轮新增玉兔透明层均无绿幕。`sheets/chang_e_16frames.png` 仍是已标记为 STALE 的旧绿幕资源，未在未获确认的情况下删除。主角、吴刚、玉兔三份旧小图以及独立发现面孔备用图已按用户确认清理；月池与宫墙的兼容回退仍保留，不作为主路径视觉依据。
- **音频：** CG 音效通过现有 `AudioManager` 和事件生命周期管理；新 WAV 均为本地生成的低音量提示音，跳过、重启、结束都会停止 CG 一次性音效，环境音不被误停。
- **运行时证据：** 本轮新增/刷新 52 张真实 `Game.draw()` 证据，覆盖玉兔 4 种遮挡状态、复命 7 个边界、死亡 D1/D2/D3、开场首尾、5 个正式结局首尾，均有 480×270 与 960×540 两档，位于既有 `assets/candidates/contact-sheets/` 目录；另有 20 面板集中审查板 `runtime-closure-review-preview.png` 和带逐卡标注/放大查看/勾选清单的网页 `pages/runtime-closure-preview.html`。
- **自动化结果：** `uv run pytest -q`：**334 passed**；`git diff --check`：通过。没有重新打包、提交或推送。
- **删除确认边界：** 旧绿幕 `assets/sprites/moonspace/sheets/chang_e_16frames.png`、旧结局/复命 fallback（`cg/be_wugang_pollution.png`、`be_yutu_pollution.png`、`be_double_pollution.png`、`be_wait_trap.png`、`cg/report_staging.png`）和历史候选/副本仍保留，待后续单独确认；本次用户已确认的小精灵与发现面孔备用图不再属于待确认删除项。`pound_table.png`、`sign_board.png` 在本轮开始前已处于删除状态，未再次执行删除；`SignBoard` 仍有程序绘制回退。当前工作区保持 dirty，不能把未提交/未确认删除状态描述为已发布包。

### 13.7 2026-08-10 用户确认清理旧小精灵与发现面孔备用图

- 用户确认小精灵没有实际用途，并同意清理 `player_envoy.png`、`wugang_chop.png`、`yutu_pounding.png`；同时清理旧的 `transition_found_you_face.png` 以及审查页中的 `transition-found-you.png` 副本。
- `entities/player.py`、`entities/wugang.py`、`entities/yutu.py` 不再加载三份小图；主角、吴刚、玉兔在正式大图缺失时分别使用既有程序化安全回退，玉兔仍保持透明本体/杵覆盖层与静态药臼分层。
- `ui/scene_transition.py` 不再尝试加载独立发现面孔，监控 24 帧主路径和程序化发现回退保持不变；审查页已移除对应卡片，并保留 `scene-transition.png` 场景转场资源。
- 本节之后的状态以当前代码和资源为准；前文角色资源盘点中的 small/fallback 条目是历史审查快照，不代表清理后的当前路径。
