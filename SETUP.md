# Local AI Code Review - Setup Guide

Complete guide for setting up the local AI-powered code review system.

## Quick Start

### 1. Install Ollama

**Linux/WSL:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:** Download from [ollama.com/download](https://ollama.com/download)

**macOS:**
```bash
brew install ollama
```

### 2. Start Ollama Server

```bash
ollama serve
```

### 3. Pull the Model

```bash
# Recommended (best for code review)
ollama pull deepseek-coder:6.7b

# Alternative options:
# ollama pull codellama:7b       # Lighter alternative
# ollama pull qwen2.5-coder:7b   # Excellent alternative
```

### 4. Test Locally

```bash
cd /path/to/gpt-code-review-action
./test.sh
```

---

## GitHub Actions Usage

### In Your Workflow

```yaml
on: [pull_request]

jobs:
  code-review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write

    steps:
      - uses: actions/checkout@v4
      
      - uses: your-username/ai-code-review-action@main
        with:
          ollama-model: deepseek-coder:6.7b
          # max-length: 8000
```

### Available Inputs

| Input | Default | Description |
|-------|---------|-------------|
| `ollama-model` | `deepseek-coder:6.7b` | Ollama model to use |
| `max-length` | `8000` | Max chars to send to model |
| `review-title` | `# 🤖 AI Code Review` | Comment header |
| `post-if-error` | `true` | Post comment on errors |

---

## What Gets Analyzed

### Static Analysis (Fast, No LLM)
- ✅ AST structural issues
- ✅ Security vulnerabilities (hardcoded secrets, SQL injection, unsafe eval)
- ✅ Complexity metrics (cyclomatic, nesting depth)

### LLM Analysis (Local AI)
- ✅ Code correctness
- ✅ Best practices
- ✅ Performance concerns
- ✅ Maintainability

---

## Model Comparison

| Model | Size | Speed | Quality | Notes |
|-------|------|-------|---------|-------|
| `deepseek-coder:6.7b` | 4GB | ⚡ Fast | ★★★★☆ | **Recommended** |
| `codellama:7b` | 4GB | ⚡ Fast | ★★★☆☆ | Lighter |
| `qwen2.5-coder:7b` | 4.5GB | ⚡ Fast | ★★★★☆ | Great alternative |
| `deepseek-coder:33b` | 20GB | 🐢 Slow | ★★★★★ | Best quality |

---

## Troubleshooting

### Ollama server not running
```bash
ollama serve &
```

### Model not found
```bash
ollama pull deepseek-coder:6.7b
ollama list  # Verify
```

### GitHub Actions timeout
- Ensure model size fits in runner RAM (14GB available)
- Consider caching the model with `actions/cache`

---

## Architecture

```
git diff → analyze_code_changes.py
              ├── AST Analysis (built-in)
              ├── Security Analyzer (local_llm/)
              ├── Complexity Analyzer (local_llm/)
              └── Ollama Client → Local LLM
                                      ↓
                              PR Comment
```

All processing happens locally. No data leaves your machine or GitHub runner.
