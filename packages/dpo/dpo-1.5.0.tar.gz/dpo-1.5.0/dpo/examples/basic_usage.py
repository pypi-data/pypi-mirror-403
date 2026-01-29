from dpo import DPO_NAS, DPO_Config
import json


def main():
    """Main execution"""
    config = DPO_Config.thorough()
    optimizer = DPO_NAS(config)
    results = optimizer.optimize()
    print("Best Fitness:", results['best_fitness'])
    print("Best Architecture:")
    print(json.dumps(results['best_architecture'], indent=2))


if __name__ == "__main__":
    main()
