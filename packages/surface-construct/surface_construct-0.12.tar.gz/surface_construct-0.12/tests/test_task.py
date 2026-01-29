import os
import shutil
from random import randint

import ase.io
import pytest
from ase import Atom, Atoms
from ase.constraints import FixAtoms
from ase.visualize import view
from lasp_ase.lasp import Lasp
from surface_construct import SurfaceGrid
from surface_construct import AdsGridCombiner
from surface_construct import Adsorbate
from surface_construct.tasks import SurfaceSiteSampleTask, AFMTask
from ase.optimize import LBFGS, BFGS


class TestTask:
    """
    Simple Ru 0001 suface
    """
    def setup_method(self):
        self.task_dir = '%x' % randint(16**3, 16**4 - 1)
        if not os.path.exists(self.task_dir):
            os.makedirs(self.task_dir)
        os.chdir(self.task_dir)

    def teardown_method(self):
        os.chdir("../")
 #       if os.path.exists(self.task_dir):
 #           shutil.rmtree(self.task_dir)

    def test_C_Ru(self):
        """
        C atom on Ru(0001) surface
        :return:
        """
        shutil.copyfile('../atoms_files/RuCHO_lasp.in', 'lasp.in')
        shutil.copyfile('../atoms_files/RuCHO_pf2.pot', 'RuCHO.pot')
        atoms = ase.io.read('../atoms_files/ru_0001_POSCAR')
        atoms.calc = Lasp()
        ads_atoms = ase.Atoms('C',[[0.,0.,0.]])
        ads_obj = Adsorbate(ads_atoms)
        sg_obj = SurfaceGrid(atoms)
        ads_grid_comb = AdsGridCombiner(sg_obj, ads_obj)
        sampler =[
            {
                'size': 3,  # 采样大小
                'surface': "InitialSGSampler",  # 表面采样方法
            },  # 第一步采样
            {
                'size': 5,  # 采样大小
                'surface': ("MaxDiversitySGSampler", "MinEnergySGSampler", "MaxSigmaSGSampler"),  # 表面采样方法
                'weight': (0.1, 0.45, 0.45),  # 表面采样方法的权重
            }  # 第二步采样
        ]
        task_obj = SurfaceSiteSampleTask(combiner=ads_grid_comb, sampler=sampler, optimizer=BFGS)
        task_obj.run()
        print('Done')

    def test_H_CuO_Cu(self):
        """
        H atom on CuO/Cu surface
        :return:
        """
        shutil.copyfile('../atoms_files/CuCHO_lasp.in', 'lasp.in')
        shutil.copyfile('../atoms_files/CuCHO.pot', 'CuCHO.pot')
        atoms = ase.io.read('../atoms_files/CuOx-Cu100-CONTCAR')
        atoms.calc = Lasp()
        ads_atoms = ase.Atoms('H',[[0.,0.,0.]])
        ads_obj = Adsorbate(ads_atoms)
        sg_obj = SurfaceGrid(atoms)
        ads_grid_comb = AdsGridCombiner(sg_obj, ads_obj)
        sampler =[
            {
                'surface': "KeyPointSGSampler",  # 表面采样方法
            },  # 第一步采样
            {
                'size': 3,  # 采样大小
                'surface': ("MaxDiversitySGSampler", "MinEnergySGSampler", "MaxSigmaSGSampler"),  # 表面采样方法
                'weight': (0.4, 0.3, 0.3),  # 表面采样方法的权重
            }  # 第二步采样
        ]
        task_obj = SurfaceSiteSampleTask(combiner=ads_grid_comb, sampler=sampler, optimizer=LBFGS)
        task_obj.run()
        print('Done')

    def test_C4H9_Ru(self):
        adsatoms = ase.io.read('../atoms_files/C4H9.xyz')
        adsatoms.append(Atom('X', adsatoms.positions[0]))  # Add dock point with same pos with atoms[0]
        ads_obj = Adsorbate(adsatoms)
        ads_obj.rotation_delta = 60
        ads_obj.dihedral_delta = 90
        ads_obj.refine_dihedral_grid()
        shutil.copyfile('../atoms_files/RuCHO_lasp.in', 'lasp.in')
        shutil.copyfile('../atoms_files/RuCHO_pf2.pot', 'RuCHO.pot')
        satoms = ase.io.read('../atoms_files/ru_0001_POSCAR')
        satoms.calc = Lasp()
        sg_obj = SurfaceGrid(satoms, interval=0.1, rads=ads_obj.rads, lpca=False, subtype='slab')
        sg_obj.gridize()
        com_obj = AdsGridCombiner(sg_obj, ads_obj)
        sampler =[
            {
                'surface': "KeyPointSGSampler",  # 表面采样方法
            },  # 第一步采样
            {
                'size': 2,  # 采样大小
                'surface': ("MaxDiversitySGSampler", "MinEnergySGSampler", "MaxSigmaSGSampler"),  # 表面采样方法
                'weight': (0.4, 0.3, 0.3),  # 表面采样方法的权重
            }  # 第二步采样
        ]
        task_obj = SurfaceSiteSampleTask(combiner=com_obj, sampler=sampler, optimizer=None)
        task_obj.run()
        print('Done')

    def test_afm(self):
        tip_atoms = Atoms('Ru4CO',positions=[
            [4.96420026, 5.33360004, 5.96179962],
            [2.98259974, 6.51570022, 6.69340014],
            [6.93529963, 6.55210018, 6.65879965],
            [4.97309983, 3.62199992, 6.84219956],
            [4.93830025, 5.30839980, 3.98790002],
            [4.91949975, 5.28810024, 2.48350024],
        ])

        tip_atoms.constraints = FixAtoms(mask=tip_atoms.symbols == 'Ru')
        tip_obj = Adsorbate(tip_atoms)
        tip_obj.dock_point_indices = [[5]] # O atom as docker_point
        shutil.copyfile('../atoms_files/RuCHO_lasp.in', 'lasp.in')
        shutil.copyfile('../atoms_files/RuCHO_pf2.pot', 'RuCHO.pot')
        satoms = ase.io.read('../atoms_files/ru_0001_POSCAR')
        satoms.calc = Lasp()
        sg_obj = SurfaceGrid(satoms, interval=0.1, rads=tip_obj.rads, lpca=False, subtype='slab')
        sg_obj.gridize()
        com_obj = AdsGridCombiner(sg_obj, tip_obj)

        sampler =[
            {
                'surface': "KeyPointSGSampler",  # 表面采样方法
            },  # 第一步采样
            {
                'size': 2,  # 采样大小
                'surface': ("MaxDiversitySGSampler", "MaxSigmaSGSampler"),  # 表面采样方法
                'weight': (0.5, 0.5),  # 表面采样方法的权重
            }  # 第二步采样
        ]
        task_obj = AFMTask(combiner=com_obj, sampler=sampler, optimizer=LBFGS, nz=10) # nz 定义 z方向采多少样
        task_obj.run()
        print('Done')