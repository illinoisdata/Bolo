import argparse
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from .api import InferClient, create_a_venv, pipeline, remove_venv, fetch_templates


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bolopipe", description="Inspect BoloPipe registry records")
    sub = parser.add_subparsers(dest="command", required=True)

    create_venv_parser = sub.add_parser("create-venv", help="Create a venv for a model")
    create_venv_parser.add_argument("repo_id", help="HuggingFace repository id")
    create_venv_parser.add_argument("--venv-path", default=None, help="Path to create the venv")

    run_parser = sub.add_parser("run", help="Run inference for a model")
    run_parser.add_argument("repo_id", help="HuggingFace repository id")
    run_parser.add_argument("params", nargs="*", metavar="KEY=VALUE", help="Template parameters")

    remove_venv_parser = sub.add_parser("remove-venv", help="Remove the venv for a model")
    remove_venv_parser.add_argument("repo_id", help="HuggingFace repository id")

    sub.add_parser("fetch-templates", help="Download the bolo templates cache for this version")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "create-venv":
        create_a_venv(args.repo_id, args.venv_path)
        return 0

    if args.command == "run":
        client = InferClient()
        repo_name = "__SEP__".join(args.repo_id.split("/"))
        venv_dir = client.db_dir / "tmp_venv" / repo_name
        venv_python = venv_dir / "bin" / "python"
        venv_bolo = venv_dir / "bin" / "bolo"

        if not venv_python.exists():
            parser.error(
                f"no venv found at {venv_dir}; "
                f"run `bolo create-venv {args.repo_id}` first"
            )

        if Path(sys.executable).resolve() != venv_python.resolve():
            return subprocess.call([str(venv_bolo), "run", args.repo_id, *args.params])

        kwargs = {}
        for item in args.params:
            if "=" not in item:
                parser.error(f"invalid parameter {item!r}, expected KEY=VALUE")
            k, _, v = item.partition("=")
            kwargs[k] = v
        result = pipeline(args.repo_id, **kwargs)
        if result is not None:
            print(result)
        return 0

    if args.command == "remove-venv":
        remove_venv(args.repo_id)
        return 0

    if args.command == "fetch-templates":
        fetch_templates()
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
