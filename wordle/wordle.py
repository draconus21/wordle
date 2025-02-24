import re
import click
import string
from getpass import getpass
from enum import Enum
from abc import ABC, abstractmethod
import numpy as np
from pydantic import BaseModel, field_validator, ConfigDict, computed_field, ValidationError, ValidationInfo
from typing import List, Dict, Optional, Set


from wordle.prep_data import wordle_len as W_LEN

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

qwerty = ["qwertyuiop", " asdfghjkl", "  zxcvbnm"]


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

    def __len__(self):
        return len(self.word_to_guess)

    def process_guess(self, guess: str):
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


class BetterGuess:
    def __init__(self, dataset, max_wlen=W_LEN):
        self.alphabet = _Alphabet()
        self.max_wlen = max_wlen
        self.dataset = dataset

    def __len__(self):
        return len(self.dataset)

    @property
    def vocab_size(self):
        return len(self.alphabet)

    def make_guess(self):
        return np.random.choice(self.dataset, 1)[0]

    def build_probabilities(self):
        # probability for each position in word
        # max_wlen: 5
        # _, _, _, _, _

        stoi = {l.ltr: i for i, l in enumerate(self.alphabet.letters.values())}
        itos = {i: l.ltr for i, l in enumerate(self.alphabet.letters.values())}

        self.encode = lambda w: [stoi[l] for l in w]  # string -> list of ints
        self.decode = lambda w: "".join([itos[i] for i in w])  # list of ints -> string

        counter = np.zeros([self.max_wlen, self.vocab_size], dtype=np.float32)
        for w in self.dataset:
            _w = self.encode(w)
            for i, c in enumerate(_w):
                counter[i, c] += 1  # c-1 since we are not using <start> and <end>

        probs = counter / np.sum(counter, axis=1, keepdims=True)
        return probs

    def update(self, word: WordleWord):
        self.alphabet = word.alphabet  # update alphabet

        ltrs = "".join([l.ltr for l in self.alphabet.letters.values()])
        reg_str = [f"[{ltrs}]"] * len(word)
        for l in self.alphabet.letters.values():
            if l.status in [Status.IN_POSITION, Status.IN_WORD]:
                for p in l.position:
                    if p > 0:
                        reg_str[p - 1] = l.ltr
                    elif p < 0:
                        reg_str[-p - 1] = reg_str[-p - 1].replace(l.ltr, "")
                    else:
                        raise ValueError(f"Invalid position, {p} for {l}")
        reg_str = "".join(reg_str)
        reg_str = f"^{reg_str}$"

        regex = re.compile(reg_str)
        new_dataset = [w for w in self.dataset if regex.match(w)]
        self.dataset = new_dataset


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
def run():
    """Run the wordle game"""
    w = WordleWord("hello")
    g = BetterGuess(list(valid_words))

    # ge = ["iodal", "benjy", "xerus", "letch", "legge"]
    for i in range(MAX_STEPS):
        cur_guess = g.make_guess()
        w.process_guess(cur_guess)
        g.update(w)
        print(cur_guess, len(g))
