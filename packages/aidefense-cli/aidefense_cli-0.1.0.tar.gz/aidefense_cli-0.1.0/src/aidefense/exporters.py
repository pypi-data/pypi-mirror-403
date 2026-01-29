from __future__ import annotations

from datetime import date

from .models import DefenseSession


def export_markdown(session: DefenseSession) -> str:
    header = session.header
    header_lines: list[str] = []

    any_header = any(
        [
            header.course,
            header.class_name,
            header.student_id,
            header.student_name,
            header.teacher_signature,
            header.date,
        ]
    )

    if any_header:
        header_lines.append("# 人工智能导论课程答辩记录")
        if header.course:
            header_lines.append(f"课程名：{header.course}")
        if header.class_name:
            header_lines.append(f"班级：{header.class_name}")
        if header.student_id:
            header_lines.append(f"学号：{header.student_id}")
        if header.student_name:
            header_lines.append(f"姓名：{header.student_name}")

        signature = header.teacher_signature or "__________"
        header_lines.append(f"教师签名：{signature}")

        header_date = header.date or date.today().isoformat()
        header_lines.append(f"日期：{header_date}")
        header_lines.append("")

    p = session.problem

    chat_text = []
    for msg in session.history:
        if msg.role == "system":
            continue
        who = "学生" if msg.role == "user" else "AI助教"
        chat_text.append(f"[{who}]：\n{msg.content}\n")
    chat_block = "\n---\n".join(chat_text)

    return "\n".join(
        [
            *header_lines,
            f"## 题目\n标题：{p.title}\n题型：{p.kind}  难度：{p.difficulty}\n",
            "## 1. 学生提交代码",
            "```python",
            session.user_code.rstrip(),
            "```",
            "",
            "## 2. 运行结果",
            "```text",
            session.output_text.rstrip(),
            "```",
            "",
            "## 3. 答辩对话记录",
            chat_block.strip(),
            "",
        ]
    )
