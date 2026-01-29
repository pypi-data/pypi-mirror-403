from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from time import monotonic

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.shortcuts import radiolist_dialog

from .config import load_provider_config, save_provider_config
from .core import continue_chat, generate_problem, start_defense
from .exporters import export_markdown
from .models import DefenseSession, HeaderInfo, Problem, ProviderConfig
from .providers import MoonshotProvider, OpenAICompatibleProvider
from .storage import load_problem, load_session, save_problem, save_session


def _print(text: str) -> None:
    print(text, flush=True)


def _stream_with_status(chunks, *, label: str = "生成中") -> str:
    start = monotonic()
    last_status_len = 0
    buf = ""
    spinner = "|/-\\"
    spinner_i = 0

    def _render_status() -> None:
        nonlocal last_status_len, spinner_i
        elapsed = monotonic() - start
        spin = spinner[spinner_i % len(spinner)]
        spinner_i += 1
        status = f"[{spin} {label}… {len(buf)} chars, {elapsed:0.1f}s]"
        pad = " " * max(0, last_status_len - len(status))
        print("\r" + status + pad, end="", flush=True)
        last_status_len = len(status)

    _render_status()

    try:
        for chunk in chunks:
            buf += chunk
            # clear status line, print chunk, redraw status
            print("\r" + (" " * last_status_len) + "\r", end="", flush=True)
            print(chunk, end="", flush=True)
            _render_status()
    except KeyboardInterrupt:
        print("\r" + (" " * last_status_len) + "\r", end="", flush=True)
        print("[interrupted]", flush=True)
    finally:
        print("\r" + (" " * last_status_len) + "\r", end="", flush=True)

    return buf


def _provider_from_config(cfg: ProviderConfig):
    if cfg.name == "moonshot":
        return MoonshotProvider(cfg)
    return OpenAICompatibleProvider(cfg)


