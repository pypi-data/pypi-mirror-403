#!/usr/bin/env python3
"""
Full performance benchmark comparing all rapidvalidators with original validators
"""

import time
import statistics
import validators as original
import rapidvalidators as rapid

ITERATIONS = 10000
WARMUP = 100

# Extended test data
TEST_DATA = {
    "email": {
        "valid": ["test@example.com", "user.name+tag@domain.org", "admin@sub.example.co.uk"],
        "invalid": ["not-an-email", "@nodomain.com", ""],
    },
    "url": {
        "valid": ["https://example.com", "http://www.google.com/search?q=test", "ftp://files.example.com"],
        "invalid": ["not-a-url", "example.com", ""],
    },
    "domain": {
        "valid": ["example.com", "subdomain.example.org", "my-site.co.uk"],
        "invalid": ["localhost", "-invalid.com", ""],
    },
    "ipv4": {
        "valid": ["192.168.1.1", "10.0.0.1", "8.8.8.8"],
        "invalid": ["256.1.1.1", "1.2.3", ""],
    },
    "ipv6": {
        "valid": ["::1", "2001:db8::1", "fe80::1"],
        "invalid": ["not-ipv6", ":::", ""],
    },
    "uuid": {
        "valid": ["2bc1c94f-0deb-43e9-92a1-4775189ec9f8", "550e8400-e29b-41d4-a716-446655440000"],
        "invalid": ["not-a-uuid", "", "2bc1c94f"],
    },
    "slug": {
        "valid": ["hello-world", "my-blog-post", "test123"],
        "invalid": ["Hello-World", "has spaces", ""],
    },
    "md5": {
        "valid": ["d41d8cd98f00b204e9800998ecf8427e", "098f6bcd4621d373cade4e832627b4f6"],
        "invalid": ["not-md5", "", "short"],
    },
    "sha256": {
        "valid": ["e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"],
        "invalid": ["not-sha256", ""],
    },
    "sha1": {
        "valid": ["da39a3ee5e6b4b0d3255bfef95601890afd80709", "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"],
        "invalid": ["not-sha1", ""],
    },
    "sha512": {
        "valid": ["cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e"],
        "invalid": ["not-sha512", ""],
    },
    "mac_address": {
        "valid": ["00:11:22:33:44:55", "AA:BB:CC:DD:EE:FF", "00-11-22-33-44-55"],
        "invalid": ["00:11:22:33:44", "GG:HH:II:JJ:KK:LL", ""],
    },
    "iban": {
        "valid": ["GB82WEST12345698765432", "DE89370400440532013000"],
        "invalid": ["INVALID", "GB00TEST00000000000000", ""],
    },
    "btc_address": {
        "valid": ["1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2", "3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy"],
        "invalid": ["invalid", "0x1234567890123456789012345678901234567890", ""],
    },
    "eth_address": {
        "valid": ["0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed", "0x0000000000000000000000000000000000000000"],
        "invalid": ["invalid", "5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed", ""],
    },
    "visa": {
        "valid": ["4532015112830366", "4916338506082832", "4556737586899855"],
        "invalid": ["1234567890123456", "not-a-card", ""],
    },
    "mastercard": {
        "valid": ["5425233430109903", "2223000048410010", "5500000000000004"],
        "invalid": ["1234567890123456", "not-a-card", ""],
    },
}


def benchmark_function(func, test_values, iterations):
    """Benchmark a single function."""
    # Warmup
    for _ in range(WARMUP):
        for val in test_values:
            try:
                func(val)
            except:
                pass

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


def get_validator_pairs():
    """Get pairs of (original, rapid) validators to test."""
    pairs = []

    # Map of validator names to functions
    validators_map = [
        ("email", original.email, rapid.email),
        ("url", original.url, rapid.url),
        ("domain", original.domain, rapid.domain),
        ("ipv4", original.ipv4, rapid.ipv4),
        ("ipv6", original.ipv6, rapid.ipv6),
        ("uuid", original.uuid, rapid.uuid),
        ("slug", original.slug, rapid.slug),
        ("md5", original.md5, rapid.md5),
        ("sha1", original.sha1, rapid.sha1),
        ("sha256", original.sha256, rapid.sha256),
        ("sha512", original.sha512, rapid.sha512),
        ("mac_address", original.mac_address, rapid.mac_address),
        ("iban", original.iban, rapid.iban),
        ("btc_address", original.btc_address, rapid.btc_address),
        ("eth_address", original.eth_address, rapid.eth_address),
        ("visa", original.visa, rapid.visa),
        ("mastercard", original.mastercard, rapid.mastercard),
    ]

    return validators_map


