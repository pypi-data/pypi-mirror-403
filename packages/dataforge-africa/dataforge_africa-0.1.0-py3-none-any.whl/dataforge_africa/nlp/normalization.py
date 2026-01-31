def normalize_sepedi(text: str) -> str:
    text = text.lower()
    text = text.replace("š", "s")
    text = text.replace("?", "")
    text = text.replace("!", "")
    return text.strip()
