from dataclasses import dataclass
from pathlib import Path

from loguru import logger

from ._decorators import with_timer
from .parser import read_srt, write_srt
from .prompts import PromptConfig
from .translator import TranslatorClient, translate_all


@dataclass(slots=True)
class TranslationConfig:
    input_path: Path
    output_path: Path
    target_language: str = "Brazilian Portuguese"
    source_language: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    model: str = "gpt-4o-mini"
    max_concurrent: int = 5
    batch_size: int = 15


class TranslationService:
    def __init__(self, config: TranslationConfig) -> None:
        self._config = config
        self._client = TranslatorClient(
            api_key=config.api_key,
            base_url=config.base_url,
            model=config.model,
            max_concurrent=config.max_concurrent,
        )
        self._prompt_config = PromptConfig(
            target_language=config.target_language,
            source_language=config.source_language,
        )

    @with_timer
    async def run(self) -> None:
        logger.info(f"Reading: {self._config.input_path}")
        blocks = read_srt(self._config.input_path)
        logger.info(f"Found {len(blocks)} subtitle blocks")

        source = self._config.source_language
        source_info = f" from {source}" if source else ""
        logger.info(f"Translating{source_info} to {self._config.target_language}")

        translated = await translate_all(
            blocks=blocks,
            client=self._client,
            prompt_config=self._prompt_config,
            batch_size=self._config.batch_size,
        )

        write_srt(self._config.output_path, translated)
        logger.info(f"Saved: {self._config.output_path}")
