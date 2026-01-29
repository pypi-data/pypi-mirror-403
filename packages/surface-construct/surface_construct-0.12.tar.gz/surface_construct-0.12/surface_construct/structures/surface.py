import itertools

import ase
import ase.build.surface
import numpy as np
import pandas as pd
import spglib
from tqdm import tqdm

from surface_construct.utils.atoms import topo_identity,dist_identity, get_atoms_topo_id, bondvalence, \
    refined_atoms, atoms2spg, coprime_factor, adj_matrix, topodist_matrix, atoms2graph, coordnum_adj


class Crystal(object):

    def __init__(self, atoms, name=None):
        """
        TODO: spglib properties

        :param atoms:
        """
        assert np.all(atoms.pbc)
        self.atoms = atoms
        self._miller_dict = None
        self._max_hkl = None
        self._primary_hkl = None  # list of all primary_hkl
        if name is None:
            self.name = atoms.get_chemical_formula(mode='metal', empirical=True)

    def get_refined_crystal(self):
        # 比较晶胞参数，如果相同，则返回 None
        ratoms = refined_atoms(self.atoms)
        rcell_par = ratoms.cell.cellpar()
        cell_par = self.atoms.cell.cellpar()
        if np.any(np.abs(np.sort(cell_par) - np.sort(rcell_par)) > 0.01):
            return Crystal(ratoms)
        return None

    @property
    def max_hkl(self):
        return self._max_hkl

    @max_hkl.setter
    def max_hkl(self, v):
        self._max_hkl = v
        # 重新计算相关属性
        self._miller_dict = None
        self._primary_hkl = None

    @property
    def miller_dict(self):
        """
        Generate a bunch of miller index
        :return: dict, primary index as the key, all degenerate index as value
        """
        if self._miller_dict is None:
            max_hkl = self._max_hkl
            if max_hkl is None:
                max_hkl = (3, 3, 3)
            elif type(max_hkl) in (int,):
                max_hkl = [max_hkl] * 3

            upx = max_hkl[0]
            downx = -1 * max_hkl[0]
            upy = max_hkl[1]
            downy = -1 * max_hkl[1]
            upz = max_hkl[2]
            downz = -1 * max_hkl[2]
            miller_dict = {}
            full_list = list(itertools.product(range(downx, upx + 1),
                                               range(downy, upy + 1),
                                               range(downz, upz + 1)))
            full_list.remove((0, 0, 0))
            for i, j, m in full_list:
                indices = reduce_miller_indices((i, j, m))
                hkl, all_indices = get_symmetry_miller(self.atoms, indices)
                if hkl not in miller_dict:
                    miller_dict[hkl] = all_indices
                if (i, j, m) not in miller_dict[hkl]:
                    miller_dict[hkl].append((i, j, m))
            # print(len(miller_dict),len(full_list),len(miller_dict)/len(full_list))

            self._max_hkl = max_hkl
            self._miller_dict = miller_dict

        return self._miller_dict

    @property
    def primary_hkl(self):
        if self._primary_hkl is None:
            self._primary_hkl = list(self.miller_dict.keys())

        return self._primary_hkl

    def create_surface(self, hkl):
        return Surface(self, hkl)

    @property
    def density(self):
        V = self.atoms.get_volume()
        N = len(self.atoms)
        return N / V


class Surface:
    def __init__(self, crystal, hkl):
        self.crystal = crystal
        self.hkl = hkl
        self.reduced_hkl = reduce_miller_indices(hkl)
        self.primary_hkl, self.peer_hkl = get_symmetry_miller(crystal.atoms,
                                                              self.reduced_hkl)
        self._refine = None
        self._area = None
        self._surface_parameter = None
        self.original_surface_parameter = None

    @property
    def surface_parameter(self, refine=False):
        if refine != self._refine or self._surface_parameter is None:
            slab = self.create_slab(refine=refine)
            len_ang = slab.atoms.cell.cellpar()
            self._surface_parameter = len_ang
        return self._surface_parameter

    @surface_parameter.setter
    def surface_parameter(self, v):
        self._surface_parameter = v

    def create_slab(self, layers=3, vacuum=15.0, atoms=None, refine=None, from_last=False):
        slab = Slab(self, layers, vacuum, atoms=atoms, refine=refine, from_last=from_last)
        return slab

    @property
    def area(self):
        if self._area is None:
            sp = self.surface_parameter
            a, b, angle = sp[0], sp[1], sp[-1]
            self._area = a * b * np.sin(angle / 180 * np.pi)

        return self._area

    @area.setter
    def area(self,v):
        self._area = v

