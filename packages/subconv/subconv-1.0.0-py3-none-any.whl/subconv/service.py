from dataclasses import dataclass
from pathlib import Path

from loguru import logger

from ._decorators import with_timer
from .parser import read_srt, write_srt
from .translator import TranslatorClient, translate_all


@dataclass(slots=True)
class TranslationConfig:
    input_path: Path
    output_path: Path
    api_key: str | None = None
    model: str = "gpt-4o-mini"
    max_concurrent: int = 5
    batch_size: int = 15


class TranslationService:
    def __init__(self, config: TranslationConfig) -> None:
        self._config = config
        self._client = TranslatorClient(
            api_key=config.api_key,
            model=config.model,
            max_concurrent=config.max_concurrent,
        )

    @with_timer
    async def run(self) -> None:
        logger.info(f"Reading: {self._config.input_path}")
        blocks = read_srt(self._config.input_path)
        logger.info(f"Found {len(blocks)} subtitle blocks")

        translated = await translate_all(
            blocks=blocks,
            client=self._client,
            batch_size=self._config.batch_size,
        )

        write_srt(self._config.output_path, translated)
        logger.info(f"Saved: {self._config.output_path}")
