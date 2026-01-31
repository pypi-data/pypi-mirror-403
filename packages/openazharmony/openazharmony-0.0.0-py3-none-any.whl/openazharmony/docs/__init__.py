from __future__ import annotations

import argparse
from importlib import resources
from pathlib import Path


def list_docs() -> list[str]:
    files = []
    for entry in resources.files(__package__).iterdir():
        if entry.suffix == ".md":
            files.append(entry.stem)
    return sorted(files)


def read_doc(name: str) -> str:
    if not name:
        raise ValueError("Document name is required.")
    filename = name if name.lower().endswith(".md") else f"{name}.md"
    doc_path = resources.files(__package__) / filename
    if not doc_path.is_file():
        available = ", ".join(list_docs()) or "none"
        raise FileNotFoundError(f"Unknown document '{name}'. Available: {available}.")
    return doc_path.read_text(encoding="utf-8")


def write_docs(target_dir: str | Path) -> list[Path]:
    target = Path(target_dir).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for entry in resources.files(__package__).iterdir():
        if entry.suffix != ".md":
            continue
        content = entry.read_text(encoding="utf-8")
        destination = target / entry.name
        destination.write_text(content, encoding="utf-8")
        written.append(destination)
    return written


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read openazharmony documentation bundled with the package."
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available documentation files.",
    )
    parser.add_argument(
        "--show",
        metavar="NAME",
        help="Print a documentation file to stdout (e.g. PYTHON, AZURE).",
    )
    parser.add_argument(
        "--write-dir",
        metavar="PATH",
        help="Write all documentation files to a directory.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.list:
        for name in list_docs():
            print(name)
        return 0

    if args.show:
        print(read_doc(args.show))
        return 0

    if args.write_dir:
        written = write_docs(args.write_dir)
        for path in written:
            print(path)
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
