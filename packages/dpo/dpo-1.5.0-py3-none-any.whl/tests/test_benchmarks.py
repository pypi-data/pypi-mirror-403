"""Quick test for benchmarks module"""
from dpo.benchmarks import (
    NASBench101Benchmark,
    NASBench201Benchmark,
    NASBench301Benchmark,
    HPOBenchBenchmark,
    NATSBenchBenchmark,
    ComprehensiveBenchmarkEvaluator,
)


def test_benchmark_imports():
    """Test that all benchmarks can be imported"""
    print("Testing benchmark imports...")
    assert NASBench101Benchmark is not None
    assert NASBench201Benchmark is not None
    assert NASBench301Benchmark is not None
    assert HPOBenchBenchmark is not None
    assert NATSBenchBenchmark is not None
    assert ComprehensiveBenchmarkEvaluator is not None
    print("✓ All imports successful")


def test_comprehensive_evaluator():
    """Test comprehensive evaluator initialization"""
    print("\nTesting comprehensive evaluator...")
    evaluator = ComprehensiveBenchmarkEvaluator()
    assert evaluator is not None
    assert len(evaluator.benchmarks) == 5
    print("✓ Evaluator initialized with 5 benchmarks")


def test_single_architecture_evaluation():
    """Test evaluation of a single architecture"""
    print("\nTesting single architecture evaluation...")
    
    evaluator = ComprehensiveBenchmarkEvaluator()
    
    arch = {
        'operations': ['conv_3x3'] * 12,
        'kernels': [3] * 12,
        'skip_connections': [0, 0, 1, 0, 0],
        'depth_multiplier': 0.8,
        'channel_multiplier': 0.8,
        'num_layers': 12,
    }
    
    results = evaluator.evaluate_architecture(arch)
    
    assert 'benchmarks' in results
    assert 'nasbench101' in results['benchmarks']
    assert 'nasbench201' in results['benchmarks']
    assert 'nasbench301' in results['benchmarks']
    assert 'hpobench' in results['benchmarks']
    assert 'nats_bench' in results['benchmarks']
    
    print("✓ Architecture evaluated on all benchmarks")
    
    # Print sample results
    print("\nSample results:")
    for bench_name, bench_result in results['benchmarks'].items():
        if 'error' not in bench_result:
            print(f"  {bench_name}: OK")
        else:
            print(f"  {bench_name}: {bench_result['error']}")


if __name__ == '__main__':
    test_benchmark_imports()
    test_comprehensive_evaluator()
    test_single_architecture_evaluation()
    print("\n✓ All tests passed!")
