from enum import Enum
from abc import ABC, abstractmethod
import numpy as np
from pydantic import BaseModel, field_validator, ConfigDict, computed_field, ValidationError
from typing import List, Optional


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


def validated_word(word: str) -> str:
    assert len(word) == W_LEN, f"Must be a {W_LEN}-letter word"
    _word = word.lower()
    assert _word in valid_words, f"{word} is not a valid word"
    return _word


class WordleWord(BaseModel):
    model_config: ConfigDict = ConfigDict(extra="forbid", validate_assignment=True)
    guess: List[str] = []
    current_guess: Optional[str] = None
    word: str

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

        _last_guess = self.current_guess
        assert len(_last_guess) == W_LEN, f"Expecting {W_LEN}, but got {len(_last_guess)}"
        return [
            2 if _last_guess[i] == self.word[i] else (1 if _last_guess[i] in self.word else 0) for i in range(W_LEN)
        ]

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
        ]
        if self.guess:
            msg.append(f"Last guess:\n{self.current_guess}")
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

        return [validated_word(v) for v in val]

    @field_validator("current_guess")
    def v_current(cls, val):
        if val is None:
            return val
        return validated_word(val)

    @field_validator("word")
    def v_word(cls, val):
        return validated_word(val)


class Game(ABC):
    def __init__(self, word):
        self.wordle = WordleWord(word=word)

    @abstractmethod
    def get_next_guess(self) -> str:
        pass

    def play(self):
        while not self.wordle.game_ended:
            next_guess = self.get_next_guess()
            try:
                self.wordle.current_guess = next_guess
                self.wordle.guess.append(next_guess)
            except ValidationError as e:
                print(f"Not a valid guess [{e.errors()[-1]['ctx']['error']}]. Try again")
        print(self.wordle.game_status)


class GameHuman(Game):
    def get_next_guess(self) -> str:
        return input(self.wordle.printed_res)


if __name__ == "__main__":
    w = GameHuman(word="hello")
    w.play()
