from pathlib import Path
from wordle.wordle import Game

from fasthtml import common
from fasthtml import live_reload, ft


class GameFH(Game):
    def __init__(self, word, vs_mode=False):
        super().__init__(word=word, vs_mode=vs_mode)
        self.cur_pos = 0

    def get_next_guess(self) -> str:
        pass


game = GameFH("scams")

css = common.StyleX((Path(__file__).parent / "assets/wordle.css").resolve())
app = live_reload.FastHTMLWithLiveReload(hdrs=(css,))


def play_area():
    n_rows = 5
    n_cols = 5
    return ft.Div(
        *[
            ft.Div(*[ft.Div(f"", id="box_{i}{j}", cls="cell") for j in range(n_cols)], id=f"row_{i}", cls="row")
            for i in range(n_rows)
        ],
        cls="board",
    )
    # return ft.Table(
    #    *[
    #        ft.Tr(*[ft.Td(f"{i}_{j}", id="box_{i}{j}", cls="cell") for j in range(n_cols)], id=f"row_{i}", cls="row")
    #        for i in range(n_rows)
    #    ]
    # )


@app.get("/")
def setup():
    return ft.Div(ft.H1("Wordle"), play_area(), cls="container")


common.serve()
