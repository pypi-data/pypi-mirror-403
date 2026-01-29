import ase.io
import pytest

from ase.visualize import view
import ase
from surface_construct import GridGenerator
from ase.cluster.cubic import FaceCenteredCubic
from surface_construct import SurfaceGrid

class TestSurfaceGrid:
    def test_Cu_cluster(self):
        """
        GridGenerator.
        Runtime is about 9s
        :return:
        """
        surfaces = [(1, 0, 0), (1, 1, 0), (1, 1, 1)]
        layers = [4, 4, 4]
        lc = 3.61000
        atoms = FaceCenteredCubic('Cu', surfaces, layers, latticeconstant=lc)

        atoms.cell = [35, 35, 35]
        atoms.pbc = False  # True is very slow
        atoms.center()

        gridgen = GridGenerator(atoms, interval=0.1)
        grid = gridgen.grid
        print(len(grid))

    def test_Ag_cluster(self):
        # Ag55
        # Time: 4.23s
        atoms = ase.io.read('atoms_files/Ag.xyz')
        gridgen = GridGenerator(atoms, interval=0.2, subtype='cluster')
        grid = gridgen.grid
        print(len(grid))

    def test_Ru0001_slab(self):
        # Ru(0001)
        # Time: 4.23s
        atoms = ase.io.read('atoms_files/ru_0001_POSCAR')
        gridgen = GridGenerator(atoms, interval=0.1, subtype='slab')
        grid = gridgen.grid
        print(len(grid))

    def test_Ru0001_grid_graph(self):
        # Ru(0001)
        atoms = ase.io.read('atoms_files/ru_0001_POSCAR')
        sg_obj = SurfaceGrid(atoms, interval=0.1, ads_num=6, lpca=False)
        sg_obj.gridize(subtype='slab')
        sg_obj.vectorize()
        graph = sg_obj.grid_graph
        vip = sg_obj.vip_id
        uvip = sg_obj.unique_vip_id
        uvip_points = sg_obj.points[uvip]  # [[x,y,z],....]  Nx3
        print(len(vip))
        print(sg_obj.vector_unit)
        print(len(sg_obj.vector))

    def test_In2O3_slab(self):
        # In2O3. Should use larger scale.
        atoms = ase.io.read('atoms_files/POSCAR_In2O3_110')
        sg_obj = SurfaceGrid(atoms, interval=0.1, ads_num=6, lpca=False)
        sg_obj.gridize(subtype='slab')
        print(f"Number of points before remove_unconnected: {len(sg_obj.points)}")
        sg_obj.remove_unconnected()
        print(f"Number of points after remove_unconnected: {len(sg_obj.points)}")
        sg_obj.vectorize()
        graph = sg_obj.grid_graph
        vip = sg_obj.vip_id
        print(len(vip))
        print(sg_obj.vector_unit)

    def test_Fe3C_slab(self):
        atoms = ase.io.read('atoms_files/Fe3C001_07_CONTCAR')
        sg_obj = SurfaceGrid(atoms, interval=0.1, ads_num=6, lpca=False)
        sg_obj.gridize(subtype='slab')
        sg_obj.vectorize()
        graph = sg_obj.grid_graph
        grid_site_label, site_dict = sg_obj.get_grid_site_type()
        grid_index_label, index_dict = sg_obj.get_grid_index_type()
        vip = sg_obj.vip_id
        print(len(vip))
        print(list(site_dict.keys()))

    def test_Fe3C_slab2(self):
        atoms = ase.io.read('atoms_files/Fe3C_001.vasp')
        sg_obj = SurfaceGrid(atoms, interval=0.1, ads_num=6, lpca=False)
        sg_obj.gridize(subtype='slab')
        atoms = sg_obj.atoms
        print(len(sg_obj.points))

    def test_ZSM5(self):
        atoms = ase.io.read('atoms_files/zsm5.cif')
        gridgen = GridGenerator(atoms, interval=0.5, subtype='bulk', rsub='vdw_radii', scale=1.0)
        grid = gridgen.grid
        print(len(grid))

    def test_interface1(self):
        atoms = ase.io.read('atoms_files/CuOx-Cu100-CONTCAR')
        sg_obj = SurfaceGrid(atoms, interval=0.2, ads_num=6, lpca=False)
        sg_obj.gridize(subtype='slab')
        sg_obj.vectorize()
        vip = sg_obj.vip_id
        uvip = sg_obj.unique_vip_id
        print(len(vip), len(uvip))

    def test_In2O3_4x4(self):
        # This a large surface, contain about 75K points.
        atoms = ase.io.read('atoms_files/POSCAR_In2O3_110')
        superatoms = atoms.repeat([2,2,1])
        sg_obj = SurfaceGrid(superatoms, interval=0.1, ads_num=6, lpca=False)
        sg_obj.gridize(subtype='slab')
        Lga = sg_obj._Lga
        print(Lga.shape)

    def test_triclinic(self):
        atoms = ase.io.read('atoms_files/Fe28C12_115_12_POSCAR')
        sg_obj = SurfaceGrid(atoms, interval=0.1, ads_num=6, lpca=False)
        sg_obj.gridize(subtype='slab')
        print(sg_obj.points.shape)