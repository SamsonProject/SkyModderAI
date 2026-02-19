"""
SkyModderAI - Performance Benchmarking Suite

Benchmarks:
- Deterministic analysis speed
- Cache performance
- Export generation time
- Research pipeline throughput
- API response times

Run with: python scripts/benchmark_performance.py
"""

import json
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Benchmark:
    """Benchmark runner."""

    def __init__(self, name: str):
        self.name = name
        self.results: List[Dict[str, Any]] = []

    def run(self, func, *args, iterations: int = 10, **kwargs) -> Dict[str, Any]:
        """Run a function multiple times and collect metrics."""
        durations = []

        for i in range(iterations):
            start = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start
            durations.append(duration)

        # Calculate stats
        avg = sum(durations) / len(durations)
        min_d = min(durations)
        max_d = max(durations)
        p95 = sorted(durations)[int(len(durations) * 0.95)] if len(durations) > 1 else max_d

        stats = {
            "name": self.name,
            "iterations": iterations,
            "avg_ms": round(avg * 1000, 2),
            "min_ms": round(min_d * 1000, 2),
            "max_ms": round(max_d * 1000, 2),
            "p95_ms": round(p95 * 1000, 2),
        }

        self.results.append(stats)
        return stats

    def report(self) -> str:
        """Generate benchmark report."""
        report = []
        report.append("=" * 70)
        report.append("SkyModderAI Performance Benchmark Report")
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("=" * 70)
        report.append("")

        for result in self.results:
            report.append(f"\n{result['name']}")
            report.append("-" * len(result["name"]))
            report.append(f"  Iterations: {result['iterations']}")
            report.append(f"  Average:    {result['avg_ms']} ms")
            report.append(f"  Min:        {result['min_ms']} ms")
            report.append(f"  Max:        {result['max_ms']} ms")
            report.append(f"  P95:        {result['p95_ms']} ms")

        report.append("")
        report.append("=" * 70)

        return "\n".join(report)


def benchmark_deterministic_analysis(runner: Benchmark):
    """Benchmark deterministic analysis functions."""
    from deterministic_analysis import (
        analyze_load_order_deterministic,
        generate_bespoke_setups_deterministic,
    )

    print("\nRunning deterministic analysis benchmarks...")

    # Small mod list (10 mods)
    small_list = [f"Mod_{i}.esp" for i in range(10)]
    runner.run(
        analyze_load_order_deterministic,
        small_list,
        "skyrimse",
        iterations=20,
        name="Deterministic Analysis (10 mods)",
    )

    # Medium mod list (50 mods)
    medium_list = [f"Mod_{i}.esp" for i in range(50)]
    runner.run(
        analyze_load_order_deterministic,
        medium_list,
        "skyrimse",
        iterations=20,
        name="Deterministic Analysis (50 mods)",
    )

    # Large mod list (200 mods)
    large_list = [f"Mod_{i}.esp" for i in range(200)]
    runner.run(
        analyze_load_order_deterministic,
        large_list,
        "skyrimse",
        iterations=10,
        name="Deterministic Analysis (200 mods)",
    )

    # Setup generation
    preferences = {"combat": "souls_like", "graphics": "balanced", "stability": "max"}
    runner.run(
        generate_bespoke_setups_deterministic,
        "skyrimse",
        preferences,
        None,
        3,
        iterations=20,
        name="Bespoke Setup Generation",
    )


def benchmark_caching(runner: Benchmark):
    """Benchmark cache operations."""
    from cache_service import get_cache

    print("\nRunning cache benchmarks...")

    cache = get_cache()

    # Write benchmark
    def write_test():
        cache.set("benchmark:test", {"data": "test"}, ttl=60)

    runner.run(write_test, iterations=50, name="Cache Write")

    # Read benchmark
    def read_test():
        cache.get("benchmark:test")

    runner.run(read_test, iterations=100, name="Cache Read")

    # Search cache benchmark
    def search_cache():
        cache.cache_search("skyrimse", "texture mods")
        cache.set_search("skyrimse", "texture mods", [{"result": "test"}], ttl=3600)

    runner.run(search_cache, iterations=50, name="Cache Search Operations")


def benchmark_presentation(runner: Benchmark):
    """Benchmark presentation/export functions."""
    from presentation_service import (
        _format_as_markdown,
        create_guide_content,
        format_as_html,
        format_as_latex,
    )

    print("\nRunning presentation benchmarks...")

    # Create test content
    content = create_guide_content(
        title="Benchmark Test Guide",
        summary="Testing export performance",
        sections=[{"title": f"Section {i}", "content": "Content here"} for i in range(10)],
        warnings=[{"level": "high", "message": "Test warning"} for _ in range(5)],
        recommendations=[{"priority": "high", "content": f"Recommendation {i}"} for i in range(10)],
        sources=[
            {"title": f"Source {i}", "url": "https://example.com", "credibility_score": 0.9}
            for i in range(5)
        ],
    )

    # LaTeX formatting
    runner.run(format_as_latex, content, iterations=10, name="LaTeX Formatting")

    # HTML formatting
    runner.run(format_as_html, content, iterations=20, name="HTML Formatting")

    # Markdown formatting
    runner.run(_format_as_markdown, content, iterations=20, name="Markdown Formatting")


def benchmark_reliability(runner: Benchmark):
    """Benchmark reliability weighting."""
    from reliability_weighter import get_reliability_weighter

    print("\nRunning reliability weighting benchmarks...")

    weighter = get_reliability_weighter()

    # Test source
    source = {
        "url": "https://nexusmods.com/skyrimspecialedition/mods/123",
        "type": "nexus_mods",
        "endorsements": 1500,
        "published_date": "2025-06-15T00:00:00",
        "author": "Arthmoor",
        "content": "Unofficial Skyrim Special Edition Patch",
        "game_version": "skyrimse",
    }

    def score_source():
        return weighter.score_source(source)

    runner.run(score_source, iterations=100, name="Reliability Scoring")

    # Filter benchmark
    sources = [source.copy() for _ in range(50)]

    def filter_sources():
        return weighter.filter_by_reliability(sources, min_score=0.5)

    runner.run(filter_sources, iterations=20, name="Reliability Filtering (50 sources)")


def run_all_benchmarks():
    """Run all benchmarks and generate report."""
    runner = Benchmark("SkyModderAI")

    print("=" * 70)
    print("SkyModderAI Performance Benchmarking Suite")
    print("=" * 70)

    benchmark_deterministic_analysis(runner)
    benchmark_caching(runner)
    benchmark_presentation(runner)
    benchmark_reliability(runner)

    # Generate report
    report = runner.report()
    print("\n" + report)

    # Save report
    report_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "benchmark_report.json"
    )

    with open(report_path, "w") as f:
        json.dump(runner.results, f, indent=2)

    print(f"\nReport saved to: {report_path}")

    return runner.results


if __name__ == "__main__":
    results = run_all_benchmarks()

    # Exit with appropriate code
    avg_times = [r["avg_ms"] for r in results]
    if any(t > 1000 for t in avg_times):  # Any avg > 1 second
        print("\n⚠️  Warning: Some operations exceeded 1 second average")
        sys.exit(1)
    else:
        print("\n✅ All benchmarks passed (avg < 1 second)")
        sys.exit(0)
