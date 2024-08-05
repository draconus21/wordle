from pathlib import Path
from wordle.wordle import Game
from pydantic import ValidationError
from typing import List

from fasthtml import common
from fasthtml import ft

import logging

logging.basicConfig(level=logging.INFO)


n_rows = 5
n_cols = 5
guesses = [[" " for i in range(n_cols)] for j in range(n_rows)]


class GameFH(Game):
    def __init__(self, word, vs_mode=False):
        super().__init__(word=word, vs_mode=vs_mode)
        self.cur_row = 0
        self.cur_col = 0

    def get_next_guess(self, guesses: List[List[str]]) -> str:
        return "".join(guesses[self.cur_row])


game = GameFH("scams")

css = common.StyleX((Path(__file__).parent / "assets/wordle.css").resolve())
app, rt = common.fast_app(hdrs=(css,), live=True)


def msg_area(msg=""):
    return ft.Div(msg, id="msg-area", cls="message", hx_swap_oob="true")


def play_area():
    global n_rows
    global n_cols
    global guesses
    return ft.Div(
        *[
            ft.Div(
                *[ft.Div(guesses[i][j], id=f"box_{i}{j}", cls="cell") for j in range(n_cols)],
                id=f"row_{i}",
                cls="row",
            )
            for i in range(n_rows)
        ],
        id="play-area",
        cls="board",
    )


def button(key):
    return ft.Button(
        key,
        cls="key" if len(key) == 1 else "key large",
        hx_get=f"/keypress/{key}",
        id=f"key-{key}",
        hx_swap_oob="true",
        target_id="play-area",
        hx_swap="outerHTML",
    )


def keyboard():
    keys = ["qwertyuioq", "asdfghjkl", "zxcvbnm"]
    board_keys = [
        ft.Div(
            *[button(k) for k in row],
            cls="keyboard_row",
        )
        for row in keys
    ]
    board_keys.extend([ft.Div(button("Enter"), button("Delete"))])
    return ft.Div(
        *board_keys,
        cls="keyboard",
    )


def home():
    return ft.Div(
        ft.H1("Wordle"),
        msg_area(),
        play_area(),
        keyboard(),
        cls="container",
    )


@app.get("/keypress/{key}")
def key_pressed(key: str):
    global game
    global guesses
    error = ""

    if key == "Enter":  # check word
        try:
            guess = game.get_next_guess(guesses)
            game.wordle.current_guess = guess
            game.wordle.guess.append(game.wordle.current_guess)
            game.cur_row += min(1, n_rows)  # TODO: handle end of game
            game.cur_col = 0
        except ValidationError as e:
            error = f"{guess} is not a valid guess [{e.errors()[-1]['ctx']['error']}]. Try again"
            logging.error(error)
    elif key == "Delete":  # delete character
        game.cur_col = max(0, game.cur_col - 1)
        guesses[game.cur_row][game.cur_col] = ""
    else:
        guesses[game.cur_row][game.cur_col] = key
        game.cur_col = min(game.cur_col + 1, n_cols)
    logging.info(f"{game.cur_row}: {game.cur_col}")
    return button(key), play_area(), msg_area(error)


@app.get("/")
def setup():
    return home()


common.serve()
