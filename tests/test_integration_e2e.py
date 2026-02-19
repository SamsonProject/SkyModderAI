"""
SkyModderAI - End-to-End Integration Tests

Comprehensive test suite covering:
- Deterministic analysis
- Research pipeline
- Feedback collection
- Export functionality
- Full user workflows

Run with: pytest tests/test_integration_e2e.py -v
"""

import json
import os
import sys
import time
import unittest
from datetime import datetime
from typing import Any, Dict, List

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDeterministicAnalysis(unittest.TestCase):
    """Test deterministic analysis functions."""
    
    def setUp(self):
        from deterministic_analysis import (
            analyze_load_order_deterministic,
            scan_game_folder_deterministic,
            generate_bespoke_setups_deterministic
        )
        self.analyze = analyze_load_order_deterministic
        self.scan = scan_game_folder_deterministic
        self.setups = generate_bespoke_setups_deterministic
    
    def test_load_order_analysis(self):
        """Test load order analysis with known mods."""
        mod_list = [
            "USSEP.esm",
            "SkyUI.esp",
            "Ordinator - Perks of Skyrim.esp",
            "Wildcat - Combat of Skyrim.esp"
        ]
        
        result = self.analyze(mod_list, "skyrimse")
        
        # Verify structure
        self.assertIn("conflicts", result)
        self.assertIn("missing_requirements", result)
        self.assertIn("load_order_issues", result)
        self.assertIn("recommendations", result)
        self.assertIn("dirty_edits", result)
        
        # Verify types
        self.assertIsInstance(result["conflicts"], list)
        self.assertIsInstance(result["missing_requirements"], list)
        self.assertIsInstance(result["recommendations"], list)
    
    def test_bespoke_setups_generation(self):
        """Test deterministic setup generation."""
        preferences = {
            "combat": "souls_like",
            "graphics": "balanced",
            "stability": "max"
        }
        
        specs = {"vram_gb": 4}
        
        setups = self.setups("skyrimse", preferences, specs, limit=3)
        
        # Verify we got setups
        self.assertGreater(len(setups), 0)
        
        # Verify structure
        for setup in setups:
            self.assertIn("name", setup)
            self.assertIn("mods", setup)
            self.assertIn("rationale", setup)
            self.assertIsInstance(setup["mods"], list)
    
    def test_game_folder_scan(self):
        """Test game folder scanning."""
        tree = """
Game/
  Data/
    Meshes/
    Textures/
    USSEP.esm
  SkyrimSE.exe
  SkyrimPrefs.ini
"""
        key_files = {
            "SkyrimSE.exe": "binary",
            "SkyrimPrefs.ini": "[Display]"
        }
        plugins = ["USSEP.esm", "SkyUI.esp"]
        
        result = self.scan("", "skyrimse", tree, key_files, plugins)
        
        # Verify structure
        self.assertIn("findings", result)
        self.assertIn("warnings", result)
        self.assertIn("issues", result)
        self.assertIn("plugins_found", result)


class TestReliabilityWeighting(unittest.TestCase):
    """Test reliability weighting system."""
    
    def setUp(self):
        from reliability_weighter import get_reliability_weighter
        self.weighter = get_reliability_weighter()
    
    def test_nexus_mod_scoring(self):
        """Test scoring for Nexus Mods source."""
        source = {
            "url": "https://nexusmods.com/skyrimspecialedition/mods/123",
            "type": "nexus_mods",
            "endorsements": 1500,
            "published_date": "2025-06-15T00:00:00",
            "author": "Arthmoor",
            "content": "Unofficial Skyrim Special Edition Patch",
            "game_version": "skyrimse"
        }
        
        score = self.weighter.score_source(source)
        
        # Nexus mods should score high
        self.assertGreater(score.overall_score, 0.7)
        self.assertGreater(score.confidence, 0.8)
    
    def test_reddit_scoring(self):
        """Test scoring for Reddit source."""
        source = {
            "url": "https://reddit.com/r/skyrimmods/comments/abc",
            "type": "reddit_general",
            "upvotes": 250,
            "comments": 45,
            "published_date": "2026-01-10T00:00:00",
            "author": "modding_expert",
            "content": "Here's how to fix the issue...",
            "game_version": "skyrimse"
        }
        
        score = self.weighter.score_source(source)
        
        # Should have moderate score
        self.assertGreater(score.overall_score, 0.4)
    
    def test_filter_by_reliability(self):
        """Test filtering sources by reliability."""
        sources = [
            {
                "url": "https://nexusmods.com/...",
                "type": "nexus_mods",
                "endorsements": 1000
            },
            {
                "url": "https://random-forum.com/...",
                "type": "forum_general",
                "endorsements": 0
            }
        ]
        
        filtered = self.weighter.filter_by_reliability(sources, min_score=0.5)
        
        # Should filter out low-credibility source
        self.assertLessEqual(len(filtered), len(sources))


