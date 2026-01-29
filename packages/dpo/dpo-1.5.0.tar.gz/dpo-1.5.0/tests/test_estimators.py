from dpo.evaluation import ZeroShotEstimator, SurrogateEstimator
from dpo.architecture import ArchitectureGene

def test_estimators_run():
    gene = ArchitectureGene()
    arch = gene.to_architecture_dict()
    zs = ZeroShotEstimator()
    sg = SurrogateEstimator()
    loss1, m1 = zs.estimate(arch)
    loss2, m2 = sg.estimate(arch)
    assert isinstance(loss1, float) and isinstance(loss2, float)
    assert 'latency_ms' in m1 and 'latency_ms' in m2
