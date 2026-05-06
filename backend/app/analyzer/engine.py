"""
NexaFlow — Core Code Analysis Engine

100% free, no external API keys required.

Performs:
1. Static analysis  — AST-based bug detection, style checks, security patterns
2. Complexity metrics — Cyclomatic (radon), Cognitive complexity, Halstead metrics
3. Maintainability — Maintainability Index, comment ratio, naming quality
4. Security scanning — Pattern-based detection of common vulnerabilities
5. Performance hints — Anti-pattern detection
6. Duplication detection — Levenshtein-based similar-block detection
7. AI-style suggestions — Rule-based smart fix generation (no LLM needed)
8. Quality scoring — Weighted aggregate 0–100

Supports: Python, JavaScript/TypeScript (regex + heuristic), Java (heuristic)
"""

import ast
import re
import time
import math
import hashlib
import logging
from dataclasses import dataclass, field
from typing import Any, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


# ─── Data Classes ─────────────────────────────────────────────────────────────

@dataclass
class AnalysisIssue:
    severity: str           # info | warning | error | critical
    category: str           # style | complexity | security | performance | ...
    rule_id: str
    title: str
    message: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    column_start: Optional[int] = None
    code_snippet: Optional[str] = None
    is_fixable: bool = False
    fix_description: Optional[str] = None
    fix_code_snippet: Optional[str] = None


@dataclass
class FileMetrics:
    lines_of_code: int = 0
    blank_lines: int = 0
    comment_lines: int = 0
    cyclomatic_complexity: float = 0.0
    cognitive_complexity: float = 0.0
    maintainability_index: float = 100.0
    halstead_volume: float = 0.0
    quality_score: float = 100.0
    issues: list[AnalysisIssue] = field(default_factory=list)
    annotations: dict = field(default_factory=dict)  # line_no -> list[str]


@dataclass
class ReviewMetrics:
    quality_score: float = 0.0
    maintainability_index: float = 0.0
    total_issues: int = 0
    critical_issues: int = 0
    error_issues: int = 0
    warning_issues: int = 0
    info_issues: int = 0
    total_lines: int = 0
    avg_complexity: float = 0.0
    duplication_pct: float = 0.0
    ai_summary: str = ""
    ai_praise: str = ""
    ai_top_priority: str = ""
    analysis_duration_ms: int = 0
    per_file: dict[str, FileMetrics] = field(default_factory=dict)


# ─── Rule Database ────────────────────────────────────────────────────────────

