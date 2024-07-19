import json
from pathlib import Path

wordle_len = 5
data_file = Path(f"{__file__}").parent.parent / "data" / "all_word_curl.json"
data_file = data_file.resolve()
wordle_data_file = data_file.parent / data_file.name.replace(".json", f"_wordle_{wordle_len}.json")

if __name__ == "__main__":
    print(f"reading from {data_file}")
    with open(data_file, "r") as f:
        data = json.load(f)

    wordle_data = {k: v for k, v in data.items() if len(k) == wordle_len}

    with open(wordle_data_file, "w") as f:
        json.dump(wordle_data, f, indent=2)
    print(f"written to {wordle_data_file}")