class Slab(object):
    def __init__(self, surface, layers=3, vacuum=15.0, atoms=None, refine=False, from_last=False):
        """
        TODO: construct from atoms without surface
        :param surface:
        :param layers:
        :param vacuum:
        :param atoms:
        :param refine:
        :param from_last: peel atoms from last index, default is from first.
        """
        self.surface = surface
        self.layers = layers
        self.vacuum = vacuum
        self.from_last = from_last
        if not atoms:
            atoms = ase.build.surface(surface.crystal.atoms,
                                      surface.primary_hkl,
                                      layers,
                                      periodic=True,
                                      vacuum=vacuum)
        if refine:
            atoms = refined_atoms(atoms)

        self.refine = refine  # 构造好了就要再更改了
        self.atoms = atoms
        self.natoms = len(self.atoms)
        self.natoms_per_layer = int(self.natoms / layers)  # Dirty: atoms 变量必须包含整数倍的层

        self._sheet_list = None
        self._peel_set = None
        self._sheet_window = None

        self._adj_matrix = None
        self._graph = None
        self._all_cn = None
        self._bulk_cn = None

        self._skin_id = None
        self._bulk_id = None
        self._bottom_id = None

    @property
    def graph(self):
        """
        Networkx Graph for slab model. 主要的目的是为了生成 termination 共用同一个母版。
        :return:
        """
        if self._graph is None:
            self._graph = atoms2graph(self.atoms, adj=self.adj_matrix)
        return self._graph

    @property
    def thickness(self):
        posz = self.atoms.positions[:, 2]
        result = posz.max() - posz.min()
        return result

    @property
    def thickness_per_layer(self):
        return self.thickness / self.layers

    @property
    def adj_matrix(self):
        if self._adj_matrix is None:
            self._adj_matrix = adj_matrix(self.atoms)
        return self._adj_matrix

    def supercell(self, size=(1, 1)):
        """
        TODO: super size the surface too.
        :param size:
        :return:
        """
        multiple = size[0] * size[1]
        if multiple == 1:
            return self
        # make supercell
        P = [[size[0], 0, 0],
             [0, size[1], 0],
             [0, 0, 1]]
        extended_atoms = ase.build.make_supercell(self.atoms, P, wrap=False)  # Note: wrap may change the atoms order.
        # reorder atoms
        new_atoms = ase.Atoms(cell=extended_atoms.cell, pbc=extended_atoms.pbc)
        # append atoms layer by layer
        for ilayer in range(self.layers):
            for icell in range(multiple):
                atoms_id = [i + self.natoms_per_layer * ilayer + self.natoms * icell
                            for i in range(self.natoms_per_layer)]
                new_atoms.extend(extended_atoms[atoms_id])
        # TODO: create new super surface
        super_slab = Slab(self.surface, self.layers, vacuum=self.vacuum, atoms=new_atoms, from_last=self.from_last)
        super_slab.surface.surface_parameter = new_atoms.cell.cellpar()
        super_slab.surface.area = None
        super_slab.refine = True  # 不能在初始化时定义，否则会重构成单胞。但是这里为什么要定义为 True 呢？
        return super_slab

    def set_layers(self, layers):
        """
        This is useful to merge layers, such as we got a slab with 6 layers, we want to merge them to 3 layers
        :param layers:
        :return:
        """
        if self.layers % layers != 0:
            raise "Error: 无法被整除！"

        if layers < 3:
            raise "Error: 层数不能小于3！"

        self.layers = layers
        self.natoms_per_layer = int(self.natoms / layers)
        # 重新定义 self._skin_id, self._bulk_id, self._bottom_id
        self._skin_id = None
        self._bulk_id = None
        self._bottom_id = None
        self._sheet_list = None
        self._peel_set = None
        self._bulk_cn = None

    @property
    def all_cn(self):
        """
        Slab 中所有原子的配位数
        :return: 配位数列表，[{(原子序号，原子序号): 数量}]
        """
        if self._all_cn is None:
            self._all_cn = coordnum_adj(self.adj_matrix)

        return self._all_cn

    @property
    def bulk_cn(self):
        """
        Slab 中所有体相位置原子的配位数
        :return: 配位数列表，[{(原子序号，原子序号): 数量}]
        """
        if self._bulk_cn is None:
            self._bulk_cn = [self.all_cn[i] for i in self.bulk_id]
        return self._bulk_cn

    @property
    def skin_id(self):  # Dirty trick
        """
        表层 skin 的原子序号。假设体系有三层，以第一层为表层。
        :return:
        """
        if self._skin_id is None:
            if self.from_last:
                self._skin_id = list(range(self.natoms_per_layer * (self.layers - 1),
                                  self.natoms_per_layer * self.layers))
            else:
                self._skin_id = list(range(0, self.natoms_per_layer))
        return self._skin_id

    @property
    def bulk_id(self):  # Dirty trick
        """
        体相原子的原子序号。假设体系有三层，以中间层为表层。
        :return:
        """
        if self._bulk_id is None:
            self._bulk_id = list(range(self.natoms_per_layer,
                                       self.natoms_per_layer * (self.layers - 1)))
        return self._bulk_id

    @property
    def bottom_id(self):  # Dirty trick
        """
        底层原子的原子序号。假设体系有三层，以最下层为底层。
        :return:
        """
        if self._bottom_id is None:
            if not self.from_last:
                self._bottom_id = list(range(self.natoms_per_layer * (self.layers - 1),
                                  self.natoms_per_layer * self.layers))
            else:
                self._bottom_id =  list(range(0, self.natoms_per_layer))
        return self._bottom_id

    def estimate_terminations(self, sheet_window=0.5):
        """
        估算终结的个数。根据二项式系数之和 2^k 进行估算，结果一般会高估。
        :return:
        """
        # return 2 ** self.natoms_per_layer - 1
        self.sheet_window = sheet_window
        return sum([2 ** len(sheet) - 1 for sheet in self.sheet_list])

    @property
    def sheet_window(self):
        return self._sheet_window

    @sheet_window.setter
    def sheet_window(self, v):
        if self._sheet_window != v:
            self._sheet_window = v
            # 重置 sheet_list 和 peel_set
            self._sheet_list = None
            self._peel_set = None
        else:
            pass

    @property
    def sheet_list(self):
        """

        :return: list of sheet iz
        """
        if self._sheet_list:
            return self._sheet_list

        pos = self.atoms.positions
        skin_id = self.skin_id
        posz = pos[skin_id, 2]
        zmin, zmax = pos[:, 2].min(), pos[:, 2].max()
        posz = posz - zmin if posz[0] - zmin < zmax - posz[0] else zmax - posz
        sorted_posz = sorted(zip(skin_id,posz), key=lambda lst: lst[1])
        posz = [i[1] for i in sorted_posz]
        posz_idx = [i[0] for i in sorted_posz]  # 由小到大排列，从外表面到内部
        posz_mx, posz_my = np.meshgrid(posz, posz)
        posz_dist = np.abs(posz_mx - posz_my)
        idx_row, idx_col = np.argwhere(posz_dist < self.sheet_window).T
        idx_row_set = sorted([[i, posz[i]] for i in set(idx_row)], key=lambda lst: lst[1])  # 从外表面到內表面排序，否则在切除的时候会混乱
        sheet_list = []
        for ir,_ in idx_row_set:
            idx_col_set = set([posz_idx[i] for i in idx_col[idx_row == ir]])
            if idx_col_set in sheet_list:
                continue
            if any([idx_col_set.issubset(old_set) for old_set in sheet_list]):
                continue
            for old_set in sheet_list[:]:
                if idx_col_set.issuperset(old_set):
                    sheet_list.remove(old_set)
            sheet_list.append(idx_col_set)

        self._sheet_list = sheet_list
        return sheet_list

    @property
    def peel_set(self):
        if self._peel_set:
            return self._peel_set

        peel_list = []
        base_peel = set()
        for sheet in self.sheet_list:
            base_peel.difference_update(sheet)  # 需要把本层相关的去掉
            peel_list += [base_peel.union(set(idx_list)) for n in range(1, len(sheet) + 1)
                          for idx_list in itertools.combinations(sheet, n)]
            base_peel.update(sheet)
        peel_set = set([tuple(i) for i in peel_list])
        self._peel_set = peel_set

        return self._peel_set

    def get_all_terminations(self, sheet_window=0.5, unique=False, id_type='topo'):
        """
        Extract all the termination for given miller indices

        :return: dict, key is the topoeigen value to distinguish the surface,
            value is the list of the degenerate termination.
        """
        print("Estimate total terminations count, ", self.estimate_terminations(sheet_window))
        self.sheet_window = sheet_window
        peel_set = self.peel_set
        print("Real total terminations count, ", len(peel_set))
        terminations = [self.create_terminations(peel) for peel in peel_set]

        if unique:
            terminations_dict = {termination.get_identity(id_type=id_type): termination
                                 for termination in tqdm(terminations)}
            print("Unique terminations count, ", len(terminations_dict))
            return terminations_dict
            # terminations = list(terminations_dict.values())

        return terminations

    def create_terminations(self, peel_id=None):
        """
        Extract all the termination for given miller indices

        :return: dict, key is the topoeigen value to distinguish the surface,
            value is the list of the degenerate termination.
        """
        if peel_id is None:
            peel_id = []
        _ = self.graph  # 保证已经计算 graph，这样就不需要在termination中重复计算了, self.adj_matrix 也已经算过了
        return Termination(self, peel_id)


