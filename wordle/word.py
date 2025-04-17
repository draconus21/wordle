import string
from enum import Enum
from pydantic import BaseModel, ConfigDict
from typing import List, Dict

from wordle.prep_data import wordle_len

W_LEN = wordle_len
MAX_STEPS = 6


class GameStatus(Enum):
    WON = "won"
    LOST = "lost"
    IN_PROGRESS = "in progress"


def get_data():
    import json
    from wordle.prep_data import wordle_data_file

    with open(wordle_data_file, "r") as f:
        data = json.load(f)
    assert len(data) > 0
    return set(data.keys())


valid_words = get_data()


class Status(Enum):
    NOT_GUESSED = 0
    IN_WORD = 1
    IN_POSITION = 2


class _Letter(BaseModel):
    model_config: ConfigDict = ConfigDict(extra="forbid", validate_assignment=True)
    ltr: str
    status: Status = Status.NOT_GUESSED
    position: List[int] = []


class _Alphabet(BaseModel):
    letters: Dict[str, _Letter] = {l: _Letter(ltr=l) for l in string.ascii_lowercase}

    def __len__(self):
        return len(self.letters)


class WordleWord:
    def __init__(self, word_to_guess: str):
        self.word_to_guess = word_to_guess
        self.alphabet = _Alphabet()
        self.game_status = GameStatus.IN_PROGRESS

    def __len__(self):
        return len(self.word_to_guess)

    def process_guess(self, guess: str):
        if guess == self.word_to_guess:
            self.game_status = GameStatus.WON
            return

        for i, l in enumerate(guess):
            if l == self.word_to_guess[i]:
                if (i + 1) not in self.alphabet.letters[l].position:
                    self.alphabet.letters[l].position.append(i + 1)
                    self.alphabet.letters[l].status = Status.IN_POSITION
            elif l in self.word_to_guess:
                if -(i + 1) not in self.alphabet.letters[l].position:
                    self.alphabet.letters[l].position.append(-(i + 1))
                    self.alphabet.letters[l].status = Status.IN_WORD
            elif l in self.alphabet.letters:
                del self.alphabet.letters[l]

    @property
    def current_word(self):
        w = ["_"] * len(self.word_to_guess)
        for l in [l for l in self.alphabet.letters.values() if l.status == Status.IN_POSITION]:
            for p in l.position:
                if p > 0:
                    w[p - 1] = l.ltr
        return "".join(w)
