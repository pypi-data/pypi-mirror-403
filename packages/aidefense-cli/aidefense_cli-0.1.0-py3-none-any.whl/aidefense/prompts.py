from __future__ import annotations

from .models import Difficulty, Problem, ProblemKind


def build_generate_prompt(topic: str, kind: ProblemKind, difficulty: Difficulty) -> str:
    difficulty_rules = {
        "简单": "核心逻辑 5-15 行；测试用例 2-3 个；尽量只用 Python 标准库或 numpy。",
        "适中": "核心逻辑 15-40 行；包含至少 1 个边界情况；可使用 numpy（可选 sklearn）。",
        "较难": "多函数/类组织，或核心逻辑 40+ 行；至少包含：复杂度分析/鲁棒性/数值稳定性/可解释性 之一；测试更严格。",
    }[difficulty]

    return f"""
你是一名资深计算机科学教授。请为《人工智能导论》课程设计一道 Python 编程练习题。

主题：{topic}
题型：{kind}
难度：{difficulty}
约束：{difficulty_rules}

请严格只返回一个合法的 JSON 对象，不要包含 Markdown 格式（如 ```json）。格式如下：
{{
  \"title\": \"简短的中文标题(不要带编号)\",
  \"description\": \"详细的 Markdown 格式题目描述。包含算法原理简述（支持 LaTeX 公式，如 $E=mc^2$）、具体任务要求。\",
  \"initialCode\": \"Python 初始代码。如果是代码补全，请留出 # TODO 位置；如果是完整实现，提供类结构或空函数。\",
  \"hint\": \"一句话提示\"
}}

强制要求：initialCode 必须包含可直接运行的测试数据或断言逻辑（例如 assert 或打印对错），学生运行后能明确知道是否通过。
如果题目需要可视化，明确要求使用 matplotlib，并使用 plt.show()。
""".strip()


def build_defense_prompt(problem: Problem, user_code: str, output_text: str) -> str:
    return f"""
我是学生。我刚刚完成了题目【{problem.title}】。
题型：{problem.kind}，难度：{problem.difficulty}

我的代码如下：
```python
{user_code}
```

我的运行输出如下：
```text
{output_text}
```

请你作为严厉但循循善诱的大学计算机老师：
1) 先用中文简短点评我的代码逻辑和结果是否正确（如不正确，指出可能错的方向，不要直接给最终答案）。
2) 然后只提出 1 个深入的答辩问题（根据难度调整深度），问题要能检验我是否真的理解关键点。

要求：中文回复，简短一点。
""".strip()


def build_chat_system_prompt(problem: Problem, user_code: str, output_text: str) -> str:
    return f"你是一名人工智能导论课程的答辩老师。当前题目：{problem.title}。题型：{problem.kind}。难度：{problem.difficulty}。学生代码：{user_code}。运行输出：{output_text}。请继续答辩对话。"