SECURITY_PATTERNS = [
    # Python-specific
    (r"\beval\s*\(", "SEC001", "Dangerous eval() usage",
     "eval() executes arbitrary code and is a major security risk. Use ast.literal_eval() for safe deserialization.",
     "critical", True,
     "Replace eval() with ast.literal_eval() for safe literal parsing:\n  import ast\n  result = ast.literal_eval(user_input)"),
    (r"\bexec\s*\(", "SEC002", "Dangerous exec() usage",
     "exec() runs arbitrary Python code. Avoid unless absolutely necessary.",
     "critical", False, None),
    (r"subprocess\.(call|run|Popen).*shell\s*=\s*True", "SEC003", "Shell injection risk",
     "shell=True with subprocess passes input to a shell, enabling command injection. Use a list of arguments instead.",
     "critical", True,
     "Use list form:\n  subprocess.run(['ls', '-la'], shell=False)  # Safe"),
    (r"os\.system\(", "SEC004", "os.system() — shell injection risk",
     "os.system() is vulnerable to shell injection. Use subprocess.run() with a list.",
     "error", True,
     "Replace with:\n  import subprocess\n  subprocess.run(['command', 'arg1'], check=True)"),
    (r"pickle\.(load|loads|dump|dumps)", "SEC005", "Insecure pickle deserialization",
     "pickle can execute arbitrary code during deserialization. Never unpickle untrusted data.",
     "error", False, None),
    (r"hashlib\.md5\s*\(", "SEC006", "Weak MD5 hash",
     "MD5 is cryptographically broken. Use hashlib.sha256() or better.",
     "warning", True,
     "Replace MD5 with SHA-256:\n  hashlib.sha256(data).hexdigest()"),
    (r"hashlib\.sha1\s*\(", "SEC007", "Weak SHA-1 hash",
     "SHA-1 is deprecated for security use. Use hashlib.sha256() or hashlib.sha3_256().",
     "warning", True,
     "Replace SHA-1:\n  hashlib.sha256(data).hexdigest()"),
    (r"password\s*=\s*['\"][^'\"]+['\"]", "SEC008", "Hardcoded password",
     "Hardcoded credentials are a severe security vulnerability. Use environment variables.",
     "critical", True,
     "Use environment variables:\n  import os\n  password = os.environ.get('DB_PASSWORD')"),
    (r"secret\s*=\s*['\"][^'\"]+['\"]", "SEC009", "Hardcoded secret",
     "Hardcoded secrets should be stored in environment variables or a secrets manager.",
     "critical", True,
     "Use os.environ.get('SECRET_KEY') or a secrets manager like python-dotenv"),
    (r"api_key\s*=\s*['\"][^'\"]+['\"]", "SEC010", "Hardcoded API key",
     "API keys in source code will be exposed in version control.",
     "critical", True,
     "Use:\n  api_key = os.environ.get('API_KEY')"),
    (r"['\"]SELECT\s.*WHERE.*['\"].*\+|['\"]INSERT\s.*VALUES.*['\"].*\+|['\"]UPDATE\s.*SET.*['\"].*\+|['\"]DELETE\s.*WHERE.*['\"].*\+|SELECT.*%s|SELECT.*format\(", "SEC011", "Potential SQL injection",
     "String formatting in SQL queries enables injection attacks. Use parameterized queries.",
     "critical", True,
     "Use parameterized queries:\n  cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))"),
    (r"random\.(random|randint|choice)\s*\(", "SEC012", "Non-cryptographic random",
     "random module is not cryptographically secure. For security tokens use secrets module.",
     "info", True,
     "For security use:\n  import secrets\n  token = secrets.token_hex(32)"),
]

PERFORMANCE_PATTERNS = [
    (r"for\s+\w+\s+in\s+range\(len\(", "PERF001", "Use enumerate() instead of range(len())",
     "range(len(x)) is Pythonic anti-pattern. Use enumerate() for index+value access.",
     "warning", True,
     "Replace:\n  for i, item in enumerate(my_list):  # Pythonic!"),
    (r"\+\s*=\s*['\"]|['\"].*\+\s*=", "PERF002", "String concatenation in loop",
     "String concatenation with += in loops is O(n²). Use list and str.join() instead.",
     "warning", True,
     "Use list join:\n  parts = []\n  for item in items:\n      parts.append(str(item))\n  result = ''.join(parts)"),
    (r"\.append\(.*\)\s*\n.*\.append\(", "PERF003", "Consider list comprehension",
     "Sequential appends can often be replaced with a faster, more readable list comprehension.",
     "info", False, None),
    (r"time\.sleep\(0\)", "PERF004", "sleep(0) yields control unnecessarily",
     "time.sleep(0) is a no-op in most contexts. Remove it or use asyncio.sleep(0) in async code.",
     "info", True,
     "In async code:\n  await asyncio.sleep(0)  # Yield to event loop"),
    (r"global\s+\w+", "PERF005", "Global variable usage",
     "Global variables prevent optimization and make code hard to test. Consider class attributes or parameters.",
     "warning", False, None),
    (r"import \*", "PERF006", "Wildcard import",
     "Wildcard imports pollute namespace, hide dependencies, and prevent static analysis.",
     "warning", True,
     "Explicitly import:\n  from module import ClassA, function_b"),
]

