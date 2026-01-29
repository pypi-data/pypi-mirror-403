# aidefense-cli

AI 导论编程题出题与答辩命令行工具（默认 Moonshot/Kimi）。

## Install

From PyPI (after publish):

```bash
python -m pip install aidefense-cli
```

Editable (for development):

```bash
python -m pip install -e .
```

## Quick start

Set env vars (recommended):

```bash
set AIDEF_API_KEY=sk-...
set AIDEF_API_BASE=https://api.moonshot.cn/v1
set AIDEF_MODEL=moonshot-v1-8k
```

Start REPL:

```bash
aidef
```

Inside REPL:

- `gen` 生成题目（会要求输入：主题/题型/难度）
- `code paste` 粘贴学生代码（以单独一行 `EOF` 结束）
- `output paste` 粘贴运行输出（以单独一行 `EOF` 结束）
- `defend` 发起答辩（只问 1 个深入问题）
- `say 你的回复...` 继续多轮答辩
- `export md record.md` 导出 Markdown 记录

