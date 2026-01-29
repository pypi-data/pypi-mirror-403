import asyncio
import os
import re
from itertools import batched

from openai import AsyncOpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from ._decorators import with_semaphore, with_timer
from ._metaclasses import SingletonMeta
from .core.models import SubtitleBlock
from .prompts import PromptConfig, build_translation_prompt

TRANSLATION_PATTERN = re.compile(r"^(\d+)\.\s*(.+)$")


class TranslatorClient(metaclass=SingletonMeta):
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str = "gpt-4o-mini",
        max_concurrent: int = 5,
    ) -> None:
        self._client = AsyncOpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            base_url=base_url or os.getenv("OPENAI_BASE_URL"),
        )
        self._model = model
        self._semaphore = asyncio.Semaphore(max_concurrent)

    @property
    def semaphore(self) -> asyncio.Semaphore:
        return self._semaphore

    async def complete(self, prompt: str) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""


def format_blocks_for_prompt(blocks: list[SubtitleBlock]) -> str:
    return "\n".join(f"{b.number}. {b.text}" for b in blocks)


def parse_translations(response: str) -> dict[int, str]:
    translations: dict[int, str] = {}

    for line in response.strip().split("\n"):
        _line = line.strip()
        if not _line:
            continue

        if match := TRANSLATION_PATTERN.match(_line):
            number, text = match.groups()
            translations[int(number)] = text

    return translations


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
)
async def translate_batch(
    client: TranslatorClient,
    blocks: list[SubtitleBlock],
    prompt_config: PromptConfig,
) -> list[SubtitleBlock]:
    @with_semaphore(client.semaphore)
    async def _translate() -> list[SubtitleBlock]:
        numbered_texts = format_blocks_for_prompt(blocks)
        prompt = build_translation_prompt(numbered_texts, prompt_config)
        response = await client.complete(prompt)
        translations = parse_translations(response)

        return [block.with_text(translations.get(block.number, block.text)) for block in blocks]

    return await _translate()


@with_timer
async def translate_all(
    blocks: list[SubtitleBlock],
    client: TranslatorClient,
    prompt_config: PromptConfig,
    batch_size: int = 15,
) -> list[SubtitleBlock]:
    batches = list(batched(blocks, batch_size))

    tasks = [translate_batch(client, list(batch), prompt_config) for batch in batches]

    results = await asyncio.gather(*tasks)

    translated = [block for batch_result in results for block in batch_result]
    translated.sort(key=lambda b: b.number)

    return translated
