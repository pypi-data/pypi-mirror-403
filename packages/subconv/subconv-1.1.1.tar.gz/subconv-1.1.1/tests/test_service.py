from unittest.mock import AsyncMock, patch

import pytest

from subconv.core.models import SubtitleBlock
from subconv.service import TranslationConfig, TranslationService


class TestTranslationConfig:
    def test_create_config_with_defaults(self, tmp_path):
        input_path = tmp_path / "input.srt"
        output_path = tmp_path / "output.srt"

        config = TranslationConfig(
            input_path=input_path,
            output_path=output_path,
        )

        assert config.input_path == input_path
        assert config.output_path == output_path
        assert config.target_language == "Brazilian Portuguese"
        assert config.source_language is None
        assert config.api_key is None
        assert config.model == "gpt-4o-mini"
        assert config.max_concurrent == 5
        assert config.batch_size == 15

    def test_create_config_with_custom_values(self, tmp_path):
        input_path = tmp_path / "input.srt"
        output_path = tmp_path / "output.srt"

        config = TranslationConfig(
            input_path=input_path,
            output_path=output_path,
            target_language="Spanish",
            source_language="English",
            api_key="custom-key",
            model="gpt-4",
            max_concurrent=10,
            batch_size=20,
        )

        assert config.target_language == "Spanish"
        assert config.source_language == "English"
        assert config.api_key == "custom-key"
        assert config.model == "gpt-4"
        assert config.max_concurrent == 10
        assert config.batch_size == 20

    def test_create_config_with_only_target_language(self, tmp_path):
        input_path = tmp_path / "input.srt"
        output_path = tmp_path / "output.srt"

        config = TranslationConfig(
            input_path=input_path,
            output_path=output_path,
            target_language="Japanese",
        )

        assert config.target_language == "Japanese"
        assert config.source_language is None


class TestTranslationService:
    @pytest.fixture
    def sample_config(self, tmp_path, sample_srt_content):
        input_path = tmp_path / "input.srt"
        output_path = tmp_path / "output.srt"
        input_path.write_text(sample_srt_content, encoding="utf-8")

        return TranslationConfig(
            input_path=input_path,
            output_path=output_path,
            api_key="test-key",
        )

    @pytest.fixture
    def sample_config_with_languages(self, tmp_path, sample_srt_content):
        input_path = tmp_path / "input.srt"
        output_path = tmp_path / "output.srt"
        input_path.write_text(sample_srt_content, encoding="utf-8")

        return TranslationConfig(
            input_path=input_path,
            output_path=output_path,
            target_language="Spanish",
            source_language="English",
            api_key="test-key",
        )

    def test_service_initialization(self, sample_config):
        from subconv._metaclasses import SingletonMeta

        SingletonMeta._instances.clear()

        with patch("subconv.translator.AsyncOpenAI"):
            service = TranslationService(sample_config)

            assert service._config is sample_config
            assert service._prompt_config.target_language == "Brazilian Portuguese"
            assert service._prompt_config.source_language is None

        SingletonMeta._instances.clear()

    def test_service_initialization_with_languages(self, sample_config_with_languages):
        from subconv._metaclasses import SingletonMeta

        SingletonMeta._instances.clear()

        with patch("subconv.translator.AsyncOpenAI"):
            service = TranslationService(sample_config_with_languages)

            assert service._prompt_config.target_language == "Spanish"
            assert service._prompt_config.source_language == "English"

        SingletonMeta._instances.clear()

    @pytest.mark.asyncio
    async def test_service_run_creates_output_file(self, sample_config):
        from subconv._metaclasses import SingletonMeta

        SingletonMeta._instances.clear()

        translated_blocks = [
            SubtitleBlock(number=1, timestamp="00:00:01,000 --> 00:00:04,000", text="Olá mundo"),
            SubtitleBlock(
                number=2, timestamp="00:00:05,000 --> 00:00:08,000", text="Como você está?"
            ),
            SubtitleBlock(number=3, timestamp="00:00:09,000 --> 00:00:12,000", text="Estou bem"),
        ]

        with patch("subconv.translator.AsyncOpenAI"):
            with patch("subconv.service.translate_all", new_callable=AsyncMock) as mock_translate:
                mock_translate.return_value = translated_blocks

                service = TranslationService(sample_config)
                await service.run()

                assert sample_config.output_path.exists()
                content = sample_config.output_path.read_text()
                assert "Olá mundo" in content

        SingletonMeta._instances.clear()

    @pytest.mark.asyncio
    async def test_service_run_calls_translate_all_with_correct_params(self, sample_config):
        from subconv._metaclasses import SingletonMeta

        SingletonMeta._instances.clear()

        with patch("subconv.translator.AsyncOpenAI"):
            with patch("subconv.service.translate_all", new_callable=AsyncMock) as mock_translate:
                mock_translate.return_value = []

                service = TranslationService(sample_config)
                await service.run()

                mock_translate.assert_called_once()
                call_kwargs = mock_translate.call_args[1]
                assert call_kwargs["batch_size"] == sample_config.batch_size
                assert call_kwargs["prompt_config"].target_language == "Brazilian Portuguese"

        SingletonMeta._instances.clear()

    @pytest.mark.asyncio
    async def test_service_run_reads_input_file(self, sample_config, sample_subtitle_blocks):
        from subconv._metaclasses import SingletonMeta

        SingletonMeta._instances.clear()

        with patch("subconv.translator.AsyncOpenAI"):
            with patch("subconv.service.translate_all", new_callable=AsyncMock) as mock_translate:
                mock_translate.return_value = sample_subtitle_blocks

                service = TranslationService(sample_config)
                await service.run()

                call_kwargs = mock_translate.call_args[1]
                blocks = call_kwargs["blocks"]
                assert len(blocks) == 3
                assert blocks[0].text == "Hello world"

        SingletonMeta._instances.clear()

    @pytest.mark.asyncio
    async def test_service_run_with_source_language(self, sample_config_with_languages):
        from subconv._metaclasses import SingletonMeta

        SingletonMeta._instances.clear()

        with patch("subconv.translator.AsyncOpenAI"):
            with patch("subconv.service.translate_all", new_callable=AsyncMock) as mock_translate:
                mock_translate.return_value = []

                service = TranslationService(sample_config_with_languages)
                await service.run()

                call_kwargs = mock_translate.call_args[1]
                assert call_kwargs["prompt_config"].target_language == "Spanish"
                assert call_kwargs["prompt_config"].source_language == "English"

        SingletonMeta._instances.clear()