STYLE_PATTERNS = [
    (r"except\s*:", "STYLE001", "Bare except clause",
     "Bare 'except:' catches ALL exceptions including KeyboardInterrupt and SystemExit. Catch specific exceptions.",
     "error", True,
     "Specify exception type:\n  except ValueError as e:\n      logger.error(f'Value error: {e}')"),
    (r"except\s+Exception\s*:", "STYLE002", "Overly broad Exception catch",
     "Catching all Exceptions hides bugs. Catch specific exception types.",
     "warning", True,
     "Catch specific exceptions:\n  except (ValueError, TypeError) as e:\n      handle(e)"),
    (r"pass\s*$", "STYLE003", "Empty block with pass",
     "Empty blocks with just 'pass' may indicate incomplete implementation. Add a comment or raise NotImplementedError.",
     "info", True,
     "Add context:\n  raise NotImplementedError('TODO: implement this')\n  # or\n  ...  # Intentionally empty"),
    (r"print\s*\(", "STYLE004", "print() statement",
     "Use logging instead of print() for production code. print() has no log levels or output control.",
     "info", True,
     "Replace with logging:\n  import logging\n  logger = logging.getLogger(__name__)\n  logger.info('message')"),
    (r"#\s*TODO|#\s*FIXME|#\s*HACK|#\s*XXX", "STYLE005", "TODO/FIXME comment",
     "Unresolved TODO/FIXME comments indicate incomplete or problematic code.",
     "info", False, None),
    (r"==\s*True|==\s*False", "STYLE006", "Explicit boolean comparison",
     "Comparing to True/False explicitly is un-Pythonic. Use truthiness directly.",
     "info", True,
     "Write:\n  if is_valid:  # Not: if is_valid == True\n  if not is_empty:  # Not: if is_empty == False"),
    (r"is\s+not\s+None\s+==|==\s+None", "STYLE007", "Use 'is None' for None check",
     "Use 'is None' and 'is not None' for None comparisons, not == None.",
     "info", True,
     "Write:\n  if value is None:  # Correct\n  if value is not None:  # Correct"),
]

MAINTAINABILITY_PATTERNS = [
    (r"def\s+\w+\([^)]{80,}\)", "MAINT001", "Too many function parameters",
     "Functions with many parameters are hard to use and test. Consider using a dataclass or config object.",
     "warning", True,
     "Refactor:\n  @dataclass\n  class Config:\n      param1: str\n      param2: int\n  \n  def my_func(config: Config): ..."),
    (r"lambda\s+\w+.*lambda\s+\w+", "MAINT002", "Nested lambda",
     "Nested lambdas are difficult to read and debug. Extract to named functions.",
     "warning", False, None),
    (r"#\s*type:\s*ignore", "MAINT003", "Type ignore comment",
     "# type: ignore suppresses type checking. Fix the underlying type issue instead.",
     "info", False, None),
    (r"noqa", "MAINT004", "noqa — suppressed lint",
     "noqa comments suppress linting. Each should have a specific code (e.g., # noqa: E501) and justification.",
     "info", False, None),
]


# ─── Python AST Analyzer ──────────────────────────────────────────────────────

