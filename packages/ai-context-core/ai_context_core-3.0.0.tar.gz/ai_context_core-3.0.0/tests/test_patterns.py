import unittest
import ast
from src.ai_context_core.analyzer.patterns import detect_singleton


class TestPatterns(unittest.TestCase):
    def test_singleton_new_override(self):
        code = """
class MySingleton:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
"""
        tree = ast.parse(code)
        results = detect_singleton(tree)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["class"], "MySingleton")
        self.assertGreaterEqual(results[0]["confidence"], 60)

    def test_singleton_get_instance(self):
        code = """
class Database:
    _inst = None
    @classmethod
    def get_instance(cls):
        if not cls._inst:
            cls._inst = Database()
        return cls._inst
"""
        tree = ast.parse(code)
        results = detect_singleton(tree)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["class"], "Database")
        # Static var (20) + Classmethod get_instance (30) = 50
        self.assertEqual(results[0]["confidence"], 50)

    def test_not_a_singleton(self):
        code = """
class NormalClass:
    def __init__(self, x):
        self.x = x
"""
        tree = ast.parse(code)
        results = detect_singleton(tree)
        self.assertEqual(len(results), 0)

    def test_factory_class_and_method(self):
        from src.ai_context_core.analyzer.patterns import detect_factory

        code = """
class WidgetFactory:
    def create_widget(self, type):
        if type == 'a':
            return WidgetA()
        return WidgetB()
"""
        tree = ast.parse(code)
        results = detect_factory(tree)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["class"], "WidgetFactory")
        self.assertEqual(results[0]["method"], "create_widget")
        # Class name "Factory" (30) + name prefix "create_" (40) + returns Call (30) = 100
        self.assertEqual(results[0]["confidence"], 100)

    def test_factory_method_only(self):
        from src.ai_context_core.analyzer.patterns import detect_factory

        code = """
class ServiceProvider:
    def build_service(self):
        return ExternalService()
"""
        tree = ast.parse(code)
        results = detect_factory(tree)
        self.assertEqual(len(results), 1)
        # prefix "build_" (40) + returns Call (30) = 70
        self.assertEqual(results[0]["confidence"], 70)

    def test_observer_pattern(self):
        from src.ai_context_core.analyzer.patterns import detect_observer

        code = """
class NewsAgency:
    def __init__(self):
        self.subscribers = []
    
    def subscribe(self, subscriber):
        self.subscribers.append(subscriber)
        
    def notify_all(self, message):
        for sub in self.subscribers:
            sub.update(message)
"""
        tree = ast.parse(code)
        results = detect_observer(tree)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["class"], "NewsAgency")
        # init collection (20) + subscribe (15) + notify (15) + loop in notify (30) = 80
        self.assertEqual(results[0]["confidence"], 80)

    def test_strategy_pattern(self):
        from src.ai_context_core.analyzer.patterns import detect_strategy

        code = """
class DataProcessor:
    def __init__(self, strategy):
        self.strategy = strategy
        
    def process(self, data):
        return self.strategy.execute(data)
"""
        tree = ast.parse(code)
        results = detect_strategy(tree)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["class"], "DataProcessor")
        # injection (30) + call (40) = 70
        self.assertEqual(results[0]["confidence"], 70)

    def test_functional_decorator(self):
        from src.ai_context_core.analyzer.patterns import detect_decorator

        code = """
import functools
def my_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper
"""
        tree = ast.parse(code)
        results = detect_decorator(tree)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["class"], "my_decorator")
        # inner returns (50) + wraps (40) = 90
        self.assertEqual(results[0]["confidence"], 90)

    def test_class_decorator(self):
        from src.ai_context_core.analyzer.patterns import detect_decorator

        code = """
class ClassDecorator:
    def __init__(self, func):
        self.func = func
    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)
"""
        tree = ast.parse(code)
        results = detect_decorator(tree)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["class"], "ClassDecorator")
        # init+call = 60
        self.assertEqual(results[0]["confidence"], 60)

    def test_singleton_confidence_levels(self):
        from src.ai_context_core.analyzer.patterns import detect_singleton

        # Only static var = 20 (not reported as < 50)
        code_low = "class A: _instance = None"
        self.assertEqual(len(detect_singleton(ast.parse(code_low))), 0)

        # Static var (20) + method (30) = 50
        code_mid = """
class B:
    _instance = None
    @classmethod
    def get_instance(cls): pass
"""
        self.assertEqual(detect_singleton(ast.parse(code_mid))[0]["confidence"], 50)

        # __new__ (60) + Static var (20) = 80
        code_high = """
class C:
    _instance = None
    def __new__(cls): pass
"""
        self.assertEqual(detect_singleton(ast.parse(code_high))[0]["confidence"], 80)


if __name__ == "__main__":
    unittest.main()