def run_repl(*, autosave_config: bool = True) -> None:
    command_completer = WordCompleter(
        [
            "set",
            "set header",
            "gen",
            "load problem",
            "save problem",
            "load session",
            "save session",
            "code file",
            "code paste",
            "output file",
            "output paste",
            "defend",
            "say",
            "export md",
            "show",
            "help",
            "exit",
        ],
        ignore_case=True,
    )
    prompt = PromptSession("aidef> ", completer=command_completer)

    provider_cfg = load_provider_config()
    current_problem: Problem | None = None
    session: DefenseSession | None = None
    header = HeaderInfo()

    help_text = """Commands:
  set key|base|model|provider <value>
  set header               (interactive)
  gen                      (interactive generate)
  load problem <path>
  save problem <path>
  load session <path>
  save session <path>
  code file <path>         (attach student code)
  code paste               (multi-line, end with EOF)
  output file <path>
  output paste
  defend                   (needs problem+code+output)
  say <message>
  export md <path>
  show
  help
  exit
"""

    _print("AI 导论答辩 REPL. Type 'help' for commands.")

    while True:
        try:
            line = prompt.prompt()
        except (EOFError, KeyboardInterrupt):
            _print("exit")
            return

        cmd = line.strip()
        if not cmd:
            continue

        if cmd in {"exit", "quit"}:
            return
        if cmd == "help":
            _print(help_text)
            continue

        if cmd == "show":
            _print(f"provider={provider_cfg.name} base={provider_cfg.api_base} model={provider_cfg.model}")
            if current_problem:
                _print(f"problem={current_problem.title} kind={current_problem.kind} diff={current_problem.difficulty}")
            else:
                _print("problem=<none>")
            if session:
                _print(f"session.history={len(session.history)}")
            continue

        parts = cmd.split(" ")

        if parts[0] == "set" and len(parts) >= 3:
            key = parts[1]
            value = " ".join(parts[2:]).strip()
            if key == "key":
                provider_cfg.api_key = value
            elif key == "base":
                provider_cfg.api_base = value
            elif key == "model":
                provider_cfg.model = value
            elif key == "provider":
                provider_cfg.name = value
            else:
                _print("Unknown set key")
                continue

            if autosave_config:
                save_provider_config(provider_cfg)
            _print("ok")
            continue

        if cmd == "set header":
            course = prompt.prompt("课程名(可空): ").strip() or None
            class_name = prompt.prompt("班级(可空): ").strip() or None
            student_id = prompt.prompt("学号(可空): ").strip() or None
            student_name = prompt.prompt("姓名(可空): ").strip() or None
            teacher_signature = prompt.prompt("教师签名(可空): ").strip() or None
            date_str = prompt.prompt("日期(YYYY-MM-DD，可空默认今天): ").strip() or None
            header = HeaderInfo(
                course=course,
                class_name=class_name,
                student_id=student_id,
                student_name=student_name,
                teacher_signature=teacher_signature,
                date=date_str,
            )
            _print("ok")
            continue

        if cmd == "gen":
            topic = prompt.prompt("题目主题: ").strip()
            if not topic:
                _print("topic required")
                continue

            kind_dialog = radiolist_dialog(
                title="题型",
                text="选择题型",
                values=[("代码补全", "代码补全"), ("完整实现", "完整实现")],
            )
            kind = kind_dialog.run() or "代码补全"

            diff_dialog = radiolist_dialog(
                title="难度",
                text="选择难度",
                values=[("简单", "简单"), ("适中", "适中"), ("较难", "较难")],
            )
            difficulty = diff_dialog.run() or "简单"

            provider = _provider_from_config(provider_cfg)
            try:
                prob = generate_problem(
                    topic=topic, kind=kind, difficulty=difficulty, provider=provider
                )
            except Exception as e:
                _print(f"generate failed: {e}")
                continue

            current_problem = prob
            session = DefenseSession(problem=prob, header=header, provider=provider_cfg)
            _print(f"generated: {prob.title}")
            continue

        if len(parts) >= 3 and parts[0] == "load" and parts[1] == "problem":
            current_problem = load_problem(parts[2])
            session = DefenseSession(problem=current_problem, header=header, provider=provider_cfg)
            _print("ok")
            continue

        if len(parts) >= 3 and parts[0] == "save" and parts[1] == "problem":
            if not current_problem:
                _print("no problem")
                continue
            save_problem(current_problem, parts[2])
            _print("ok")
            continue

        if len(parts) >= 3 and parts[0] == "load" and parts[1] == "session":
            session = load_session(parts[2])
            current_problem = session.problem
            header = session.header
            provider_cfg = session.provider
            _print("ok")
            continue

        if len(parts) >= 3 and parts[0] == "save" and parts[1] == "session":
            if not session:
                _print("no session")
                continue
            save_session(session, parts[2])
            _print("ok")
            continue

        if len(parts) >= 2 and parts[0] == "code":
            if not session:
                if current_problem:
                    session = DefenseSession(problem=current_problem, header=header, provider=provider_cfg)
                else:
                    _print("no session/problem")
                    continue

            if parts[1] == "file" and len(parts) >= 3:
                session.user_code = Path(parts[2]).read_text(encoding="utf-8")
                _print("ok")
                continue
            if parts[1] == "paste":
                _print("Paste code, end with a line containing only EOF")
                lines: list[str] = []
                while True:
                    l = prompt.prompt("... ")
                    if l.strip() == "EOF":
                        break
                    lines.append(l)
                session.user_code = "\n".join(lines)
                _print("ok")
                continue

        if len(parts) >= 2 and parts[0] == "output":
            if not session:
                _print("no session")
                continue
            if parts[1] == "file" and len(parts) >= 3:
                session.output_text = Path(parts[2]).read_text(encoding="utf-8")
                _print("ok")
                continue
            if parts[1] == "paste":
                _print("Paste output, end with a line containing only EOF")
                lines: list[str] = []
                while True:
                    l = prompt.prompt("... ")
                    if l.strip() == "EOF":
                        break
                    lines.append(l)
                session.output_text = "\n".join(lines)
                _print("ok")
                continue

        if cmd == "defend":
            if not session:
                _print("no session")
                continue
            if not session.user_code.strip() or not session.output_text.strip():
                _print("need code and output")
                continue

            provider = _provider_from_config(provider_cfg)
            _print("--- AI ---")
            try:
                # streaming print
                assistant_msg = ""
                from .models import ChatMessage
                from .prompts import build_defense_prompt

                defense_prompt = build_defense_prompt(
                    session.problem, session.user_code, session.output_text
                )
                session.history.append(
                    ChatMessage(role="user", content="我已提交运行，请开始答辩检查。")
                )
                session.history.append(ChatMessage(role="assistant", content=""))

                messages = [
                    {
                        "role": "system",
                        "content": "你是一名人工智能课程的大学老师。正在进行代码答辩。",
                    },
                    {"role": "user", "content": defense_prompt},
                ]

                assistant_msg = _stream_with_status(provider.stream(messages), label="答辩生成")
                session.history[-1].content = assistant_msg.strip()
            except Exception as e:
                _print(f"defend failed: {e}")
            continue

        if parts[0] == "say" and len(parts) >= 2:
            if not session:
                _print("no session")
                continue
            provider = _provider_from_config(provider_cfg)
            msg = cmd[len("say ") :]
            _print("--- AI ---")
            try:
                from .models import ChatMessage
                from .prompts import build_chat_system_prompt

                session.history.append(ChatMessage(role="user", content=msg))
                session.history.append(ChatMessage(role="assistant", content=""))

                api_messages = [
                    {
                        "role": "system",
                        "content": build_chat_system_prompt(
                            session.problem, session.user_code, session.output_text
                        ),
                    }
                ]
                for m in session.history:
                    if m.role == "system":
                        continue
                    api_messages.append({"role": m.role, "content": m.content})

                assistant_msg = _stream_with_status(provider.stream(api_messages), label="对话生成")
                session.history[-1].content = assistant_msg.strip()
            except Exception as e:
                _print(f"chat failed: {e}")
            continue

        if len(parts) >= 3 and parts[0] == "export" and parts[1] == "md":
            if not session:
                _print("no session")
                continue
            out_path = Path(parts[2])
            out_path.write_text(export_markdown(session), encoding="utf-8")
            _print("ok")
            continue

        _print("unknown command; type 'help'")