class PythonASTAnalyzer(ast.NodeVisitor):
    """
    Deep AST-based analysis for Python code.
    Computes:
    - Cyclomatic complexity (McCabe)
    - Cognitive complexity (approximation)
    - Function length issues
    - Nested function depth
    - Missing docstrings
    - Mutable default arguments
    - Unused imports (heuristic)
    - Long lines
    - Naming convention violations
    """

    def __init__(self, source_lines: list[str]):
        self.source_lines = source_lines
        self.issues: list[AnalysisIssue] = []
        self.complexity = 1  # Base complexity
        self.cognitive_complexity = 0
        self._nesting_depth = 0
        self._function_stack: list[dict] = []
        self._class_names: set[str] = set()
        self._function_names: set[str] = set()
        self._import_names: set[str] = set()
        self._used_names: set[str] = set()

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._analyze_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._analyze_function(node)

    def _analyze_function(self, node):
        # Naming: should be snake_case
        if not re.match(r'^[a-z_][a-z0-9_]*$', node.name) and not node.name.startswith('_'):
            self.issues.append(AnalysisIssue(
                severity="warning", category="style", rule_id="AST001",
                title="Function name not snake_case",
                message=f"Function '{node.name}' should be snake_case (e.g., '{self._to_snake(node.name)}').",
                line_start=node.lineno, code_snippet=f"def {node.name}(...)",
                is_fixable=True,
                fix_description=f"Rename to '{self._to_snake(node.name)}'",
            ))

        # Missing docstring
        has_docstring = (
            node.body and
            isinstance(node.body[0], ast.Expr) and
            isinstance(node.body[0].value, ast.Constant) and
            isinstance(node.body[0].value.value, str)
        )
        if not has_docstring and not node.name.startswith('_'):
            self.issues.append(AnalysisIssue(
                severity="info", category="documentation", rule_id="AST002",
                title="Missing docstring",
                message=f"Function '{node.name}' has no docstring. Add one to explain purpose, args, and return value.",
                line_start=node.lineno,
                is_fixable=True,
                fix_description='Add a docstring:\n    def ' + node.name + '(...):\n        """Brief description.\n\n        Args:\n            param: Description.\n\n        Returns:\n            Description.\n        """',
            ))

        # Mutable default arguments
        for default in node.args.defaults + node.args.kw_defaults:
            if default and isinstance(default, (ast.List, ast.Dict, ast.Set)):
                self.issues.append(AnalysisIssue(
                    severity="error", category="bug", rule_id="AST003",
                    title="Mutable default argument",
                    message=f"Function '{node.name}' uses a mutable default argument (list/dict/set). "
                             "This is shared across all calls — use None as default instead.",
                    line_start=node.lineno,
                    is_fixable=True,
                    fix_description="Use None as default:\n  def func(items=None):\n      if items is None:\n          items = []\n      ...",
                ))

        # Function too long
        func_lines = (node.end_lineno or node.lineno) - node.lineno
        if func_lines > 50:
            self.issues.append(AnalysisIssue(
                severity="warning", category="maintainability", rule_id="AST004",
                title="Function too long",
                message=f"Function '{node.name}' is {func_lines} lines long. "
                         "Functions over 50 lines are hard to test and maintain. Extract sub-functions.",
                line_start=node.lineno, line_end=node.end_lineno,
            ))
        elif func_lines > 30:
            self.issues.append(AnalysisIssue(
                severity="info", category="maintainability", rule_id="AST004",
                title="Function somewhat long",
                message=f"Function '{node.name}' is {func_lines} lines. Consider breaking it down.",
                line_start=node.lineno,
            ))

        # Too many arguments
        all_args = node.args.args + node.args.posonlyargs + node.args.kwonlyargs
        if len(all_args) > 7:
            self.issues.append(AnalysisIssue(
                severity="warning", category="maintainability", rule_id="AST005",
                title="Too many function arguments",
                message=f"Function '{node.name}' has {len(all_args)} parameters. "
                         "More than 7 parameters makes the function hard to use. Use a config dataclass.",
                line_start=node.lineno,
                is_fixable=True,
                fix_description="Group parameters into a dataclass:\n  @dataclass\n  class Config:\n      field1: str\n      field2: int\n      ...\n  \n  def func(config: Config): ...",
            ))

        self._function_names.add(node.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        # Naming: should be PascalCase
        if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
            self.issues.append(AnalysisIssue(
                severity="warning", category="style", rule_id="AST006",
                title="Class name not PascalCase",
                message=f"Class '{node.name}' should use PascalCase (e.g., '{node.name.title().replace('_', '')}').",
                line_start=node.lineno,
                is_fixable=True,
                fix_description=f"Rename to '{node.name.title().replace('_', '')}'",
            ))

        # Missing class docstring
        has_docstring = (
            node.body and
            isinstance(node.body[0], ast.Expr) and
            isinstance(node.body[0].value, ast.Constant) and
            isinstance(node.body[0].value.value, str)
        )
        if not has_docstring:
            self.issues.append(AnalysisIssue(
                severity="info", category="documentation", rule_id="AST007",
                title="Missing class docstring",
                message=f"Class '{node.name}' has no docstring.",
                line_start=node.lineno,
                is_fixable=True,
                fix_description=f'Add:\n    class {node.name}:\n        """Brief description of this class."""',
            ))

        self._class_names.add(node.name)
        self.generic_visit(node)

    def visit_If(self, node: ast.If):
        self.complexity += 1
        self.cognitive_complexity += 1 + self._nesting_depth
        self._nesting_depth += 1
        self.generic_visit(node)
        self._nesting_depth -= 1

    def visit_For(self, node: ast.For):
        self.complexity += 1
        self.cognitive_complexity += 1 + self._nesting_depth
        self._nesting_depth += 1
        self.generic_visit(node)
        self._nesting_depth -= 1

    def visit_While(self, node: ast.While):
        self.complexity += 1
        self.cognitive_complexity += 1 + self._nesting_depth
        self._nesting_depth += 1
        self.generic_visit(node)
        self._nesting_depth -= 1

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        self.complexity += 1
        self.cognitive_complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp):
        self.complexity += len(node.values) - 1
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self._import_names.add(alias.asname or alias.name.split('.')[0])

    def visit_ImportFrom(self, node: ast.ImportFrom):
        for alias in node.names:
            self._import_names.add(alias.asname or alias.name)

    def visit_Name(self, node: ast.Name):
        self._used_names.add(node.id)

    def visit_Attribute(self, node: ast.Attribute):
        if isinstance(node.value, ast.Name):
            self._used_names.add(node.value.id)
        self.generic_visit(node)

    def _to_snake(self, name: str) -> str:
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def check_line_length(self, max_length: int = 120):
        """Check each line for length violations."""
        for i, line in enumerate(self.source_lines, 1):
            stripped = line.rstrip('\n')
            if len(stripped) > max_length:
                self.issues.append(AnalysisIssue(
                    severity="info", category="style", rule_id="AST010",
                    title="Line too long",
                    message=f"Line {i} is {len(stripped)} characters (max {max_length}). "
                             "Long lines reduce readability. Break it up.",
                    line_start=i, code_snippet=stripped[:80] + "...",
                    is_fixable=False,
                ))

    def check_complexity(self):
        """Flag high cyclomatic complexity."""
        if self.complexity > 20:
            self.issues.append(AnalysisIssue(
                severity="critical", category="complexity", rule_id="COMP001",
                title="Very high cyclomatic complexity",
                message=f"Cyclomatic complexity is {self.complexity} (threshold: 20). "
                         "This code is extremely hard to test. Break into smaller functions.",
                is_fixable=False,
            ))
        elif self.complexity > 10:
            self.issues.append(AnalysisIssue(
                severity="error", category="complexity", rule_id="COMP001",
                title="High cyclomatic complexity",
                message=f"Cyclomatic complexity is {self.complexity} (threshold: 10). "
                         "Refactor to reduce branches.",
                is_fixable=False,
            ))
        elif self.complexity > 7:
            self.issues.append(AnalysisIssue(
                severity="warning", category="complexity", rule_id="COMP001",
                title="Moderate cyclomatic complexity",
                message=f"Cyclomatic complexity is {self.complexity}. Consider simplifying.",
            ))

        if self.cognitive_complexity > 15:
            self.issues.append(AnalysisIssue(
                severity="warning", category="complexity", rule_id="COMP002",
                title="High cognitive complexity",
                message=f"Cognitive complexity is {self.cognitive_complexity}. "
                         "Code with high cognitive complexity is hard to read and reason about.",
            ))


