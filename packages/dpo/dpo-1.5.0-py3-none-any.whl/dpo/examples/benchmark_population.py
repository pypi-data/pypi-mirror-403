"""Population benchmark evaluation example"""
import json
from pathlib import Path
from dpo import DPO_NAS, DPO_Config
from dpo.benchmarks import ComprehensiveBenchmarkEvaluator


def benchmark_population():
    """Run optimization and benchmark the best architecture"""
    
    print("="*70)
    print("STEP 1: RUNNING DPO-NAS OPTIMIZATION")
    print("="*70)
    
    # Step 1: Run optimization
    config = DPO_Config.balanced()
    optimizer = DPO_NAS(config)
    opt_results = optimizer.optimize()
    
    best_architecture = opt_results['best_architecture']
    print(f"\nBest Fitness: {opt_results['best_fitness']:.4f}")
    print(f"Best Architecture:\n{json.dumps(best_architecture, indent=2)}")
    
    print("\n" + "="*70)
    print("STEP 2: BENCHMARKING BEST ARCHITECTURE")
    print("="*70)
    
    # Step 2: Benchmark
    evaluator = ComprehensiveBenchmarkEvaluator(data_dir='./benchmark_data')
    benchmark_results = evaluator.evaluate_architecture(best_architecture)
    
    # Step 3: Print results
    print("\n\nOPTIMIZATION SUMMARY:")
    print("-" * 50)
    print(f"Iterations: {len(opt_results['history']['iterations'])}")
    print(f"Best Fitness: {opt_results['best_fitness']:.4f}")
    print(f"Final Avg Fitness: {opt_results['history']['avg_fitness'][-1]:.4f}")
    
    print("\n\nBENCHMARK RESULTS:")
    print("-" * 50)
    for bench_name, bench_result in benchmark_results['benchmarks'].items():
        print(f"\n{bench_name.upper()}:")
        if 'error' not in bench_result:
            # Extract key metrics for display
            if bench_name == 'nasbench101':
                print(f"  Test Accuracy: {bench_result.get('test_accuracy', 'N/A'):.4f}")
            elif bench_name == 'nasbench201':
                print(f"  Mean Accuracy: {bench_result.get('mean_accuracy', 'N/A'):.4f}")
            elif bench_name == 'nasbench301':
                print(f"  Predicted Accuracy: {bench_result.get('predicted_accuracy', 'N/A'):.4f}")
            elif bench_name == 'hpobench':
                print(f"  Final Accuracy: {bench_result.get('final_accuracy', 'N/A'):.4f}")
            elif bench_name == 'nats_bench':
                if 'scaling' in bench_result and 'scaling_analysis' in bench_result['scaling']:
                    print(f"  Mean Accuracy: {bench_result['scaling']['scaling_analysis'].get('mean_accuracy', 'N/A'):.4f}")
        else:
            print(f"  Error: {bench_result['error']}")
    
    # Step 4: Save
    output_dir = Path('./benchmark_results')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    summary = {
        'optimization': {
            'best_fitness': opt_results['best_fitness'],
            'iterations': len(opt_results['history']['iterations']),
            'best_architecture': best_architecture,
        },
        'benchmarks': benchmark_results['benchmarks'],
    }
    
    summary_file = output_dir / 'comprehensive_results.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    print(f"\n\nSummary saved to: {summary_file}")
    
    report_path = evaluator.generate_report('./benchmark_reports')
    print(f"Report saved to: {report_path}")


if __name__ == '__main__':
    benchmark_population()
