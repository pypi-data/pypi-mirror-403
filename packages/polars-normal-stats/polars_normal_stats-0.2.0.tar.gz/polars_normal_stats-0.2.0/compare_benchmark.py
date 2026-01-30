import subprocess
import sys
import os
import json
from pathlib import Path

# Add benchmarks directory to sys.path to import benchmark_core
sys.path.append(str(Path(__file__).parent / "benchmarks"))
from benchmarks.benchmark_core import run_benchmark

def run_tests():
    print("Running tests...")
    result = subprocess.run([sys.executable, "-m", "pytest", "tests/test_normal.py"], capture_output=True, text=True)
    if result.returncode != 0:
        print("Tests failed!")
        print(result.stdout)
        print(result.stderr)
        return False
    print("All tests passed.")
    return True

def load_baseline(path):
    if not os.path.exists(path):
        return None
    with open(path, 'r') as f:
        return json.load(f)

def compare_results(current, baseline):
    if not baseline:
        print("No baseline found to compare against.")
        return

    print("\nPerformance Comparison (Current vs Baseline):")
    print(f"{'Rows':>12} | {'Func':>12} | {'Mean (s)':>12} | {'Var (s)':>12} | {'Base (s)':>12} | {'Change (%)':>12}")
    print("-" * 90)

    baseline_map = {res['size']: res for res in baseline}
    
    improved_count = 0
    total_count = 0

    for curr_res in current:
        size = curr_res['size']
        if size not in baseline_map:
            continue
        
        base_res = baseline_map[size]
        for func in ['normal_cdf', 'normal_ppf', 'normal_pdf']:
            curr_time = curr_res[func]
            curr_var = curr_res.get(f"{func}_var", 0.0)
            base_time = base_res[func]
            
            diff_pct = (curr_time - base_time) / base_time * 100
            
            status = ""
            if diff_pct < -5: # Improvement of more than 5%
                status = "IMPROVED"
                improved_count += 1
            elif diff_pct > 5: # Regression of more than 5%
                status = "REGRESSION"
            
            total_count += 1
            print(f"{size:12,} | {func:12} | {curr_time:12.4f} | {curr_var:12.2e} | {base_time:12.4f} | {diff_pct:+11.2f}% {status}")

    print(f"\nSummary: {improved_count}/{total_count} function/size combinations showed >5% improvement.")

def main():
    # 1. Run tests
    if not run_tests():
        sys.exit(1)

    # 2. Load baseline
    baseline_path = "benchmarks/baseline.json"
    baseline = load_baseline(baseline_path)

    # 3. Run benchmark
    print("\nRunning benchmarks...")
    current_results = run_benchmark()

    # 4. Compare
    compare_results(current_results, baseline)
    
    # Optionally save as new baseline if requested
    if len(sys.argv) > 1 and sys.argv[1] == "--save-baseline":
        with open(baseline_path, 'w') as f:
            json.dump(current_results, f, indent=4)
        print(f"\nCurrent results saved as new baseline in {baseline_path}")

if __name__ == "__main__":
    main()
