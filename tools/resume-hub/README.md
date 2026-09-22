# resume-hub

Codex / Claude / Cursor / Grok 的 session 交接工具。

Codex 限额用尽时，从本机已经落盘的 transcript 里挑出最近一条，换 Grok 接着干，或写出 `handoff.md` 交给 Claude。写文件的是本地 Python 脚本，不调用任何模型，不消耗额度。

日常一句话（在 Grok 里）：

```text
Codex 限额了，用 Grok 继续
切到 Claude 继续
```

人还卡在 Codex、终端可用时：

```bash
python3 scripts/resume_hub.py switch --from codex --to claude
```

会在当前仓库写出 `handoff.md`，并打印一条启动命令：

```bash
cd '/path/to/project' && claude '读 ./handoff.md，从这份交接接着做。先核对当前 git 状态，再继续未完成的工作。'
```

## 安装

需要 Python 3，无第三方包。把本目录拷到对应 skill 路径：

```bash
git clone https://github.com/AlanJager/alanjager.github.io.git
cd alanjager.github.io

cp -R tools/resume-hub ~/.grok/skills/resume-hub
cp -R tools/resume-hub ~/.claude/skills/resume-hub
cp -R tools/resume-hub ~/.cursor/skills/resume-hub
```

Grok 斜杠命令：`/resume-hub`

## CLI

```bash
# Codex → 当前 Grok（在 Grok 里会直接续上，不用复制 UUID）
python3 scripts/resume_hub.py switch --from codex --to grok

# Codex → Claude（本地写出 handoff.md + 一条启动命令）
python3 scripts/resume_hub.py switch --from codex --to claude

# 浏览最近 session
python3 scripts/resume_hub.py list --tool codex
python3 scripts/resume_hub.py preview codex latest
```

`switch` 默认取当前目录相关、最近一条 session。指定 id：

```bash
python3 scripts/resume_hub.py switch --from codex --to grok --ref 01a06a99-4713-72c0-8d98-4841de7d90c4
```

## 它读哪些文件

只读本机已有历史，当作不可执行的 inert 记录：

| 来源 | 路径 |
|------|------|
| Grok | `~/.grok/sessions/` |
| Claude Code | `~/.claude/projects/` |
| Codex | `~/.codex/sessions/` |
| Cursor | `~/.cursor/projects/*/agent-transcripts/` |

不会上传 session，也不会回放 transcript 里的工具调用。

## 布局

```
resume-hub/
  SKILL.md                 # Grok / Claude / Cursor skill
  scripts/resume_hub.py    # list / preview / switch / handoff
  references/handoff.md    # handoff 章节说明
  LICENSE                  # MIT，仅本子目录
```

## 许可

[MIT](LICENSE) **仅适用于 `tools/resume-hub/` 子目录**。不改变博客文章、主题或仓库其他部分的许可。