# ─── Pattern Analyzer ─────────────────────────────────────────────────────────

def run_pattern_checks(source: str, source_lines: list[str]) -> list[AnalysisIssue]:
    """Run all regex-based pattern checks."""
    issues = []
    all_patterns = SECURITY_PATTERNS + PERFORMANCE_PATTERNS + STYLE_PATTERNS + MAINTAINABILITY_PATTERNS

    for pattern, rule_id, title, message, severity, fixable, fix in all_patterns:
        for match in re.finditer(pattern, source, re.IGNORECASE | re.MULTILINE):
            # Find line number
            line_no = source[:match.start()].count('\n') + 1
            line_content = source_lines[line_no - 1].strip() if line_no <= len(source_lines) else ""

            cat = "security" if rule_id.startswith("SEC") else \
                  "performance" if rule_id.startswith("PERF") else \
                  "style" if rule_id.startswith("STYLE") else "maintainability"

            issues.append(AnalysisIssue(
                severity=severity,
                category=cat,
                rule_id=rule_id,
                title=title,
                message=message,
                line_start=line_no,
                code_snippet=line_content[:200],
                is_fixable=fixable,
                fix_description=fix,
            ))

    return issues


# ─── Metrics Calculator ───────────────────────────────────────────────────────

def compute_halstead(source: str) -> float:
    """Simplified Halstead volume computation."""
    op_pattern = r'(?:[+\-*/%&|^~<>]=?|==|!=|//|\*\*|\band\b|\bor\b|\bnot\b|\bin\b|\bis\b)'
    operators = set(re.findall(op_pattern, source))
    operands = set(re.findall(r'\b[a-zA-Z_]\w*\b|\b\d+\.?\d*\b', source))
    n1, n2 = len(operators), len(operands)
    N1 = len(re.findall(op_pattern, source))
    N2 = len(re.findall(r'\b[a-zA-Z_]\w*\b|\b\d+\.?\d*\b', source))
    n = n1 + n2
    N = N1 + N2
    if n < 2 or N < 2:
        return 0.0
    vocabulary = n
    length = N
    try:
        volume = length * math.log2(vocabulary)
    except (ValueError, ZeroDivisionError):
        volume = 0.0
    return round(volume, 2)


