#!/usr/bin/env python3
"""
Local AI Code Review - Main Script

This script analyzes code changes using a local LLM (via Ollama)
combined with AST analysis, security checks, and complexity metrics.

No external API keys required - runs fully offline.
"""

import os
import sys
import ast

# Add parent directory to path for local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from local_llm import OllamaClient, CodeReviewer


def analyze_ast(code: str) -> list:
    """
    Perform basic AST analysis on Python code.
    
    Args:
        code: Python source code
        
    Returns:
        List of issues found
    """
    issues = []

    try:
        tree = ast.parse(code)
    except Exception:
        return ["Could not parse code"]

    for node in ast.walk(tree):
        # Long functions
        if isinstance(node, ast.FunctionDef):
            if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
                func_length = node.end_lineno - node.lineno
                if func_length > 40:
                    issues.append(f"Function '{node.name}' too long ({func_length} lines)")
            elif len(node.body) > 40:
                issues.append(f"Function '{node.name}' too long (>40 lines)")

        # Print statements
        if isinstance(node, ast.Call):
            if hasattr(node.func, "id") and node.func.id == "print":
                issues.append("Consider using logging instead of print()")

        # Bare except
        if isinstance(node, ast.ExceptHandler):
            if node.type is None:
                issues.append("Bare except detected - specify exception type")

    return issues


def main():
    """Main entry point for code review."""
    
    # ==============================
    # Configuration from environment
    # ==============================
    model = os.environ.get("MODEL", "deepseek-coder:6.7b")
    ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    commit_title = os.environ.get("COMMIT_TITLE", "")
    commit_message = os.environ.get("COMMIT_BODY", "")
    max_length = int(os.environ.get("MAX_LENGTH", "8000"))
    
    # ==============================
    # Read git diff from stdin
    # ==============================
    raw_diff = sys.stdin.read()
    
    if not raw_diff.strip():
        print("No diff provided")
        sys.exit(0)
    
    # ==============================
    # Extract added code for analysis
    # ==============================
    code_lines = []
    for line in raw_diff.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            code_lines.append(line[1:])
    
    code = "\n".join(code_lines)
    
    # ==============================
    # Run AST analysis
    # ==============================
    ast_issues = analyze_ast(code)
    
    # ==============================
    # Initialize local LLM client
    # ==============================
    try:
        client = OllamaClient(model=model, host=ollama_host)
        
        # Check if server is running
        if not client.is_server_running():
            print("⚠️ Local AI review skipped (Ollama unavailable)\n")
            
            # Output static analysis only
            print("## Static Analysis Results\n")
            if ast_issues:
                for issue in ast_issues:
                    print(f"- ⚠️ {issue}")
            else:
                print("✅ No structural issues found")
            return  # Don't crash, just return
        
        # ==============================
        # Run full code review
        # ==============================
        reviewer = CodeReviewer(
            client=client,
            include_security=True,
            include_complexity=True
        )
        
        review_text = reviewer.review_diff(
            diff=raw_diff,
            ast_issues=ast_issues,
            commit_title=commit_title,
            commit_message=commit_message,
            max_length=max_length
        )
        
        print(review_text)
        
    except Exception as e:
        # Fallback to static analysis on any error
        print(f"⚠️ LLM review failed: {e}\n")
        print("## Static Analysis Results\n")
        if ast_issues:
            for issue in ast_issues:
                print(f"- ⚠️ {issue}")
        else:
            print("✅ No structural issues found")


if __name__ == "__main__":
    main()
