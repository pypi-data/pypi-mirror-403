import pytest
from ase.visualize import view
import numpy as np
from ase.build import molecule
from surface_construct import Adsorbate
from surface_construct.utils.atoms import set_dihedrals,atoms_regulate


class TestAdsorbate:

    def test_pointgroup_benzene(self):
        atoms = molecule("C6H6")
        ads_obj = Adsorbate(atoms)
        print(ads_obj.info)
        pointgroup = ads_obj.point_group
        assert pointgroup == "D6h"

    def test_pointgroup_CO2(self):
        atoms = molecule("CO2")
        ads_obj = Adsorbate(atoms)
        print(ads_obj.info)
        pointgroup = ads_obj.point_group
        assert pointgroup == "Dinfh"

    def test_pointgroup_CO(self):
        atoms = molecule("CO")
        ads_obj = Adsorbate(atoms)
        print(ads_obj.info)
        pointgroup = ads_obj.point_group
        assert pointgroup == "Cinfv"

    def test_pointgroup_CH4(self):
        atoms = molecule("CH4")
        ads_obj = Adsorbate(atoms)
        print(ads_obj.info)
        pointgroup = ads_obj.point_group
        assert pointgroup == "Td"

    def test_rotation_grid_benzene(self):
        atoms = molecule("C6H6")
        ads_obj = Adsorbate(atoms)
        ads_obj.rotation_delta = 30
        rot_grid = ads_obj.rotation_grid
        print(f"Rotation angle interval is {ads_obj.rotation_delta}.")


    def test_all_dihedrals_propane(self):
        atoms = molecule("C3H8")
        ads_obj = Adsorbate(atoms)
        all_dihedrals = ads_obj.all_dihedrals
        assert all_dihedrals == [(1, 0, 2, 6), (2, 0, 1, 5)]

    def test_regulate_propane(self):
        atoms = molecule("C3H8")
        ads_obj = Adsorbate(atoms)
        ads_obj.regulate()
        com1 = ads_obj.atoms.get_center_of_mass()
        pa1 = ads_obj.principal_axis
        assert com1 == pytest.approx(0.0, abs=1e-5)
        assert pa1 == pytest.approx(np.array([1,0,0]), abs=1e-5)

    def test_rads_propane(self):
        atoms = molecule("C3H8")
        ads_obj = Adsorbate(atoms)
        rads = ads_obj.rads
        assert rads == pytest.approx(1.194, abs=1e-3)

    def test_dihedral_mask_propane(self):
        atoms = molecule("C3H8")
        ads_obj = Adsorbate(atoms)
        all_dih = ads_obj.all_dihedrals
        dih_mask_list = []
        for dih in all_dih:
            dih_mask = ads_obj.get_dihedral_mask(dih)
            dih_mask_list.append(dih_mask)
        assert dih_mask_list == [{0, 1, 3, 4, 5, 7, 8}, {0, 2, 3, 4, 6, 9, 10}]

    def test_dihedrals_grid_propane(self):
        atoms = molecule("C3H8")
        ads_obj = Adsorbate(atoms)
        ads_obj.dihedral_delta = 30
        dih_grid = ads_obj.dihedral_grid
        print(len(dih_grid))
        dihedrals_list = [ads_obj.get_dihedrals(v) for v in dih_grid]
        atoms_list = [set_dihedrals(ads_obj.atoms, d) for d in dihedrals_list]
        atoms_list_aligned = [atoms_regulate(atoms_list[0])]
        for i in atoms_list[1:]:
            atoms_list_aligned.append(atoms_regulate(i,atoms_list_aligned[0]))
        #view(atoms_list_aligned)
        ads_obj.refine_dihedral_grid(tolerance=0.5)
        refined_dih_grid = ads_obj.dihedral_grid
        print(len(refined_dih_grid))

    def test_rotations_grid_propane(self):
        atoms = molecule("C3H8")
        ads_obj = Adsorbate(atoms)
        ads_obj.rotation_delta = 30
        rot_grid = ads_obj.rotation_grid
        print(f"Rotation angle interval is {ads_obj.rotation_delta}.")
        print(f"Rotation grid are {len(rot_grid)}")

