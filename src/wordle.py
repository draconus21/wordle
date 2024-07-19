from enum import Enum
import numpy as np
from abc import ABC, abstractmethod
from pydantic import BaseModel, field_validator, ConfigDict, computed_field, ValidationError
from typing import List


from prep_data import wordle_len as W_LEN

MAX_STEPS = 5


class GameStatus(Enum):
    WON = "won"
    LOST = "lost"
    IN_PROGRESS = "in progress"


class WordleWord(ABC, BaseModel):
    model_config: ConfigDict = ConfigDict(extra="forbid", validate_assignment=True)
    guess: List[str] = []
    word: str

    @computed_field
    @property
    def next_valid_guess(self) -> str:
        try:
            self.guess.append(self.next_guess)
            return self.guess[-1]
        except ValidationError as e:
            print("Not a valid guess. Try again")
            return self.next_valid_guess

    @computed_field
    @property
    @abstractmethod
    def next_guess(self) -> str:
        pass

    @computed_field
    @property
    def result(self) -> List[int]:
        """
        checks guess against word
        0 -> letter not in word
        1 -> letter in word, but incorrect pos
        2 -> letter in word, AND in currect pos
        """

        if not self.guess:
            return [0] * W_LEN

        _last_guess = self.guess[-1]
        assert len(_last_guess) == W_LEN, f"Expecting {W_LEN}, but got {len(_last_guess)}"
        return [
            2 if _last_guess[i] == self.word[i] else (1 if _last_guess[i] in self.word else 0) for i in range(W_LEN)
        ]

    @computed_field
    @property
    def game_status(self) -> GameStatus:
        if self.result == [2] * W_LEN:
            GameStatus.WON

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
        ]
        if self.guess:
            msg.append(f"Last guess:\n{self.guess[-1]}")
            msg.append("".join([str(i) for i in self.result]))
        msg.append("**" * 10)
        if len(self.guess) < MAX_STEPS:
            msg.append("Your next guess: ")
        return "\n".join(msg)

    @field_validator("guess")
    def v_guess(cls, val):
        if len(val) == 0:  # no gueses yet
            return val
        assert len(val) <= MAX_STEPS, f"Out of tries"
        assert all([len(v) == W_LEN for v in val]), f"Must be a list of {W_LEN}-letter words"
        # TODO: check if val in valid_words
        return [v.lower() for v in val]

    @field_validator("word")
    def v_word(cls, val):
        assert len(val) == W_LEN
        # TODO: check if val in valid_words
        return val.lower()


class WordleHuman(WordleWord):
    def next_guess(self) -> str:
        return input(self.printed_res)


class Game:
    def __init__(self, word):
        self.wordle = WordleHuman(word=word)

    def play_usr(self):
        while not self.wordle.game_ended:
            self.wordle.next_valid_guess
        print(self.wordle.game_status)


def get_data():
    import json
    from prep_data import wordle_data_file

    with open(wordle_data_file, "r") as f:
        data = json.load(f)
    assert len(data) > 0
    return set(data.keys())


if __name__ == "__main__":
    w = Game(word="hello")
    w.play_usr()
