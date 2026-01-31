import shutil
import tempfile
import pathlib
import json
from ai_context_core.analyzer import engine, fs_utils


class TestIncrementalCache:
    def setup_method(self):
        self.test_dir = pathlib.Path(tempfile.mkdtemp())
        self.src_dir = self.test_dir / "src"
        self.src_dir.mkdir()

        # Create dummy python files
        (self.src_dir / "module_a.py").write_text("def foo():\n    pass")
        (self.src_dir / "module_b.py").write_text("class Bar:\n    pass")

    def teardown_method(self):
        shutil.rmtree(self.test_dir)

    def test_cache_creation_and_usage(self):
        analyzer = engine.ProjectAnalyzer(str(self.test_dir))

        # 1. First run (Cold Cache)
        results_1 = analyzer.analyze()

        assert len(results_1["complexity"]["most_complex_modules"]) == 2
        cache_file = self.test_dir / ".ai_context_cache.json"
        assert cache_file.exists()

        # Verify cache content
        cache_data = json.loads(cache_file.read_text())
        assert len(cache_data) == 2
        assert "src/module_a.py" in cache_data

        # 2. Second run (Warm Cache)
        # Re-initialize to simulate fresh run ensuring it loads from disk
        analyzer_2 = engine.ProjectAnalyzer(str(self.test_dir))

        results_2 = analyzer_2.analyze()

        # Ideally cached run is faster, but with 2 tiny files overhead might dominate.
        # So we check if results are identical.
        assert results_1["metrics"] == results_2["metrics"]

    def test_cache_invalidation(self):
        analyzer = engine.ProjectAnalyzer(str(self.test_dir))
        analyzer.analyze()

        # Modify a file
        (self.src_dir / "module_a.py").write_text("def foo():\n    print('modified')")

        # Run again
        analyzer_2 = engine.ProjectAnalyzer(str(self.test_dir))
        analyzer_2.analyze()

        # Check if modification was picked up (e.g. by checking hash in cache)
        cache_data = json.loads((self.test_dir / ".ai_context_cache.json").read_text())
        new_hash = fs_utils.calculate_file_hash(self.src_dir / "module_a.py")

        assert cache_data["src/module_a.py"]["hash"] == new_hash
