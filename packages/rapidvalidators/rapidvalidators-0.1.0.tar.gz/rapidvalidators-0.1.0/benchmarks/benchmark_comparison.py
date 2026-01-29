#!/usr/bin/env python3
"""
Performance benchmark comparing rapidvalidators (Rust) vs validators (Python)

Run with: python benchmarks/benchmark_comparison.py
"""

import time
import statistics
import validators as original
import rapidvalidators as rapid

# Test data for each validator
TEST_DATA = {
    "email": {
        "valid": [
            "test@example.com",
            "user.name+tag@domain.org",
            "admin@subdomain.example.co.uk",
            "test123@test-domain.com",
            "a@b.co",
        ],
        "invalid": [
            "not-an-email",
            "@nodomain.com",
            "spaces in@email.com",
            "missing.at.sign",
            "",
        ],
    },
    "url": {
        "valid": [
            "https://example.com",
            "http://www.google.com/search?q=test",
            "https://api.github.com/repos/user/repo",
            "ftp://files.example.com/path/to/file",
            "https://example.com:8080/path?query=value#fragment",
        ],
        "invalid": [
            "not-a-url",
            "example.com",  # no scheme
            "http://",
            "://missing-scheme.com",
            "",
        ],
    },
    "domain": {
        "valid": [
            "example.com",
            "subdomain.example.org",
            "my-site.co.uk",
            "test123.io",
            "a.bc",
        ],
        "invalid": [
            "localhost",
            "-invalid.com",
            "no spaces.com",
            ".com",
            "",
        ],
    },
    "ipv4": {
        "valid": [
            "192.168.1.1",
            "10.0.0.1",
            "172.16.0.1",
            "8.8.8.8",
            "255.255.255.255",
        ],
        "invalid": [
            "256.1.1.1",
            "1.2.3",
            "1.2.3.4.5",
            "abc.def.ghi.jkl",
            "",
        ],
    },
    "ipv6": {
        "valid": [
            "::1",
            "2001:db8::1",
            "fe80::1",
            "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
            "::ffff:192.168.1.1",
        ],
        "invalid": [
            "not-ipv6",
            "2001:db8::1::1",
            "12345::1",
            ":::",
            "",
        ],
    },
    "uuid": {
        "valid": [
            "2bc1c94f-0deb-43e9-92a1-4775189ec9f8",
            "550e8400-e29b-41d4-a716-446655440000",
            "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
            "f47ac10b-58cc-4372-a567-0e02b2c3d479",
            "A987FBC9-4BED-3078-CF07-9141BA07C9F3",
        ],
        "invalid": [
            "not-a-uuid",
            "2bc1c94f-0deb-43e9-92a1",
            "2bc1c94f0deb43e992a14775189ec9f8",  # no dashes
            "2bc1c94f-0deb-43e9-92a1-4775189ec9f8-extra",
            "",
        ],
    },
    "slug": {
        "valid": [
            "hello-world",
            "my-blog-post",
            "test123",
            "a",
            "this-is-a-longer-slug-with-numbers-123",
        ],
        "invalid": [
            "Hello-World",
            "has spaces",
            "-leading-dash",
            "trailing-dash-",
            "",
        ],
    },
    "md5": {
        "valid": [
            "d41d8cd98f00b204e9800998ecf8427e",
            "098f6bcd4621d373cade4e832627b4f6",
            "5d41402abc4b2a76b9719d911017c592",
            "e99a18c428cb38d5f260853678922e03",
            "d8e8fca2dc0f896fd7cb4cb0031ba249",
        ],
        "invalid": [
            "not-md5",
            "d41d8cd98f00b204e9800998ecf8427",  # too short
            "d41d8cd98f00b204e9800998ecf8427ee",  # too long
            "zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz",  # invalid chars
            "",
        ],
    },
    "sha256": {
        "valid": [
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
            "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824",
            "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9",
            "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
        ],
        "invalid": [
            "not-sha256",
            "e3b0c44298fc1c149afbf4c8996fb924",  # too short
            "zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz",
            "",
        ],
    },
    "mac_address": {
        "valid": [
            "00:11:22:33:44:55",
            "AA:BB:CC:DD:EE:FF",
            "00-11-22-33-44-55",
            "0011.2233.4455",
            "001122334455",
        ],
        "invalid": [
            "00:11:22:33:44",
            "GG:HH:II:JJ:KK:LL",
            "not-a-mac",
            "",
        ],
    },
}

# Number of iterations for each benchmark
ITERATIONS = 10000
WARMUP = 100


def benchmark_function(func, test_values, iterations):
    """Benchmark a single function with given test values."""
    # Warmup
    for _ in range(WARMUP):
        for val in test_values:
            try:
                func(val)
            except:
                pass

    # Actual benchmark
    times = []
    for _ in range(iterations):
        start = time.perf_counter_ns()
        for val in test_values:
            try:
                func(val)
            except:
                pass
        end = time.perf_counter_ns()
        times.append(end - start)

    return times


