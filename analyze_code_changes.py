import os
import sys
import requests
import json
import ast

def analyze_ast(code):
    issues = []

    try:
        tree = ast.parse(code)
    except Exception:
        return ["Could not parse code"]

    for node in ast.walk(tree):

        # long functions
        if isinstance(node, ast.FunctionDef):
            if len(node.body) > 40:
                issues.append(f"Function '{node.name}' too long (>40 lines)")

        # print statements
        if isinstance(node, ast.Call):
            if hasattr(node.func, "id") and node.func.id == "print":
                issues.append("Avoid print(), use logging")

        # bare except
        if isinstance(node, ast.ExceptHandler):
            if node.type is None:
                issues.append("Bare except detected")

    return issues

# ==============================
# Check API key
# ==============================
API_KEY = os.environ.get("OPENROUTER_API_KEY")
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
raw_diff = sys.stdin.read()

code_lines = []
for line in raw_diff.splitlines():
    if line.startswith("+") and not line.startswith("+++"):
        code_lines.append(line[1:])

code = "\n".join(code_lines)
ast_issues = analyze_ast(code)

prompt = (
    f"Commit title: {commit_title}\n"
    f"Commit message: {commit_message}\n\n"
    "Static AST analysis:\n"
    + ("\n".join(ast_issues) if ast_issues else "No structural issues found.")
    + "\n\nCode changes:\n```\n"
    + code +
    "\n```"
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
    response.raise_for_status()
    data = response.json()

    if "choices" in data:
        review_text = data["choices"][0]["message"]["content"]
    else:
        review_text = f"OpenRouter error:\n{json.dumps(data, indent=2)}"


except Exception as e:
    review_text = f"OpenRouter failed to generate review: {e}"

print(review_text)
