from wordle.wordle import WordleWord, BetterGuess, DataStats, valid_words
from abc import ABC

qwerty = ["qwertyuiop", " asdfghjkl", "  zxcvbnm"]


class Game(ABC):
    def __init__(self, word_to_guess, guess_strategy):
        self.top_k = 5
        self.wordle = WordleWord(word_to_guess)
        self.guesser = BetterGuess(list(valid_words), stats_table=DataStats(list(valid_words)), top_k=self.top_k)
