from __future__ import annotations

import argparse

from .repl import run_repl


def main() -> None:
    parser = argparse.ArgumentParser(prog="aidef", description="AI 导论答辩命令行工具", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--no-save", action="store_true", help="Do not persist config to disk")
    args = parser.parse_args()

    run_repl(autosave_config=not args.no_save)


if __name__ == "__main__":
    main()