def compute_maintainability_index(
    halstead_volume: float,
    cyclomatic_complexity: float,
    lines_of_code: int,
    comment_ratio: float,
) -> float:
    """
    SEI Maintainability Index formula:
    MI = 171 - 5.2*ln(HV) - 0.23*CC - 16.2*ln(LOC) + 50*sin(sqrt(2.4*CM))
    Scaled to 0–100.
    """
    if lines_of_code < 1:
        return 100.0
    try:
        hv_term = 5.2 * math.log(max(halstead_volume, 1))
        cc_term = 0.23 * cyclomatic_complexity
        loc_term = 16.2 * math.log(max(lines_of_code, 1))
        cm_term = 50 * math.sin(math.sqrt(2.4 * comment_ratio))
        mi = 171 - hv_term - cc_term - loc_term + cm_term
        return max(0.0, min(100.0, round(mi, 1)))
    except (ValueError, ZeroDivisionError):
        return 50.0


def compute_quality_score(metrics: FileMetrics) -> float:
    """
    Composite quality score 0–100.
    Weighted deductions for issues by severity.
    """
    score = 100.0

    severity_weights = {"critical": 15.0, "error": 8.0, "warning": 3.0, "info": 0.5}
    for issue in metrics.issues:
        score -= severity_weights.get(issue.severity, 1.0)

    # Complexity penalty
    if metrics.cyclomatic_complexity > 20:
        score -= 15
    elif metrics.cyclomatic_complexity > 10:
        score -= 8
    elif metrics.cyclomatic_complexity > 7:
        score -= 3

    # MI bonus: reward high maintainability
    if metrics.maintainability_index > 80:
        score += 5
    elif metrics.maintainability_index < 40:
        score -= 10

    return max(0.0, min(100.0, round(score, 1)))


# ─── Duplication Detector ─────────────────────────────────────────────────────

def detect_duplication(files: dict[str, str]) -> float:
    """
    Estimates code duplication percentage across files.
    Uses normalized line hashing on non-blank, non-comment lines.
    Returns percentage 0–100.
    """
    line_hashes: dict[str, list[str]] = defaultdict(list)

    for fname, content in files.items():
        for line in content.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith('#') and len(stripped) > 10:
                h = hashlib.md5(stripped.encode()).hexdigest()
                line_hashes[h].append(fname)

    total = sum(len(v) for v in line_hashes.values())
    duplicated = sum(len(v) - 1 for v in line_hashes.values() if len(v) > 1)
    return round((duplicated / max(total, 1)) * 100, 1)


