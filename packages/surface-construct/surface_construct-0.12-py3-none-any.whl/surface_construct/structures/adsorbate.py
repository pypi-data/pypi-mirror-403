import ase
import numpy as np
from typing import Tuple, Sequence, Dict, Union
from ase.geometry.analysis import Analysis as ase_Analysis
from ase.geometry.distance import distance as ase_distance
from scipy.spatial import cKDTree

from surface_construct.utils.atoms import atoms2graph, atoms_regulate, set_dihedrals, topodist_matrix, topo_identity
from surface_construct.utils.geometry import dih_grid, sample_rotations_with_symmetry, view_samples, \
    estimate_rotation_samples
from surface_construct.utils.pymsym_wrapper import get_pure_rotations, get_point_group, get_Cn


def get_dock_point_idx(atoms_pos, x_pos):
    if len(x_pos) == 0:
        return []
    tree = cKDTree(atoms_pos)
    x_tree = cKDTree(x_pos)
    dd = tree.sparse_distance_matrix(x_tree, max_distance=2.0, p=2).toarray()
    idx = dd.argmin(axis=0).reshape(1,-1)
    return idx

class Adsorbate:
    """
    吸附分子的类，类似与表面格点类，它包含了所有可能的姿态和二面角构象的离散化空间。
    还可以计算分子的质心，内坐标，主轴。
    """
    def __init__(self, atoms:ase.Atoms, **kwargs):
        # TODO：加上半径的参数，计算分子半径
        self.atoms = atoms.copy()
        del self.atoms[atoms.numbers == 0]
        self.dock_point_indices = get_dock_point_idx(self.atoms.positions,
                                                     atoms.positions[atoms.numbers == 0])
        self._atoms_graph = None
        self.nl = kwargs.get('nl', None)
        self.analysis = ase_Analysis(self.atoms, nl=self.nl)
        if self.nl is None:
            self.nl = self.analysis.nl
        self._adj_matrix = self.analysis.adjacency_matrix[0].toarray()
        self.internal_coords = dict()
        self.kwargs = kwargs
        self.is_regulated = False
        self.rtype = kwargs.get('rtype', 'covalent_radii')
        self._rads = None
        self._all_dihedrals = None
        self._dihedral_grid = None
        if len(self.atoms) < 4:
            self._all_dihedrals = []
            self._dihedral_grid = []
        self._dihedral_mask_dct = dict()
        self._dihedral_delta = None
        self._rotation_delta = None
        self._symmetry_rotations = None
        self._symmetry_rotation_operations = None
        self._rotation_grid = None
        self._rotation_grid_points = None  # 旋转角的空间点
        if len(self.atoms) == 1:
            self._rotation_grid = []

    @property
    def info(self):
        px, py, pz = self.principal_axis
        info = [f"Adsorbate molecule info: {self.atoms.get_chemical_formula()}",
                f"    Point Group: {self.point_group}",
                f"    Radius: {self.rads}",
                f"    Principal axis: [{px:8.3f}, {py:8.3f}, {pz:8.3f}] ",
                ]
        if self.dihedral_delta:
            info+=[
                f"    Number of dihedral grid: {len(self.dihedral_grid)}",
                f"    Number of dihedral: {len(self.all_dihedrals)}",
            ]
        info += [f"    Number of symmetry rotation operations: {len(self.symmetry_rotation_operations)}",
                f"    Number of symmetry rotations: {len(self._symmetry_rotations)}",]
        if self.rotation_delta:
            info.append(f"    Number of rotation grid: {len(self.rotation_grid)}")
        if len(self.dock_points)>0:
            info.append(f"    Number of dock points: {len(self.dock_points)}")
        return '\n'.join(info)

    @property
    def dock_points(self):
        pos = self.atoms.positions
        dp = [pos[i].mean(axis=0) for i in self.dock_point_indices]
        return np.asarray(dp)

    @property
    def point_group(self):
        return get_point_group(self.atoms)

    def regulate(self) -> None:
        """
        将分子旋转到主轴 = z, 次主轴=x, 第三轴 = y
        """
        # com to 0,0,0
        constraints = self.atoms.constraints.copy()  # 需要先消除限制，因为会影响set_com 和旋转
        self.atoms.constraints = []
        if len(self.atoms) > 1:
            atoms_regulate(self.atoms)
        else:
            self.atoms.set_center_of_mass([0.,0.,0.])
        self.is_regulated = True
        self.atoms.constraints = constraints

    @property
    def com(self):
        if self.is_regulated:
            return np.array([0., 0., 0.])
        else:
            return self.atoms.center_of_mass()

    @property
    def principal_axis(self):
        # 分子主轴向量
        #if not self.is_regulated:
        #    self.regulate()
        evals, evecs = self.atoms.get_moments_of_inertia(vectors=True)
        return evecs[np.argmin(np.abs(evals))]

    @property
    def rads(self):
        # 分子的半径，sg_obj 构造时作为参考
        # 思考：这是为了生成格点的半径，格点的位置是一种参考的位置，可以尽量接近真实的吸附结构。
        # 因而使用吸附原子的半径作为半径比较好，而不是分子的质心。当然，这是对于比较平整的slab 模型而言，对于团簇而言，也是如此吗？
        # 可以认为是的，到时候分子的质心沿着法向向量移动就可以了。
        if self._rads is not None:
            return self._rads

        from ase.data import covalent_radii, vdw_radii
        if self.rtype in ['covalent_radii', 'natural_cutoff']:
            radii = covalent_radii
        elif self.rtype == 'vdw_radii':
            radii = vdw_radii
        else:
            radii = covalent_radii

        if len(self.dock_point_indices) != 0: # 使用吸附原子的半径作为半径, 返回一个列表
            self._rads = np.mean([radii[self.atoms.numbers[i]]
                                  for ids in self.dock_point_indices for i in ids])
            return self._rads

        if not self.is_regulated:
            self.regulate()
        positions = self.atoms.positions
        dim_length = np.array([
            max(positions[:,0]) - min(positions[:,0]),
            max(positions[:,1]) - min(positions[:,1]),
            max(positions[:,2]) - min(positions[:,2])
        ])
        shortest_dim = np.argmin(dim_length)
        idx0 =np.argmin(positions[:,shortest_dim])
        idx1 =np.argmax(positions[:,shortest_dim])
        num0 = self.atoms.numbers[idx0]
        num1 = self.atoms.numbers[idx1]
        self._rads = (dim_length[shortest_dim] + radii[num0] + radii[num1]) / 2
        return self._rads

    @rads.setter
    def rads(self, value:float) -> None:
        self._rads = value

    @property
    def natoms(self) -> int:
        return len(self.atoms)

    @property
    def all_dihedrals(self)->Sequence:  # 只包含可以活动的二面角
        if self._all_dihedrals is None:
            print("Analysis all unique dihedrals by ase.geometry.analysis.Analysis")
            all_dihedrals = []
            for i, lst in enumerate(self.analysis.unique_dihedrals[0]):
                for jkl in lst:
                    j,k,l = jkl
                    all_dihedrals.append((i, j, k, l))
            self._all_dihedrals = self._filter_dihedral(all_dihedrals)
        return self._all_dihedrals

    @all_dihedrals.setter
    def all_dihedrals(self, value:Sequence[Tuple]) -> None:
        self._all_dihedrals = value

    def rm_dihedral(self, value) -> Tuple:
        d = self._all_dihedrals.pop(value)
        return d

    def add_dihedral(self, value:Tuple[int]) -> None:
        if self._all_dihedrals is None:
            self._all_dihedrals = [value]
        else:
            self._all_dihedrals.append(value)

    def _filter_dihedral(self, dihedrals: Sequence[Tuple[int]]) -> Sequence[Tuple]:
        # (i,j,k,l) 只保留 j,k 不同的二面角，且 i,l 尽可能是非H元素, 优先级 C > 其他重元素 > H
        filtered_dihedrals = {}
        # 构造 dict = {(j,k): (i,l)}
        for i,j,k,l in dihedrals:
            if j > k:  # 翻转 j,k 和 i,l
                key = (k, j)
                v = (l, i)
            else:
                key = (j, k)
                v = (i, l)
            if key in filtered_dihedrals:
                v_old = filtered_dihedrals[key]
                for idx, xx in enumerate(zip(v, v_old)):
                    ii, iio = xx
                    inum = self.atoms.numbers[ii]
                    ionum = self.atoms.numbers[iio]
                    if ionum != 6:
                        if inum == 6 or (inum > ionum):
                            filtered_dihedrals[key][idx] = ii
            else:
                filtered_dihedrals[key] = v

        filtered_dihedrals = [(val[0], key[0], key[1], val[1]) for key,val in filtered_dihedrals.items()]
        return filtered_dihedrals

    @property
    def atoms_graph(self):
        if self._atoms_graph is None:
            self._atoms_graph = atoms2graph(self.atoms, adj=self._adj_matrix)

        return self._atoms_graph

    @property
    def topo_id(self):
        dm = topodist_matrix(self._adj_matrix)
        ids = topo_identity(dm)
        return ids

    def get_dihedral_mask(self, dihedral: Tuple[int, int, int, int]) -> set:
        """
        为二面角生成移动的 mask indices
        :param dihedral:
        :return:
        """
        dm = self._dihedral_mask_dct.get(dihedral, None)
        if dm is None:
            import networkx as nx
            new_graph = self.atoms_graph.copy()
            i,j,k,l = dihedral
            if not new_graph.has_edge(j,k):
                raise ValueError(f"{j}-{k} is not connected, please check the dihedral.")
            # 删除 j-k 生成新的图
            new_graph.remove_edge(j,k)
            components = list(nx.connected_components(new_graph))
            ncomponent = len(components)
            if ncomponent == 1:
                raise NotImplementedError(f"{j}-{k} is in a ring, this is not supported yet.")
            elif ncomponent > 2:
                raise ValueError(f"Break {j}-{k} bond produces {ncomponent} parts.")
            comp1, comp2 = components[0], components[1]
            if len(comp1) > len(comp2):
                dm = comp1
            else:
                dm = comp2
            self._dihedral_mask_dct[dihedral] = dm
        return dm

    @property
    def dihedral_delta(self):
        return self._dihedral_delta

    @dihedral_delta.setter
    def dihedral_delta(self, value):
        if self._dihedral_delta !=value:
            self._dihedral_delta = value
            self._dihedral_grid = None
            n = int(360/self.dihedral_delta) ** len(self.all_dihedrals)
            print(f"Number of dihedrals before refine: {n}")

    @property
    def dihedral_grid(self):
        if self.dihedral_delta is None:
            print("Please set dihedral_delta first!")
            return None

        if self._dihedral_grid is None:
            self._dihedral_grid = dih_grid(len(self.all_dihedrals), int(360/self.dihedral_delta))
        return self._dihedral_grid

    def refine_dihedral_grid(self, tolerance=0.5) -> None:
        atoms_list = []
        for dih_values in self.dihedral_grid:
            dih_dict = {i: {'value': dih_values[idx], 'mask': self.get_dihedral_mask(i)}
                        for idx, i in enumerate(self.all_dihedrals)}
            # 设置 二面角
            atoms = set_dihedrals(self.atoms, dih_dict)
            # regularize
            atoms_regulate(atoms)
            atoms_list.append(atoms)
        # 计算分子之间的距离
        n_structures = len(atoms_list)
        dist_matrix = np.zeros((n_structures, n_structures))
        for i in range(n_structures):
            for j in range(i + 1, n_structures):
                dist = ase_distance(atoms_list[i], atoms_list[j], permute=True)
                # TODO: 使用 CDTree 计算相似性
                #       比如，先对 H 原子求dist，然后再对其他原子分别求相似性。
                #       或者分别对不同类型原子用 cdist
                dist_matrix[i, j] = dist
                dist_matrix[j, i] = dist

        ## 排除相似的分子
        selected_indices = []
        selected_mask = np.zeros(n_structures, dtype=bool)
        for i in range(n_structures):
            if not selected_mask[i]:
                selected_indices.append(i)
                # 标记所有相似的结构
                similar_indices = np.where(dist_matrix[i] < tolerance)[0]
                selected_mask[similar_indices] = True
        self._dihedral_grid = self.dihedral_grid[selected_indices]

    def get_vip_dih(self)->Sequence:
        # TODO: 对气相分子C空间进行采样，得到势能面，然后进行关键点识别（critical point）（盆分析），得到极小值点的集合
        return []

    def get_dihedrals(self, dih_value=None)->dict:
        if dih_value is None: # 返回当前结构的二面角
            dih_value = [self.atoms.get_dihedral(*d)  for d in self.all_dihedrals]

        dihedrals = {d: {'value': dih_value[i], 'mask': self.get_dihedral_mask(d)}
                           for i, d in enumerate(self.all_dihedrals)}
        return dihedrals

    @property
    def symmetry_rotation_operations(self) -> Dict:
        if len(self.atoms) == 1:
            self._symmetry_rotations = []
            return dict()
        if self._symmetry_rotations is None:
            self._symmetry_rotations = get_pure_rotations(self.atoms)
            self._symmetry_rotation_operations = get_Cn(self.atoms)
        return self._symmetry_rotation_operations

    @property
    def rotation_delta(self) -> float:
        return self._rotation_delta

    @rotation_delta.setter
    def rotation_delta(self, value) -> None:
        if len(self.atoms) == 1:
            print("No rotation for monatomic molecule.")
            self._rotation_grid = []
        else:
            self._rotation_delta = value
            n = estimate_rotation_samples(value, self.point_group)
            print(f"Number of rotation samples: {n}")
            self._rotation_grid = None

    @property
    def rotation_grid(self):
        """
        :return: rotation quaternions grid
        """
        if len(self.atoms) == 1:
            return None

        if self.rotation_delta is None:
            print("Please set rotation_delta first!")
            return None

        if self._rotation_grid is None:
            _ = self.symmetry_rotation_operations
            self._rotation_grid = sample_rotations_with_symmetry(avg_deg=self.rotation_delta,
                                                   point_group=self.point_group,
                                                   sym_quats=[i.as_quat(scalar_first=True)
                                                              for i in self._symmetry_rotations]
                                                   )
        return self._rotation_grid

    @rotation_grid.setter
    def rotation_grid(self, values:Sequence) -> None: # define your own grid, or modify them.
        self._rotation_grid = values

    def view_rotation_grid(self, save_path=None) -> None:
        view_samples(self.rotation_grid, save_path=save_path)

    def view_rotation_atoms(self):
        from scipy.spatial.transform import Rotation
        from ase.visualize import view

        if self.rotation_grid is None:
            print("Please set rotation_grid first!")
            return None

        euler = Rotation.from_quat(self.rotation_grid, scalar_first=True).as_euler('zxz', degrees=True)
        atoms_list = []
        for eu in euler:
            A = self.atoms.copy()
            A.euler_rotate(*eu)
            atoms_list.append(A)
        view(atoms_list)
        return None

