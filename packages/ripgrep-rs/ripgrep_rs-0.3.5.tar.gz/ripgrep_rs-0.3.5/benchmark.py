"""Benchmark script for ripgrep_rs vs subprocess ripgrep."""

import subprocess
import time
from pathlib import Path

import ripgrep_rs


def count_lines_in_result(result_list: list[str]) -> int:
    """Count actual match lines from grouped file results."""
    total = 0
    for item in result_list:
        lines = [l for l in item.strip().split("\n") if l]
        total += len(lines)
    return total


def bench_subprocess_grep(
    path: str, pattern: str, n: int = 5, max_count: int | None = None
) -> tuple[float, int]:
    times = []
    match_count = 0
    for _ in range(n):
        start = time.perf_counter()
        cmd = ["rg", "--no-heading", "-n", pattern, path]
        if max_count:
            cmd.extend(["--max-count", str(max_count)])
        result = subprocess.run(cmd, capture_output=True)
        times.append(time.perf_counter() - start)
        try:
            stdout = result.stdout.decode("utf-8", errors="replace")
            match_count = len([l for l in stdout.strip().split("\n") if l])
        except Exception:
            match_count = -1
    return min(times) * 1000, match_count


def bench_lib_grep(
    path: str, pattern: str, n: int = 5, max_count: int | None = None
) -> tuple[float, int]:
    times = []
    match_count = 0
    for _ in range(n):
        start = time.perf_counter()
        result = ripgrep_rs.search(
            [pattern], paths=[path], line_number=True, max_count=max_count
        )
        times.append(time.perf_counter() - start)
        match_count = count_lines_in_result(result)
    return min(times) * 1000, match_count


def bench_subprocess_files(path: str, n: int = 5) -> tuple[float, int]:
    times = []
    file_count = 0
    for _ in range(n):
        start = time.perf_counter()
        result = subprocess.run(
            ["rg", "--files", path],
            capture_output=True,
            text=True,
        )
        times.append(time.perf_counter() - start)
        file_count = len([l for l in result.stdout.strip().split("\n") if l])
    return min(times) * 1000, file_count


def bench_lib_files(path: str, n: int = 5) -> tuple[float, int]:
    times = []
    file_count = 0
    for _ in range(n):
        start = time.perf_counter()
        result = ripgrep_rs.files([""], paths=[path])
        times.append(time.perf_counter() - start)
        file_count = len(result)
    return min(times) * 1000, file_count


def run_benchmark(
    name: str,
    path: str,
    pattern: str = "import",
    iterations: int = 5,
    max_count: int | None = None,
):
    """Run a complete benchmark suite for a given path."""
    print(f"\n{'=' * 60}")
    print(f"BENCHMARK: {name}")
    print(f"Path: {path}")
    print(f"{'=' * 60}")

    # File listing
    print("\n--- File Listing (rg --files) ---")
    t_sub, c_sub = bench_subprocess_files(path, iterations)
    t_lib, c_lib = bench_lib_files(path, iterations)
    ratio = t_sub / t_lib if t_lib > 0 else float("inf")
    winner = "library" if t_lib < t_sub else "subprocess"
    print(f"  subprocess: {t_sub:8.2f}ms ({c_sub:,} files)")
    print(f"  library:    {t_lib:8.2f}ms ({c_lib:,} files)")
    print(f"  Ratio:      {ratio:.2f}x ({winner} faster)")

    # Grep
    limit_info = f" (max_count={max_count})" if max_count else ""
    print(f"\n--- Grep for '{pattern}'{limit_info} ---")
    t_sub, c_sub = bench_subprocess_grep(path, pattern, iterations, max_count)
    t_lib, c_lib = bench_lib_grep(path, pattern, iterations, max_count)
    ratio = t_sub / t_lib if t_lib > 0 else float("inf")
    winner = "library" if t_lib < t_sub else "subprocess"
    print(f"  subprocess: {t_sub:8.2f}ms ({c_sub:,} matches)")
    print(f"  library:    {t_lib:8.2f}ms ({c_lib:,} matches)")
    print(f"  Ratio:      {ratio:.2f}x ({winner} faster)")


def main():
    print("ripgrep_rs Benchmark Suite")
    print("Comparing library bindings vs subprocess calls")

    # Find test directories
    script_dir = Path(__file__).parent

    # Small: the ripgrep project itself
    small_path = str(script_dir)

    # Medium: parent oss directory if it exists
    medium_path = str(script_dir.parent)

    # Large: go up further if possible
    large_path = (
        str(script_dir.parent.parent)
        if script_dir.parent.parent.exists()
        else medium_path
    )

    # Run benchmarks
    run_benchmark("Small (this project)", small_path, pattern="fn ", iterations=10)
    run_benchmark("Medium (parent dir)", medium_path, pattern="import", iterations=5)

    # Only run large if it's different from medium
    # Skip grep for large dirs (too many matches cause OOM)
    if large_path != medium_path:
        print(f"\n{'=' * 60}")
        print("BENCHMARK: Large (grandparent) - FILES ONLY")
        print(f"Path: {large_path}")
        print(f"{'=' * 60}")
        print("\n--- File Listing (rg --files) ---")
        t_sub, c_sub = bench_subprocess_files(large_path, 3)
        t_lib, c_lib = bench_lib_files(large_path, 3)
        ratio = t_sub / t_lib if t_lib > 0 else float("inf")
        winner = "library" if t_lib < t_sub else "subprocess"
        print(f"  subprocess: {t_sub:8.2f}ms ({c_sub:,} files)")
        print(f"  library:    {t_lib:8.2f}ms ({c_lib:,} files)")
        print(f"  Ratio:      {ratio:.2f}x ({winner} faster)")
        print("\n  (Skipping grep for large dir - too many matches)")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("- Library now uses parallel execution for both files and search")
    print("- Should be faster than subprocess across all sizes")


if __name__ == "__main__":
    main()
