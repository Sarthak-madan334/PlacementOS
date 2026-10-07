"""Standalone CLI command to parse a resume file without starting the web server or database."""

import json
import sys
from pathlib import Path

from app.services.resume_parser import parse_resume_bytes


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m app.cli.parse_resume <path_to_resume_file>", file=sys.stderr)
        sys.exit(1)

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"Error: File '{file_path}' does not exist", file=sys.stderr)
        sys.exit(1)

    with open(file_path, "rb") as f:
        content = f.read()

    try:
        result = parse_resume_bytes(content=content, filename=file_path.name)
        print(json.dumps(result.model_dump(), indent=2, default=str))
    except Exception as e:
        print(f"Parser error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
