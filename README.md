# PromptFloater

桌面悬浮提示词快速复制工具。支持 Windows 和 macOS。

## 安装

### 1. 安装 Python 3.8+

- **Windows**: [python.org/downloads](https://www.python.org/downloads/) 下载安装，勾选 "Add Python to PATH"
- **macOS**: `brew install python3` 或从 python.org 下载

### 2. 启动

启动脚本会自动创建项目内 `.venv` 并安装依赖，不会污染系统 Python。

| 平台 | 方式 |
|------|------|
| **Windows** | 双击 `启动.bat` |
| **macOS** | 双击 `启动.command`（首次需右键 → 打开） |
| **命令行** | `.venv\Scripts\python.exe app.py`（Windows）或 `.venv/bin/python3 app.py`（macOS） |

## 依赖

| 包 | 用途 |
|---|------|
| `pywebview` | 桌面悬浮窗（Windows 用 Edge WebView2，macOS 用 WKWebView） |
| `pyperclip` | 跨平台剪贴板 |

## 使用

- **点击条目** → 复制到剪贴板
- **悬停条目** → 显示中文简介
- **搜索** → 输入关键词过滤
- **贴边** → 窗口缩成六边形球贴到屏幕右侧
- **固定** → 图钉锁定防止自动缩回
- **导出/导入** → JSON 格式备份

### Command Deck 快捷键

| 按键 | 操作 |
|---|---|
| `/` | 聚焦搜索 |
| `↑` / `↓` | 移动当前选择 |
| `Enter` | 复制当前选择 |
| `1`–`9` | 复制当前列表对应条目 |
| `N` | 新建提示词 |
| `E` | 编辑当前选择 |
| `F` | 收藏/取消收藏当前选择 |
| `Esc` | 关闭弹窗、清空搜索或退出输入状态 |

鼠标与键盘共享同一个选中项。导入、导出和分类管理位于底部状态栏的 `···` 工具菜单。

## 数据与日志

- `data/prompts.json` 是随程序分发的默认数据，仅在首次运行时迁移。
- Windows 用户数据：`%APPDATA%\PromptFloater`
- macOS 用户数据：`~/Library/Application Support/PromptFloater`
- 主数据：`prompts.json`；上一版备份：`prompts.json.bak`
- 日志：`logs/promptfloater.log`（滚动保留 3 份）

## 开发检查

```bash
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## 系统要求

- Windows 10+ 或 macOS 11+
- Python 3.8+
- 无需浏览器或额外运行时
