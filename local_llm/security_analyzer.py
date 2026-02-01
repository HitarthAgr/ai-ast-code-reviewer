"""
Security Analyzer for Code Review

Performs static security analysis to detect common vulnerabilities
without requiring LLM inference. Pure Python implementation.
"""

import re
import ast
from typing import List, Dict, Any, Tuple


class SecurityAnalyzer:
    """Static security analyzer for Python code."""
    
    # Patterns for detecting potential security issues
    SECURITY_PATTERNS = [
        # Hardcoded secrets
        (r'(?i)(password|passwd|pwd|secret|api_key|apikey|token|auth)\s*=\s*["\'][^"\']+["\']',
         "Potential hardcoded secret detected", "HIGH"),
        
        # SQL Injection patterns
        (r'(?i)(execute|cursor\.execute)\s*\(\s*["\'].*%s.*["\'].*%',
         "Potential SQL injection (use parameterized queries)", "HIGH"),
        (r'(?i)(execute|cursor\.execute)\s*\(\s*f["\']',
         "SQL injection risk: f-string in SQL query", "HIGH"),
        (r'(?i)(execute|cursor\.execute)\s*\(\s*["\'].*\+',
         "SQL injection risk: string concatenation in SQL", "HIGH"),
        
        # Command injection
        (r'os\.system\s*\(',
         "os.system() is vulnerable to command injection, use subprocess", "MEDIUM"),
        (r'subprocess\.(call|run|Popen)\s*\([^)]*shell\s*=\s*True',
         "shell=True can lead to command injection", "MEDIUM"),
        
        # Unsafe deserialization
        (r'pickle\.loads?\s*\(',
         "pickle is unsafe for untrusted data", "HIGH"),
        (r'yaml\.load\s*\([^)]*\)',
         "yaml.load() is unsafe, use yaml.safe_load()", "MEDIUM"),
        
        # Path traversal
        (r'open\s*\([^)]*\+[^)]*\)',
         "Potential path traversal: validate file paths", "MEDIUM"),
        
        # Weak cryptography
        (r'(?i)(md5|sha1)\s*\(',
         "Weak hash algorithm, consider SHA-256 or better", "LOW"),
        (r'(?i)random\.(random|randint|choice)\s*\(',
         "Use secrets module for cryptographic purposes", "LOW"),
        
        # Debug/development code
        (r'(?i)debug\s*=\s*True',
         "Debug mode enabled", "LOW"),
        (r'(?i)# ?TODO|# ?FIXME|# ?HACK',
         "Unresolved TODO/FIXME comment", "INFO"),
    ]
    
    # Dangerous function calls to detect via AST
    DANGEROUS_FUNCTIONS = {
        "eval": ("eval() is dangerous, avoid if possible", "HIGH"),
        "exec": ("exec() can execute arbitrary code", "HIGH"),
        "compile": ("compile() with user input is risky", "MEDIUM"),
        "__import__": ("Dynamic imports can be security risks", "MEDIUM"),
        "input": ("Python 2 input() evaluates code, use raw_input()", "INFO"),
    }
    
    # Dangerous imports
    DANGEROUS_IMPORTS = {
        "pickle": ("pickle module can execute arbitrary code", "MEDIUM"),
        "marshal": ("marshal is not secure for untrusted data", "MEDIUM"),
        "shelve": ("shelve uses pickle internally", "MEDIUM"),
    }
    
    def __init__(self):
        """Initialize the security analyzer."""
        self.issues: List[Dict[str, Any]] = []
    
    def analyze(self, code: str) -> List[Dict[str, Any]]:
        """
        Analyze code for security issues.
        
        Args:
            code: Python source code to analyze
            
        Returns:
            List of security issues found
        """
        self.issues = []
        
        # Pattern-based analysis
        self._analyze_patterns(code)
        
        # AST-based analysis
        self._analyze_ast(code)
        
        return self.issues
    
    def _analyze_patterns(self, code: str) -> None:
        """Run regex pattern matching for security issues."""
        lines = code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern, message, severity in self.SECURITY_PATTERNS:
                if re.search(pattern, line):
                    self.issues.append({
                        "type": "security",
                        "severity": severity,
                        "line": line_num,
                        "message": message,
                        "snippet": line.strip()[:80]
                    })
    
    def _analyze_ast(self, code: str) -> None:
        """Run AST-based security analysis."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return
        
        for node in ast.walk(tree):
            # Check function calls
            if isinstance(node, ast.Call):
                func_name = self._get_func_name(node)
                if func_name in self.DANGEROUS_FUNCTIONS:
                    message, severity = self.DANGEROUS_FUNCTIONS[func_name]
                    self.issues.append({
                        "type": "security",
                        "severity": severity,
                        "line": getattr(node, 'lineno', 0),
                        "message": message,
                        "snippet": f"{func_name}(...)"
                    })
            
            # Check imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in self.DANGEROUS_IMPORTS:
                        message, severity = self.DANGEROUS_IMPORTS[alias.name]
                        self.issues.append({
                            "type": "security",
                            "severity": severity,
                            "line": getattr(node, 'lineno', 0),
                            "message": message,
                            "snippet": f"import {alias.name}"
                        })
            
            if isinstance(node, ast.ImportFrom):
                if node.module in self.DANGEROUS_IMPORTS:
                    message, severity = self.DANGEROUS_IMPORTS[node.module]
                    self.issues.append({
                        "type": "security",
                        "severity": severity,
                        "line": getattr(node, 'lineno', 0),
                        "message": message,
                        "snippet": f"from {node.module} import ..."
                    })
    
    def _get_func_name(self, node: ast.Call) -> str:
        """Extract function name from a Call node."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return ""
    
    def format_report(self) -> str:
        """Format security issues as a readable report."""
        if not self.issues:
            return "✅ No security issues detected"
        
        # Group by severity
        by_severity = {"HIGH": [], "MEDIUM": [], "LOW": [], "INFO": []}
        for issue in self.issues:
            by_severity[issue["severity"]].append(issue)
        
        report = ["## 🔒 Security Analysis\n"]
        
        severity_icons = {
            "HIGH": "🔴",
            "MEDIUM": "🟠", 
            "LOW": "🟡",
            "INFO": "ℹ️"
        }
        
        for severity in ["HIGH", "MEDIUM", "LOW", "INFO"]:
            issues = by_severity[severity]
            if issues:
                report.append(f"\n### {severity_icons[severity]} {severity} Severity\n")
                for issue in issues:
                    report.append(f"- Line {issue['line']}: {issue['message']}")
                    if issue.get('snippet'):
                        report.append(f"  ```\n  {issue['snippet']}\n  ```")
        
        return "\n".join(report)
