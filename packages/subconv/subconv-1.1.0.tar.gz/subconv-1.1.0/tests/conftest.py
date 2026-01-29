import pytest

from subconv.core.models import SubtitleBlock


@pytest.fixture
def sample_subtitle_block():
    return SubtitleBlock(
        number=1,
        timestamp="00:00:01,000 --> 00:00:04,000",
        text="Hello world",
    )


@pytest.fixture
def sample_subtitle_blocks():
    return [
        SubtitleBlock(
            number=1,
            timestamp="00:00:01,000 --> 00:00:04,000",
            text="Hello world",
        ),
        SubtitleBlock(
            number=2,
            timestamp="00:00:05,000 --> 00:00:08,000",
            text="How are you?",
        ),
        SubtitleBlock(
            number=3,
            timestamp="00:00:09,000 --> 00:00:12,000",
            text="I am fine",
        ),
    ]


@pytest.fixture
def sample_srt_content():
    return """1
00:00:01,000 --> 00:00:04,000
Hello world

2
00:00:05,000 --> 00:00:08,000
How are you?

3
00:00:09,000 --> 00:00:12,000
I am fine"""


@pytest.fixture
def sample_multiline_srt_content():
    return """1
00:00:01,000 --> 00:00:04,000
Hello world
This is a second line

2
00:00:05,000 --> 00:00:08,000
How are you?"""
