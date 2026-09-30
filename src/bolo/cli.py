import argparse
from typing import Sequence

from .api import pipeline, fetch_templates


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bolopipe", description="Inspect BoloPipe registry records")
    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("run", help="Run inference for a model")
    run_parser.add_argument("repo_id", help="HuggingFace repository id")
    run_parser.add_argument("params", nargs="*", metavar="KEY=VALUE", help="Template parameters")

    sub.add_parser("fetch-templates", help="Download the bolo templates cache for this version")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
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

    if args.command == "fetch-templates":
        fetch_templates()
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