def run_benchmarks():
    """Run all benchmarks and collect results."""
    results = {}

    validators_to_test = [
        ("email", original.email, rapid.email),
        ("url", original.url, rapid.url),
        ("domain", original.domain, rapid.domain),
        ("ipv4", original.ipv4, rapid.ipv4),
        ("ipv6", original.ipv6, rapid.ipv6),
        ("uuid", original.uuid, rapid.uuid),
        ("slug", original.slug, rapid.slug),
        ("md5", original.md5, rapid.md5),
        ("sha256", original.sha256, rapid.sha256),
        ("mac_address", original.mac_address, rapid.mac_address),
    ]

    print("=" * 70)
    print("RAPIDVALIDATORS vs VALIDATORS - Performance Benchmark")
    print("=" * 70)
    print(f"\nIterations per test: {ITERATIONS}")
    print(f"Test values per validator: 10 (5 valid + 5 invalid)")
    print(f"Total calls per validator: {ITERATIONS * 10:,}")
    print("\nRunning benchmarks...\n")

    for name, orig_func, rapid_func in validators_to_test:
        print(f"Benchmarking {name}...", end=" ", flush=True)

        test_data = TEST_DATA.get(name, {"valid": [], "invalid": []})
        test_values = test_data["valid"] + test_data["invalid"]

        # Benchmark original
        orig_times = benchmark_function(orig_func, test_values, ITERATIONS)

        # Benchmark rapid
        rapid_times = benchmark_function(rapid_func, test_values, ITERATIONS)

        # Calculate statistics (in microseconds)
        orig_mean = statistics.mean(orig_times) / 1000
        orig_median = statistics.median(orig_times) / 1000
        orig_stdev = statistics.stdev(orig_times) / 1000 if len(orig_times) > 1 else 0

        rapid_mean = statistics.mean(rapid_times) / 1000
        rapid_median = statistics.median(rapid_times) / 1000
        rapid_stdev = statistics.stdev(rapid_times) / 1000 if len(rapid_times) > 1 else 0

        speedup = orig_mean / rapid_mean if rapid_mean > 0 else float('inf')

        results[name] = {
            "original": {"mean": orig_mean, "median": orig_median, "stdev": orig_stdev},
            "rapid": {"mean": rapid_mean, "median": rapid_median, "stdev": rapid_stdev},
            "speedup": speedup,
        }

        print(f"done (speedup: {speedup:.1f}x)")

    return results


def print_report(results):
    """Print a formatted benchmark report."""
    print("\n" + "=" * 70)
    print("BENCHMARK RESULTS")
    print("=" * 70)

    print(f"\n{'Validator':<15} {'Original (µs)':<18} {'Rapid (µs)':<18} {'Speedup':<10}")
    print("-" * 70)

    total_orig = 0
    total_rapid = 0

    for name, data in sorted(results.items(), key=lambda x: -x[1]["speedup"]):
        orig = data["original"]["mean"]
        rapid = data["rapid"]["mean"]
        speedup = data["speedup"]
        total_orig += orig
        total_rapid += rapid

        print(f"{name:<15} {orig:>12.2f} ± {data['original']['stdev']:<6.2f} "
              f"{rapid:>12.2f} ± {data['rapid']['stdev']:<6.2f} {speedup:>8.1f}x")

    print("-" * 70)
    avg_speedup = total_orig / total_rapid if total_rapid > 0 else 0
    print(f"{'AVERAGE':<15} {total_orig/len(results):>12.2f}{'':>8} "
          f"{total_rapid/len(results):>12.2f}{'':>8} {avg_speedup:>8.1f}x")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    speedups = [d["speedup"] for d in results.values()]
    min_speedup = min(speedups)
    max_speedup = max(speedups)
    avg_speedup = statistics.mean(speedups)

    fastest = max(results.items(), key=lambda x: x[1]["speedup"])
    slowest = min(results.items(), key=lambda x: x[1]["speedup"])

    print(f"\nAverage speedup:  {avg_speedup:.1f}x faster")
    print(f"Min speedup:      {min_speedup:.1f}x ({slowest[0]})")
    print(f"Max speedup:      {max_speedup:.1f}x ({fastest[0]})")

    print(f"\nTotal validators benchmarked: {len(results)}")
    print(f"All validators show improvement: {'Yes' if min_speedup > 1 else 'No'}")

    print("\n" + "=" * 70)


def save_report(results, filename="benchmark_report.md"):
    """Save benchmark results to a markdown file."""
    with open(filename, "w") as f:
        f.write("# RapidValidators Performance Benchmark Report\n\n")
        f.write(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Iterations:** {ITERATIONS:,} per test\n")
        f.write(f"**Test values:** 10 per validator (5 valid + 5 invalid)\n\n")

        f.write("## Results\n\n")
        f.write("| Validator | Original (µs) | RapidValidators (µs) | Speedup |\n")
        f.write("|-----------|---------------|----------------------|---------|\n")

        for name, data in sorted(results.items(), key=lambda x: -x[1]["speedup"]):
            orig = data["original"]["mean"]
            rapid = data["rapid"]["mean"]
            speedup = data["speedup"]
            f.write(f"| {name} | {orig:.2f} | {rapid:.2f} | **{speedup:.1f}x** |\n")

        speedups = [d["speedup"] for d in results.values()]
        avg_speedup = statistics.mean(speedups)

        f.write(f"\n## Summary\n\n")
        f.write(f"- **Average speedup:** {avg_speedup:.1f}x faster\n")
        f.write(f"- **Min speedup:** {min(speedups):.1f}x\n")
        f.write(f"- **Max speedup:** {max(speedups):.1f}x\n")
        f.write(f"- **Total validators tested:** {len(results)}\n")

        f.write("\n## Methodology\n\n")
        f.write("- Each validator was tested with 5 valid and 5 invalid inputs\n")
        f.write("- Each test was run for 10,000 iterations after a 100-iteration warmup\n")
        f.write("- Times are measured using `time.perf_counter_ns()` for nanosecond precision\n")
        f.write("- Statistics include mean time per batch of 10 validations\n")

    print(f"\nReport saved to: {filename}")


if __name__ == "__main__":
    results = run_benchmarks()
    print_report(results)
    save_report(results, "benchmarks/benchmark_report.md")
