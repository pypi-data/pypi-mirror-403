"""
ArpraxProfiler: The Professional Algorithm Analysis Toolkit
-----------------------------------------------------------
The complete suite for OHPV2 Analysis, Benchmarking, and Visualization.

Features:
- Multi-mode timing (min/mean/median).
- Automatic plotting (if matplotlib is installed).
- Decorator support for quick-profiling.
- "Stress Suite" for multi-algo vs multi-input battles.
- Garbage Collection control and Recursion safety.
"""

import timeit
import gc
import copy
import sys
import statistics
import functools
from typing import Callable, List, Dict, Any, Union, Optional

class ArpraxProfiler:
    def __init__(self, repeats: int = 5, warmup: int = 1, mode: str = "min"):
        """
        :param repeats: Number of runs per benchmark.
        :param warmup: Warmup runs to stabilize CPU cache.
        :param mode: 'min' (noise-free), 'mean' (statistical), or 'median' (robust).
        """
        self.repeats = repeats
        self.warmup = warmup
        self.mode = mode

        # Storage for the @profile decorator
        self._profile_stats = {}

    # ---------------------------------------------------------
    # 1. Core Benchmarking Logic
    # ---------------------------------------------------------
    def benchmark(self, func: Callable, *args) -> float:
        """
        Runs the function with GC disabled and returns the timing based on 'mode'.
        """
        # 1. WARMUP
        for _ in range(self.warmup):
            safe_args = copy.deepcopy(args)
            func(*safe_args)

        times = []
        gc_old = gc.isenabled()
        gc.disable()

        try:
            for _ in range(self.repeats):
                safe_args = copy.deepcopy(args) # Critical for sorting algos

                start = timeit.default_timer()
                func(*safe_args)
                end = timeit.default_timer()

                times.append(end - start)
        finally:
            if gc_old: gc.enable()

        # 2. STATISTICAL MODES
        if self.mode == "median":
            return statistics.median(times)
        elif self.mode == "mean":
            return statistics.mean(times)
        else:
            return min(times) # Default: Industry standard for micro-benchmarks

    # ---------------------------------------------------------
    # 2. OHPV2 Analysis (Doubling Test)
    # ---------------------------------------------------------
    def run_doubling_test(
        self,
        func: Callable,
        input_gen: Callable[[int], Any],
        start_n: int = 250,
        rounds: int = 6
    ) -> List[Dict[str, Any]]:

        sys.setrecursionlimit(max(3000, sys.getrecursionlimit()))
        results = []
        prev_time = 0
        n = start_n

        for _ in range(rounds):
            # 3. MULTI-ARG SUPPORT
            # Input generator can return (arr, target) or just arr
            data = input_gen(n)
            args = data if isinstance(data, tuple) else (data,)

            curr_time = self.benchmark(func, *args)

            ratio = curr_time / prev_time if prev_time > 0 else 0
            complexity = self._guess_complexity(ratio)

            results.append({
                "N": n,
                "Time": curr_time,
                "Ratio": ratio,
                "Complexity": complexity
            })

            prev_time = curr_time
            n *= 2

        return results

    # ---------------------------------------------------------
    # 3. Stress Suite (Multi-Algo Battle)
    # ---------------------------------------------------------
    def run_stress_suite(
        self,
        funcs: Dict[str, Callable],
        input_gen: Callable[[int], Any],
        n_values: List[int] = [1000, 2000, 4000]
    ) -> Dict[int, Dict[str, float]]:
        """
        Runs multiple algorithms against multiple input sizes.
        """
        suite_results = {}

        for n in n_values:
            suite_results[n] = {}
            data = input_gen(n)
            args = data if isinstance(data, tuple) else (data,)

            for name, func in funcs.items():
                # Benchmark handles the deepcopy, so we can reuse args
                time_taken = self.benchmark(func, *args)
                suite_results[n][name] = time_taken

        return suite_results

    # ---------------------------------------------------------
    # 4. The Decorator (@profiler.profile)
    # ---------------------------------------------------------
    def profile(self, func: Callable):
        """
        Decorator to quick-profile any function during normal execution.
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = timeit.default_timer()
            result = func(*args, **kwargs)
            end = timeit.default_timer()

            elapsed = end - start

            if func.__name__ not in self._profile_stats:
                self._profile_stats[func.__name__] = []
            self._profile_stats[func.__name__].append(elapsed)

            return result
        return wrapper

    def print_decorator_report(self):
        print("\n📝 DECORATOR PROFILE REPORT")
        print(f"{'Function':<20} | {'Calls':<6} | {'Avg Time (s)':<12} | {'Total Time'}")
        print("-" * 55)
        for fname, times in self._profile_stats.items():
            avg_t = statistics.mean(times)
            total_t = sum(times)
            print(f"{fname:<20} | {len(times):<6} | {avg_t:<12.5f} | {total_t:.5f}")

    # ---------------------------------------------------------
    # 5. Visualization (Matplotlib Optional)
    # ---------------------------------------------------------
    def plot_analysis(self, results: List[Dict[str, Any]], title: str = "Algorithm Growth"):
        """
        Plots N vs Time from doubling test results.
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print("⚠️ Matplotlib not found. Install it to enable plotting: pip install matplotlib")
            return

        ns = [row['N'] for row in results]
        times = [row['Time'] for row in results]

        plt.figure(figsize=(10, 6))
        plt.plot(ns, times, marker='o', linestyle='-', color='b', label='Measured Time')

        plt.title(f"OHPV2 Analysis: {title}")
        plt.xlabel("Input Size (N)")
        plt.ylabel("Time (seconds)")
        plt.grid(True)
        plt.legend()
        plt.show()

    # ---------------------------------------------------------
    # Helper Methods
    # ---------------------------------------------------------
    def _guess_complexity(self, ratio: float) -> str:
        if ratio < 0.1: return "-"
        if ratio < 1.4: return "O(1) / Log"
        if 1.6 <= ratio <= 2.4: return "O(N)"
        if 3.5 <= ratio <= 4.6: return "O(N^2)"
        if 7.0 <= ratio <= 9.0: return "O(N^3)"
        return "?"

    def print_analysis(self, func_name: str, results: List[Dict[str, Any]]):
        print(f"\n🔬 ANALYSIS: {func_name} (Mode: {self.mode})")
        print(f"{'N':<10} | {'Time (s)':<12} | {'Ratio':<8} | {'Est. Complexity':<15}")
        print("-" * 55)
        for row in results:
            r_str = f"{row['Ratio']:.2f}" if row['Ratio'] > 0 else "-"
            print(f"{row['N']:<10} | {row['Time']:<12.5f} | {r_str:<8} | {row['Complexity']:<15}")

# ==========================================
# 🧪 DEMO USAGE
# ==========================================
if __name__ == "__main__":
    import random

    profiler = ArpraxProfiler(mode="min")

    # 1. Multi-Argument Test
    def two_sum(arr, target):
        for x in arr:
            if x == target: return True
        return False

    def two_sum_gen(n):
        # Returns TUPLE: (arr, target)
        return ([random.randint(0, 100) for _ in range(n)], -1)

    print("--- 1. Doubling Test (Multi-Arg) ---")
    results = profiler.run_doubling_test(two_sum, two_sum_gen, rounds=5)
    profiler.print_analysis("Two Sum", results)

    # 2. Plotting (Optional)
    # profiler.plot_analysis(results, title="Two Sum Linear Scan")

    # 3. Decorator Usage
    print("\n--- 2. Decorator Test ---")

    @profiler.profile
    def sleepy_algo(x):
        import time
        time.sleep(x)

    sleepy_algo(0.1)
    sleepy_algo(0.1)

    profiler.print_decorator_report()