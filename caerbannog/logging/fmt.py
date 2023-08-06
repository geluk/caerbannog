from .ansi import *


def target(content: str) -> str:
    if content == "":
        content = "''"
    return f"{FG_CYAN_BOLD}{content}{RESET}"


def subject(content: str) -> str:
    if content == "":
        content = "''"
    return f"{FG_BLUE}{content}{FG_RESET}"


def code(content: str) -> str:
    if content == "":
        content = "''"
    return f"{FG_BRIGHT_BLACK}{content}{FG_RESET}"
