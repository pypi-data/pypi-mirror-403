import os
from click.testing import CliRunner
from ai_context_core.analyzer.reporting import generate_dependency_diagram
from ai_context_core.analyzer.html_builder import HTMLBuilder
from ai_context_core.analyzer.ai_recommendations import AIRecommender
from ai_context_core.cli import cli


class TestVisualization:
    def test_mermaid_generation(self):
        deps = {
            "import_graph": {
                "src/module_a.py": ["src.module_b.utils"],
                "src/module_b/utils.py": ["src.module_c"],
                "src/module_c.py": [],
            }
        }
        graph = generate_dependency_diagram(deps)
        assert "graph TD" in graph
        # Check node cleaning logic
        assert "module_a --> utils" in graph
        assert "classDef module" in graph

    def test_html_builder(self):
        builder = HTMLBuilder("Test Report")
        builder.add_section("Section 1", "<p>Content</p>")
        html = builder.render()
        assert "<!DOCTYPE html>" in html
        assert "<title>Test Report</title>" in html
        assert "<h2>Section 1</h2>" in html

    def test_ai_recommender_heuristics(self):
        recommender = AIRecommender()
        # Mock analysis results triggering alerts
        results = {
            "metrics": {
                "quality_score": 40,  # Critical
                "docstring_coverage": 10,  # Low
                "test_files_count": 0,  # Critical
                "entry_points_count": 5,
            },
            "complexity": {"most_complex_modules": []},
        }
        recs = recommender.analyze_codebase(results)

        # Verify Critical Project Health
        assert any(
            r["priority"] == "Critical" and "Quality Score" in r["message"]
            for r in recs
        )
        # Verify Documentation Alert
        assert any(r["category"] == "Documentation" for r in recs)
        # Verify Testing Alert
        assert any(r["category"] == "Testing" for r in recs)

    def test_modules_heuristics(self):
        recommender = AIRecommender()
        module_data = {
            "complexity": 35,  # Critical > 30
            "maintenance_index": 40,  # Low < 50
        }
        suggestions = recommender.analyze_module(module_data)
        assert any("Critical Complexity" in s["message"] for s in suggestions)
        assert any("Low Maintainability" in s["message"] for s in suggestions)

    def test_cli_html_format(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create a dummy file to analyze
            with open("test_script.py", "w") as f:
                f.write("def foo(): pass\n")

            # Run with HTML format
            result = runner.invoke(cli, ["analyze", "--format", "html"])

            assert result.exit_code == 0
            assert os.path.exists("PROJECT_SUMMARY.html")
            assert not os.path.exists("PROJECT_SUMMARY.md")
            assert os.path.exists("AI_CONTEXT.md")

            # Verify HTML content
            with open("PROJECT_SUMMARY.html") as f:
                content = f.read()
                assert "<!DOCTYPE html>" in content
                assert "KEY METRICS" in content

    def test_cli_markdown_format_default(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open("test_script.py", "w") as f:
                f.write("def foo(): pass\n")

            result = runner.invoke(cli, ["analyze"])  # Default is markdown

            assert result.exit_code == 0
            assert os.path.exists("PROJECT_SUMMARY.md")
            assert not os.path.exists("PROJECT_SUMMARY.html")
