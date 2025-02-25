import re
import numpy as np
from abc import ABC, abstractmethod

from wordle.word import WordleWord, _Alphabet, Status, W_LEN


class Guesser(ABC):
    def __init__(self, dataset, max_wlen=W_LEN):
        self.alphabet = _Alphabet()
        self.dataset = dataset
        self.max_wlen = max_wlen

    def guess(self):
        _guess = self._make_guess()
        if _guess in self.dataset:
            self.dataset.remove(_guess)
        else:
            raise ValueError(f"Invalid guess: {_guess}")
        return _guess

    @abstractmethod
    def _make_guess(self):
        pass

    def update_probabilities(self):
        pass

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


class RandomGuesser(Guesser):
    def __init__(self, dataset, max_wlen=W_LEN):
        super().__init__(dataset, max_wlen)
        self.update_probabilities()

    def __len__(self):
        return len(self.dataset)

    def _make_guess(self):
        return np.random.choice(self.dataset)
