from dpo.architecture import ArchitectureGene

def test_gene_initialization():
    gene = ArchitectureGene()
    assert gene.gene.shape[0] == gene.D
    arch = gene.to_architecture_dict()
    assert 'operations' in arch and 'kernels' in arch
