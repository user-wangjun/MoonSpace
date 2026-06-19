# MoonSpace 项目规则

## 开发环境
- 游戏引擎：Godot 4.x
- 脚本语言：GDScript
- 编辑器：Godot Editor（推荐）或 VS Code + godot-tools 插件
- 平台目标：Windows PC（可扩展 Web/HTML5）

## 代码规范
- 命名约定：snake_case（文件/变量/函数），PascalCase（类名/节点名）
- 节点命名：PascalCase（Player、WuGang、LaurelTree）
- 目录结构：
  - `scenes/` - .tscn 场景文件
  - `scripts/` - .gd 脚本文件（按功能分子目录）
  - `assets/` - 资源文件（精灵、瓦片、字体）
- 文件组织：每个场景文件对应一个同名脚本（场景名 = 脚本名）

## 像素风格规范
- 精灵大小：16×16 或 32×32
- 游戏分辨率：480×270（16:9）
- 瓦片大小：16×16
- 渲染模式：`texture_filter = Nearest`（硬像素边缘，不平滑）
- 渲染后端：mobile（`rendering_method = mobile`），像素游戏无需高端渲染

## 输入映射
- WASD / 方向键：移动
- Shift（保持）：跑步
- E / 空格：交互
- Tab：打开规则手册

## 分支管理
- 功能分支：`feature/<描述>`
- 修复分支：`fix/<描述>`
- 文档分支：`docs/<描述>`
- 主分支：`master`

## 测试
- 测试框架：GUT（Godot Unit Testing）
- 核心逻辑（规则引擎、状态管理）必须有单测
- TDD 循环：RED → GREEN → REFACTOR

## 提交流程
- 遵循 Conventional Commits 规范
- 格式：`<type>(<scope>): <description>`
- 类型：feat/fix/docs/chore/test/refactor
