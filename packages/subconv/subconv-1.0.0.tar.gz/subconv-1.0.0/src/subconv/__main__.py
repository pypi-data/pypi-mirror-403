import asyncio
from pathlib import Path

import click
from dotenv import load_dotenv

from subconv import TranslationConfig, TranslationService

load_dotenv()


@click.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.argument("output_file", type=click.Path(path_type=Path))
@click.option(
    "--model",
    "-m",
    default="gpt-4o-mini",
    help="OpenAI model to use",
)
@click.option(
    "--concurrent",
    "-c",
    default=5,
    type=int,
    help="Maximum concurrent API requests",
)
@click.option(
    "--batch-size",
    "-b",
    default=15,
    type=int,
    help="Number of subtitles per batch",
)
def main(
    input_file: Path,
    output_file: Path,
    model: str,
    concurrent: int,
    batch_size: int,
) -> None:
    config = TranslationConfig(
        input_path=input_file,
        output_path=output_file,
        model=model,
        max_concurrent=concurrent,
        batch_size=batch_size,
    )

    service = TranslationService(config)
    asyncio.run(service.run())


if __name__ == "__main__":
    main()
