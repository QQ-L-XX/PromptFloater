# PromptFloater

![PromptFloater command deck preview](docs/assets/promptfloater-hero.svg)

<p align="center">
  <a href="https://www.python.org/"><img alt="Python 3.8+" src="https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white"></a>
  <a href="https://pywebview.flowrl.com/"><img alt="pywebview" src="https://img.shields.io/badge/Desktop-pywebview-d6ff62?style=for-the-badge"></a>
  <img alt="Platform" src="https://img.shields.io/badge/Windows%20%7C%20macOS-ready-111111?style=for-the-badge">
  <img alt="Tests" src="https://img.shields.io/badge/tests-45%20passing-d6ff62?style=for-the-badge">
</p>

<p align="center">
  <strong>PromptFloater 是一个桌面悬浮式 Prompt 指挥台。</strong><br>
  把常用提示词、片段、命令和工作流放在一个轻量窗口里，用鼠标或键盘一秒复制。
</p>

---

## 为什么做它

写提示词最烦的不是“想不到”，而是那些每天都要重复复制、修改、找来找去的片段。PromptFloater 把这件事变成一个很快的小动作：

- 常驻桌面边缘，需要时滑出；
- 用 `/` 搜索，`↑`/`↓` 选择，`Enter` 复制；
- 用分类、收藏和快捷键管理高频提示词；
- 数据保存在本机，不依赖云端服务。

## 亮点

| 能力 | 说明 |
|---|---|
| Command Deck UI | 黑曜石风格桌面指挥台，低干扰、高密度、键盘友好 |
| 快速复制 | 点击、回车、数字键 `1`–`9` 都能复制当前条目 |
| 搜索过滤 | `/` 聚焦搜索，按标题、内容、分类快速定位 |
| 收藏与分类 | 支持收藏、分类管理、导入和导出 JSON |
| 贴边悬浮 | 窗口可缩成六边形小球贴在屏幕右侧 |
| 本地优先 | 用户数据写入系统应用数据目录，并保留 `.bak` 备份 |
| 稳健存储 | JSON Schema 校验、原子写入、损坏恢复、滚动日志 |

## 快速开始

### 1. 安装 Python

需要 Python 3.8 或更高版本。

- Windows：从 [python.org/downloads](https://www.python.org/downloads/) 安装，勾选 `Add Python to PATH`
- macOS：`brew install python3` 或从 python.org 安装

### 2. 启动

启动脚本会自动创建项目内 `.venv` 并安装依赖，不会污染系统 Python。

| 平台 | 启动方式 |
|---|---|
| Windows | 双击 `启动.bat` |
| macOS | 双击 `启动.command`（首次可能需要右键 → 打开） |
| 命令行 | Windows: `.venv\Scripts\python.exe app.py` |
| 命令行 | macOS/Linux: `.venv/bin/python3 app.py` |

## 快捷键

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

鼠标与键盘共享同一个选中项。复制成功时，对应条目会短暂显示 `COPIED ✓`。

## 项目结构

```text
PromptFloater
├─ app.py                    # pywebview 桌面入口
├─ demo.html                 # 桌面窗口结构与样式
├─ renderer/app.js           # 前端交互、搜索、快捷键、复制反馈
├─ promptfloater/
│  ├─ api.py                 # 前后端桥接 API
│  ├─ paths.py               # 跨平台用户数据目录
│  ├─ schema.py              # Prompt 数据校验
│  ├─ storage.py             # 原子写入、备份、恢复
│  └─ logging_setup.py       # 滚动日志
├─ data/prompts.json         # 首次运行默认提示词数据
├─ tests/                    # 单元测试与 UI 契约测试
└─ docs/assets/              # GitHub 仓库页视觉素材
```

## 数据与日志

`data/prompts.json` 只作为首次运行的默认数据。真实用户数据会放到系统应用数据目录：

| 系统 | 用户数据目录 |
|---|---|
| Windows | `%APPDATA%\PromptFloater` |
| macOS | `~/Library/Application Support/PromptFloater` |
| Linux | `${XDG_DATA_HOME:-~/.local/share}/PromptFloater` |

主要文件：

- `prompts.json`：当前提示词库；
- `prompts.json.bak`：上一版备份；
- `logs/promptfloater.log`：滚动日志，默认保留 3 份。

## 开发与验证

```bash
python -m unittest discover -s tests -v
```

当前测试覆盖：

- 数据 Schema 校验；
- 原子存储与备份恢复；
- Python API 返回结构；
- 前端安全 DOM 渲染；
- Command Deck 视觉与快捷键契约；
- Windows/macOS 启动脚本行为。

## 依赖

| 包 | 用途 |
|---|---|
| `pywebview` | 桌面悬浮窗，Windows 使用 Edge WebView2，macOS 使用 WKWebView |
| `pyperclip` | 跨平台剪贴板 |

## Roadmap

- [ ] 打包 Windows `.exe` 和 macOS `.app`
- [ ] 增加真实截图/GIF 演示
- [ ] 支持提示词变量模板
- [ ] 支持全局热键唤起
- [ ] 增加主题色配置

## License

暂未添加开源许可证。公开发布前建议补充 `LICENSE`，例如 MIT。
