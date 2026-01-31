import os
import sys
import requests
import json

# ==============================
# Check API key
# ==============================
API_KEY = os.environ.get("OPENAI_API_KEY")
if not API_KEY:
    print("No OpenRouter API key found")
    sys.exit(1)

model_engine = os.environ["MODEL"]
commit_title = os.environ["COMMIT_TITLE"]
commit_message = os.environ["COMMIT_BODY"]
max_length = int(os.environ["MAX_LENGTH"])

# ==============================
# Read git diff
# ==============================
code = sys.stdin.read()

prompt = (
    f"Commit title: {commit_title}\n"
    f"Commit message: {commit_message}\n\n"
    f"{os.environ['PROMPT']}\n\n"
    f"Code changes:\n```\n{code}\n```"
)

if len(prompt) > max_length:
    prompt = prompt[:max_length]

messages = [
    {"role": "system", "content": "You are a strict senior code reviewer."},
    {"role": "user", "content": prompt}
]

# ==============================
# OpenRouter API call
# ==============================
try:
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "model": model_engine,
            "messages": messages,
            "temperature": 0.5,
            "max_tokens": 1024
        })
    )

    data = response.json()

    review_text = data["choices"][0]["message"]["content"]

except Exception as e:
    review_text = f"OpenRouter failed to generate review: {e}"

print(review_text)
