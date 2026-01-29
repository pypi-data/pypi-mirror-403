#!/usr/bin/env python3
"""
Benchmarking script for nameplate parsing functions.

This script measures the performance of the address, name, and contact
parsing functions under various conditions. It provides timing data
for single operations and throughput numbers for batch processing.

Usage:
    uv run python scripts/benchmark.py
    uv run python scripts/benchmark.py --iterations 10000
    uv run python scripts/benchmark.py --format json

Output:
    Displays timing statistics including:
    - Mean, median, min, max times per operation
    - Operations per second (throughput)
    - Batch processing efficiency

Requirements:
    - Python 3.12+
    - nameplate package installed

Example Output:
    === Address Parsing Benchmarks ===
    Simple address:     0.045 ms/op (22,222 ops/sec)
    Complex address:    0.052 ms/op (19,231 ops/sec)
    Batch (100):        3.2 ms total (32 µs/item)
"""

import argparse
import json
import statistics
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nameplate import (
    parse_address,
    parse_addresses,
    parse_contact,
    parse_contacts,
    parse_name,
    parse_names,
)


# =============================================================================
# BENCHMARK DATA
# =============================================================================

# Sample data for benchmarking - representative real-world examples
SAMPLE_ADDRESSES = [
    "123 Main St, Boston, MA 02101",
    "456 Oak Avenue Apt 2B, Chicago, IL 60601",
    "PO Box 789, Miami, FL 33101",
    "100 N Martin Luther King Jr Blvd, Atlanta, GA 30301",
    "1600 Pennsylvania Avenue NW, Washington, DC 20500",
    "350 Fifth Avenue Suite 7510, New York, NY 10118",
    "1 Infinite Loop, Cupertino, CA 95014",
    "RR 2 Box 45, Springfield, MO 65801",
    "742 Evergreen Terrace, Springfield, IL 62701",
    "221B Baker Street, London, CA 90210",  # Intentionally odd
]

SAMPLE_NAMES = [
    "John Smith",
    "Dr. Jane Doe",
    "Robert Johnson Jr.",
    "Mary Jane Watson-Parker",
    "Ludwig van Beethoven",
    "Dr. Martin Luther King Jr.",
    'William "Bill" Clinton',
    "Juan de la Vega",
    "Patrick O'Brien",
    "Gen. Douglas MacArthur",
]

SAMPLE_CONTACTS = [
    "John Smith 123 Main St, Boston, MA 02101",
    "Dr. Jane Doe 456 Oak Ave, Chicago, IL 60601",
    "Robert Johnson Jr. PO Box 789, Miami, FL 33101",
    "Mary Watson 100 N Main St, Denver, CO 80202",
    "Juan de la Vega 350 Fifth Ave, New York, NY 10118",
]