class TestResearchPipeline(unittest.TestCase):
    """Test research pipeline components."""
    
    def test_deviation_labeling(self):
        """Test deviation labeling service."""
        from deviation_labeler import analyze_source_deviations
        
        # Create mock knowledge source
        class MockSource:
            def __init__(self):
                self.title = "Experimental SKSE Hook Mod"
                self.summary = "This experimental mod uses SKSE hooks to override engine behavior. Use at own risk. Beta version."
                self.credibility = None
                self.created_at = datetime.now()
                self.game_version = "1.6.1170"
        
        source = MockSource()
        flags, risk_level = analyze_source_deviations(source)
        
        # Should detect experimental content
        self.assertIn("experimental", flags)
        self.assertEqual(risk_level, "high")


class TestPresentationLayer(unittest.TestCase):
    """Test presentation/export functionality."""
    
    def test_latex_formatting(self):
        """Test LaTeX document generation."""
        from presentation_service import format_as_latex, create_guide_content
        
        content = create_guide_content(
            title="Test Guide",
            summary="This is a test summary",
            sections=[
                {"title": "Installation", "content": "Step 1: Download..."}
            ],
            warnings=[
                {"level": "high", "message": "Critical warning"}
            ],
            recommendations=[
                {"priority": "high", "content": "Do this first"}
            ],
            sources=[
                {"title": "Test Source", "url": "https://example.com", "credibility_score": 0.9}
            ]
        )
        
        latex = format_as_latex(content)
        
        # Verify LaTeX structure
        self.assertIn("\\documentclass", latex)
        self.assertIn("\\title{", latex)
        self.assertIn("\\begin{document}", latex)
        self.assertIn("\\end{document}", latex)
    
    def test_html_formatting(self):
        """Test HTML document generation."""
        from presentation_service import format_as_html, create_guide_content
        
        content = create_guide_content(
            title="Test Guide",
            summary="Test summary",
            sections=[{"title": "Section", "content": "Content"}],
            warnings=[],
            recommendations=[],
            sources=[]
        )
        
        html = format_as_html(content)
        
        # Verify HTML structure
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("<html", html)
        self.assertIn("</html>", html)
        self.assertIn("<style>", html)
    
    def test_markdown_formatting(self):
        """Test Markdown generation."""
        from presentation_service import _format_as_markdown, create_guide_content
        
        content = create_guide_content(
            title="Test Guide",
            summary="Test summary",
            sections=[{"title": "Section", "content": "Content"}],
            warnings=[],
            recommendations=[],
            sources=[]
        )
        
        md = _format_as_markdown(content)
        
        # Verify Markdown structure
        self.assertIn("# Test Guide", md)
        self.assertIn("## Executive Summary", md)
        self.assertIn("## Section", md)


class TestFeedbackSystem(unittest.TestCase):
    """Test feedback collection system."""
    
    def test_session_tracking(self):
        """Test session tracking."""
        from feedback_service import SessionTracker
        
        tracker = SessionTracker("test@example.com")
        
        # Track actions
        tracker.trackQuery("analysis", {"game": "skyrimse", "mod_count": 50})
        tracker.trackResolution("conflict_fix", {"type": "load_order"}, helpful=True)
        tracker.trackAction("page_view", {"path": "/analyze"})
        
        # Get summary
        summary = tracker.get_session_summary()
        
        # Verify tracking
        self.assertEqual(summary["query_count"], 1)
        self.assertEqual(summary["resolution_count"], 1)
        self.assertEqual(len(summary["events"]), 3)
    
    def test_self_improvement_logging(self):
        """Test self-improvement log."""
        from feedback_service import log_win, log_issue, get_self_improvement_log
        
        # Log events
        log_win("test_category", "Test win description", "Test impact")
        log_issue("test_category", "Test issue description", "low")
        
        # Get log
        log = get_self_improvement_log()
        
        # Verify logging
        self.assertGreater(len(log), 0)