def run_benchmarks():
    """Run all benchmarks."""
    results = {}
    validators_to_test = get_validator_pairs()

    print("=" * 80)
    print("RAPIDVALIDATORS vs VALIDATORS - Full Performance Benchmark")
    print("=" * 80)
    print(f"\nIterations: {ITERATIONS:,}")
    print(f"Warmup: {WARMUP}")
    print("\nRunning benchmarks...\n")

    for name, orig_func, rapid_func in validators_to_test:
        print(f"  {name:<15}", end="", flush=True)

        test_data = TEST_DATA.get(name, {"valid": ["test"], "invalid": [""]})
        test_values = test_data["valid"] + test_data["invalid"]

        orig_times = benchmark_function(orig_func, test_values, ITERATIONS)
        rapid_times = benchmark_function(rapid_func, test_values, ITERATIONS)

        orig_mean = statistics.mean(orig_times) / 1000  # to microseconds
        rapid_mean = statistics.mean(rapid_times) / 1000
        speedup = orig_mean / rapid_mean if rapid_mean > 0 else float('inf')

        results[name] = {
            "original_us": orig_mean,
            "rapid_us": rapid_mean,
            "speedup": speedup,
            "calls": len(test_values) * ITERATIONS,
        }

        bar_len = int(min(speedup, 50))
        bar = "█" * bar_len
        print(f" {speedup:>6.1f}x  {bar}")

    return results


def print_report(results):
    """Print detailed report."""
    print("\n" + "=" * 80)
    print("DETAILED RESULTS (sorted by speedup)")
    print("=" * 80)

    print(f"\n{'Validator':<15} {'Original':<12} {'Rapid':<12} {'Speedup':<10} {'Category'}")
    print("-" * 80)

    categories = {
        "email": "Network", "url": "Network", "domain": "Network",
        "ipv4": "Network", "ipv6": "Network", "mac_address": "Network",
        "uuid": "Data", "slug": "Data",
        "md5": "Hash", "sha1": "Hash", "sha256": "Hash", "sha512": "Hash",
        "iban": "Finance", "btc_address": "Crypto", "eth_address": "Crypto",
        "visa": "Cards", "mastercard": "Cards",
    }

    sorted_results = sorted(results.items(), key=lambda x: -x[1]["speedup"])

    for name, data in sorted_results:
        cat = categories.get(name, "Other")
        print(f"{name:<15} {data['original_us']:>8.2f} µs  {data['rapid_us']:>8.2f} µs  "
              f"{data['speedup']:>6.1f}x     {cat}")

    print("-" * 80)

    # Summary statistics
    speedups = [d["speedup"] for d in results.values()]
    orig_total = sum(d["original_us"] for d in results.values())
    rapid_total = sum(d["rapid_us"] for d in results.values())

    print(f"\n{'TOTALS':<15} {orig_total:>8.2f} µs  {rapid_total:>8.2f} µs  "
          f"{orig_total/rapid_total:>6.1f}x")

    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)

    print(f"\n  Validators tested:    {len(results)}")
    print(f"  Average speedup:      {statistics.mean(speedups):.1f}x")
    print(f"  Median speedup:       {statistics.median(speedups):.1f}x")
    print(f"  Min speedup:          {min(speedups):.1f}x ({min(results.items(), key=lambda x: x[1]['speedup'])[0]})")
    print(f"  Max speedup:          {max(speedups):.1f}x ({max(results.items(), key=lambda x: x[1]['speedup'])[0]})")

    # Category breakdown
    print("\n" + "-" * 40)
    print("SPEEDUP BY CATEGORY")
    print("-" * 40)

    cat_speedups = {}
    for name, data in results.items():
        cat = categories.get(name, "Other")
        if cat not in cat_speedups:
            cat_speedups[cat] = []
        cat_speedups[cat].append(data["speedup"])

    for cat, speeds in sorted(cat_speedups.items(), key=lambda x: -statistics.mean(x[1])):
        avg = statistics.mean(speeds)
        print(f"  {cat:<12} {avg:>6.1f}x average ({len(speeds)} validators)")

    print("\n" + "=" * 80)


