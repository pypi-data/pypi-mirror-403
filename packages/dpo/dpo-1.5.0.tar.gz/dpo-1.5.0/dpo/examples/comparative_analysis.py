"""Comparative analysis: DPO-NAS vs Random Baseline"""
import json
import numpy as np
from pathlib import Path
from dpo.benchmarks import ComprehensiveBenchmarkEvaluator
from dpo import DPO_NAS, DPO_Config


class ComparativeAnalysis:
    """Compare DPO-NAS against random baseline"""
    
    def __init__(self):
        self.evaluator = ComprehensiveBenchmarkEvaluator()
        self.results = {}
    
    def evaluate_dpo(self, num_runs: int = 3):
        """Run DPO-NAS multiple times"""
        print(f"\n{'='*70}")
        print(f"EVALUATING DPO-NAS ({num_runs} runs)")
        print('='*70)
        
        dpo_results = []
        for run in range(num_runs):
            print(f"\n--- Run {run + 1}/{num_runs} ---")
            
            config = DPO_Config.balanced()
            optimizer = DPO_NAS(config)
            opt_result = optimizer.optimize()
            
            print(f"Optimization complete. Best fitness: {opt_result['best_fitness']:.4f}")
            
            benchmark_result = self.evaluator.evaluate_architecture(
                opt_result['best_architecture']
            )
            
            dpo_results.append({
                'run': run + 1,
                'fitness': opt_result['best_fitness'],
                'benchmarks': benchmark_result['benchmarks'],
            })
        
        self.results['dpo'] = dpo_results
        return dpo_results
    
    def evaluate_baseline(self, num_random: int = 5):
        """Generate and evaluate random architectures"""
        print(f"\n{'='*70}")
        print(f"EVALUATING RANDOM BASELINE ({num_random} architectures)")
        print('='*70)
        
        baseline_results = []
        for i in range(num_random):
            print(f"\n--- Random Architecture {i + 1}/{num_random} ---")
            
            arch = {
                'operations': [np.random.choice(['conv_3x3', 'conv_5x5', 'max_pool']) for _ in range(12)],
                'kernels': [np.random.choice([1, 3, 5]) for _ in range(12)],
                'skip_connections': [np.random.randint(0, 2) for _ in range(5)],
                'depth_multiplier': float(np.random.uniform(0.3, 1.5)),
                'channel_multiplier': float(np.random.uniform(0.3, 1.5)),
                'num_layers': 12,
            }
            
            benchmark_result = self.evaluator.evaluate_architecture(arch)
            baseline_results.append({
                'index': i,
                'benchmarks': benchmark_result['benchmarks'],
            })
        
        self.results['baseline'] = baseline_results
        return baseline_results
    
    def compute_comparison_metrics(self) -> dict:
        """Compare DPO-NAS vs Baseline"""
        print(f"\n{'='*70}")
        print("COMPUTING COMPARISON METRICS")
        print('='*70)
        
        comparison = {
            'dpo_avg': self._average_metrics(self.results['dpo']),
            'baseline_avg': self._average_metrics(self.results['baseline']),
        }
        
        for benchmark in ['nasbench101', 'nasbench201', 'nasbench301', 'hpobench', 'nats_bench']:
            dpo_acc = comparison['dpo_avg'].get(benchmark, {}).get('accuracy', 0)
            baseline_acc = comparison['baseline_avg'].get(benchmark, {}).get('accuracy', 0)
            
            improvement = ((dpo_acc - baseline_acc) / baseline_acc * 100) if baseline_acc > 0 else 0
            comparison[f'{benchmark}_improvement'] = improvement
        
        return comparison
    
    def _average_metrics(self, results_list: list) -> dict:
        """Compute averages across runs"""
        avg = {}
        
        for benchmark in ['nasbench101', 'nasbench201', 'nasbench301', 'hpobench', 'nats_bench']:
            accuracies = []
            for result in results_list:
                bench_data = result.get('benchmarks', {}).get(benchmark, {})
                
                if benchmark == 'nasbench101':
                    acc = bench_data.get('test_accuracy', 0)
                elif benchmark == 'nasbench201':
                    acc = bench_data.get('mean_accuracy', 0)
                elif benchmark == 'nasbench301':
                    acc = bench_data.get('predicted_accuracy', 0)
                elif benchmark == 'hpobench':
                    acc = bench_data.get('final_accuracy', 0)
                elif benchmark == 'nats_bench':
                    if 'scaling' in bench_data and 'scaling_analysis' in bench_data['scaling']:
                        acc = bench_data['scaling']['scaling_analysis'].get('mean_accuracy', 0)
                    else:
                        acc = 0
                else:
                    acc = 0
                
                if acc:
                    accuracies.append(acc)
            
            if accuracies:
                avg[benchmark] = {
                    'accuracy': float(np.mean(accuracies)),
                    'std': float(np.std(accuracies)),
                    'min': float(np.min(accuracies)),
                    'max': float(np.max(accuracies)),
                }
        
        return avg
    
    def generate_report(self) -> str:
        """Generate Markdown report"""
        report_dir = Path('./benchmark_reports')
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = report_dir / 'comparative_analysis.md'
        
        with open(report_file, 'w') as f:
            f.write("# DPO-NAS vs Random Baseline\n\n")
            f.write("## Summary\n\n")
            f.write("| Benchmark | DPO-NAS | Baseline | Improvement |\n")
            f.write("|-----------|---------|----------|-------------|\n")
            
            comparison = self.compute_comparison_metrics()
            for benchmark in ['nasbench101', 'nasbench201', 'nasbench301', 'hpobench', 'nats_bench']:
                dpo = comparison['dpo_avg'].get(benchmark, {}).get('accuracy', 0)
                baseline = comparison['baseline_avg'].get(benchmark, {}).get('accuracy', 0)
                improvement = comparison.get(f'{benchmark}_improvement', 0)
                f.write(f"| {benchmark} | {dpo:.4f} | {baseline:.4f} | {improvement:+.2f}% |\n")
            
            f.write("\n## Detailed Results\n\n")
            
            # DPO-NAS details
            f.write("### DPO-NAS Results\n\n")
            for result in self.results.get('dpo', []):
                f.write(f"**Run {result['run']}**\n")
                f.write(f"- Fitness: {result['fitness']:.4f}\n")
                f.write("\n")
            
            # Baseline details
            f.write("### Random Baseline Results\n\n")
            for result in self.results.get('baseline', []):
                f.write(f"**Architecture {result['index'] + 1}**\n")
                f.write("\n")
        
        return str(report_file)


