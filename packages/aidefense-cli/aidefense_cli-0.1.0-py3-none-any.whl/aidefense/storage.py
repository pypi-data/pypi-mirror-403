from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .models import ChatMessage, DefenseSession, HeaderInfo, Problem, ProviderConfig


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def save_problem(problem: Problem, path: str | Path) -> None:
    _write_json(Path(path), asdict(problem))


def load_problem(path: str | Path) -> Problem:
    data = _read_json(Path(path))
    return Problem(**data)


def save_session(session: DefenseSession, path: str | Path) -> None:
    _write_json(Path(path), asdict(session))


def load_session(path: str | Path) -> DefenseSession:
    data = _read_json(Path(path))

    problem = Problem(**data["problem"])
    header = HeaderInfo(**(data.get("header") or {}))
    provider = ProviderConfig(**(data.get("provider") or {}))
    history = [ChatMessage(**m) for m in (data.get("history") or [])]

    return DefenseSession(
        problem=problem,
        user_code=data.get("user_code", ""),
        output_text=data.get("output_text", ""),
        history=history,
        header=header,
        provider=provider,
        created_at=data.get("created_at") or "",
    )


def load_bank(path: str | Path) -> list[Problem]:
    data = _read_json(Path(path))
    return [Problem(**p) for p in data]


def save_bank(problems: list[Problem], path: str | Path) -> None:
    _write_json(Path(path), [asdict(p) for p in problems])


def append_problem_to_bank(problem: Problem, path: str | Path) -> None:
    bank_path = Path(path)
    if bank_path.exists():
        problems = load_bank(bank_path)
    else:
        problems = []

    problems.append(problem)
    save_bank(problems, bank_path)
