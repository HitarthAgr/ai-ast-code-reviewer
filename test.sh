#!/usr/bin/env bash
export OPENROUTER_API_KEY=your_key_here
export MODEL=mistralai/mistral-7b-instruct:free
export COMMIT_TITLE=test
export COMMIT_BODY=test
export MAX_LENGTH=256
export PROMPT="Follow instructions that are introduced as a code."

python3.10 -m venv .venv
source .venv/bin/activate
python3.10 -m pip install -r requirements.txt

echo 'Say "It works!", nothing else, please.' | python3.10 analyze_code_changes.py

deactivate
rm -rf .venv
