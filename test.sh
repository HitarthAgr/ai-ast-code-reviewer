#!/usr/bin/env bash
# Local test script for AI code review
# No API keys required - uses local Ollama

set -e

export MODEL=${MODEL:-deepseek-coder:6.7b}
export OLLAMA_HOST=${OLLAMA_HOST:-http://localhost:11434}
export COMMIT_TITLE="Test commit"
export COMMIT_BODY="Testing local AI code review"
export MAX_LENGTH=8000

# Check if Ollama is running
if ! curl -s "$OLLAMA_HOST/api/tags" > /dev/null 2>&1; then
    echo "❌ Ollama server not running!"
    echo ""
    echo "To start Ollama:"
    echo "  1. Install: curl -fsSL https://ollama.com/install.sh | sh"
    echo "  2. Start:   ollama serve"
    echo "  3. Pull:    ollama pull $MODEL"
    exit 1
fi

echo "✅ Ollama server is running"
echo "📦 Using model: $MODEL"
echo ""

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -q -r requirements.txt

echo "Running test review..."
echo ""

# Test with sample code
cat << 'EOF' | python analyze_code_changes.py
+def calculate_password(user_input):
+    password = "admin123"  # hardcoded password
+    result = eval(user_input)  # dangerous eval
+    print(result)
+    try:
+        do_something()
+    except:  # bare except
+        pass
+    return result
EOF

# Cleanup
deactivate
rm -rf .venv

echo ""
echo "✅ Test complete!"
