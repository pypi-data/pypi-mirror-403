import re

def to_snake_case(text: str) -> str:
    text = re.sub(r'(?<!^)(?=[A-Z])', '_', text)
    text = text.lower().replace(' ', '_')
    # Remove consecutive underscores
    return re.sub(r'_+', '_', text)


def to_pascal_case(text: str) -> str:
    words = text.replace('-', ' ').replace('_', ' ').split()
    return ''.join(word.capitalize() for word in words)
