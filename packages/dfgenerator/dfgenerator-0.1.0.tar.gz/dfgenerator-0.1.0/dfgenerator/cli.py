"""Command line interface for generating sample data frames."""

from __future__ import annotations

from pathlib import Path

import click

from .core import DEFAULT_FAKER_LOCALE, ColumnSpec, DataFrameBuilder, RowTemplate, choices, sequence
from .loaders import build_from_config


def build_default_dataset(row_count: int):
    """Generate a small but varied dataset for demonstrations."""
    template = RowTemplate(
        [
            ColumnSpec("id", sequence(1)),
            ColumnSpec("city", choices(["Paris", "Berlin", "Boston"])),
            ColumnSpec("score", lambda index: 10 * (index + 1)),
        ],
        base={"source": "dfgenerator"},
    )
    return DataFrameBuilder().from_template(template, row_count).build()


@click.command()
@click.option(
    "-c",
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help="YAML configuration file describing the dataset.",
)
@click.option(
    "-s",
    "--schema",
    type=click.Path(exists=True, path_type=Path),
    help="JSON Schema file to generate data from.",
)
@click.option(
    "-n",
    "--rows",
    type=int,
    default=5,
    show_default=True,
    help="Number of rows to generate.",
)
@click.option(
    "-f",
    "--format",
    type=click.Choice(["csv", "json"], case_sensitive=False),
    default="csv",
    show_default=True,
    help="Output format.",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    help="Destination file. If omitted, a preview is printed to stdout.",
)
@click.option(
    "--lines",
    is_flag=True,
    help="Write line-delimited JSON when --format json is selected.",
)
@click.option(
    "--faker-locale",
    default=DEFAULT_FAKER_LOCALE,
    show_default=True,
    help="Locale used when Faker providers are defined.",
)
@click.option(
    "--seed",
    type=int,
    help="Seed for Faker-generated values.",
)
def main(
    config: Path | None,
    schema: Path | None,
    rows: int,
    format: str,
    output: Path | None,
    lines: bool,
    faker_locale: str,
    seed: int | None,
) -> None:  # pragma: no cover - exercised via __main__
    """Generate small, deterministic datasets for tests."""

    # Validate mutually exclusive options
    if config and schema:
        raise click.ClickException("Cannot use both --config and --schema options together")

    if schema:
        # Load from JSON Schema
        from .loaders import load_jsonschema_dataset

        dataset = load_jsonschema_dataset(
            schema,
            rows=rows,
            faker_locale=faker_locale,
            seed=seed,
        )
    elif config:
        # Load from YAML config
        try:
            import yaml  # type: ignore
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise click.ClickException(
                "pyyaml is required for --config usage; install with `pip install pyyaml`"
            ) from exc

        raw = config.read_text(encoding="utf-8")
        config_dict = yaml.safe_load(raw) or {}
        # CLI overrides
        config_dict["faker_locale"] = faker_locale
        if seed is not None:
            config_dict["seed"] = seed
        dataset = build_from_config(config_dict)
    else:
        # Generate default dataset
        dataset = build_default_dataset(rows)

    if output:
        path = dataset.to_file(output, fmt=format, lines=lines)
        click.echo(f"Generated {len(dataset.rows)} rows into {path.resolve()}")
    else:
        click.echo(dataset.preview(limit=min(rows, 10)))
