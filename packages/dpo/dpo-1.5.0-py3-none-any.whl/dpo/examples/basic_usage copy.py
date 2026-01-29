from dpo import DPO_NAS, DPO_Config


def main():
    """Main execution"""
    config = DPO_Config.fast()
    optimizer = DPO_NAS(config)
    results = optimizer.optimize()
    print("Best Fitness:", results['best_fitness'])
    print("Best Architecture:", results['best_architecture'])


if __name__ == "__main__":
    main()