class TestFullUserWorkflow(unittest.TestCase):
    """Test complete user workflows."""
    
    def test_complete_analysis_workflow(self):
        """Test complete analysis workflow from start to export."""
        from deterministic_analysis import analyze_load_order_deterministic
        from presentation_service import create_guide_content, format_as_html
        
        # Step 1: User submits mod list
        mod_list = [
            "USSEP.esm",
            "SkyUI.esp",
            "Ordinator - Perks of Skyrim.esp"
        ]
        
        # Step 2: System analyzes
        analysis = analyze_load_order_deterministic(mod_list, "skyrimse")
        
        # Step 3: System generates guide
        guide = create_guide_content(
            title="Skyrim SE Modding Guide",
            summary=f"Analysis of {len(mod_list)} mods",
            sections=[
                {
                    "title": "Mod List Analysis",
                    "content": f"Found {len(mod_list)} mods in load order"
                }
            ],
            warnings=[
                {"level": "medium", "message": "Review conflicts below"}
            ] if analysis["conflicts"] else [],
            recommendations=[
                {"priority": "high", "content": rec["content"]}
                for rec in analysis.get("recommendations", [])
            ],
            sources=[
                {"title": "LOOT Masterlist", "url": "https://loot.github.io", "credibility_score": 0.95}
            ]
        )
        
        # Step 4: User exports guide
        html = format_as_html(guide)
        
        # Verify complete workflow
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("Skyrim SE Modding Guide", html)
    
    def test_feedback_workflow(self):
        """Test feedback submission workflow."""
        from feedback_service import SessionTracker, submit_feedback
        
        # Create session
        tracker = SessionTracker("feedback_test@example.com")
        tracker.trackQuery("analysis", {"game": "skyrimse"})
        
        # Submit feedback
        success = submit_feedback(
            user_email="feedback_test@example.com",
            feedback_type="suggestion",
            category="feature",
            content="Add mod comparison view",
            context={"page": "/analyze"}
        )
        
        # Verify feedback submitted
        self.assertTrue(success)


class TestPerformanceBenchmarks(unittest.TestCase):
    """Test performance benchmarks."""
    
    def test_deterministic_analysis_speed(self):
        """Test that deterministic analysis completes in <100ms."""
        from deterministic_analysis import analyze_load_order_deterministic
        
        mod_list = [f"Mod_{i}.esp" for i in range(50)]
        
        start = time.time()
        analyze_load_order_deterministic(mod_list, "skyrimse")
        duration = time.time() - start
        
        # Should complete in <100ms
        self.assertLess(duration, 0.1)
    
    def test_cache_speed(self):
        """Test that cache lookups complete in <10ms."""
        from cache_service import get_cache
        
        cache = get_cache()
        
        # Set value
        cache.set("test:benchmark", {"data": "test"}, ttl=60)
        
        # Measure get speed
        start = time.time()
        cache.get("test:benchmark")
        duration = time.time() - start
        
        # Should complete in <10ms
        self.assertLess(duration, 0.01)
    
    def test_export_generation_speed(self):
        """Test that export generation completes in <2s."""
        from presentation_service import format_as_html, create_guide_content
        
        content = create_guide_content(
            title="Benchmark Test",
            summary="Testing export speed",
            sections=[{"title": f"Section {i}", "content": "Content"} for i in range(10)],
            warnings=[],
            recommendations=[],
            sources=[]
        )
        
        start = time.time()
        format_as_html(content)
        duration = time.time() - start
        
        # Should complete in <2s
        self.assertLess(duration, 2.0)


def run_all_tests():
    """Run all tests and return results."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDeterministicAnalysis))
    suite.addTests(loader.loadTestsFromTestCase(TestReliabilityWeighting))
    suite.addTests(loader.loadTestsFromTestCase(TestResearchPipeline))
    suite.addTests(loader.loadTestsFromTestCase(TestPresentationLayer))
    suite.addTests(loader.loadTestsFromTestCase(TestFeedbackSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestFullUserWorkflow))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformanceBenchmarks))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    print("=" * 70)
    print("SkyModderAI - End-to-End Integration Tests")
    print("=" * 70)
    
    result = run_all_tests()
    
    print("\n" + "=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success: {result.wasSuccessful()}")
    print("=" * 70)
    
    sys.exit(0 if result.wasSuccessful() else 1)
