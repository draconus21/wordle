import numpy as np
from wordle.guesser.base import Guesser
from wordle.word import WordleWord, _Alphabet, W_LEN


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


class BetterGuesser(Guesser):
    def __init__(self, dataset, top_k=5, max_wlen=W_LEN):
        super().__init__(dataset, max_wlen)
        self.stats_table = DataStats(dataset)
        self.probs = None
        self.top_k = top_k
        self.update_probabilities()

    def __len__(self):
        return len(self.dataset)

    @property
    def vocab_size(self):
        return len(self.alphabet)

    def _make_guess(self):
        w = np.array(list(self.probs.keys()))
        p = np.array(list(self.probs.values()))

        # pick top_k elements
        if len(w) > self.top_k:
            idx = np.argpartition(-p, self.top_k)[: self.top_k]
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
        super().update(word)
        self.update_probabilities()
