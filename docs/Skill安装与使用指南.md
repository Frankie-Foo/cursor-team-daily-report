# Cursor 日报 Skill — 同事安装与使用指南

> 看完这篇就会用。不用懂代码，**直接跟 Cursor 说话**就行。

---

## 这个 Skill 能干嘛？

每天帮你自动做一件事：**总结你今天用 Cursor 做了什么**，然后：

- 写成一份结构化日报（JSON + Markdown）
- 存进团队数据库（主管可查）
- 备份到 Git 仓库

**你不需要**自己写日报、不需要记今天问了 AI 什么。  
**你需要**平时正常用 Cursor 干活，下班前让 Skill 跑一下（或设好自动跑）。

---

## 第一次使用：跟 Cursor 说这几段话

> 前提：电脑已装 **Cursor** 和 **Python**。  
> 打开 Cursor，新建对话，**按顺序**复制下面的话发给 Cursor，让它帮你操作。

### 第 1 步：下载项目

```
请帮我 clone 这个仓库到 D盘：
https://github.com/Frankie-Foo/cursor-team-daily-report.git

clone 完成后进入目录，运行 scripts/setup.ps1 安装依赖。
```

### 第 2 步：填写我的信息

先找 **Frank 主管** 拿数据库密码，然后对 Cursor 说：

```
请帮我在 cursor-team-daily-report 项目里配置：

1. 复制 config/user.example.json 为 config/user.json
2. 复制 .env.example 为 .env
3. user.json 里填写：
   - username: 【填你的英文名，见下表】
   - cursor_workspace: 【填你平时干活的 Cursor 项目路径，例如 D:/经销商PDCA】
4. .env 里填写 DB_PASSWORD: 【主管给你的密码】
   CURSOR_REPORT_USER: 【同上 username】
```

**username 对照表（必须一模一样）：**

Sam、Gary、May、Frank、Lina、April、Ivan、Viki、Vivi、Haiwen、Chris、Qiqi、Xianna、Zhangyi

### 第 3 步：安装 Skill

```
请帮我安装 cursor-daily-report skill：
运行 cursor-team-daily-report 仓库里的 scripts/install_skill.ps1
把 skill 装到我的 Cursor 个人 skills 目录。
```

### 第 4 步：试跑一下

```
请运行 cursor-daily-report skill，帮我发布今天的日报：
python scripts/publish_daily.py --date today --git-push
```

看到成功输出（有 daily/你的名字/日期.json）就 OK 了。

---

## 日常使用：就一句话

以后每天下班前，在 Cursor 里直接说：

```
运行 cursor-daily-report，帮我发今天的日报。
```

或者更短：

```
发今日 Cursor 日报
```

Cursor 会自动：

1. 读取你今天在 Cursor 里的对话记录  
2. 总结成中文日报  
3. 写入数据库 + Git  

**今天没用 Cursor？** 也可以说「发今日日报」，会生成一条「今日无会话」的记录，正常的。

---

## 推荐：设成每天自动跑（可选）

对 Cursor 说：

```
请帮我创建一个 Cursor Automation：
- 名称：Cursor 团队日报
- 时间：工作日 17:30
- Cron：30 17 * * 1-5
- 使用 cursor-daily-report skill
- 每天自动执行 python scripts/publish_daily.py --date today --git-push
```

设好后就不用每天手动说了。

---

## 两个路径别搞混

| 是什么 | 填什么 |
|--------|--------|
| **日报仓库** | `D:/cursor-team-daily-report`（clone 下来的，装 skill 用） |
| **日常工作项目** | 你实际干活的那个文件夹，填在 `user.json` 的 `cursor_workspace` |

常见错误：把 `cursor_workspace` 填成日报仓库 → 会找不到今天的对话记录。

---

## 常见问题

**Q：Cursor 说找不到 skill？**  
→ 再说一次：「请安装 cursor-team-daily-report 仓库的 install_skill.ps1」

**Q：报数据库连接失败？**  
→ 找 Frank 确认 `.env` 里的密码

**Q：报找不到 transcripts？**  
→ 检查 `user.json` 里 `cursor_workspace` 是不是你的**业务项目**路径

**Q：主管能看到我什么？**  
→ 普通同事只能看自己的；组长看组内；总监看全员。不用额外登录。

---

## 需要帮助

- 配置问题 → 找 **Frank**
- 仓库地址 → https://github.com/Frankie-Foo/cursor-team-daily-report

---

*2026-06-12*
