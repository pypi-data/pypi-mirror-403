import pytest

from subconv.core.models import SubtitleBlock


class TestSubtitleBlock:
    def test_create_subtitle_block(self):
        block = SubtitleBlock(
            number=1,
            timestamp="00:00:01,000 --> 00:00:04,000",
            text="Hello world",
        )

        assert block.number == 1
        assert block.timestamp == "00:00:01,000 --> 00:00:04,000"
        assert block.text == "Hello world"

    def test_subtitle_block_is_frozen(self, sample_subtitle_block):
        with pytest.raises(AttributeError):
            sample_subtitle_block.text = "New text"

    def test_with_text_returns_new_block(self, sample_subtitle_block):
        new_block = sample_subtitle_block.with_text("New text")

        assert new_block is not sample_subtitle_block
        assert new_block.text == "New text"
        assert new_block.number == sample_subtitle_block.number
        assert new_block.timestamp == sample_subtitle_block.timestamp

    def test_with_text_preserves_original(self, sample_subtitle_block):
        sample_subtitle_block.with_text("New text")

        assert sample_subtitle_block.text == "Hello world"

    def test_to_srt_format(self, sample_subtitle_block):
        result = sample_subtitle_block.to_srt_format()

        expected = "1\n00:00:01,000 --> 00:00:04,000\nHello world"
        assert result == expected

    def test_to_srt_format_with_special_characters(self):
        block = SubtitleBlock(
            number=1,
            timestamp="00:00:01,000 --> 00:00:04,000",
            text="Hello <i>world</i>",
        )

        result = block.to_srt_format()

        assert "<i>world</i>" in result

    def test_equality(self):
        block1 = SubtitleBlock(number=1, timestamp="00:00:01,000 --> 00:00:04,000", text="Hello")
        block2 = SubtitleBlock(number=1, timestamp="00:00:01,000 --> 00:00:04,000", text="Hello")

        assert block1 == block2

    def test_inequality(self):
        block1 = SubtitleBlock(number=1, timestamp="00:00:01,000 --> 00:00:04,000", text="Hello")
        block2 = SubtitleBlock(number=1, timestamp="00:00:01,000 --> 00:00:04,000", text="World")

        assert block1 != block2