class Termination(object):
    """
    定义：slab 是刚切出来的结构，skin是表面第一层，bulk是内层，bottom是底层表面
    peel 是削掉的原子，dermis 是 skin 削掉 peel 以后的部分
    dermis + bulk 组成完整的终结面。
    """

    def __init__(self, slab, peel_id, atoms=None):

        assert slab.layers >= 3

        self.peel_id = peel_id
        self.slab = slab
        self.surface = slab.surface
        self.layers = slab.layers
        self.natoms_per_layer = slab.natoms_per_layer
        # self.natoms = slab.natoms
        # 注意下面的都是以母版slab 的序号为基础
        self.skin_id = sorted(slab.skin_id)  # 为什么要排序？
        self.bulk_id = slab.bulk_id
        self.bottom_id = slab.bottom_id
        self.dermis_id = sorted(list(set(self.skin_id) - set(peel_id)))  # 真皮层，为什么要排序？
        self.termination_id = [idx for idx in range(self.slab.natoms) if idx not in peel_id]

        self.atoms = atoms
        if atoms is None:
            self.atoms = self.slab.atoms[self.termination_id]

        # 根据 termination.atoms 重新对原子编号
        if self.slab.from_last:
            # TODO: dirty, add the case for both side, or disordered the index
            self.atoms_dermis_id = np.arange(len(self.atoms)-len(self.dermis_id), len(self.atoms))
            self.atoms_bulk_id = self.bulk_id[:]
            self.atoms_bottom_id = self.bottom_id[:]
        else:
            self.atoms_dermis_id = np.arange(len(self.dermis_id))
            self.atoms_bulk_id = np.arange(len(self.dermis_id), len(self.dermis_id + self.bulk_id))
            self.atoms_bottom_id = np.arange(len(self.dermis_id + self.bulk_id), len(self.atoms))

        self._adj_matrix = None
        self._all_cn = None
        self._cus_cn = None
        self._dermis_cn = None
        self._peel_cn = None
        self._cus_id = None
        self._atoms_cus_id = None

        self._thickness = None
        self.identity = None
        self.identity_type = None
        self.dsuc = None

    @property
    def adj_matrix(self):
        # TODO: use get_sub_matrix()
        if self._adj_matrix is None:
            row_idx, col_idx = np.asarray(list(itertools.product(self.termination_id, self.termination_id))).T
            dim = len(self.termination_id)
            self._adj_matrix = self.slab.adj_matrix[row_idx, col_idx].reshape((dim, dim))

        return self._adj_matrix

    @property
    def all_cn(self):
        if not self._all_cn:
            self._all_cn = coordnum_adj(self.adj_matrix)
        return self._all_cn

    @property
    def slab_bulk_cn(self):
        return self.slab.bulk_cn

    @property
    def dermis_cn(self):
        if self._dermis_cn is None:
            self._dermis_cn = [self.all_cn[i] for i in self.atoms_dermis_id]
        return self._dermis_cn

    @property
    def peel_cn(self):
        if self._peel_cn is None:
            bulk_cn = [self.all_cn[i] for i in self.atoms_bulk_id]  # not real bulk
            self._peel_cn = [bulk_cn[i] for i in self.peel_id]
        return self._peel_cn

    @property
    def atoms_cus_id(self):
        """
        Cus is the coordinate unsaturated site. The atoms_cus_id is the index
        of self.atoms.
        :return:
        """
        if self._atoms_cus_id is None:
            skin_idx = list(self.atoms_dermis_id) + list(self.atoms_bulk_id)
            self._atoms_cus_id = [idx for idx, item in zip(skin_idx, self.cus_cn)
                                  if any([i != 0 for i in item.values()])]
        return self._atoms_cus_id

    @property
    def cus_id(self):
        """
        Cus is the coordinate unsaturated site.The cus_id is the index
        of self.slab.atoms.
        :return:
        """
        if self._cus_id is None:
            slab_idx = self.dermis_id + self.bulk_id
            self._cus_id = [idx for idx, item in zip(slab_idx, self.cus_cn)
                            if any([i != 0 for i in item.values()])]

        return self._cus_id

    @property
    def cus_cn(self):
        """
        Cus is the coordinate unsaturated site number.
        :return:
        """
        if self._cus_cn is None:
            terminal_bulk_cn = [self.all_cn[i] for i in self.atoms_bulk_id]
            slab_bulk_cn = self.slab.bulk_cn
            result = []  # idx is the id of self.atoms
            for idx, item in zip(self.dermis_id, self.dermis_cn):  # Must take all surface layer into account.
                if self.slab.from_last:
                    i = idx - (self.layers - 1) * self.natoms_per_layer
                else:
                    i = idx
                cus_item = {}
                for k in item:
                    cus_item[k] = slab_bulk_cn[i][k] - item[k]
                result.append(cus_item)
            for idx, item in zip(self.bulk_id, terminal_bulk_cn):
                cus_item = {}
                for k in item:
                    cus_item[k] = slab_bulk_cn[idx - self.natoms_per_layer][k] - item[k]
                result.append(cus_item)

            self._cus_cn = result  # _cus_cn 中不仅有cus的cn，还有其他的cn，只是都是0而已

        # 接下来，我们构造新的 cus_cn
        # cus_cn 是一个dict：{cus_id: cn_dict}
        # cus_cn = {idx: self._cus_cn[idx] for idx in self.cus_id}
        return self._cus_cn

    def pseudo_layer(self, fromslab=False):
        """
        The pseudo layer is consist of dermis and complementary sub skin
        :return:
        """
        if fromslab:
            dermis = self.dermis_id
            bulk = np.array(self.bulk_id, dtype=int)
        else:
            dermis = self.atoms_dermis_id
            bulk = np.array(self.atoms_bulk_id, dtype=int)

        complement = [bulk[i] for i in self.peel_id]

        return np.concatenate([dermis, complement])

    def get_identity(self, id_type='topo'):
        if (not self.identity) or (self.identity_type!=id_type):
            pseudo_skin_atoms = self.atoms[self.atoms_cus_id]
            # add ghost at the top of the surface, in order to distinguish the surface
            pseudo_skin_z = pseudo_skin_atoms.positions[:, 2]
            if self.slab.from_last:  # dirty: index 0 at bottom and max index at top
                tips = np.concatenate(np.argwhere(pseudo_skin_z == pseudo_skin_z.max()))  # get the tip atoms id
                ghost_xyz = pseudo_skin_atoms.positions[tips]
                ghost_xyz[:, 2] = ghost_xyz[:, 2] + 0.5
            else:
                tips = np.concatenate(np.argwhere(pseudo_skin_z == pseudo_skin_z.min()))  # get the tip atoms id
                ghost_xyz = pseudo_skin_atoms.positions[tips]
                ghost_xyz[:, 2] = ghost_xyz[:, 2] - 0.5
            pseudo_skin_atoms.extend(ase.Atoms('X' + str(len(ghost_xyz)), ghost_xyz))
            if id_type == 'topo':
                identity = get_atoms_topo_id(pseudo_skin_atoms)
            elif id_type == 'dist':
                identity = dist_identity(pseudo_skin_atoms)
            else:
                raise NotImplementedError
            self.identity = identity
            self.identity_type = id_type
        return self.identity

    def get_identity_fast(self):
        """
        使用 slab 中预先保存的 topodist_matrix，从中取出相应的元素，组成新的matrix，然后新加入 X 进入 matrix。节省生成 topodist_matrix 的时间
        :return:
        """
        if not self.identity:
            slab_adj_matrix = self.slab.adj_matrix
            cus_id = self.cus_id
            row_idx, col_idx = np.asarray(list(itertools.product(cus_id, cus_id))).T
            len_cus = len(cus_id)
            pseudo_skin_adj_matrix = slab_adj_matrix[row_idx, col_idx].reshape((len_cus, len_cus))
            # 得到顶端原子的序号，相对于 pseudo_skin 的序号
            pseudo_skin_atoms = self.atoms[self.atoms_cus_id]
            pseudo_skin_z = pseudo_skin_atoms.positions[:, 2]
            tips_id = np.concatenate(np.argwhere(pseudo_skin_z == pseudo_skin_z.min()))
            # 定义目标matrix
            n_tip = len(tips_id)
            ghost_adj_matrix = np.zeros((n_tip + len_cus, n_tip + len_cus))
            ghost_adj_matrix[:len_cus, :len_cus] = pseudo_skin_adj_matrix
            for idx, tip in enumerate(tips_id):
                ghost_adj_matrix[idx + len_cus, tip] = 1
                ghost_adj_matrix[tip, idx + len_cus] = 1

            identity = topo_identity(topodist_matrix(ghost_adj_matrix))

            self.identity = identity
        return self.identity

    @property
    def thickness(self):
        if self._thickness is None:
            posz = self.atoms.positions[:, 2]
            self._thickness = posz.max() - posz.min()
        return self._thickness

    def dauc(self, parameters=None):
        """
        DAUC means degree of atomic under-coordinate. Use original bond valence
        instead of generalized atomic valence in Ma Huan and Guo Wenping's work.

        TODO: Add option of gav and bv.

        :return:
        """
        surface_bv = bondvalence(self.atoms, index=self.atoms_cus_id, parameters=parameters)
        bulk_cus_id = [i if i in self.bulk_id else i + self.natoms_per_layer for i in self.cus_id]
        bulk_bv = bondvalence(self.slab.atoms, index=bulk_cus_id, parameters=parameters)
        result = [(j - i) / j for i, j in zip(surface_bv, bulk_bv)]
        # result = 1 - np.array(surface_bv)/np.array(reordered_bulk_bv)
        return result

    def get_dsuc(self, parameters=None):
        """
        DSUC means Degree of Surface Under-Coordinate.

        :return:
        """
        if self.dsuc is None:
            d = self.dauc(parameters=parameters)
            self.dsuc = np.square(d).sum() / self.surface.area * 100  # unit per nm**2

        return self.dsuc


