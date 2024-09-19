set -ue pipefail

pip install -e .[dev]
pip install ipykernel matplotlib
uvicorn wordle.fh_app:app --reload