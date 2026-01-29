"""NATS-Bench Benchmark Wrapper for DPO-NAS"""
import logging
import numpy as np
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class NATSBenchBenchmark:
    """Wrapper for NATS-Bench evaluation with scaling and transfer learning analysis"""
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize NATS-Bench API
        
        Args:
            data_dir: Directory containing NATS-Bench data
        """
        self.api = None
        self.cache = {}
        self.transfer_results = []
        self.data_dir = data_dir
        
        try:
            from nats_bench import create
            file_path = f"{data_dir}/NATS-tss-v1_0-3ffb9-simple" if data_dir else None
            if file_path:
                self.api = create(file_path, 'tss', fast_mode=True, verbose=False)
                logger.info("NATS-Bench API initialized successfully")
            else:
                logger.warning("NATS-Bench data_dir not provided, using simulation mode")
        except ImportError:
            logger.warning("nats_bench library not installed, using simulation mode")
        except Exception as e:
            logger.warning(f"Failed to initialize NATS-Bench API: {e}, using simulation mode")
    
    def _convert_to_nats_format(self, arch_dict: Dict) -> str:
        """Convert DPO-NAS architecture to NATS-Bench format"""
        # NATS-Bench uses similar format to NAS-Bench-201
        op_mapping = {
            'conv_3x3': 'nor_conv_3x3',
            'conv_5x5': 'nor_conv_3x3',
            'conv_1x1': 'nor_conv_1x1',
            'skip_connect': 'skip_connect',
            'avg_pool': 'avg_pool_3x3',
            'max_pool': 'avg_pool_3x3',
        }
        
        operations = arch_dict.get('operations', [])
        edges = []
        
        for i, op in enumerate(operations[:6]):  # NATS uses 6 edges
            mapped_op = op_mapping.get(op, 'nor_conv_3x3')
            node_id = i % 3
            edges.append(f"{mapped_op}~{node_id}")
        
        arch_str = f"|{edges[0]}|+|{edges[1]}|{edges[2]}|+|{edges[3]}|{edges[4]}|{edges[5]}|"
        return arch_str
    
    def evaluate_scaling(self, arch_dict: Dict, datasets: List[str] = None) -> Dict:
        """
        Evaluate architecture scaling across multiple datasets
        
        Args:
            arch_dict: DPO-NAS architecture dictionary
            datasets: List of datasets to evaluate on (default: ['cifar10', 'cifar100'])
            
        Returns:
            Dictionary with results for each dataset and scaling analysis
        """
        if datasets is None:
            datasets = ['cifar10', 'cifar100', 'ImageNet16-120']
        
        arch_hash = str(arch_dict) + str(datasets)
        
        if arch_hash in self.cache:
            logger.info("Returning cached NATS-Bench scaling result")
            return self.cache[arch_hash]
        
        try:
            if self.api:
                arch_str = self._convert_to_nats_format(arch_dict)
                arch_index = self.api.query_index_by_arch(arch_str)
                
                results = {}
                for dataset in datasets:
                    info = self.api.get_more_info(arch_index, dataset, hp='200')
                    results[dataset] = {
                        'accuracy': info['test-accuracy'],
                        'latency': info.get('latency', 0),
                        'parameters': info.get('params', 0),
                    }
            else:
                results = self._simulate_scaling_evaluation(arch_dict, datasets)
            
            # Add scaling analysis
            accuracies = [res['accuracy'] for res in results.values()]
            results['scaling_analysis'] = {
                'mean_accuracy': float(np.mean(accuracies)),
                'std_accuracy': float(np.std(accuracies)),
                'scaling_efficiency': float(np.min(accuracies) / np.max(accuracies)) if accuracies else 0.0,
            }
            
            self.cache[arch_hash] = results
            return results
            
        except Exception as e:
            logger.error(f"NATS-Bench scaling evaluation failed: {e}, using simulation")
            return self._simulate_scaling_evaluation(arch_dict, datasets)
    
    def _simulate_scaling_evaluation(self, arch_dict: Dict, datasets: List[str]) -> Dict:
        """Simulate scaling evaluation"""
        num_layers = len(arch_dict.get('operations', []))
        num_skips = sum(arch_dict.get('skip_connections', []))
        
        dataset_base_acc = {
            'cifar10': 0.92,
            'cifar100': 0.72,
            'ImageNet16-120': 0.44,
        }
        
        results = {}
        for dataset in datasets:
            base_acc = dataset_base_acc.get(dataset, 0.80)
            acc_bonus = 0.02 * (num_skips / max(1, len(arch_dict.get('skip_connections', [1]))))
            accuracy = base_acc + acc_bonus + np.random.normal(0, 0.01)
            
            results[dataset] = {
                'accuracy': float(np.clip(accuracy, 0, 1)),
                'latency': float(10 + num_layers * 2),
                'parameters': float(num_layers * 100000),
            }
        
        accuracies = [res['accuracy'] for res in results.values()]
        results['scaling_analysis'] = {
            'mean_accuracy': float(np.mean(accuracies)),
            'std_accuracy': float(np.std(accuracies)),
            'scaling_efficiency': float(np.min(accuracies) / np.max(accuracies)) if accuracies else 0.0,
        }
        
        return results
    
    def evaluate_transfer(self, arch_dict: Dict, source_dataset: str = 'cifar10', 
                         target_dataset: str = 'cifar100') -> Dict:
        """
        Simulate transfer learning evaluation
        
        Args:
            arch_dict: DPO-NAS architecture dictionary
            source_dataset: Source dataset name
            target_dataset: Target dataset name
            
        Returns:
            Dictionary with transfer learning metrics
        """
        # Evaluate on both datasets
        scaling_results = self.evaluate_scaling(arch_dict, [source_dataset, target_dataset])
        
        source_acc = scaling_results[source_dataset]['accuracy']
        target_acc = scaling_results[target_dataset]['accuracy']
        
        # Compute transfer degradation
        transfer_degradation = float((source_acc - target_acc) / source_acc) if source_acc > 0 else 0.0
        
        result = {
            'source_dataset': source_dataset,
            'target_dataset': target_dataset,
            'source_accuracy': source_acc,
            'transfer_accuracy': target_acc,
            'transfer_degradation': transfer_degradation,
            'transfer_efficiency': float(1.0 - abs(transfer_degradation)),
        }
        
        self.transfer_results.append(result)
        return result
    
    def get_transfer_analysis(self) -> Dict:
        """
        Get aggregated transfer learning statistics
        
        Returns:
            Dictionary with transfer learning analysis
        """
        if not self.transfer_results:
            return {
                'num_transfers': 0,
                'avg_transfer_efficiency': 0.0,
                'std_transfer_efficiency': 0.0,
            }
        
        efficiencies = [r['transfer_efficiency'] for r in self.transfer_results]
        
        return {
            'num_transfers': len(self.transfer_results),
            'avg_transfer_efficiency': float(np.mean(efficiencies)),
            'std_transfer_efficiency': float(np.std(efficiencies)),
            'min_transfer_efficiency': float(np.min(efficiencies)),
            'max_transfer_efficiency': float(np.max(efficiencies)),
        }
