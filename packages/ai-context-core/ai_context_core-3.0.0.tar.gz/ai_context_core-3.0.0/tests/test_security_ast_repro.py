import ast
from ai_context_core.analyzer.issues import ASTSecurityDetector


def test_ast_security_no_false_positives():
    code = """
def safe_function():
    # This is a comment saying we should not use exec(
    print("This string contains eval( which should not be flagged")
    
    x = "os.system('rm -rf /')" # This is just a string variable
    
    return "subprocess.call( is dangerous but not here"
    """
    tree = ast.parse(code)
    detector = ASTSecurityDetector()
    issues = detector.detect(tree)

    # Should find NO issues because these are all strings or comments
    assert len(issues) == 0


def test_ast_security_detects_real_issues():
    code = """
import os
def unsafe_function():
    exec("print('hello')")
    eval("1 + 1")
    os.system("ls -la")
    """
    tree = ast.parse(code)
    detector = ASTSecurityDetector()
    issues = detector.detect(tree)

    patterns = [i["pattern"] for i in issues]
    assert "exec" in patterns
    assert "eval" in patterns
    assert "os.system" in patterns