def get_symmetry_miller(crystal, hkl):
    """
    Get primary miller indices and the peer indices according to the crystal space group.
    """

    cell = atoms2spg(crystal)
    rotations = spglib.get_symmetry(cell)['rotations']
    peer_hkl = np.matmul(hkl, rotations)
    peer_hkl = list(set(map(tuple, peer_hkl)))
    peer_hkl = sorted(peer_hkl, reverse=True)
    primary_hkl = peer_hkl[0]

    return primary_hkl, peer_hkl


def reduce_miller_indices(hkl):
    """
    Refine an arbitrary miller indices to common indices
    :param hkl: tuple, (h,k,l)
    :return: tuple, common indices
    """
    sign = np.sign(hkl).tolist()  # get the signs
    # choose the one with less negative value
    new_sign = [-1 * i for i in sign]
    if sign.count(-1) > new_sign.count(-1):
        sign = new_sign
    # choose the one with positive in the front
    elif sign.count(-1) == new_sign.count(-1):
        if sign.index(-1) < new_sign.index(-1):
            sign = new_sign

    hkl = np.abs(hkl)
    factor = coprime_factor(hkl)
    idx = list(map(int, np.divide(hkl, factor)))
    idx = tuple(np.array(idx) * sign)
    return idx


def get_terminations_score(terminations, cus=True):
    """

    :param terminations:
    :param cus: Whether calculate cus or not.
    :return:
    """

    if cus:
        cuses = []
        termination_ids = []
        for i, t in tqdm(enumerate(terminations)):
            cus = t.get_cus_cn()
            # idata = pd.DataFrame(cus, index=[len(data) + idx for idx in range(len(cus))])
            termination_ids += [i] * len(cus)
            cuses += t.get_cus_cn()
            # data = pd.concat([data, idata])
        data = pd.DataFrame(cuses)
        data['termination'] = termination_ids
        data_by_termination = data.groupby(by='termination')
        data_sum_by_termination = data_by_termination.sum()
    else:
        data_sum_by_termination = pd.DataFrame()
    dsuc_list = [round(t.dsuc(), 2) for t in tqdm(terminations)]
    data_sum_by_termination['DSUC'] = dsuc_list
    return data_sum_by_termination