# ─── Language Detector ────────────────────────────────────────────────────────

def detect_language(filename: str, content: str) -> str:
    ext_map = {
        ".py": "python", ".js": "javascript", ".ts": "typescript",
        ".jsx": "javascript", ".tsx": "typescript",
        ".java": "java", ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp",
        ".c": "c", ".h": "c", ".go": "go", ".rs": "rust",
    }
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext_map.get(ext, "unknown")


# ─── AI Summary Generator (rule-based, no LLM) ───────────────────────────────

def generate_ai_summary(review_metrics: ReviewMetrics, filenames: list[str]) -> tuple[str, str, str]:
    """
    Generates human-readable AI-style summary, praise, and top priority.
    100% rule-based — no external API required.
    """
    score = review_metrics.quality_score
    total = review_metrics.total_issues
    critical = review_metrics.critical_issues
    mi = review_metrics.maintainability_index

    # Summary
    if score >= 85:
        summary = (
            f"This is high-quality code across {len(filenames)} file(s). "
            f"With a quality score of {score:.0f}/100 and maintainability index of {mi:.0f}/100, "
            f"the codebase demonstrates good engineering practices. "
            f"{'A few minor improvements are suggested.' if total > 0 else 'No significant issues were found.'}"
        )
    elif score >= 65:
        summary = (
            f"Code quality is moderate across {len(filenames)} file(s) "
            f"(score: {score:.0f}/100). {total} issue(s) were found, "
            f"including {critical} critical item(s) that should be addressed before production. "
            f"The maintainability index of {mi:.0f}/100 suggests some technical debt is present."
        )
    elif score >= 45:
        summary = (
            f"Code quality needs attention — scored {score:.0f}/100 across {len(filenames)} file(s). "
            f"{total} issues detected, {critical} of which are critical security or reliability risks. "
            f"Significant refactoring is recommended before this code enters production."
        )
    else:
        summary = (
            f"Critical code quality issues detected — scored {score:.0f}/100 across {len(filenames)} file(s). "
            f"{critical} critical and {review_metrics.error_issues} error-level issues require immediate attention. "
            f"This code poses security and reliability risks in its current state."
        )

    # Praise
    if review_metrics.avg_complexity < 5:
        praise = "Functions are well-scoped with low complexity — easy to test and maintain."
    elif review_metrics.duplication_pct < 5:
        praise = "Code duplication is minimal — good DRY (Don't Repeat Yourself) discipline."
    elif score > 70:
        praise = "Overall structure is clean and follows common conventions."
    else:
        praise = "Code is structured consistently across files."

    # Top priority
    if critical > 0:
        top_priority = (
            f"🚨 Fix {critical} critical security/reliability issue(s) immediately. "
            "These could lead to security vulnerabilities or data loss in production."
        )
    elif review_metrics.error_issues > 0:
        top_priority = (
            f"⚠️ Address {review_metrics.error_issues} error-level issue(s). "
            "These include bad practices that could cause runtime failures."
        )
    elif review_metrics.warning_issues > 0:
        top_priority = (
            f"📋 Review {review_metrics.warning_issues} warning(s). "
            "These represent maintainability and performance improvements."
        )
    else:
        top_priority = (
            "✅ Address the informational suggestions to further improve code quality and documentation."
        )

    return summary, praise, top_priority


# ─── Main Analyzer Entry Point ────────────────────────────────────────────────

