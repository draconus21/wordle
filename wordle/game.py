from wordle.guesser.base import Guesser
from wordle.word import WordleWord, GameStatus
from abc import ABC

qwerty = ["qwertyuiop", " asdfghjkl", "  zxcvbnm"]


class Game(ABC):
    def __init__(self, word_to_guess: str, guesser: Guesser, max_guesses: int):
        self.top_k = 5
        self.wordle = WordleWord(word_to_guess)
        self.guesser = guesser
        self.max_guesses = max_guesses

    def play(self):
        self.guesser.update(self.wordle)
        for i in range(self.max_guesses):
            cur_guess = self.guesser.guess()
            self.wordle.process_guess(cur_guess)
            if self.wordle.game_status == GameStatus.WON:
                break
            self.guesser.update(self.wordle)

        if self.wordle.game_status != GameStatus.WON:
            self.wordle.game_status = GameStatus.LOST
        return self.wordle.game_status, i
