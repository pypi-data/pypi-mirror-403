import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from subconv.core.models import SubtitleBlock
from subconv.prompts import PromptConfig
from subconv.translator import (
    TranslatorClient,
    format_blocks_for_prompt,
    parse_translations,
    translate_all,
    translate_batch,
)


@pytest.fixture
def prompt_config():
    return PromptConfig(target_language="Brazilian Portuguese")


@pytest.fixture
def prompt_config_with_source():
    return PromptConfig(target_language="Spanish", source_language="English")


class TestFormatBlocksForPrompt:
    def test_format_single_block(self, sample_subtitle_block):
        result = format_blocks_for_prompt([sample_subtitle_block])

        assert result == "1. Hello world"

    def test_format_multiple_blocks(self, sample_subtitle_blocks):
        result = format_blocks_for_prompt(sample_subtitle_blocks)

        assert "1. Hello world" in result
        assert "2. How are you?" in result
        assert "3. I am fine" in result

    def test_format_empty_list(self):
        result = format_blocks_for_prompt([])

        assert result == ""

    def test_format_preserves_order(self, sample_subtitle_blocks):
        result = format_blocks_for_prompt(sample_subtitle_blocks)
        lines = result.split("\n")

        assert lines[0] == "1. Hello world"
        assert lines[1] == "2. How are you?"
        assert lines[2] == "3. I am fine"


class TestParseTranslations:
    def test_parse_simple_response(self):
        response = """1. Olá mundo
2. Como você está?
3. Estou bem"""

        result = parse_translations(response)

        assert result == {1: "Olá mundo", 2: "Como você está?", 3: "Estou bem"}

    def test_parse_response_with_extra_whitespace(self):
        response = """  1. Olá mundo
  2. Como você está?  """

        result = parse_translations(response)

        assert result[1] == "Olá mundo"
        assert result[2] == "Como você está?"

    def test_parse_response_with_empty_lines(self):
        response = """1. Olá mundo

2. Como você está?

3. Estou bem"""

        result = parse_translations(response)

        assert len(result) == 3

    def test_parse_empty_response(self):
        result = parse_translations("")

        assert result == {}

    def test_parse_response_with_invalid_lines(self):
        response = """1. Olá mundo
invalid line
2. Como você está?"""

        result = parse_translations(response)

        assert len(result) == 2
        assert 1 in result
        assert 2 in result

    def test_parse_response_with_no_valid_lines(self):
        response = """no valid lines here
just some text
nothing numbered"""

        result = parse_translations(response)

        assert result == {}

    def test_parse_response_with_special_characters(self):
        response = """1. <i>Olá</i> mundo!
2. Como você está?"""

        result = parse_translations(response)

        assert result[1] == "<i>Olá</i> mundo!"


@pytest.fixture
def mock_translator_client():
    with patch.object(TranslatorClient, "__init__", lambda self, **kwargs: None):
        client = object.__new__(TranslatorClient)
        client._semaphore = asyncio.Semaphore(5)
        client._client = MagicMock()
        client._model = "gpt-4o-mini"
        return client


