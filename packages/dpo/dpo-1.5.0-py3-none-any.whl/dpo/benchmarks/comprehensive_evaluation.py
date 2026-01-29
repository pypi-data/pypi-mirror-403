"""Comprehensive Benchmark Evaluator for DPO-NAS"""
import logging
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from .nasbench101_wrapper import NASBench101Benchmark
from .nasbench201_wrapper import NASBench201Benchmark
from .nasbench301_wrapper import NASBench301Benchmark
from .hpobench_wrapper import HPOBenchBenchmark
from .nats_bench_wrapper import NATSBenchBenchmark

logger = logging.getLogger(__name__)


class ComprehensiveBenchmarkEvaluator:
    """Unified evaluator for all NAS benchmarks"""
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize all benchmark wrappers
        
        Args:
            data_dir: Root directory containing all benchmark data
        """
        self.data_dir = data_dir
        logger.info("Initializing comprehensive benchmark evaluator")
        
        # Initialize all benchmarks
        self.benchmarks = {
            'nasbench101': NASBench101Benchmark(data_dir),
            'nasbench201': NASBench201Benchmark(data_dir),
            'nasbench301': NASBench301Benchmark(data_dir),
            'hpobench': HPOBenchBenchmark(),
            'nats_bench': NATSBenchBenchmark(data_dir),
        }
        
        self.evaluation_history = []
        
        logger.info("All benchmarks initialized")
    
    def evaluate_architecture(self, arch_dict: Dict) -> Dict:
        """
        Evaluate architecture across all benchmarks
        
        Args:
            arch_dict: DPO-NAS architecture dictionary
            
        Returns:
            Dictionary with results from all benchmarks
        """
        logger.info("Starting comprehensive architecture evaluation")
        
        results = {
            'architecture': arch_dict,
            'timestamp': datetime.now().isoformat(),
            'benchmarks': {},
        }
        
        # NAS-Bench-101
        try:
            logger.info("Evaluating on NAS-Bench-101")
            nb101_result = self.benchmarks['nasbench101'].evaluate(arch_dict)
            results['benchmarks']['nasbench101'] = {
                'validation_accuracy': nb101_result.validation_accuracy,
                'test_accuracy': nb101_result.test_accuracy,
                'training_time': nb101_result.training_time,
                'computational_cost': nb101_result.computational_cost,
            }
        except Exception as e:
            logger.error(f"NAS-Bench-101 evaluation failed: {e}")
            results['benchmarks']['nasbench101'] = {'error': str(e)}
        
        # NAS-Bench-201
        try:
            logger.info("Evaluating on NAS-Bench-201")
            nb201_result = self.benchmarks['nasbench201'].robustness_analysis(arch_dict)
            results['benchmarks']['nasbench201'] = nb201_result
        except Exception as e:
            logger.error(f"NAS-Bench-201 evaluation failed: {e}")
            results['benchmarks']['nasbench201'] = {'error': str(e)}
        
        # NAS-Bench-301
        try:
            logger.info("Evaluating on NAS-Bench-301")
            nb301_result = self.benchmarks['nasbench301'].predict_performance(arch_dict)
            results['benchmarks']['nasbench301'] = nb301_result
        except Exception as e:
            logger.error(f"NAS-Bench-301 evaluation failed: {e}")
            results['benchmarks']['nasbench301'] = {'error': str(e)}
        
        # HPOBench
        try:
            logger.info("Evaluating on HPOBench")
            hpo_result = self.benchmarks['hpobench'].evaluate_anytime(arch_dict)
            results['benchmarks']['hpobench'] = hpo_result
        except Exception as e:
            logger.error(f"HPOBench evaluation failed: {e}")
            results['benchmarks']['hpobench'] = {'error': str(e)}
        
        # NATS-Bench
        try:
            logger.info("Evaluating on NATS-Bench")
            nats_scaling = self.benchmarks['nats_bench'].evaluate_scaling(arch_dict)
            nats_transfer = self.benchmarks['nats_bench'].evaluate_transfer(arch_dict)
            results['benchmarks']['nats_bench'] = {
                'scaling': nats_scaling,
                'transfer': nats_transfer,
            }
        except Exception as e:
            logger.error(f"NATS-Bench evaluation failed: {e}")
            results['benchmarks']['nats_bench'] = {'error': str(e)}
        
        self.evaluation_history.append(results)
        logger.info("Comprehensive evaluation complete")
        
        return results
    
    def evaluate_population(self, architectures: List[Dict]) -> Dict:
        """
        Evaluate multiple architectures
        
        Args:
            architectures: List of DPO-NAS architecture dictionaries
            
        Returns:
            Dictionary with individual results and summary statistics
        """
        logger.info(f"Evaluating population of {len(architectures)} architectures")
        
        individual_results = []
        for idx, arch in enumerate(architectures):
            logger.info(f"Evaluating architecture {idx + 1}/{len(architectures)}")
            result = self.evaluate_architecture(arch)
            individual_results.append(result)
        
        summary = self._compute_summary(individual_results)
        
        return {
            'individual_results': individual_results,
            'summary': summary,
            'population_size': len(architectures),
        }
    
    def _compute_summary(self, evaluations: List[Dict]) -> Dict:
        """
        Compute summary statistics across population
        
        Args:
            evaluations: List of evaluation results
            
        Returns:
            Dictionary with aggregated statistics
        """
        summary = {}
        
        # NAS-Bench-101 summary
        nb101_accs = []
        for eval_result in evaluations:
            nb101 = eval_result['benchmarks'].get('nasbench101', {})
            if 'test_accuracy' in nb101:
                nb101_accs.append(nb101['test_accuracy'])
        
        if nb101_accs:
            summary['nasbench101'] = {
                'mean_accuracy': float(np.mean(nb101_accs)),
                'std_accuracy': float(np.std(nb101_accs)),
                'max_accuracy': float(np.max(nb101_accs)),
                'min_accuracy': float(np.min(nb101_accs)),
            }
        
        # NAS-Bench-201 summary
        nb201_accs = []
        for eval_result in evaluations:
            nb201 = eval_result['benchmarks'].get('nasbench201', {})
            if 'mean_accuracy' in nb201:
                nb201_accs.append(nb201['mean_accuracy'])
        
        if nb201_accs:
            summary['nasbench201'] = {
                'mean_accuracy': float(np.mean(nb201_accs)),
                'std_accuracy': float(np.std(nb201_accs)),
                'max_accuracy': float(np.max(nb201_accs)),
                'min_accuracy': float(np.min(nb201_accs)),
            }
        
        # NAS-Bench-301 summary
        nb301_accs = []
        for eval_result in evaluations:
            nb301 = eval_result['benchmarks'].get('nasbench301', {})
            if 'predicted_accuracy' in nb301:
                nb301_accs.append(nb301['predicted_accuracy'])
        
        if nb301_accs:
            summary['nasbench301'] = {
                'mean_accuracy': float(np.mean(nb301_accs)),
                'std_accuracy': float(np.std(nb301_accs)),
                'max_accuracy': float(np.max(nb301_accs)),
                'min_accuracy': float(np.min(nb301_accs)),
            }
        
        # HPOBench summary
        hpo_accs = []
        for eval_result in evaluations:
            hpo = eval_result['benchmarks'].get('hpobench', {})
            if 'final_accuracy' in hpo:
                hpo_accs.append(hpo['final_accuracy'])
        
        if hpo_accs:
            summary['hpobench'] = {
                'mean_accuracy': float(np.mean(hpo_accs)),
                'std_accuracy': float(np.std(hpo_accs)),
                'max_accuracy': float(np.max(hpo_accs)),
                'min_accuracy': float(np.min(hpo_accs)),
            }
        
        # NATS-Bench summary
        nats_accs = []
        for eval_result in evaluations:
            nats = eval_result['benchmarks'].get('nats_bench', {})
            if 'scaling' in nats and 'scaling_analysis' in nats['scaling']:
                nats_accs.append(nats['scaling']['scaling_analysis']['mean_accuracy'])
        
        if nats_accs:
            summary['nats_bench'] = {
                'mean_accuracy': float(np.mean(nats_accs)),
                'std_accuracy': float(np.std(nats_accs)),
                'max_accuracy': float(np.max(nats_accs)),
                'min_accuracy': float(np.min(nats_accs)),
            }
        
        return summary
    
    def save_results(self, filepath: str) -> None:
        """
        Save evaluation results to JSON file
        
        Args:
            filepath: Path to output JSON file
        """
        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(self.evaluation_history, f, indent=2, default=str)
        
        logger.info(f"Results saved to {filepath}")
    
    def generate_report(self, output_dir: str) -> str:
        """
        Generate Markdown report of evaluations
        
        Args:
            output_dir: Directory to save the report
            
        Returns:
            Path to generated report
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        report_file = output_path / f"benchmark_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(report_file, 'w') as f:
            f.write("# DPO-NAS Comprehensive Benchmark Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"Total Evaluations: {len(self.evaluation_history)}\n\n")
            
            if self.evaluation_history:
                f.write("## Summary Statistics\n\n")
                summary = self._compute_summary(self.evaluation_history)
                
                f.write("| Benchmark | Mean Accuracy | Std | Min | Max |\n")
                f.write("|-----------|---------------|-----|-----|-----|\n")
                
                for bench_name, stats in summary.items():
                    if 'mean_accuracy' in stats:
                        f.write(f"| {bench_name} | {stats['mean_accuracy']:.4f} | "
                               f"{stats['std_accuracy']:.4f} | {stats['min_accuracy']:.4f} | "
                               f"{stats['max_accuracy']:.4f} |\n")
                
                f.write("\n## Individual Results\n\n")
                for idx, result in enumerate(self.evaluation_history):
                    f.write(f"### Architecture {idx + 1}\n\n")
                    f.write(f"Timestamp: {result['timestamp']}\n\n")
                    
                    for bench_name, bench_result in result['benchmarks'].items():
                        f.write(f"**{bench_name}**\n")
                        if 'error' not in bench_result:
                            f.write(f"```json\n{json.dumps(bench_result, indent=2)}\n```\n\n")
                        else:
                            f.write(f"Error: {bench_result['error']}\n\n")
        
        logger.info(f"Report generated: {report_file}")
        return str(report_file)
