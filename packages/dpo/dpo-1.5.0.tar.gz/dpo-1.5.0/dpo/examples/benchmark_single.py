"""Single architecture benchmark evaluation example"""
import json
from pathlib import Path
from dpo.benchmarks import ComprehensiveBenchmarkEvaluator


def benchmark_single_architecture():
    """Evaluate a single architecture across all benchmarks"""
    
    # Initialize evaluator
    evaluator = ComprehensiveBenchmarkEvaluator(data_dir='./benchmark_data')
    
    # Example architecture
    architecture = {
        'operations': ['conv_3x3'] * 12,
        'kernels': [3] * 12,
        'skip_connections': [0, 0, 1, 0, 0],
        'depth_multiplier': 0.77,
        'channel_multiplier': 0.83,
        'num_layers': 12,
    }
    
    print("="*70)
    print("EVALUATING SINGLE ARCHITECTURE ACROSS ALL BENCHMARKS")
    print("="*70)
    
    # Evaluate
    results = evaluator.evaluate_architecture(architecture)
    
    # Print results from all benchmarks
    print("\nBENCHMARK RESULTS:\n")
    for benchmark_name, benchmark_result in results['benchmarks'].items():
        print(f"\n{benchmark_name.upper()}:")
        print("-" * 50)
        if 'error' not in benchmark_result:
            print(json.dumps(benchmark_result, indent=2))
        else:
            print(f"Error: {benchmark_result['error']}")
    
    # Save results
    output_dir = Path('./benchmark_results')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results_file = output_dir / 'single_arch_results.json'
    evaluator.save_results(str(results_file))
    print(f"\n\nResults saved to: {results_file}")
    
    # Generate report
    report_path = evaluator.generate_report('./benchmark_reports')
    print(f"Report saved to: {report_path}")


if __name__ == '__main__':
    benchmark_single_architecture()