def main():
    """Main execution"""
    print("="*70)
    print("DPO-NAS COMPARATIVE ANALYSIS")
    print("="*70)
    
    analyzer = ComparativeAnalysis()
    
    # Evaluate DPO-NAS
    analyzer.evaluate_dpo(num_runs=3)
    
    # Evaluate baseline
    analyzer.evaluate_baseline(num_random=5)
    
    # Compute comparison
    comparison = analyzer.compute_comparison_metrics()
    
    # Print results
    print(f"\n{'='*70}")
    print("COMPARISON RESULTS")
    print('='*70)
    
    for benchmark in ['nasbench101', 'nasbench201', 'nasbench301', 'hpobench', 'nats_bench']:
        dpo = comparison['dpo_avg'].get(benchmark, {})
        baseline = comparison['baseline_avg'].get(benchmark, {})
        improvement = comparison.get(f'{benchmark}_improvement', 0)
        
        print(f"\n{benchmark.upper()}")
        print(f"  DPO-NAS:        {dpo.get('accuracy', 0):.4f} ± {dpo.get('std', 0):.4f}")
        print(f"  Random Baseline: {baseline.get('accuracy', 0):.4f} ± {baseline.get('std', 0):.4f}")
        print(f"  Improvement:    {improvement:+.2f}%")
    
    # Generate report
    report = analyzer.generate_report()
    print(f"\n{'='*70}")
    print(f"Report saved to: {report}")
    print('='*70)


if __name__ == '__main__':
    main()
