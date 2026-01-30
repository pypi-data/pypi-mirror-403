import os
from pathlib import Path


def load_prompt(name):
    mydirectory = os.path.dirname(os.path.abspath(__file__))
    promptdir = Path(mydirectory) / 'prompts'
    filepath = promptdir / f"{name}.txt"
    with open(filepath) as file:
        content = file.read()
    return content
