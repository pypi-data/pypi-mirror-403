from pathlib import Path

import pytest

from subconv.parser import format_srt, parse_srt, read_srt, write_srt


class TestParseSrt:
    def test_parse_simple_srt(self, sample_srt_content):
        blocks = parse_srt(sample_srt_content)

        assert len(blocks) == 3
        assert blocks[0].number == 1
        assert blocks[0].timestamp == "00:00:01,000 --> 00:00:04,000"
        assert blocks[0].text == "Hello world"

    def test_parse_multiline_subtitle(self, sample_multiline_srt_content):
        blocks = parse_srt(sample_multiline_srt_content)

        assert len(blocks) == 2
        assert blocks[0].text == "Hello world This is a second line"

    def test_parse_empty_content(self):
        blocks = parse_srt("")

        assert blocks == []

    def test_parse_whitespace_content(self):
        blocks = parse_srt("   \n\n   ")

        assert blocks == []

    def test_parse_single_block(self):
        content = """1
00:00:01,000 --> 00:00:04,000
Hello world"""

        blocks = parse_srt(content)

        assert len(blocks) == 1
        assert blocks[0].number == 1
        assert blocks[0].text == "Hello world"

    def test_parse_preserves_order(self, sample_srt_content):
        blocks = parse_srt(sample_srt_content)

        numbers = [b.number for b in blocks]
        assert numbers == [1, 2, 3]

    def test_parse_handles_extra_newlines(self):
        content = """1
00:00:01,000 --> 00:00:04,000
Hello world



2
00:00:05,000 --> 00:00:08,000
Goodbye"""

        blocks = parse_srt(content)

        assert len(blocks) == 2

    def test_parse_handles_special_characters(self):
        content = """1
00:00:01,000 --> 00:00:04,000
<i>Hello</i> & "world"

2
00:00:05,000 --> 00:00:08,000
Test's apostrophe"""

        blocks = parse_srt(content)

        assert blocks[0].text == '<i>Hello</i> & "world"'
        assert blocks[1].text == "Test's apostrophe"


class TestFormatSrt:
    def test_format_single_block(self, sample_subtitle_block):
        result = format_srt([sample_subtitle_block])

        expected = "1\n00:00:01,000 --> 00:00:04,000\nHello world"
        assert result == expected

    def test_format_multiple_blocks(self, sample_subtitle_blocks):
        result = format_srt(sample_subtitle_blocks)

        assert "1\n00:00:01,000 --> 00:00:04,000\nHello world" in result
        assert "2\n00:00:05,000 --> 00:00:08,000\nHow are you?" in result
        assert "\n\n" in result

    def test_format_empty_list(self):
        result = format_srt([])

        assert result == ""

    def test_format_blocks_separated_by_double_newline(self, sample_subtitle_blocks):
        result = format_srt(sample_subtitle_blocks)

        parts = result.split("\n\n")
        assert len(parts) == 3


class TestReadSrt:
    def test_read_srt_file(self, tmp_path, sample_srt_content):
        file_path = tmp_path / "test.srt"
        file_path.write_text(sample_srt_content, encoding="utf-8")

        blocks = read_srt(file_path)

        assert len(blocks) == 3
        assert blocks[0].text == "Hello world"

    def test_read_srt_with_string_path(self, tmp_path, sample_srt_content):
        file_path = tmp_path / "test.srt"
        file_path.write_text(sample_srt_content, encoding="utf-8")

        blocks = read_srt(str(file_path))

        assert len(blocks) == 3

    def test_read_srt_with_path_object(self, tmp_path, sample_srt_content):
        file_path = tmp_path / "test.srt"
        file_path.write_text(sample_srt_content, encoding="utf-8")

        blocks = read_srt(Path(file_path))

        assert len(blocks) == 3

    def test_read_nonexistent_file(self, tmp_path):
        file_path = tmp_path / "nonexistent.srt"

        with pytest.raises(FileNotFoundError):
            read_srt(file_path)


class TestWriteSrt:
    def test_write_srt_file(self, tmp_path, sample_subtitle_blocks):
        file_path = tmp_path / "output.srt"

        write_srt(file_path, sample_subtitle_blocks)

        assert file_path.exists()
        content = file_path.read_text(encoding="utf-8")
        assert "Hello world" in content

    def test_write_srt_with_string_path(self, tmp_path, sample_subtitle_blocks):
        file_path = tmp_path / "output.srt"

        write_srt(str(file_path), sample_subtitle_blocks)

        assert file_path.exists()

    def test_write_and_read_roundtrip(self, tmp_path, sample_subtitle_blocks):
        file_path = tmp_path / "roundtrip.srt"

        write_srt(file_path, sample_subtitle_blocks)
        read_blocks = read_srt(file_path)

        assert len(read_blocks) == len(sample_subtitle_blocks)
        for original, read in zip(sample_subtitle_blocks, read_blocks, strict=True):
            assert original.number == read.number
            assert original.timestamp == read.timestamp
            assert original.text == read.text

    def test_write_empty_list(self, tmp_path):
        file_path = tmp_path / "empty.srt"

        write_srt(file_path, [])

        assert file_path.exists()
        assert file_path.read_text() == ""

    def test_write_overwrites_existing_file(self, tmp_path, sample_subtitle_blocks):
        file_path = tmp_path / "overwrite.srt"
        file_path.write_text("old content")

        write_srt(file_path, sample_subtitle_blocks)

        content = file_path.read_text()
        assert "old content" not in content
        assert "Hello world" in content
