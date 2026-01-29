import pytest

from subconv.prompts import PromptConfig, build_translation_prompt


class TestPromptConfig:
    def test_create_with_target_only(self):
        config = PromptConfig(target_language="Spanish")

        assert config.target_language == "Spanish"
        assert config.source_language is None

    def test_create_with_both_languages(self):
        config = PromptConfig(target_language="Spanish", source_language="English")

        assert config.target_language == "Spanish"
        assert config.source_language == "English"

    def test_format_source_instruction_without_source(self):
        config = PromptConfig(target_language="Spanish")

        result = config.format_source_instruction()

        assert result == ""

    def test_format_source_instruction_with_source(self):
        config = PromptConfig(target_language="Spanish", source_language="English")

        result = config.format_source_instruction()

        assert result == " from English"

    def test_is_frozen(self):
        config = PromptConfig(target_language="Spanish")

        with pytest.raises(AttributeError):
            config.target_language = "French"


class TestBuildTranslationPrompt:
    def test_builds_prompt_with_target_only(self):
        config = PromptConfig(target_language="Spanish")
        numbered_texts = "1. Hello\n2. World"

        result = build_translation_prompt(numbered_texts, config)

        assert "Spanish" in result
        assert "1. Hello" in result
        assert "2. World" in result
        assert "<ROLE>" in result
        assert "<CONTEXT>" in result
        assert "<INSTRUCTIONS>" in result
        assert "<OUTPUT_FORMAT>" in result
        assert "<EXAMPLES>" in result
        assert "<INPUT>" in result

    def test_builds_prompt_with_both_languages(self):
        config = PromptConfig(target_language="Japanese", source_language="English")
        numbered_texts = "1. Hello"

        result = build_translation_prompt(numbered_texts, config)

        assert "Japanese" in result
        assert "from English" in result

    def test_prompt_contains_translation_instructions(self):
        config = PromptConfig(target_language="French")
        numbered_texts = "1. Test"

        result = build_translation_prompt(numbered_texts, config)

        assert "preserving its number" in result
        assert "natural and conversational" in result
        assert "tone, emotion, and intent" in result

    def test_prompt_contains_output_format(self):
        config = PromptConfig(target_language="German")
        numbered_texts = "1. Test"

        result = build_translation_prompt(numbered_texts, config)

        assert "[number]. [translated text]" in result
        assert "Do not include explanations" in result

    def test_prompt_without_source_has_no_from(self):
        config = PromptConfig(target_language="German")
        numbered_texts = "1. Test"

        result = build_translation_prompt(numbered_texts, config)

        assert "from German" not in result

    def test_empty_numbered_texts(self):
        config = PromptConfig(target_language="Italian")

        result = build_translation_prompt("", config)

        assert "Italian" in result
        assert "<INPUT>" in result

    def test_prompt_has_examples_section(self):
        config = PromptConfig(target_language="Portuguese")
        numbered_texts = "1. Test"

        result = build_translation_prompt(numbered_texts, config)

        assert "Hello, how are you?" in result
        assert "I'm fine, thanks!" in result

    def test_prompt_emphasizes_subtitle_context(self):
        config = PromptConfig(target_language="Korean")
        numbered_texts = "1. Test"

        result = build_translation_prompt(numbered_texts, config)

        assert "subtitle" in result.lower()
        assert "concise" in result
