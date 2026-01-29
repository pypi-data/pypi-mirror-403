import pytest
import ase.io

from surface_construct.sg_sampler import InitialSGSampler, KeyPointSGSampler, MaxDiversitySGSampler
from surface_construct import SurfaceGrid


class TestSampling1:
    """
    Simple Ru 0001 suface
    """
    def setup_method(self):
        self.atoms = ase.io.read('atoms_files/ru_0001_POSCAR')
        self.sg_obj = SurfaceGrid(self.atoms, interval=0.1, ads_num=6, lpca=True)
        self.sg_obj.initialize()

    def teardown_method(self):
        pass

    def test_initial_sampling(self):
        for size in range(1, 6):
            sample_obj = InitialSGSampler(self.sg_obj)
            samples = sample_obj.samples(size=size)
            self.sg_obj.plot_cluster(figname=f'sampling_{size}')
            self.sg_obj.del_sample()

    def test_keypoint_sampling(self):
        sample_obj = KeyPointSGSampler(self.sg_obj)
        samples = sample_obj.samples()
        self.sg_obj.plot_cluster(figname=f'KeyPoint_sampling')

    def test_max_diversity_sampling(self):
        sample_obj = MaxDiversitySGSampler(self.sg_obj)
        samples = sample_obj.samples(size=4)
        self.sg_obj.plot_cluster(figname=f'MaxDiversity_sampling')

    def test_max_sigma_sampling(self):
        pass
