import re


def clean_for_tts(value: str) -> str:
    text = value.replace("\ufeff", "")
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
    text = re.sub(r"(?m)^\s{0,3}#{1,6}\s*", "", text)
    text = re.sub(r"(?m)^\s*-{3,}\s*$", "", text)
    text = re.sub(r"(?m)^\s*[-*+]\s+", "", text)
    text = re.sub(r"(?m)^\s*\d+[.)]\s+", "", text)
    text = re.sub(r"[*_`~]{1,3}", "", text)
    text = re.sub(r"(?m)^\s*\[([^\]]+)\]\s*$", r"\1.", text)
    text = text.replace("#", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()
