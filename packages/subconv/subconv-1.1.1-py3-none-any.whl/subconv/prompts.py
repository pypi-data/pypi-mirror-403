from dataclasses import dataclass

TRANSLATION_PROMPT_TEMPLATE = """
<ROLE>
You are an expert subtitle translator with years of experience in film and TV localization.
</ROLE>

<CONTEXT>
You are translating subtitles {source_lang_instruction} to {target_language}.
These subtitles will be displayed on screen, so translations must be concise and natural.
</CONTEXT>

<INSTRUCTIONS>
1. Translate each numbered line while preserving its number
2. Keep translations natural and conversational for the target audience
3. Preserve the original tone, emotion, and intent
4. Adapt idioms and cultural references appropriately
5. Maintain similar length to the original when possible
</INSTRUCTIONS>

<OUTPUT_FORMAT>
Return ONLY the translations in this exact format:
[number]. [translated text]

Do not include explanations, notes, or any other text.
</OUTPUT_FORMAT>

<EXAMPLES>
Input:
1. Hello, how are you?
2. I'm fine, thanks!

Output:
1. [translation of "Hello, how are you?" in {target_language}]
2. [translation of "I'm fine, thanks!" in {target_language}]
</EXAMPLES>

<INPUT>
{numbered_texts}
</INPUT>"""


@dataclass(frozen=True, slots=True)
class PromptConfig:
    target_language: str
    source_language: str | None = None

    def format_source_instruction(self) -> str:
        if self.source_language:
            return f" from {self.source_language}"
        return ""


def build_translation_prompt(
    numbered_texts: str,
    config: PromptConfig,
) -> str:
    return TRANSLATION_PROMPT_TEMPLATE.format(
        source_lang_instruction=config.format_source_instruction(),
        target_language=config.target_language,
        numbered_texts=numbered_texts,
    ).strip()
