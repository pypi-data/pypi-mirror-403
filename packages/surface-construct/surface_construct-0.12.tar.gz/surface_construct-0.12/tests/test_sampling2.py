import pytest
import ase.io

from surface_construct import SurfaceGrid
from surface_construct.sg_sampler import InitialSGSampler, KeyPointSGSampler, MaxDiversitySGSampler

class TestSampling2:
    """
    Cu-CuO interface
    """
    def setup_method(self):
        atoms = ase.io.read('atoms_files/CuOx-Cu100-CONTCAR')
        self.sg_obj = SurfaceGrid(atoms, interval=0.2, ads_num=6, lpca=False)
        self.sg_obj.initialize()

    def teardown_method(self):
        pass

    def test_initial_sampling(self):
        for size in [4, 8, 16]:
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
        samples = sample_obj.samples(size=10)
        self.sg_obj.plot_cluster(figname=f'MaxDiversity_sampling')

    def test_max_sigma_sampling(self):
        pass

    def test_exclude_too_close_sampling(self):
        samples = [0,1,2,3]
        sample_obj = KeyPointSGSampler(self.sg_obj)
        result_sample = sample_obj.exclude_too_close_sample(samples)
        print(self.sg_obj.points[samples])
        print(result_sample)