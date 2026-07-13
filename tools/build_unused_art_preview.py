"""Build a numbered HTML preview for unused or low-value art assets."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "unused_art_preview.html"

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".svg", ".ico"}
TEXT_EXTS = {".py", ".html", ".css", ".js", ".ts", ".tsx", ".json", ".md", ".txt", ".yml", ".yaml", ".toml", ".ps1", ".bat"}
SKIP_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", "build", "dist", "release"}

EXPLICIT_UNUSED = {
    "assets/sprites/placeholder_npc.png": ("正式资源 / 旧占位图", "当前 Python 代码、工具、测试都没有引用。", "中"),
    "assets/sprites/placeholder_player.png": ("正式资源 / 旧占位图", "当前 Python 代码、工具、测试都没有引用。", "中"),
    "assets/sprites/tiles/moon_tiles.png": ("正式资源 / 旧瓦片", "当前地图使用大背景或程序绘制，旧瓦片图没有文件名引用。", "中"),
    "assets/tilesets/moon_palace_floor.png": ("正式资源 / Godot 遗留", "只在旧设计文档里出现，当前 Python 运行时没有引用。", "中"),
    "assets/sprites/moonspace/courtyard_bg.png": ("正式资源 / 已被大图替代", "运行时加载 courtyard_bg_large.png；该小图只被生成/导入脚本提到。", "中"),
}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def all_images() -> list[Path]:
    images: list[Path] = []
    for base in (ROOT / "assets", ROOT / "tmp"):
        if base.exists():
            images.extend(p for p in base.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTS)
    return sorted(images, key=lambda p: rel(p).lower())


def text_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTS or path == OUT:
            continue
        if set(path.relative_to(ROOT).parts) & SKIP_DIRS:
            continue
        files.append(path)
    return files


def reference_index() -> dict[str, list[str]]:
    texts: list[tuple[str, str]] = []
    for path in text_files():
        try:
            texts.append((rel(path), path.read_text(encoding="utf-8", errors="ignore")))
        except OSError:
            pass

    refs: dict[str, list[str]] = {}
    for image in all_images():
        name = image.name
        refs[rel(image)] = [path for path, body in texts if name in body]
    return refs


def classify(path: Path, refs: list[str]) -> tuple[str, str, str] | None:
    path_rel = rel(path)
    name = path.name

    if path_rel in EXPLICIT_UNUSED:
        return EXPLICIT_UNUSED[path_rel]

    if path_rel.startswith("tmp/"):
        if "/imagegen-v4-large-assets/" in path_rel or "/imagegen-v3-preview/assets/" in path_rel:
            return ("tmp / 可再生成暂存图", "暂存替换资源，正式游戏加载 assets 下的版本；脚本可重新生成。", "低")
        if "/screenshots/" in path_rel or "/visual-check/" in path_rel or "/qa/" in path_rel:
            return ("tmp / 截图与视觉检查", "一次性验证截图，不参与运行时加载；保留价值主要是人工回看。", "低")
        return ("tmp / 临时候选与中间产物", "临时目录资源，不随正式构建加载；适合人工确认后清理。", "低")

    if path_rel.startswith("assets/source/imagegen/") and name.startswith("candidate_") and "confirmed" not in name and not refs:
        return ("源图 / 未引用候选", "文件名没有出现在代码、工具、测试或文档里，像是被后续候选替代的源图。", "中")

    return None


def records() -> list[dict[str, object]]:
    refs = reference_index()
    items: list[dict[str, object]] = []
    for path in all_images():
        path_rel = rel(path)
        item_refs = refs.get(path_rel, [])
        result = classify(path, item_refs)
        if result is None:
            continue
        category, reason, risk = result
        stat = path.stat()
        items.append(
            {
                "id": len(items) + 1,
                "path": path_rel,
                "src": "../" + path_rel,
                "category": category,
                "reason": reason,
                "risk": risk,
                "sizeKb": round(stat.st_size / 1024, 1),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                "refs": item_refs,
            }
        )
    return items


HTML_TEMPLATE = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MoonSpace 未用美术资源预览</title>
  <style>
    :root { color-scheme: dark; --bg:#111318; --panel:#1b1f28; --soft:#252c37; --line:#3a4352; --text:#eef1f6; --muted:#aeb7c5; --accent:#9fd3c7; --warn:#f3c677; }
    * { box-sizing: border-box; }
    body { margin:0; background:var(--bg); color:var(--text); font-family:"Microsoft YaHei","Segoe UI",sans-serif; }
    header { position:sticky; top:0; z-index:2; padding:18px 22px; border-bottom:1px solid var(--line); background:rgba(17,19,24,.94); backdrop-filter:blur(10px); }
    h1 { margin:0 0 10px; font-size:22px; letter-spacing:0; }
    .summary { display:flex; flex-wrap:wrap; gap:10px; color:var(--muted); font-size:13px; }
    .summary strong { color:var(--text); }
    .toolbar { display:grid; grid-template-columns:minmax(180px,1fr) auto auto; gap:10px; margin-top:14px; }
    input, select, button { min-height:36px; border:1px solid var(--line); border-radius:6px; background:var(--panel); color:var(--text); padding:8px 10px; font:inherit; }
    button { cursor:pointer; background:#26313b; }
    main { padding:18px 22px 36px; }
    .note { margin:0 0 16px; color:var(--muted); font-size:13px; line-height:1.65; }
    .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(240px,1fr)); gap:14px; }
    .card { overflow:hidden; border:1px solid var(--line); border-radius:8px; background:var(--panel); }
    .thumb { position:relative; display:grid; place-items:center; height:174px; background:#0b0d11; background-image:linear-gradient(45deg,#151922 25%,transparent 25%),linear-gradient(-45deg,#151922 25%,transparent 25%),linear-gradient(45deg,transparent 75%,#151922 75%),linear-gradient(-45deg,transparent 75%,#151922 75%); background-size:18px 18px; background-position:0 0,0 9px,9px -9px,-9px 0; }
    .thumb img { display:block; max-width:100%; max-height:100%; object-fit:contain; image-rendering:pixelated; }
    .num { position:absolute; left:8px; top:8px; min-width:48px; padding:4px 7px; border-radius:999px; background:rgba(6,8,12,.82); color:var(--accent); font-weight:700; font-size:12px; text-align:center; }
    .body { padding:12px; }
    .path { margin:0 0 8px; overflow-wrap:anywhere; font-family:Consolas,"Cascadia Mono",monospace; font-size:12px; line-height:1.45; color:#d9e2ee; }
    .meta { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:9px; font-size:12px; }
    .pill { padding:3px 7px; border:1px solid var(--line); border-radius:999px; color:var(--muted); background:var(--soft); }
    .risk { color:var(--warn); }
    .reason { margin:0; color:var(--muted); font-size:12px; line-height:1.55; }
    .refs { margin-top:8px; color:#8e98a8; font-size:11px; line-height:1.45; overflow-wrap:anywhere; }
    @media (max-width:720px) { .toolbar { grid-template-columns:1fr; } main, header { padding-left:14px; padding-right:14px; } }
  </style>
</head>
<body>
  <header>
    <h1>MoonSpace 未用 / 临时美术资源预览</h1>
    <div class="summary">
      <span>生成时间：<strong>__GENERATED__</strong></span>
      <span>候选数量：<strong id="visible-count">__COUNT__</strong> / __COUNT__</span>
      <span>候选体积：<strong>__MB__ MB</strong></span>
    </div>
    <div class="toolbar">
      <input id="search" type="search" placeholder="按编号、路径、分类搜索">
      <select id="category"><option value="">全部分类</option></select>
      <button id="copy">复制当前可见路径</button>
    </div>
  </header>
  <main>
    <p class="note">编号固定显示在缩略图左上角。清单不包含运行时正在加载的正式图片，也不包含测试明确要求保留的 confirmed 源图和原始 atlas。风险“低”通常是 tmp 截图/暂存物；风险“中”表示在 assets 下，删除前建议看一眼。</p>
    <section id="grid" class="grid"></section>
  </main>
  <script id="records" type="application/json">__DATA__</script>
  <script>
    const records = JSON.parse(document.getElementById("records").textContent);
    const grid = document.getElementById("grid");
    const search = document.getElementById("search");
    const category = document.getElementById("category");
    const count = document.getElementById("visible-count");
    const copyButton = document.getElementById("copy");
    for (const value of [...new Set(records.map(item => item.category))].sort()) {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = value;
      category.appendChild(option);
    }
    function itemNumber(id) { return "#" + String(id).padStart(3, "0"); }
    function escapeHtml(value) {
      return String(value).replace(/[&<>"']/g, char => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" }[char]));
    }
    function render() {
      const needle = search.value.trim().toLowerCase();
      const selectedCategory = category.value;
      grid.textContent = "";
      const visible = records.filter(item => {
        const haystack = `${itemNumber(item.id)} ${item.path} ${item.category} ${item.reason}`.toLowerCase();
        return (!needle || haystack.includes(needle)) && (!selectedCategory || item.category === selectedCategory);
      });
      count.textContent = visible.length;
      for (const item of visible) {
        const card = document.createElement("article");
        card.className = "card";
        const refs = item.refs.length ? `<div class="refs">文件名引用：${escapeHtml(item.refs.join("；"))}</div>` : "";
        card.innerHTML = `
          <div class="thumb"><span class="num">${itemNumber(item.id)}</span><a href="${item.src}" target="_blank" title="打开原图"><img loading="lazy" src="${item.src}" alt="${escapeHtml(item.path)}"></a></div>
          <div class="body">
            <p class="path">${escapeHtml(item.path)}</p>
            <div class="meta"><span class="pill">${escapeHtml(item.category)}</span><span class="pill risk">风险：${escapeHtml(item.risk)}</span><span class="pill">${item.sizeKb} KB</span><span class="pill">${escapeHtml(item.modified)}</span></div>
            <p class="reason">${escapeHtml(item.reason)}</p>${refs}
          </div>`;
        grid.appendChild(card);
      }
    }
    async function copyVisiblePaths() {
      const paths = [...grid.querySelectorAll(".path")].map(node => node.textContent).join("\\n");
      await navigator.clipboard.writeText(paths);
      copyButton.textContent = "已复制";
      setTimeout(() => copyButton.textContent = "复制当前可见路径", 1100);
    }
    search.addEventListener("input", render);
    category.addEventListener("change", render);
    copyButton.addEventListener("click", copyVisiblePaths);
    render();
  </script>
</body>
</html>
"""


def main() -> None:
    items = records()
    data = json.dumps(items, ensure_ascii=False)
    html = (
        HTML_TEMPLATE.replace("__GENERATED__", datetime.now().strftime("%Y-%m-%d %H:%M"))
        .replace("__COUNT__", str(len(items)))
        .replace("__MB__", f"{sum(float(item['sizeKb']) for item in items) / 1024:.2f}")
        .replace("__DATA__", data.replace("</", "<\\/"))
    )
    OUT.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} with {len(items)} candidates.")


if __name__ == "__main__":
    main()
