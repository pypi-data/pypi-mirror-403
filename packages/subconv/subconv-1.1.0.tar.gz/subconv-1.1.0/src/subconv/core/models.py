from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class SubtitleBlock:
    number: int
    timestamp: str
    text: str

    def with_text(self, new_text: str) -> "SubtitleBlock":
        return SubtitleBlock(
            number=self.number,
            timestamp=self.timestamp,
            text=new_text,
        )

    def to_srt_format(self) -> str:
        return f"{self.number}\n{self.timestamp}\n{self.text}"