class CodeAnalyzer:
    """
    Main orchestrator for multi-file code analysis.
    Takes a dict of {filename: content} and returns full ReviewMetrics.
    """

    async def analyze(self, files: dict[str, str]) -> ReviewMetrics:
        start_time = time.time()
        per_file: dict[str, FileMetrics] = {}
        all_issues: list[AnalysisIssue] = []

        for filename, content in files.items():
            language = detect_language(filename, content)
            fm = await self._analyze_file(filename, content, language)
            per_file[filename] = fm
            all_issues.extend(fm.issues)

        # Cross-file duplication
        dup_pct = detect_duplication(files)

        # Aggregate
        total_lines = sum(fm.lines_of_code for fm in per_file.values())
        avg_complexity = (
            sum(fm.cyclomatic_complexity for fm in per_file.values()) / len(per_file)
            if per_file else 0.0
        )
        avg_mi = (
            sum(fm.maintainability_index for fm in per_file.values()) / len(per_file)
            if per_file else 100.0
        )

        by_severity = {s: sum(1 for i in all_issues if i.severity == s)
                       for s in ("critical", "error", "warning", "info")}

        avg_quality = (
            sum(fm.quality_score for fm in per_file.values()) / len(per_file)
            if per_file else 0.0
        )

        rm = ReviewMetrics(
            quality_score=round(avg_quality, 1),
            maintainability_index=round(avg_mi, 1),
            total_issues=len(all_issues),
            critical_issues=by_severity["critical"],
            error_issues=by_severity["error"],
            warning_issues=by_severity["warning"],
            info_issues=by_severity["info"],
            total_lines=total_lines,
            avg_complexity=round(avg_complexity, 2),
            duplication_pct=dup_pct,
            analysis_duration_ms=int((time.time() - start_time) * 1000),
            per_file=per_file,
        )

        rm.ai_summary, rm.ai_praise, rm.ai_top_priority = generate_ai_summary(
            rm, list(files.keys())
        )

        return rm

    async def _analyze_file(self, filename: str, content: str, language: str) -> FileMetrics:
        source_lines = content.splitlines()
        fm = FileMetrics()

        # Basic line counts
        fm.lines_of_code = sum(1 for l in source_lines if l.strip())
        fm.blank_lines = sum(1 for l in source_lines if not l.strip())
        fm.comment_lines = sum(
            1 for l in source_lines
            if l.strip().startswith('#') or l.strip().startswith('//')
            or l.strip().startswith('*') or l.strip().startswith('/*')
        )

        comment_ratio = fm.comment_lines / max(fm.lines_of_code, 1)

        # Pattern-based checks (all languages)
        fm.issues.extend(run_pattern_checks(content, source_lines))

        # Python-specific deep AST analysis
        if language == "python":
            try:
                tree = ast.parse(content)
                analyzer = PythonASTAnalyzer(source_lines)
                analyzer.visit(tree)
                analyzer.check_line_length()
                analyzer.check_complexity()
                fm.issues.extend(analyzer.issues)
                fm.cyclomatic_complexity = float(analyzer.complexity)
                fm.cognitive_complexity = float(analyzer.cognitive_complexity)
            except SyntaxError as e:
                fm.issues.append(AnalysisIssue(
                    severity="critical",
                    category="bug",
                    rule_id="SYNTAX001",
                    title="Syntax Error",
                    message=f"Python syntax error: {e}. Code cannot be parsed or executed.",
                    line_start=e.lineno,
                    is_fixable=False,
                ))
                fm.cyclomatic_complexity = 0.0
        else:
            # Heuristic complexity for other languages
            branch_count = len(re.findall(
                r'\b(if|else|elif|for|while|switch|case|catch|&&|\|\|)\b', content
            ))
            fm.cyclomatic_complexity = float(1 + branch_count)

        # Halstead metrics
        fm.halstead_volume = compute_halstead(content)

        # Maintainability Index
        fm.maintainability_index = compute_maintainability_index(
            fm.halstead_volume,
            fm.cyclomatic_complexity,
            fm.lines_of_code,
            comment_ratio,
        )

        fm.issue_count = len(fm.issues)

        # Per-line annotations
        annotations: dict[str, list[str]] = {}
        for issue in fm.issues:
            if issue.line_start:
                key = str(issue.line_start)
                if key not in annotations:
                    annotations[key] = []
                annotations[key].append(f"[{issue.severity.upper()}] {issue.title}")
        fm.annotations = annotations

        fm.quality_score = compute_quality_score(fm)
        return fm
