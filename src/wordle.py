import string
from getpass import getpass
from enum import Enum
from abc import ABC, abstractmethod
import numpy as np
from pydantic import BaseModel, field_validator, ConfigDict, computed_field, ValidationError
from typing import List, Optional, Set


from prep_data import wordle_len as W_LEN

MAX_STEPS = 5


class GameStatus(Enum):
    WON = "won"
    LOST = "lost"
    IN_PROGRESS = "in progress"


def get_data():
    import json
    from prep_data import wordle_data_file

    with open(wordle_data_file, "r") as f:
        data = json.load(f)
    assert len(data) > 0
    return set(data.keys())


valid_words = get_data()


class WordleWord(BaseModel):
    model_config: ConfigDict = ConfigDict(extra="forbid", validate_assignment=True)
    guess: List[str] = []
    word: str
    current_guess: Optional[str] = None
    _possible_letters: Set[str] = {l for l in string.ascii_lowercase}
    _not_in_word: Set[str] = set()
    _result: List[List[int]] = list()

    @computed_field
    @property
    def result(self) -> List[int]:
        """
        checks guess against word
        0 -> letter not in word
        1 -> letter in word, but incorrect pos
        2 -> letter in word, AND in currect pos
        """

        if self.current_guess is None:
            return [0] * W_LEN
        if len(self._result) == len(self.guess):  # no need to update result (invalid input)
            return self._result[-1]

        _last_guess = self.guess[-1]
        assert len(_last_guess) == W_LEN, f"Expecting {W_LEN}, but got {len(_last_guess)}"
        res = [2 if _last_guess[i] == self.word[i] else (1 if _last_guess[i] in self.word else 0) for i in range(W_LEN)]

        # update _possible_letters, and _not_in_word
        to_remove = {
            _last_guess[i] for i, r in enumerate(res) if res[i] == 0 and _last_guess[i] in self._possible_letters
        }
        for l in to_remove:
            self._not_in_word.add(l)
            self._possible_letters.remove(l)

        self._result.append(res)
        return self._result[-1]

    @computed_field
    @property
    def game_status(self) -> GameStatus:
        if self.result == [2] * W_LEN:
            return GameStatus.WON

        if len(self.guess) >= MAX_STEPS:
            return GameStatus.LOST

        return GameStatus.IN_PROGRESS

    @computed_field
    @property
    def game_ended(self) -> bool:
        return self.game_status != GameStatus.IN_PROGRESS

    @computed_field
    @property
    def printed_res(self) -> str:
        msg = [
            "**" * 10,
            "0 -> letter not in word",
            "1 -> letter in word, but wrong pos",
            "2 -> letter in correct pos",
            f"{MAX_STEPS-len(self.guess)} tries left",
            f"letters not in word: {' '.join(sorted(self._not_in_word))}",
            f"letters left to use: {' '.join(sorted(self._possible_letters))}",
        ]
        if self.guess:
            msg.append(f"Previous valid guesses:")
            msg.append(" | ".join(self.guess))
            msg.append(" | ".join(["".join(str(i) for i in res) for res in self._result]))
            # msg.append("".join([str(i) for i in self.result]))
        msg.append("**" * 10)
        if len(self.guess) < MAX_STEPS:
            msg.append("Your next guess: ")
        return "\n".join(msg)

    @field_validator("guess")
    def v_guess(cls, val):
        if len(val) == 0:  # no gueses yet
            return val
        assert len(val) <= MAX_STEPS, f"Out of tries"

        return [validated_word(v) for v in val]

    @field_validator("current_guess")
    def v_current(cls, val):
        if val is None:
            return val
        return validated_word(val)

    @field_validator("word")
    def v_word(cls, val):
        return validated_word(val)


def validated_word(word: str) -> str:
    assert len(word) == W_LEN, f"Must be a {W_LEN}-letter word"
    _word = word.lower()
    assert _word in valid_words, f"{word} is not a valid word"
    return _word


class Game(ABC):
    def __init__(self, word):
        self.wordle = WordleWord(word=word)

    @abstractmethod
    def get_next_guess(self) -> str:
        pass

    def play(self):
        updated = False
        while not updated:
            try:
                # self.wordle.word = getpass("What's your word: ")
                self.wordle.word = list(valid_words)[np.random.randint(0, len(valid_words))]
                updated = True
            except ValidationError as e:
                print(f"Not a valid word[{e.errors()[-1]['ctx']['error']}]. Try again")

        while not self.wordle.game_ended:
            next_guess = self.get_next_guess()
            try:
                self.wordle.current_guess = next_guess
                self.wordle.guess.append(next_guess)
            except ValidationError as e:
                print(f"Not a valid guess [{e.errors()[-1]['ctx']['error']}]. Try again")
        print(f"{self.wordle.game_status}, word to guess: {self.wordle.word}")


class GameHuman(Game):
    def get_next_guess(self) -> str:
        return input(self.wordle.printed_res)


class GameAI(Game):
    def __init__(self, word):
        super().__init__(word=word)
        self._valid_words = []
        self.reset()  # sets _valid words

    def reset(self):
        self._valid_words = list(valid_words)
        np.random.shuffle(self._valid_words)

    def reduce_2(self):
        _cur_guess = self.wordle.current_guess
        _cur_res = self.wordle.result  # current result

        _cur_bow = self._valid_words

        remove = {w for w in _cur_bow if any([w[i] != l for i, l in enumerate(_cur_guess) if _cur_res[i] == 2])}
        _cur_bow = list(set(_cur_bow) - remove)

        print(f"red 2: {len(self._valid_words)} -> {len(_cur_bow)}")
        self._valid_words = _cur_bow

        ## PARANOIA
        for w in self._valid_words:
            assert all(w[i] == l for i, l in enumerate(_cur_guess) if _cur_res[i] == 2)

    def reduce_1(self):
        _cur_guess = self.wordle.current_guess
        _cur_res = self.wordle.result  # current result
        _cur_bow = self._valid_words

        _letters = self.wordle._possible_letters
        _iletters = set(string.ascii_lowercase) - self.wordle._possible_letters

        # ensure that at least one occurance of letters w/ result=1 exists
        _cur_bow = {w for w in _cur_bow if all([l in w for i, l in enumerate(_cur_guess) if _cur_res[i] == 1])}

        # remove words w/ invalidated letters
        remove = {w for w in _cur_bow if any(l in w for l in _iletters)}

        # remove words w/ invalid positions
        remove.update({w for w in _cur_bow if any([w[i] == l for i, l in enumerate(_cur_guess) if _cur_res[i] == 1])})

        _cur_bow = list(set(_cur_bow) - remove)

        print(f"red 1: {len(self._valid_words)} -> {len(_cur_bow)}")
        self._valid_words = _cur_bow

    def get_next_guess(self) -> str:
        _guesses = self.wordle.guess
        _results = np.array(self.wordle._result)
        if len(_results) == 0:
            _nxt = self._valid_words[np.random.randint(0, len(self._valid_words))]
            print(f"Next: {_nxt}")
            return _nxt

        letters = {l: 1.0 for l in self.wordle._possible_letters}

        candidate = [""] * W_LEN

        self.reduce_2()
        self.reduce_1()

        _nxt = self._valid_words[np.random.randint(0, len(self._valid_words))]
        print(f"Next: {_nxt}")
        input(self.wordle.printed_res)
        return _nxt


if __name__ == "__main__":
    w = GameAI(word="hello")
    w.play()
