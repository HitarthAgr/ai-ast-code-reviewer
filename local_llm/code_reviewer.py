"""
Code Reviewer - Main orchestrator for AI-powered code review

Combines AST analysis, security checks, complexity metrics,
and LLM-based review into a comprehensive code review system.
"""

from typing import List, Dict, Any, Optional
from .ollama_client import OllamaClient
from .security_analyzer import SecurityAnalyzer
from .complexity_analyzer import ComplexityAnalyzer


class CodeReviewer:
    """
    Main code reviewer that orchestrates all analysis components.
    
    Combines:
    - Static AST analysis
    - Security vulnerability detection
    - Complexity metrics
    - LLM-based intelligent review
    """
    
    SYSTEM_PROMPT = """You are a senior code reviewer with expertise in Python. 
Your task is to review code changes and provide constructive feedback.

Focus on:
1. Code correctness and potential bugs
2. Best practices and code style
3. Performance considerations
4. Maintainability and readability
5. Any issues flagged by static analysis

Be concise but thorough. Format your response as markdown with clear sections.
If code looks good, acknowledge it briefly. Don't repeat issues already flagged by static analysis."""

    REVIEW_TEMPLATE = """## Code Review Request

### Commit Information
- **Title**: {commit_title}
- **Description**: {commit_message}

### Static Analysis Results
{static_analysis}

### Security Analysis
{security_analysis}

### Complexity Metrics
{complexity_analysis}

### Code Changes
```diff
{diff}
```

Please provide your code review focusing on issues not already covered by the static analysis above."""

    def __init__(
        self,
        client: Optional[OllamaClient] = None,
        model: str = "deepseek-coder:6.7b",
        include_security: bool = True,
        include_complexity: bool = True
    ):
        """
        Initialize the code reviewer.
        
        Args:
            client: OllamaClient instance (creates one if not provided)
            model: Model to use for LLM review
            include_security: Whether to run security analysis
            include_complexity: Whether to run complexity analysis
        """
        self.client = client or OllamaClient(model=model)
        self.security_analyzer = SecurityAnalyzer() if include_security else None
        self.complexity_analyzer = ComplexityAnalyzer() if include_complexity else None
    
    def extract_added_code(self, diff: str) -> str:
        """Extract only added lines from a git diff."""
        added_lines = []
        for line in diff.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                added_lines.append(line[1:])  # Remove the + prefix
        return "\n".join(added_lines)
    
    def run_static_analysis(self, code: str, ast_issues: List[str]) -> str:
        """
        Run all static analysis and format results.
        
        Args:
            code: Python source code
            ast_issues: Issues from basic AST analysis
            
        Returns:
            Formatted string with all static analysis results
        """
        results = []
        
        # Basic AST issues
        if ast_issues:
            results.append("**AST Analysis:**")
            for issue in ast_issues:
                results.append(f"- {issue}")
        else:
            results.append("**AST Analysis:** No structural issues found")
        
        # Security analysis
        if self.security_analyzer:
            security_issues = self.security_analyzer.analyze(code)
            if security_issues:
                results.append("\n" + self.security_analyzer.format_report())
            else:
                results.append("\n**Security:** ✅ No security issues detected")
        
        # Complexity analysis
        if self.complexity_analyzer:
            complexity_result = self.complexity_analyzer.analyze(code)
            results.append("\n" + self.complexity_analyzer.format_report())
        
        return "\n".join(results)
    
    def review_diff(
        self,
        diff: str,
        ast_issues: List[str],
        commit_title: str = "",
        commit_message: str = "",
        max_length: int = 8000
    ) -> str:
        """
        Perform a complete code review on a git diff.
        
        Args:
            diff: Git diff content
            ast_issues: Pre-computed AST issues
            commit_title: PR/commit title
            commit_message: PR/commit description
            max_length: Maximum prompt length
            
        Returns:
            Complete review text
        """
        # Extract code for analysis
        code = self.extract_added_code(diff)
        
        # Run static analysis
        security_report = ""
        complexity_report = ""
        
        if self.security_analyzer:
            self.security_analyzer.analyze(code)
            security_report = self.security_analyzer.format_report()
        
        if self.complexity_analyzer:
            self.complexity_analyzer.analyze(code)
            complexity_report = self.complexity_analyzer.format_report()
        
        # Format AST issues
        ast_report = "\n".join(f"- {issue}" for issue in ast_issues) if ast_issues else "No structural issues found"
        
        # Build the prompt
        prompt = self.REVIEW_TEMPLATE.format(
            commit_title=commit_title or "N/A",
            commit_message=commit_message or "N/A",
            static_analysis=ast_report,
            security_analysis=security_report,
            complexity_analysis=complexity_report,
            diff=diff[:max_length - 2000]  # Leave room for other content
        )
        
        # Truncate if needed
        if len(prompt) > max_length:
            prompt = prompt[:max_length]
        
        # Get LLM review
        try:
            llm_review = self.client.generate(
                prompt=prompt,
                system=self.SYSTEM_PROMPT,
                temperature=0.3,
                max_tokens=1500
            )
        except Exception as e:
            llm_review = f"LLM review failed: {e}"
        
        # Combine all results
        final_review = self._format_final_review(
            llm_review=llm_review,
            security_report=security_report,
            complexity_report=complexity_report,
            ast_issues=ast_issues
        )
        
        return final_review
    
    def _format_final_review(
        self,
        llm_review: str,
        security_report: str,
        complexity_report: str,
        ast_issues: List[str]
    ) -> str:
        """Format the final combined review output."""
        sections = []
        
        # LLM Review (main content)
        sections.append("## 🤖 AI Code Review\n")
        sections.append(llm_review)
        
        # Static Analysis Summary
        if ast_issues:
            sections.append("\n---\n")
            sections.append("## 📋 Static Analysis\n")
            for issue in ast_issues:
                sections.append(f"- ⚠️ {issue}")
        
        # Security Issues (if any HIGH/MEDIUM)
        if self.security_analyzer and self.security_analyzer.issues:
            critical = [i for i in self.security_analyzer.issues if i["severity"] in ("HIGH", "MEDIUM")]
            if critical:
                sections.append("\n---\n")
                sections.append(security_report)
        
        # Complexity Issues (if any)
        if self.complexity_analyzer and self.complexity_analyzer.issues:
            sections.append("\n---\n")
            sections.append(complexity_report)
        
        return "\n".join(sections)
    
    def quick_review(self, code: str) -> str:
        """
        Quick review without git diff context.
        
        Useful for reviewing code snippets directly.
        
        Args:
            code: Python source code to review
            
        Returns:
            Review text
        """
        prompt = f"""Please review this Python code and provide feedback:

```python
{code[:6000]}
```

Focus on:
1. Bugs or errors
2. Best practices
3. Security concerns
4. Performance issues"""

        return self.client.generate(
            prompt=prompt,
            system=self.SYSTEM_PROMPT,
            temperature=0.3,
            max_tokens=1000
        )
