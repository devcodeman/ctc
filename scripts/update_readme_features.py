"""Regenerate the README Features table from the requirements document."""

from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
README_PATH = ROOT / "README.md"
REQUIREMENTS_PATH = ROOT / "docs" / "requirements.md"

START_MARKER = "<!-- FEATURES_TABLE_START -->"
END_MARKER = "<!-- FEATURES_TABLE_END -->"

REQUIREMENT_PATTERN = re.compile(r"^\[(?P<id>[^\]]+)\]:\s*(?P<description>.+?)\s*$")


def parse_requirements(text: str) -> list[tuple[str, str]]:
    """Extract requirement identifiers and descriptions from the requirements document."""
    requirements: list[tuple[str, str]] = []
    for line in text.splitlines():
        match = REQUIREMENT_PATTERN.match(line.strip())
        if match:
            requirements.append((match.group("id"), match.group("description")))
    return requirements


def build_features_table(requirements: list[tuple[str, str]]) -> str:
    """Build the README Features table markdown from parsed requirements."""
    lines = [
        START_MARKER,
        "| Requirement | Description |",
        "|---|---|",
    ]
    lines.extend(f"| {requirement_id} | {description} |" for requirement_id, description in requirements)
    lines.append(END_MARKER)
    return "\n".join(lines)


def replace_features_table(readme_text: str, table_text: str) -> str:
    """Replace the generated Features table block inside the README."""
    pattern = re.compile(
        rf"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}",
        re.DOTALL,
    )
    if not pattern.search(readme_text):
        raise ValueError("README Features markers were not found.")
    return pattern.sub(table_text, readme_text)


def main() -> None:
    """Regenerate the README Features section from the requirements file."""
    requirements_text = REQUIREMENTS_PATH.read_text(encoding="utf-8")
    requirements = parse_requirements(requirements_text)
    if not requirements:
        raise ValueError("No requirements were found in docs/requirements.md.")
    readme_text = README_PATH.read_text(encoding="utf-8")
    updated_readme = replace_features_table(readme_text, build_features_table(requirements))
    README_PATH.write_text(updated_readme + ("\n" if not updated_readme.endswith("\n") else ""), encoding="utf-8")


if __name__ == "__main__":
    main()
