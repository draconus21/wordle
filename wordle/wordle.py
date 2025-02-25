import click
import numpy as np


from wordle.word import GameStatus, valid_words, MAX_STEPS
from wordle.game import Game
from wordle.guesser.base import RandomGuesser
from wordle.guesser.better import BetterGuesser


def play(word_to_guess, guess_strategy, top_k):
    if guess_strategy.lower() == "random":
        g = RandomGuesser(list(valid_words))
    else:
        g = BetterGuesser(list(valid_words), top_k=top_k)

    return Game(word_to_guess, g, max_guesses=MAX_STEPS).play()


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--guess-strategy", "-g", type=click.Choice(["random", "better"]), default="better", help="Guess strategy"
)
@click.option("--num-simulations", "-n", type=int, default=100, help="Number of simulations")
@click.option("--top-k", type=int, default=5, help="Top k words to consider")
def run(guess_strategy, num_simulations, top_k):
    """Run the wordle game"""
    from tqdm import tqdm

    total_steps = 0
    n_won = 0
    for i in tqdm(range(num_simulations), desc="Simulating ..."):
        w = np.random.choice(list(valid_words))
        status, steps = play(w, guess_strategy=guess_strategy, top_k=top_k)
        if status == GameStatus.WON:
            n_won += 1
        total_steps += steps / MAX_STEPS
        # print(f"Game {i+1}/{n}: {status.value}, {steps} steps")

    result = dict(
        guess_strategy=guess_strategy,
        max_guesses=MAX_STEPS,
        n_games=num_simulations,
        win_rate=n_won / num_simulations,
        avg_steps=MAX_STEPS * total_steps / num_simulations,
    )
    print(result)
