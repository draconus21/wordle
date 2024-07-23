## Wordle


A simple wordle game w/ automatic solver.

# python packages
* click
* numpy
* pydantic >= 2.0

# Human mode
```console
python src/wordle.py
```

# \[AI\] Auto-mode
```bash
python src/wordle -ai
```

You also have the option to set the word to be guess in both modes. To set the word, pass an extra option `-vs`. Then before the game begins, you will be prompted to enter a word to be guessed.

```bash
# to set the word for a game w/ another non-ai player
python src/wordle -vs
# or, to set the word for a game w/ ai
python src/wordle -ai -vs
```