from __future__ import annotations

import json
import time
from typing import Any

from .models import ChatMessage, DefenseSession, Difficulty, Problem, ProblemKind
from .prompts import build_chat_system_prompt, build_defense_prompt, build_generate_prompt
from .providers import BaseProvider


def generate_problem(*, topic: str, kind: ProblemKind, difficulty: Difficulty, provider: BaseProvider) -> Problem:
    prompt = build_generate_prompt(topic, kind, difficulty)
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": "你是一个严格遵循 JSON 格式输出的 API。"},
        {"role": "user", "content": prompt},
    ]

    content = provider.complete_text(messages)
    content = content.replace("```json", "").replace("```", "").strip()
    data = json.loads(content)

    return Problem(
        id=f"gen-{int(time.time())}",
        title=data["title"],
        description_md=data["description"],
        initial_code=data["initialCode"],
        hint=data.get("hint"),
        kind=kind,
        difficulty=difficulty,
    )


def start_defense(*, session: DefenseSession, provider: BaseProvider) -> None:
    prompt = build_defense_prompt(session.problem, session.user_code, session.output_text)
    session.history.append(ChatMessage(role="user", content="我已提交运行，请开始答辩检查。"))
    session.history.append(ChatMessage(role="assistant", content=""))

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": "你是一名人工智能课程的大学老师。正在进行代码答辩。"},
        {"role": "user", "content": prompt},
    ]

    content = provider.complete_text(messages)
    session.history[-1].content = content.strip()


def continue_chat(*, session: DefenseSession, user_message: str, provider: BaseProvider) -> None:
    session.history.append(ChatMessage(role="user", content=user_message))
    session.history.append(ChatMessage(role="assistant", content=""))

    api_messages: list[dict[str, Any]] = []
    api_messages.append(
        {
            "role": "system",
            "content": build_chat_system_prompt(
                session.problem, session.user_code, session.output_text
            ),
        }
    )

    for msg in session.history:
        if msg.role == "system":
            continue
        api_messages.append({"role": msg.role, "content": msg.content})

    content = provider.complete_text(api_messages)
    session.history[-1].content = content.strip()