def save_full_report(results):
    """Save comprehensive markdown report."""
    with open("benchmarks/BENCHMARK_REPORT.md", "w") as f:
        f.write("# RapidValidators Performance Benchmark Report\n\n")
        f.write("## Overview\n\n")
        f.write("This report compares the performance of **rapidvalidators** (Rust implementation) ")
        f.write("against the original **validators** Python library.\n\n")

        speedups = [d["speedup"] for d in results.values()]

        f.write("### Key Findings\n\n")
        f.write(f"- **Average speedup: {statistics.mean(speedups):.1f}x faster**\n")
        f.write(f"- **Median speedup: {statistics.median(speedups):.1f}x faster**\n")
        f.write(f"- **Range: {min(speedups):.1f}x to {max(speedups):.1f}x**\n")
        f.write(f"- **Validators tested: {len(results)}**\n\n")

        f.write("## Detailed Results\n\n")
        f.write("| Validator | Original (µs) | RapidValidators (µs) | Speedup | Category |\n")
        f.write("|-----------|---------------|----------------------|---------|----------|\n")

        categories = {
            "email": "Network", "url": "Network", "domain": "Network",
            "ipv4": "Network", "ipv6": "Network", "mac_address": "Network",
            "uuid": "Data", "slug": "Data",
            "md5": "Hash", "sha1": "Hash", "sha256": "Hash", "sha512": "Hash",
            "iban": "Finance", "btc_address": "Crypto", "eth_address": "Crypto",
            "visa": "Cards", "mastercard": "Cards",
        }

        for name, data in sorted(results.items(), key=lambda x: -x[1]["speedup"]):
            cat = categories.get(name, "Other")
            f.write(f"| {name} | {data['original_us']:.2f} | {data['rapid_us']:.2f} | "
                    f"**{data['speedup']:.1f}x** | {cat} |\n")

        f.write("\n## Performance by Category\n\n")

        cat_speedups = {}
        for name, data in results.items():
            cat = categories.get(name, "Other")
            if cat not in cat_speedups:
                cat_speedups[cat] = []
            cat_speedups[cat].append((name, data["speedup"]))

        for cat, items in sorted(cat_speedups.items(), key=lambda x: -statistics.mean([i[1] for i in x[1]])):
            avg = statistics.mean([i[1] for i in items])
            f.write(f"### {cat} ({avg:.1f}x average)\n\n")
            for name, spd in sorted(items, key=lambda x: -x[1]):
                f.write(f"- {name}: {spd:.1f}x\n")
            f.write("\n")

        f.write("## Methodology\n\n")
        f.write(f"- **Iterations:** {ITERATIONS:,} per validator\n")
        f.write(f"- **Warmup:** {WARMUP} iterations\n")
        f.write("- **Test data:** Mix of valid and invalid inputs for each validator\n")
        f.write("- **Timing:** `time.perf_counter_ns()` for nanosecond precision\n")
        f.write("- **Environment:** Python 3.13, macOS, Apple Silicon\n\n")

        f.write("## Conclusion\n\n")
        f.write(f"RapidValidators provides an average **{statistics.mean(speedups):.0f}x speedup** ")
        f.write("over the original validators library, with some validators seeing improvements ")
        f.write(f"of up to **{max(speedups):.0f}x**. This makes it an excellent drop-in replacement ")
        f.write("for performance-critical applications.\n")

    print("\nFull report saved to: benchmarks/BENCHMARK_REPORT.md")


if __name__ == "__main__":
    results = run_benchmarks()
    print_report(results)
    save_full_report(results)
