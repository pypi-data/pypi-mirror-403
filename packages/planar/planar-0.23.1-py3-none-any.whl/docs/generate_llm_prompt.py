"""Render the llm prompt templates into a full files."""

from argparse import ArgumentParser
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


def render_llm_prompt(output_path: Path) -> None:
    """Render the llm_prompt.template.md template using the provided context."""
    docs_dir = Path(__file__).parent
    env = Environment(loader=FileSystemLoader(docs_dir))

    # Add a function to include files as raw text (no Jinja2 processing)
    def include_raw(filename: str) -> str:
        return (docs_dir / filename).read_text()

    env.globals["include_raw"] = include_raw

    template = env.get_template("llm_prompt.template.md")
    output_path.write_text(template.render())


def main() -> None:
    """Generate the ``llm_prompt.md`` file from the template."""
    parser = ArgumentParser(
        description="Generate llm_prompt.md from llm_prompt.template.md Jinja template"
    )
    parser.add_argument("--output", default="llm_prompt.md", help="Output file name")
    args = parser.parse_args()

    output_file = Path(__file__).parent / args.output
    render_llm_prompt(output_file)
    print(f"Wrote {output_file}")


if __name__ == "__main__":
    main()
