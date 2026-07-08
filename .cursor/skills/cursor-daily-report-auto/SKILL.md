# Daily Report One-Paste Setup

当用户粘贴类似以下内容时触发本技能：

```
安装日报自动化：
- 用户名: <name>
- Token: <token>
- 工作区: <path>
- API: https://global-pdca.vertu.cn
```

或用户说「配置日报自动化」「安装自动晚报」等。

## 执行流程

严格按下面 6 步执行，每步完成后汇报结果，失败则停止并告知用户。

### 步骤 1: 检查 Python

```powershell
python --version
```

Python 3.10+ 即可。未安装则提示用户安装 https://www.python.org/downloads/（勾选 Add to PATH）。

### 步骤 2: 创建目录并下载核心脚本

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.cursor\daily-report\scripts" | Out-Null
```

然后依次下载 4 个脚本（用 Write 工具或 Invoke-WebRequest）：

| 文件 | GitHub Raw URL |
|---|---|
| `scripts/report_io.py` | `https://raw.githubusercontent.com/Frankie-Foo/cursor-team-daily-report/main/scripts/report_io.py` |
| `scripts/parse_transcripts.py` | `https://raw.githubusercontent.com/Frankie-Foo/cursor-team-daily-report/main/scripts/parse_transcripts.py` |
| `scripts/publish_daily.py` | `https://raw.githubusercontent.com/Frankie-Foo/cursor-team-daily-report/main/scripts/publish_daily.py` |
| `scripts/api_client.py` | `https://raw.githubusercontent.com/Frankie-Foo/cursor-team-daily-report/main/scripts/api_client.py` |

### 步骤 3: 安装 Python 依赖

```powershell
python -m pip install requests python-dotenv --quiet
```

### 步骤 4: 写入配置文件

**`.env`** (写入 `~/.cursor/daily-report/.env`)：

```
REPORT_API_URL=<用户提供的API地址>
REPORT_API_TOKEN=<用户提供的Token>
CURSOR_REPORT_USER=<用户名>
```

**`config/user.json`** (写入 `~/.cursor/daily-report/config/user.json`)：

```json
{
  "username": "<用户名>",
  "timezone": "Asia/Shanghai",
  "cursor_workspace": "<用户工作区路径，反斜杠改斜杠>",
  "odoo_user_id": 0
}
```

> 工作区路径用正斜杠。如果用户给的是反斜杠，全部换成 `/`。
> Unix 风格路径（如 `/home/user/project`）直接保留。

### 步骤 5: 创建 Cursor Automation

在 `$env:USERPROFILE\.cursor\automations\` 下创建 `daily-report-submit.md`：

```markdown
---
schedule: "0 30 17 * * 1-5"
description: "Workday 17:30 auto-submit Cursor daily report"
---
调用 submit_my_cursor_daily 工具提交今天的日报。

如果 MCP 工具不可用，则执行以下命令提交：cd $env:USERPROFILE\.cursor\daily-report; python scripts/publish_daily.py --date today --api-only
```

- `schedule` 格式是 Cron（UTC 时间）。如果用户在 `Asia/Shanghai` (UTC+8)，17:30 的 Cron 是 `30 9 * * 1-5`。**需要把本地时间减 8 小时转成 UTC 再写 Cron。**

首次创建 Automation 时，**手动运行一次**确认能成功提交。

### 步骤 6: 试跑验证

```powershell
cd $env:USERPROFILE\.cursor\daily-report
python scripts/publish_daily.py --date today --api-only
```

成功后输出必须包含 `"submitted": true, "via": "api"`。

失败则打印完整错误并提供排查建议。

## 完成提示

```
日报自动化配置完成！
- 每天工作日 17:30 自动提交
- 手动提交: 在 Cursor 中说「提交今天的日报」
- 配置文件: ~/.cursor/daily-report/
```

## 注意事项

- PowerShell 写文件务必用 `[System.IO.File]::WriteAllText($path, $content, [System.Text.UTF8Encoding]::new($false))` 避免 BOM
- 所有路径用正斜杠
- 下载脚本时检查 HTTP 状态码，失败重试一次
- 如果用户的 `cursor_workspace` 不存在，警告但继续