class TestTranslatorClient:
    def test_singleton_pattern(self):
        from subconv._metaclasses import SingletonMeta

        SingletonMeta._instances.clear()

        with patch("subconv.translator.AsyncOpenAI"):
            client1 = TranslatorClient(api_key="test")
            client2 = TranslatorClient(api_key="test2")

            assert client1 is client2

        SingletonMeta._instances.clear()

    def test_semaphore_property(self, mock_translator_client):
        semaphore = mock_translator_client.semaphore

        assert isinstance(semaphore, asyncio.Semaphore)

    @pytest.mark.asyncio
    async def test_complete_method(self):
        from subconv._metaclasses import SingletonMeta

        SingletonMeta._instances.clear()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "translated text"

        with patch("subconv.translator.AsyncOpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client

            client = TranslatorClient(api_key="test")
            result = await client.complete("test prompt")

            assert result == "translated text"
            mock_client.chat.completions.create.assert_called_once()

        SingletonMeta._instances.clear()


class TestTranslateBatch:
    @pytest.mark.asyncio
    async def test_translate_batch_success(self, sample_subtitle_blocks, prompt_config):
        from subconv._metaclasses import SingletonMeta

        SingletonMeta._instances.clear()

        mock_response = """1. Olá mundo
2. Como você está?
3. Estou bem"""

        with patch("subconv.translator.AsyncOpenAI"):
            with patch.object(
                TranslatorClient, "complete", new_callable=AsyncMock
            ) as mock_complete:
                mock_complete.return_value = mock_response

                client = TranslatorClient(api_key="test")
                result = await translate_batch(client, sample_subtitle_blocks, prompt_config)

                assert len(result) == 3
                assert result[0].text == "Olá mundo"
                assert result[1].text == "Como você está?"
                assert result[2].text == "Estou bem"

        SingletonMeta._instances.clear()

    @pytest.mark.asyncio
    async def test_translate_batch_preserves_metadata(self, sample_subtitle_blocks, prompt_config):
        from subconv._metaclasses import SingletonMeta

        SingletonMeta._instances.clear()

        mock_response = """1. Olá mundo
2. Como você está?
3. Estou bem"""

        with patch("subconv.translator.AsyncOpenAI"):
            with patch.object(
                TranslatorClient, "complete", new_callable=AsyncMock
            ) as mock_complete:
                mock_complete.return_value = mock_response

                client = TranslatorClient(api_key="test")
                result = await translate_batch(client, sample_subtitle_blocks, prompt_config)

                for i, block in enumerate(result):
                    assert block.number == sample_subtitle_blocks[i].number
                    assert block.timestamp == sample_subtitle_blocks[i].timestamp

        SingletonMeta._instances.clear()

    @pytest.mark.asyncio
    async def test_translate_batch_missing_translation_keeps_original(self, prompt_config):
        from subconv._metaclasses import SingletonMeta

        SingletonMeta._instances.clear()

        blocks = [
            SubtitleBlock(number=1, timestamp="00:00:01,000 --> 00:00:04,000", text="Hello"),
            SubtitleBlock(number=2, timestamp="00:00:05,000 --> 00:00:08,000", text="World"),
        ]

        mock_response = "1. Olá"

        with patch("subconv.translator.AsyncOpenAI"):
            with patch.object(
                TranslatorClient, "complete", new_callable=AsyncMock
            ) as mock_complete:
                mock_complete.return_value = mock_response

                client = TranslatorClient(api_key="test")
                result = await translate_batch(client, blocks, prompt_config)

                assert result[0].text == "Olá"
                assert result[1].text == "World"

        SingletonMeta._instances.clear()

    @pytest.mark.asyncio
    async def test_translate_batch_with_source_language(
        self, sample_subtitle_blocks, prompt_config_with_source
    ):
        from subconv._metaclasses import SingletonMeta

        SingletonMeta._instances.clear()

        mock_response = """1. Hola mundo
2. ¿Cómo estás?
3. Estoy bien"""

        with patch("subconv.translator.AsyncOpenAI"):
            with patch.object(
                TranslatorClient, "complete", new_callable=AsyncMock
            ) as mock_complete:
                mock_complete.return_value = mock_response

                client = TranslatorClient(api_key="test")
                result = await translate_batch(
                    client, sample_subtitle_blocks, prompt_config_with_source
                )

                assert len(result) == 3
                assert result[0].text == "Hola mundo"

        SingletonMeta._instances.clear()


class TestTranslateAll:
    @pytest.mark.asyncio
    async def test_translate_all_single_batch(self, sample_subtitle_blocks, prompt_config):
        from subconv._metaclasses import SingletonMeta

        SingletonMeta._instances.clear()

        mock_response = """1. Olá mundo
2. Como você está?
3. Estou bem"""

        with patch("subconv.translator.AsyncOpenAI"):
            with patch.object(
                TranslatorClient, "complete", new_callable=AsyncMock
            ) as mock_complete:
                mock_complete.return_value = mock_response

                client = TranslatorClient(api_key="test")
                result = await translate_all(
                    sample_subtitle_blocks, client, prompt_config, batch_size=15
                )

                assert len(result) == 3

        SingletonMeta._instances.clear()

    @pytest.mark.asyncio
    async def test_translate_all_multiple_batches(self, prompt_config):
        from subconv._metaclasses import SingletonMeta

        SingletonMeta._instances.clear()

        blocks = [
            SubtitleBlock(
                number=i,
                timestamp=f"00:00:{i:02d},000 --> 00:00:{i + 1:02d},000",
                text=f"Text {i}",
            )
            for i in range(1, 7)
        ]

        with patch("subconv.translator.AsyncOpenAI"):
            with patch.object(
                TranslatorClient, "complete", new_callable=AsyncMock
            ) as mock_complete:
                mock_complete.side_effect = [
                    "1. Texto 1\n2. Texto 2",
                    "3. Texto 3\n4. Texto 4",
                    "5. Texto 5\n6. Texto 6",
                ]

                client = TranslatorClient(api_key="test")
                result = await translate_all(blocks, client, prompt_config, batch_size=2)

                assert len(result) == 6
                assert mock_complete.call_count == 3

        SingletonMeta._instances.clear()

    @pytest.mark.asyncio
    async def test_translate_all_returns_sorted_by_number(self, prompt_config):
        from subconv._metaclasses import SingletonMeta

        SingletonMeta._instances.clear()

        blocks = [
            SubtitleBlock(number=3, timestamp="00:00:09,000 --> 00:00:12,000", text="Third"),
            SubtitleBlock(number=1, timestamp="00:00:01,000 --> 00:00:04,000", text="First"),
            SubtitleBlock(number=2, timestamp="00:00:05,000 --> 00:00:08,000", text="Second"),
        ]

        with patch("subconv.translator.AsyncOpenAI"):
            with patch.object(
                TranslatorClient, "complete", new_callable=AsyncMock
            ) as mock_complete:
                mock_complete.return_value = "3. Terceiro\n1. Primeiro\n2. Segundo"

                client = TranslatorClient(api_key="test")
                result = await translate_all(blocks, client, prompt_config, batch_size=15)

                numbers = [b.number for b in result]
                assert numbers == [1, 2, 3]

        SingletonMeta._instances.clear()

    @pytest.mark.asyncio
    async def test_translate_all_empty_blocks(self, prompt_config):
        from subconv._metaclasses import SingletonMeta

        SingletonMeta._instances.clear()

        with patch("subconv.translator.AsyncOpenAI"):
            client = TranslatorClient(api_key="test")
            result = await translate_all([], client, prompt_config, batch_size=15)

            assert result == []

        SingletonMeta._instances.clear()
