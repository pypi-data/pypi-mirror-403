from __future__ import annotations

import argparse
from importlib.resources import files
from pathlib import Path
from typing import Sequence


TEMPLATES_DIR = files(__package__) / "templates"


def generate_gitignore(output: str = ".gitignore") -> Path:
    template_path = TEMPLATES_DIR / "python.gitignore"
    content = template_path.read_text()

    result_path = Path(output)
    result_path.write_text(content)
    return result_path


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="gitignore-gen",
        description="Genera un archivo .gitignore estándar para proyectos Python/Django/Flask.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=".gitignore",
        help="Ruta del archivo .gitignore a generar",
    )

    args = parser.parse_args(list(argv) if argv is not None else None)
    generate_gitignore(args.output)


__all__ = ["generate_gitignore", "main"]

