from pathlib import Path
from wordle.wordle import Game

from fasthtml import common
from fasthtml import live_reload, ft


n_rows = 5
n_cols = 5
guesses = [[""] * n_cols] * n_rows


class GameFH(Game):
    def __init__(self, word, vs_mode=False):
        super().__init__(word=word, vs_mode=vs_mode)
        self.cur_row = 0
        self.cur_col = 0

    def get_next_guess(self) -> str:
        pass


game = GameFH("scams")

css = common.StyleX((Path(__file__).parent / "assets/wordle.css").resolve())
app, rt = common.fast_app(hdrs=(css,), live=True)


def play_area():
    global n_rows
    global n_cols
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
        cls="key",
        hx_get=f"/keypress/{key}",
        id=f"key-{key}",
        hx_swap_oob="true",
        target_id="play-area",
        hx_swap="outerHTML",
    )


def keyboard():
    keys = ["qwertyuioq", "asdfghjkl", "zxcvbnm"]
    return ft.Div(
        *[
            ft.Div(
                *[button(k) for k in row],
                cls="keyboard_row",
            )
            for row in keys
        ],
        cls="keyboard",
    )


def home():
    return ft.Div(
        ft.H1("Wordle"),
        play_area(),
        keyboard(),
        cls="container",
    )


@app.get("/keypress/{key}")
def key_pressed(key: str):
    global game
    global guesses
    guesses[game.cur_row][game.cur_col] = key
    game.cur_row += (game.cur_col + 1) // n_cols
    game.cur_col = (game.cur_col + 1) % n_cols
    return button(key), play_area()


@app.get("/")
def setup():
    return home()


common.serve()
