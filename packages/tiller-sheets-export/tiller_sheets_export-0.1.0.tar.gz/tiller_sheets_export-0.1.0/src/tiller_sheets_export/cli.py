import logging
from pathlib import Path

import click

from . import TillerData


@click.command()
@click.argument("spreadsheet_url")
@click.option(
    "-o",
    "--output-dir",
    default="data",
    type=click.Path(path_type=Path),
    help="Output directory for data files",
)
def main(spreadsheet_url: str, output_dir: Path):
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    data = TillerData.fetch(spreadsheet_url=spreadsheet_url)

    transactions_path, categories_path = _write_parquet(
        data=data, output_dir=output_dir
    )

    click.echo(f"Created {transactions_path}")
    click.echo(f"Created {categories_path}")


def _write_parquet(data: TillerData, output_dir: Path) -> tuple[Path, Path]:
    processed_dir = output_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    transactions_path = processed_dir / "transactions.parquet"
    categories_path = processed_dir / "categories.parquet"

    data.transactions.to_duckdb().to_parquet(str(transactions_path))
    data.categories.to_duckdb().to_parquet(str(categories_path))

    return transactions_path, categories_path


if __name__ == "__main__":
    main()
