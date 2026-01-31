from collections.abc import Callable
from typing import Any, cast

import questionary
import typer
from questionary import Choice


def choose(title: str, choices: list[Choice] | list[str]) -> Any:
    """Interactively select one of the choices exiting the process if ctrl-c is pressed."""
    if choices and isinstance(choices[0], Choice):
        for choice in choices:
            assert isinstance(choice, Choice)
            choice.value = (choice.value,)
    else:
        choices = cast(list[str], choices)
        choices = [Choice(choice, value=(choice,)) for choice in choices]

    maybe_selection = questionary.select(title, choices=choices).ask()
    if maybe_selection is None:
        raise typer.Exit(2)
    return maybe_selection[0]


def input_text(message: str, validate: Callable[[str], bool | str]) -> str:
    """Interactively receive string input which passes the validation exiting the process if ctrl-c is pressed."""
    maybe_text = questionary.text(message, validate=validate).ask()
    if maybe_text is None:
        raise typer.Exit(2)
    return maybe_text[0]
