import pytest
from ase.build import molecule
from ase.visualize import view
import ase.io
from ase import Atoms, Atom

from surface_construct import SurfaceGrid, AdsGridCombiner, Adsorbate

def Ru_ads(adsatoms):
    ads_obj = Adsorbate(adsatoms)
    satoms = ase.io.read('atoms_files/ru_0001_POSCAR')
    sg_obj = SurfaceGrid(satoms, interval=0.1, rads=ads_obj.rads, lpca=False, subtype='slab')
    sg_obj.gridize()
    com_obj = AdsGridCombiner(sg_obj, ads_obj)
    print(com_obj.info)
    return com_obj

class TestCombiner:

    def test_C(self):
        adsatoms = Atoms('C')
        com_obj = Ru_ads(adsatoms)
        com_atoms = com_obj.get_atoms(sidx=0)
        view(com_atoms)

    def test_CO(self):
        adsatoms = molecule('CO')
        adsatoms.append(Atom('X',position=adsatoms.positions[-1]+[0,0,-0.1]))  # Add dock point
        com_obj = Ru_ads(adsatoms)
        com_atoms = com_obj.get_atoms(sidx=0)
        view(com_atoms)

    def test_C2H4(self):
        adsatoms = molecule('C2H4')
        adsatoms.append(Atom('X', position=[0.0, 0.0, -0.1]))  # Add dock point
        com_obj = Ru_ads(adsatoms)
        com_obj.ads_obj.rotation_delta = 30
        com_atoms = [com_obj.get_atoms(sidx=0, ridx=ridx,opt_z=True) for ridx in range(len(com_obj.ads_obj.rotation_grid))]
        view([i for i in com_atoms if i is not None])
        pass

    def test_C4H9(self):
        adsatoms = ase.io.read('atoms_files/C4H9.xyz')
        adsatoms.append(Atom('X', adsatoms.positions[0]))  # Add dock point with same pos with atoms[0]
        com_obj = Ru_ads(adsatoms)
        com_obj.ads_obj.rotation_delta = 30
        com_atoms = [com_obj.get_atoms(sidx=0, ridx=ridx,opt_z=True) for ridx in range(len(com_obj.ads_obj.rotation_grid))]
        view([i for i in com_atoms if i is not None])
        pass

    def test_CH4(self):
        adsatoms = molecule('CH4')
        com_obj = Ru_ads(adsatoms)
        com_obj.ads_obj.rotation_delta = 30
        com_atoms = [com_obj.get_atoms(sidx=0, ridx=ridx,opt_z=True) for ridx in range(len(com_obj.ads_obj.rotation_grid))]
        view([i for i in com_atoms if i is not None])
        pass

    def test_zeolite(self):
        # porous
        pass
