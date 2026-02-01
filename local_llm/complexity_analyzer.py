"""
Complexity Analyzer for Code Review

Calculates code complexity metrics including:
- Cyclomatic complexity
- Function/class size
- Nesting depth
- Cognitive complexity estimation
"""

import ast
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class FunctionMetrics:
    """Metrics for a single function."""
    name: str
    line: int
    lines_of_code: int
    cyclomatic_complexity: int
    max_nesting_depth: int
    parameter_count: int
    

class ComplexityAnalyzer:
    """Analyzes code complexity metrics."""
    
    # Thresholds for complexity warnings
    THRESHOLDS = {
        "lines_of_code": 50,
        "cyclomatic_complexity": 10,
        "max_nesting_depth": 4,
        "parameter_count": 5,
    }
    
    def __init__(self):
        """Initialize the complexity analyzer."""
        self.functions: List[FunctionMetrics] = []
        self.classes: List[Dict[str, Any]] = []
        self.issues: List[Dict[str, Any]] = []
    
    def analyze(self, code: str) -> Dict[str, Any]:
        """
        Analyze code complexity.
        
        Args:
            code: Python source code to analyze
            
        Returns:
            Dictionary with complexity metrics and issues
        """
        self.functions = []
        self.classes = []
        self.issues = []
        
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"error": "Could not parse code", "functions": [], "issues": []}
        
        self._analyze_tree(tree)
        self._check_thresholds()
        
        return {
            "functions": [self._func_to_dict(f) for f in self.functions],
            "classes": self.classes,
            "issues": self.issues,
            "summary": self._generate_summary()
        }
    
    def _analyze_tree(self, tree: ast.AST) -> None:
        """Walk AST and collect metrics."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                metrics = self._analyze_function(node)
                self.functions.append(metrics)
            
            elif isinstance(node, ast.ClassDef):
                self.classes.append({
                    "name": node.name,
                    "line": node.lineno,
                    "method_count": sum(
                        1 for n in node.body 
                        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                    ),
                    "lines": self._count_lines(node)
                })
    
    def _analyze_function(self, node: ast.FunctionDef) -> FunctionMetrics:
        """Analyze a single function for complexity metrics."""
        return FunctionMetrics(
            name=node.name,
            line=node.lineno,
            lines_of_code=self._count_lines(node),
            cyclomatic_complexity=self._calculate_cyclomatic(node),
            max_nesting_depth=self._calculate_nesting_depth(node),
            parameter_count=len(node.args.args) + len(node.args.kwonlyargs)
        )
    
    def _count_lines(self, node: ast.AST) -> int:
        """Count lines of code in a node."""
        if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
            return node.end_lineno - node.lineno + 1
        return len(node.body) if hasattr(node, 'body') else 0
    
    def _calculate_cyclomatic(self, node: ast.AST) -> int:
        """
        Calculate cyclomatic complexity.
        
        CC = E - N + 2P where:
        - Simplified: count decision points + 1
        """
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            # Decision points
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.Assert):
                complexity += 1
            elif isinstance(child, ast.comprehension):
                complexity += 1
            # Boolean operators
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            # Ternary expression
            elif isinstance(child, ast.IfExp):
                complexity += 1
        
        return complexity
    
    def _calculate_nesting_depth(self, node: ast.AST, current_depth: int = 0) -> int:
        """Calculate maximum nesting depth."""
        max_depth = current_depth
        
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, 
                                  ast.With, ast.AsyncWith, ast.Try)):
                child_depth = self._calculate_nesting_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
            else:
                child_depth = self._calculate_nesting_depth(child, current_depth)
                max_depth = max(max_depth, child_depth)
        
        return max_depth
    
    def _check_thresholds(self) -> None:
        """Check metrics against thresholds and generate issues."""
        for func in self.functions:
            if func.lines_of_code > self.THRESHOLDS["lines_of_code"]:
                self.issues.append({
                    "type": "complexity",
                    "severity": "MEDIUM",
                    "function": func.name,
                    "line": func.line,
                    "message": f"Function too long: {func.lines_of_code} lines (max: {self.THRESHOLDS['lines_of_code']})"
                })
            
            if func.cyclomatic_complexity > self.THRESHOLDS["cyclomatic_complexity"]:
                self.issues.append({
                    "type": "complexity",
                    "severity": "MEDIUM",
                    "function": func.name,
                    "line": func.line,
                    "message": f"High cyclomatic complexity: {func.cyclomatic_complexity} (max: {self.THRESHOLDS['cyclomatic_complexity']})"
                })
            
            if func.max_nesting_depth > self.THRESHOLDS["max_nesting_depth"]:
                self.issues.append({
                    "type": "complexity",
                    "severity": "LOW",
                    "function": func.name,
                    "line": func.line,
                    "message": f"Deep nesting: {func.max_nesting_depth} levels (max: {self.THRESHOLDS['max_nesting_depth']})"
                })
            
            if func.parameter_count > self.THRESHOLDS["parameter_count"]:
                self.issues.append({
                    "type": "complexity",
                    "severity": "LOW",
                    "function": func.name,
                    "line": func.line,
                    "message": f"Too many parameters: {func.parameter_count} (max: {self.THRESHOLDS['parameter_count']})"
                })
    
    def _func_to_dict(self, func: FunctionMetrics) -> Dict[str, Any]:
        """Convert FunctionMetrics to dictionary."""
        return {
            "name": func.name,
            "line": func.line,
            "lines_of_code": func.lines_of_code,
            "cyclomatic_complexity": func.cyclomatic_complexity,
            "max_nesting_depth": func.max_nesting_depth,
            "parameter_count": func.parameter_count
        }
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary statistics."""
        if not self.functions:
            return {"total_functions": 0}
        
        return {
            "total_functions": len(self.functions),
            "total_classes": len(self.classes),
            "avg_complexity": sum(f.cyclomatic_complexity for f in self.functions) / len(self.functions),
            "max_complexity": max(f.cyclomatic_complexity for f in self.functions),
            "total_issues": len(self.issues)
        }
    
    def format_report(self) -> str:
        """Format complexity analysis as a readable report."""
        if not self.functions and not self.issues:
            return "📊 No complexity analysis available (no functions found)"
        
        report = ["## 📊 Complexity Analysis\n"]
        
        # Summary
        summary = self._generate_summary()
        report.append(f"- **Functions analyzed**: {summary.get('total_functions', 0)}")
        report.append(f"- **Classes found**: {summary.get('total_classes', 0)}")
        if summary.get('avg_complexity'):
            report.append(f"- **Average complexity**: {summary['avg_complexity']:.1f}")
        
        # Issues
        if self.issues:
            report.append("\n### ⚠️ Complexity Issues\n")
            for issue in self.issues:
                report.append(f"- `{issue['function']}` (line {issue['line']}): {issue['message']}")
        else:
            report.append("\n✅ All functions within complexity thresholds")
        
        return "\n".join(report)
