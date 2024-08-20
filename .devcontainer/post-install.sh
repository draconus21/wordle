set -ue pipefail

pip install -e .[dev]
uvicorn wordle.fh_app:app --reload