def all_surface_parameters(crystal, cellmax=20, max_hkl=(3, 3, 3)):
    """
    Extract all the surface parameters for given crystal. 数据用于 seaborn 作图
    :param crystal: Crytal object
    :param cellmax: the maximum of cell length when multiple the unit cell
    :param max_hkl: tuple or int, (hmax,kmax,lmax)
    :return:
    """
    surf_parameters = {}
    crystal.max_hkl = max_hkl

    for hkl in crystal.primary_hkl:
        surface = crystal.create_surface(hkl)
        latt = {surface.surface_parameter}
        surface.refine = True  # 包含 refine 的结果
        latt.update({surface.surface_parameter})
        # 包含交换a、b的结果
        latt.update({[sp[1], sp[0], sp[-1]] for sp in latt})

        for ilatt in latt:
            # mutiple the cell until cellmax
            na = range(1, int(cellmax / ilatt[0]) + 1)
            nb = range(1, int(cellmax / ilatt[1]) + 1)
            angle = [ilatt[2]]
            if np.abs(ilatt[2] - 90) > 0.1:  # add supplementary angles
                angle = [ilatt[2], 180 - ilatt[2]]
            com = list(itertools.product(na, nb, angle))
            sp_set = {(crystal.name, hkl, ilatt[0] * a, ilatt[1] * b, theta)
                      for a, b, theta in com}
            # 交换 ilatt[1] * b, ilatt[0] * a
            sp_set.update({(crystal.name, hkl, ilatt[1] * b, ilatt[0] * a, theta)
                           for a, b, theta in com})

            surf_parameters.update(sp_set)

    return surf_parameters
