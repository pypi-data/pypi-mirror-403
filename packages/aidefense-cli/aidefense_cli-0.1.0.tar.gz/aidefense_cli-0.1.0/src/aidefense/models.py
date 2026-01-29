from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal


Role = Literal["system", "user", "assistant"]
ProblemKind = Literal["代码补全", "完整实现"]
Difficulty = Literal["简单", "适中", "较难"]


@dataclass
class Problem:
    id: str
    title: str
    description_md: str
    initial_code: str
    hint: str | None = None
    kind: ProblemKind = "代码补全"
    difficulty: Difficulty = "简单"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))


@dataclass
class HeaderInfo:
    course: str | None = None
    class_name: str | None = None
    student_id: str | None = None
    student_name: str | None = None
    teacher_signature: str | None = None
    date: str | None = None  # ISO date: YYYY-MM-DD


@dataclass
class ChatMessage:
    role: Role
    content: str
    ts: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))


@dataclass
class ProviderConfig:
    name: str = "moonshot"
    api_key: str | None = None
    api_base: str = "https://api.moonshot.cn/v1"
    model: str = "moonshot-v1-8k"


@dataclass
class DefenseSession:
    problem: Problem
    user_code: str = ""
    output_text: str = ""
    history: list[ChatMessage] = field(default_factory=list)
    header: HeaderInfo = field(default_factory=HeaderInfo)
    provider: ProviderConfig = field(default_factory=ProviderConfig)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))


def dataclass_to_dict(obj: Any) -> Any:
    if isinstance(obj, list):
        return [dataclass_to_dict(x) for x in obj]

    if hasattr(obj, "__dataclass_fields__"):
        result: dict[str, Any] = {}
        for key in obj.__dataclass_fields__.keys():
            result[key] = dataclass_to_dict(getattr(obj, key))
        return result

    return obj
