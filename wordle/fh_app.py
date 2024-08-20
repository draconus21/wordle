from pathlib import Path
from wordle.wordle import Game, GameStatus, MAX_STEPS, W_LEN
from pydantic import ValidationError
from typing import List

from fasthtml import common
from fasthtml import ft

import logging

logging.basicConfig(level=logging.INFO)


n_rows = MAX_STEPS
n_cols = W_LEN

guesses = [[(" ", "cell") for i in range(n_cols)] for j in range(n_rows)]
key_colors = {"Enter": "key large", "Delete": "key large"}


class GameFH(Game):
    def __init__(self, word, vs_mode=False):
        super().__init__(word=word, vs_mode=vs_mode)
        self.cur_row = 0
        self.cur_col = 0

    def get_next_guess(self, guesses: List[List[str]]) -> str:
        return "".join([g[0] for g in guesses[self.cur_row]])


game = GameFH(Game.get_random_word())

css = common.StyleX((Path(__file__).parent / "assets/wordle.css").resolve())
app, rt = common.fast_app(hdrs=(css,), live=True)


def msg_area(msg=""):
    return ft.Div(msg, id="msg-area", cls="container containerx", hx_swap_oob="true")


def play_area():
    global n_rows
    global n_cols
    global guesses
    return ft.Div(
        *[
            ft.Div(
                *[ft.Div(guesses[i][j][0], id=f"box_{i}{j}", cls=guesses[i][j][1]) for j in range(n_cols)],
                id=f"row_{i}",
                cls="row",
            )
            for i in range(n_rows)
        ],
        id="play-area",
        cls="container containerx board",
    )


def button(key):
    return ft.Button(
        key,
        cls=key_colors.setdefault(key, "key"),
        hx_get=f"/keypress/{key}",
        id=f"key-{key}",
        hx_swap_oob="true",
        target_id="play-area",
        hx_swap="outerHTML",
    )


def keyboard():
    keys = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
    keys = [[button(k) for k in row] for row in keys]
    keys[2].insert(0, button("Enter"))
    keys[2].append(button("Delete"))

    return ft.Div(
        *[
            ft.Div(
                *row,
                cls="container keyboard row",
            )
            for row in keys
        ],
        cls="container containerx keyboard",
        hx_swap_oob="true",
    )


def home():
    return ft.Title("Wordle", cls="container containerx"), ft.Div(
        ft.H1("Wordle", cls="container containerx"),
        msg_area(),
        play_area(),
        keyboard(),
        cls="container containerx",
    )


@app.get("/keypress/{key}")
def key_pressed(key: str):
    global game
    global guesses
    global key_colors
    error = ""

    if key == "Enter":  # check word
        try:
            guess = game.get_next_guess(guesses)
            game.wordle.current_guess = guess
            game.wordle.guess.append(game.wordle.current_guess)
            # update colors
            for i, k in enumerate(guess):
                match (game.wordle.result[i]):
                    case 0:
                        color = "bad"
                    case 1:
                        color = "pos"
                    case 2:
                        color = "good"
                key_colors[k] = f"key {color}"
                guesses[game.cur_row][i] = (k, f"cell {color}")

            game.cur_row += min(1, n_rows)  # TODO: handle end of game
            game.cur_col = 0

        except ValidationError as e:
            error = f"{e.errors()[-1]['ctx']['error']}. Try again"
            logging.error(error)
    elif key == "Delete":  # delete character
        game.cur_col = max(0, game.cur_col - 1)
        guesses[game.cur_row][game.cur_col] = ("", "cell")
    elif game.cur_col < n_cols:
        guesses[game.cur_row][game.cur_col] = (key, "cell")
        game.cur_col = min(game.cur_col + 1, n_cols)
    else:
        logging.error("out of bounds")

    if game.wordle.game_status == GameStatus.WON:
        error = "You won!"
    elif game.wordle.game_status == GameStatus.LOST:
        error = f"You lost. The word was {game.wordle.word}."
    return button(key), play_area(), msg_area(error), keyboard()


@app.get("/")
def setup():
    return home()


common.serve()
