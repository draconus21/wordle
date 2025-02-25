import re
import click
import string
from getpass import getpass
from enum import Enum
import numpy as np
from pydantic import BaseModel, ConfigDict
from typing import List, Dict


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


class DataStats:
    def __init__(self, dataset, max_wlen=W_LEN):
        self.alphabet = _Alphabet()
        self.max_wlen = max_wlen
        self.dataset = dataset

        stoi = {l.ltr: i for i, l in enumerate(self.alphabet.letters.values())}
        itos = {i: l.ltr for i, l in enumerate(self.alphabet.letters.values())}

        self.encode = lambda w: [stoi[l] if l != "_" else "_" for l in w]  # string -> list of ints
        self.decode = lambda w: "".join([itos[i] for i in w])  # list of ints -> string

        self.probs_nx, self.probs_bf, self.prob_po = self.build_probabilities()

    @property
    def vocab_size(self):
        return len(self.alphabet)

    def build_probabilities(self):
        # probability of next letter given current letter
        counter = np.zeros([self.vocab_size, self.vocab_size], dtype=np.float32)
        for w in self.dataset:
            _w = self.encode(w)
            for i, c in enumerate(_w):
                if i == 0:
                    continue
                counter[_w[i - 1], c] += 1

        prob_next = counter / np.sum(counter, axis=1, keepdims=True)
        prob_befo = counter / np.sum(counter, axis=0, keepdims=True)

        # probability for each position in word
        # max_wlen: 5
        # _, _, _, _, _
        counter = np.zeros([self.max_wlen, self.vocab_size], dtype=np.float32)
        for w in self.dataset:
            _w = self.encode(w)
            for i, c in enumerate(_w):
                counter[i, c] += 1  # c-1 since we are not using <start> and <end>

        prob_posi = counter / np.sum(counter, axis=1, keepdims=True)

        return prob_next, prob_befo, prob_posi

    def compute_prob(self, word):
        _w = self.encode(word)
        prob = 1.0
        for i, c in enumerate(_w):
            if i == 0:
                continue
            if c == "_" or _w[i - 1] == "_":
                continue
            # prob of next letter given current letter
            prob *= self.probs_bf[_w[i - 1], c]
            # prob of current letter in current position
            prob *= self.prob_po[i, c]

        return prob


class BetterGuess:
    def __init__(self, dataset, stats_table, max_wlen=W_LEN):
        self.alphabet = _Alphabet()
        self.max_wlen = max_wlen
        self.dataset = dataset
        self.stats_table = stats_table
        self.probs = None
        self.update_probabilities()

    def __len__(self):
        return len(self.dataset)

    @property
    def vocab_size(self):
        return len(self.alphabet)

    def make_random_guess(self):
        return np.random.choice(self.dataset)

    def make_better_guess(self):
        top_k = 5
        w = np.array(list(self.probs.keys()))
        p = np.array(list(self.probs.values()))

        # pick top_k elements
        if len(w) > top_k:
            idx = np.argpartition(-p, top_k)[:top_k]
            p = np.take(p, idx)
            w = np.take(w, idx)
        else:
            idx = np.arange(len(w))

        # sample a word from top_k
        p = p / p.sum()
        idx = np.where(np.random.multinomial(1, p) == 1)

        p = p[idx][0]
        w = w[idx][0]

        return w

    def update_probabilities(self):
        probs = {w: self.stats_table.compute_prob(w) for w in self.dataset}
        tot = sum(probs.values())
        probs = {w: p / tot for w, p in probs.items()}  # normalize
        self.probs = probs

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
        self.update_probabilities()


def play(word_to_guess, guess_strategy):
    d = DataStats(list(valid_words))
    g = BetterGuess(list(valid_words), stats_table=d)
    w = WordleWord(word_to_guess)
    g.update(w)

    for i in range(MAX_STEPS):
        if guess_strategy.lower() == "random":
            cur_guess = g.make_random_guess()
        else:
            cur_guess = g.make_better_guess()
        w.process_guess(cur_guess)

        if w.game_status == GameStatus.WON:
            break

        g.update(w)

    if w.game_status != GameStatus.WON:
        w.game_status = GameStatus.LOST

    return w.game_status, i


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--guess-strategy", "-g", type=click.Choice(["random", "better"]), default="better", help="Guess strategy"
)
@click.option("--num-simulations", "-n", type=int, default=100, help="Number of simulations")
def run(guess_strategy, num_simulations):
    """Run the wordle game"""
    from tqdm import tqdm

    total_steps = 0
    n_won = 0
    for i in tqdm(range(num_simulations), desc="Simulating ..."):
        w = np.random.choice(list(valid_words))
        status, steps = play(w, guess_strategy=guess_strategy)
        if status == GameStatus.WON:
            n_won += 1
        total_steps += steps / MAX_STEPS
        # print(f"Game {i+1}/{n}: {status.value}, {steps} steps")

    result = dict(
        guess_strategy=guess_strategy,
        n_games=num_simulations,
        win_rate=n_won / num_simulations,
        avg_steps=MAX_STEPS * total_steps / num_simulations,
    )
    print(result)