# =============================================================================
# BENCHMARK UTILITIES
# =============================================================================


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run."""

    name: str
    iterations: int
    times_ms: list[float] = field(default_factory=list)

    @property
    def mean_ms(self) -> float:
        """Mean time in milliseconds."""
        return statistics.mean(self.times_ms) if self.times_ms else 0

    @property
    def median_ms(self) -> float:
        """Median time in milliseconds."""
        return statistics.median(self.times_ms) if self.times_ms else 0

    @property
    def min_ms(self) -> float:
        """Minimum time in milliseconds."""
        return min(self.times_ms) if self.times_ms else 0

    @property
    def max_ms(self) -> float:
        """Maximum time in milliseconds."""
        return max(self.times_ms) if self.times_ms else 0

    @property
    def stdev_ms(self) -> float:
        """Standard deviation in milliseconds."""
        return statistics.stdev(self.times_ms) if len(self.times_ms) > 1 else 0

    @property
    def ops_per_sec(self) -> float:
        """Operations per second."""
        return 1000 / self.mean_ms if self.mean_ms > 0 else 0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return {
            "name": self.name,
            "iterations": self.iterations,
            "mean_ms": round(self.mean_ms, 4),
            "median_ms": round(self.median_ms, 4),
            "min_ms": round(self.min_ms, 4),
            "max_ms": round(self.max_ms, 4),
            "stdev_ms": round(self.stdev_ms, 4),
            "ops_per_sec": round(self.ops_per_sec, 2),
        }


def run_benchmark(name: str, func: callable, iterations: int) -> BenchmarkResult:
    """
    Run a benchmark for a given function.

    Args:
        name: Name of the benchmark
        func: Function to benchmark (called with no arguments)
        iterations: Number of times to run the function

    Returns:
        BenchmarkResult with timing statistics
    """
    result = BenchmarkResult(name=name, iterations=iterations)

    # Warmup run
    for _ in range(min(10, iterations // 10)):
        func()

    # Timed runs
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        result.times_ms.append((end - start) * 1000)

    return result


def format_result(result: BenchmarkResult) -> str:
    """Format a benchmark result for display."""
    return (
        f"{result.name:40} "
        f"{result.mean_ms:8.4f} ms/op "
        f"({result.ops_per_sec:,.0f} ops/sec) "
        f"[±{result.stdev_ms:.4f}]"
    )


# =============================================================================
# BENCHMARKS
# =============================================================================


def benchmark_address_parsing(iterations: int) -> list[BenchmarkResult]:
    """Run address parsing benchmarks."""
    results = []

    # Simple address
    results.append(
        run_benchmark(
            "parse_address (simple)",
            lambda: parse_address("123 Main St, Boston, MA 02101"),
            iterations,
        )
    )

    # Complex address with unit
    results.append(
        run_benchmark(
            "parse_address (with unit)",
            lambda: parse_address("456 Oak Ave Apt 2B, Chicago, IL 60601"),
            iterations,
        )
    )

    # PO Box
    results.append(
        run_benchmark(
            "parse_address (PO Box)",
            lambda: parse_address("PO Box 789, Miami, FL 33101"),
            iterations,
        )
    )

    # With normalization
    results.append(
        run_benchmark(
            "parse_address (normalize)",
            lambda: parse_address("123 MAIN ST, BOSTON, MA 02101", normalize=True),
            iterations,
        )
    )

    # Batch of 10
    batch_10 = SAMPLE_ADDRESSES[:10]
    results.append(
        run_benchmark(
            "parse_addresses (batch=10)",
            lambda: parse_addresses(batch_10),
            iterations // 10,
        )
    )

    # Batch of 100
    batch_100 = SAMPLE_ADDRESSES * 10
    results.append(
        run_benchmark(
            "parse_addresses (batch=100)",
            lambda: parse_addresses(batch_100),
            iterations // 100,
        )
    )

    return results


def benchmark_name_parsing(iterations: int) -> list[BenchmarkResult]:
    """Run name parsing benchmarks."""
    results = []

    # Simple name
    results.append(
        run_benchmark(
            "parse_name (simple)",
            lambda: parse_name("John Smith"),
            iterations,
        )
    )

    # Name with prefix and suffix
    results.append(
        run_benchmark(
            "parse_name (prefix+suffix)",
            lambda: parse_name("Dr. John Smith Jr."),
            iterations,
        )
    )

    # Name with particles
    results.append(
        run_benchmark(
            "parse_name (particles)",
            lambda: parse_name("Ludwig van Beethoven"),
            iterations,
        )
    )

    # With normalization
    results.append(
        run_benchmark(
            "parse_name (normalize)",
            lambda: parse_name("JOHN SMITH", normalize=True),
            iterations,
        )
    )

    # Batch of 10
    batch_10 = SAMPLE_NAMES[:10]
    results.append(
        run_benchmark(
            "parse_names (batch=10)",
            lambda: parse_names(batch_10),
            iterations // 10,
        )
    )

    # Batch of 100
    batch_100 = SAMPLE_NAMES * 10
    results.append(
        run_benchmark(
            "parse_names (batch=100)",
            lambda: parse_names(batch_100),
            iterations // 100,
        )
    )

    return results


def benchmark_contact_parsing(iterations: int) -> list[BenchmarkResult]:
    """Run contact parsing benchmarks."""
    results = []

    # Simple contact
    results.append(
        run_benchmark(
            "parse_contact (simple)",
            lambda: parse_contact("John Smith 123 Main St, Boston, MA 02101"),
            iterations,
        )
    )

    # Complex contact
    results.append(
        run_benchmark(
            "parse_contact (complex)",
            lambda: parse_contact("Dr. Jane Doe Jr. 456 Oak Ave Apt 2B, Chicago, IL 60601"),
            iterations,
        )
    )

    # With normalization
    results.append(
        run_benchmark(
            "parse_contact (normalize)",
            lambda: parse_contact(
                "JOHN SMITH 123 MAIN ST, BOSTON, MA 02101",
                normalize=True,
            ),
            iterations,
        )
    )

    # Batch of 5
    batch_5 = SAMPLE_CONTACTS[:5]
    results.append(
        run_benchmark(
            "parse_contacts (batch=5)",
            lambda: parse_contacts(batch_5),
            iterations // 5,
        )
    )

    # Batch of 50
    batch_50 = SAMPLE_CONTACTS * 10
    results.append(
        run_benchmark(
            "parse_contacts (batch=50)",
            lambda: parse_contacts(batch_50),
            iterations // 50,
        )
    )

    return results


# =============================================================================
# MAIN
# =============================================================================


def main():
    """Run all benchmarks and display results."""
    parser = argparse.ArgumentParser(
        description="Benchmark nameplate parsing functions",
    )
    parser.add_argument(
        "--iterations",
        "-n",
        type=int,
        default=1000,
        help="Number of iterations per benchmark (default: 1000)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args()

    all_results = []

    # Run benchmarks
    print("Running benchmarks...", file=sys.stderr)

    print("\n=== Address Parsing ===", file=sys.stderr)
    address_results = benchmark_address_parsing(args.iterations)
    all_results.extend(address_results)

    print("=== Name Parsing ===", file=sys.stderr)
    name_results = benchmark_name_parsing(args.iterations)
    all_results.extend(name_results)

    print("=== Contact Parsing ===", file=sys.stderr)
    contact_results = benchmark_contact_parsing(args.iterations)
    all_results.extend(contact_results)

    # Output results
    if args.format == "json":
        output = {
            "iterations": args.iterations,
            "results": [r.to_dict() for r in all_results],
        }
        print(json.dumps(output, indent=2))
    else:
        print("\n" + "=" * 80)
        print("BENCHMARK RESULTS")
        print("=" * 80)

        print("\n--- Address Parsing ---")
        for r in address_results:
            print(format_result(r))

        print("\n--- Name Parsing ---")
        for r in name_results:
            print(format_result(r))

        print("\n--- Contact Parsing ---")
        for r in contact_results:
            print(format_result(r))

        print("\n" + "=" * 80)
        print(f"Total benchmarks: {len(all_results)}")
        print(f"Iterations per benchmark: {args.iterations}")


if __name__ == "__main__":
    main()
