# adopt from stm_sim.atoms
from typing import Dict, List

import ase
import ase.data
from ase.geometry import get_distances
from ase.data import covalent_radii
import networkx as nx
import numpy as np
import itertools
from hashlib import md5
import spglib
from .pymsym_wrapper import get_Cn


def default_bv_parameter(atomnums=None):
    # 使用共价键长之和来生成
    radii = ase.data.covalent_radii.copy()
    if atomnums is None:
        atomnums = range(len(radii))

    combinations = list(itertools.combinations(atomnums, 2))
    combinations += [(i, i) for i in atomnums]
    bv_parameter = {(i, j): (radii[i]+radii[j], 0.37) for i, j in combinations}
    return bv_parameter


def round10(x):
    return round(x, 10)


def dpair(A=None, symbols=None, radii='covalent', radii_dict=None, scale=1.2):
    if radii_dict is None:
        radii_dict = dict()
    D = {}
    if A is not None:
        atom_number_set = set(A.get_atomic_numbers())
    elif symbols is not None:
        atom_number_set = set([ase.data.atomic_numbers[i] for i in symbols])
    else:
        atom_number_set = set(ase.data.atomic_numbers.values())
    pair_list = itertools.product(atom_number_set, atom_number_set)
    if radii == 'covalent':
        R = ase.data.covalent_radii.copy()
        R[0] = 0.54  # use new ghost radii
        for ip in pair_list:
            D[ip] = (R[ip[0]] + R[ip[1]]) * scale
    elif radii == 'vdw':
        R = ase.data.vdw_radii.copy()
        R[np.isnan(R)] = 1.8
        for ip in pair_list:
            D[ip] = (R[ip[0]] + R[ip[1]]) * scale
    elif radii == 'custom':
        for ip in pair_list:
            s0 = ase.data.chemical_symbols[ip[0]]
            s1 = ase.data.chemical_symbols[ip[1]]
            # with atomic_number as key
            if ip in radii_dict:
                D[ip] = radii_dict[ip]
            elif (ip[0], ip[1]) in radii_dict:
                D[ip] = radii_dict[(ip[0], ip[1])]
            elif (ip[1], ip[0]) in radii_dict:
                D[ip] = radii_dict[(ip[1], ip[0])]
            elif ip[0] in radii_dict and ip[1] in radii_dict:
                D[ip] = radii_dict[ip[0]] + radii_dict[ip[1]]
            # with atomic_symbol as key
            elif (s0, s1) in radii_dict:
                D[ip] = radii_dict[(s0, s1)]
            elif (s1, s0) in radii_dict:
                D[ip] = radii_dict[(s1, s0)]
            elif s0 in radii_dict and s1 in radii_dict:
                D[ip] = radii_dict[s0] + radii_dict[s1]
            else:
                print("KeyError: " + str(radii_dict) + ' has no key ' + str(ip))
    else:
        print("Error: Unknown radii option: " + radii)
        return False

    return D


def bondmax(atoms, radii='covalent', scale=1.2):
    Natoms = len(atoms)
    D = dpair(atoms, radii=radii, scale=scale)
    atomic_numbers = atoms.get_atomic_numbers()
    atom_pair = itertools.product(atomic_numbers, atomic_numbers)
    bmax = []
    for ip in atom_pair:
        try:
            bmax.append(D[ip])
        except Exception as inst:
            print(type(inst).__name__ + ' : ' + ', '.join(inst.args))
    bmax = np.array(bmax).reshape(Natoms, Natoms)
    return bmax


def adj_matrix(atoms, scale=1.2, mic=None, radii='covalent', diagonal=True):
    """
    radii can be covalent,vdw or a dict. If radii is a dict, its key can be a string (atom symbol)
        and a tuple of two strings (atom symbols). diagonal 如果是 true，则填充为原子序数
    """
    atomic_numbers = atoms.get_atomic_numbers()
    if len(atoms) == 1:
        if diagonal:
            return np.ndarray(shape=(1,), buffer=atomic_numbers, dtype=int)
        else:
            return np.ndarray(shape=(1,), buffer=[0], dtype=int)

    if mic is None:
        if any(atoms.pbc):
            mic = True
        else:
            mic = False

    bmax = bondmax(atoms, radii=radii, scale=scale)
    distances = atoms.get_all_distances(mic=mic)
    adj = distances - np.array(bmax)
    n, m = adj.shape
    assert n == m
    I = np.identity(n)
    adj[adj > 0] = 0
    adj[adj < 0] = 1
    adj[I == 1] = 0
    # correction for X: coordination should be one
    for ix in getghost(atoms):
        if np.sum(adj[ix]) != 1:
            # get the shortest bond
            ixd = distances[ix]
            ixd_nonzero = ixd[np.nonzero(ixd)]
            ixd_min = np.min(ixd_nonzero)
            # set X column and row
            adj[:, ix] = 0
            adj[ix, :] = 0
            adj[ixd == ixd_min, ix] = 1
            adj[ix, ixd == ixd_min] = 1
    if diagonal:
        adj = adj + atomic_numbers * I  # set diagonal elements as atomic number
    return np.array(adj, dtype=int)


def topodist_matrix(A):
    """
    Topological distance matrix from adjacent matrix.
    Adopted from mathchem.distance_matrix.

    :param A: adjacent matrix from adj_matrix()
    :return:
    """
    n = len(A)
    if n == 1:
        return A
    atomic_numbers = A.diagonal()
    I = np.identity(n)
    A = np.array(A, dtype=float)  # use here float only for using np.inf - infinity
    n, m = A.shape
    assert n == m
    A[A == 0] = np.inf
    A[I == 1] = 0  # set diagonal elements as 0
    for i in range(n):
        r = np.array([A[i, :]])  # must convert to row vector
        A = np.minimum(A, r + r.T)
    A = A + atomic_numbers * I  # set diagonal elements as atomic number

    return np.array(A, dtype=int)


def topodist_eigen(dm):
    """
    If consider chirality of molecules, need add three non-colinear
    points of cartesian coordinates.
    dm is the topodist_matrix.
    """

    eigval = np.linalg.eigvalsh(dm)
    eigval = tuple(sorted(map(round10, eigval)))
    return eigval


def get_sub_matrix(mat, lst):
    if len(mat) == 1:
        if len(lst) == 1:
            return mat
        else:
            return []
    if len(lst) == 0:
        return []

    row_idx, col_idx = np.asarray(list(itertools.product(lst, lst)), dtype=int).T
    dim = len(lst)
    sub_mat = mat[row_idx, col_idx].reshape((dim, dim))
    return sub_mat


def topo_identity(dm):
    """
    计算 topo 结构的标识。
    If consider chirality of molecules, need add three non-collinear
    points of cartesian coordinates. 通过主轴和二轴添加
    :param dm: topodist_matrix
    :return:
    """
    if len(dm) == 1:
        eigval = dm
    elif len(dm) == 0:
        eigval = []
    else:
        eigval = np.linalg.eigvalsh(dm).round(10)
    content = ' '.join(map(str, np.sort(eigval)))
    identity = md5(content.encode('utf-8')).hexdigest()

    return identity


def get_atoms_topo_id(atoms, *args, **kwargs):
    A = adj_matrix(atoms, *args)
    dm = topodist_matrix(A)
    ids = topo_identity(dm)
    return ids


def dist_identity(atoms, mic=True):
    dm = atoms.get_all_distances(mic=mic)
    n, m = dm.shape
    I = np.identity(n)
    dm = dm + atoms.get_atomic_numbers() * I  # set diagonal elements as atomic number
    eigval = np.linalg.eigvalsh(dm).round(5)
    content = ' '.join(map(str, np.sort(eigval)))
    identity = md5(content.encode('utf-8')).hexdigest()

    return identity


def getghost(atoms):
    # get X index
    x = [idx for idx, i in enumerate(atoms.get_chemical_symbols()) if i == 'X']
    return x


def coordnum(A, scale=1.2):
    G = atoms2graph(A, scale=scale)
    atomsnum_set = set(A.numbers)
    atomsnum_combinations = itertools.product(atomsnum_set, atomsnum_set)
    cn_list = []
    cn_dict = dict([(i, 0) for i in atomsnum_combinations])
    for node in G:
        icn_dict = cn_dict.copy()
        inum = G.nodes[node]['atom'].number
        neighbors = nx.neighbors(G, node)
        for neighbor in neighbors:
            jnum = G.nodes[neighbor]['atom'].number
            icn_dict[(inum, jnum)] += 1
            if not inum == jnum:
                icn_dict[(jnum, inum)] += 1
        cn_list.append(icn_dict)

    return cn_list


def coordnum_adj(adj):
    if len(adj) == 1:
        if len(adj.shape) == 1:
            atom_num = adj[0]
        else:
            atom_num = adj[0][0]
        return [{(atom_num, atom_num): 0}]

    atomic_numbers = adj.diagonal()
    atomic_numbers_set = set(atomic_numbers)
    atomic_numbers_com = list(itertools.product(atomic_numbers_set, atomic_numbers_set))
    cn_dict_template = dict([(i, 0) for i in atomic_numbers_com])

    n = len(atomic_numbers)
    I = np.identity(n)
    adj_copy = adj.copy()
    adj_copy[I == 1] = 0  # set diagonal elements as 0
    AN_mat = np.zeros((n, n)) + atomic_numbers  # 原子序数矩阵
    adj_AN = AN_mat * adj_copy
    # 对每一行统计
    cn_list = []
    for row, atom_num in zip(adj_AN, atomic_numbers):
        cn_dict = cn_dict_template.copy()
        cn_dict.update({com: np.count_nonzero(row == (set(com)-{atom_num} or {atom_num}).pop())
                        for com in atomic_numbers_com if atom_num in com})

        #for j in atomic_numbers_set:
        #    count = np.count_nonzero(row == j)
        #    cn_dict[(atom_num, j)] = count
        #    if not atom_num == j:
        #        cn_dict[(j, atom_num)] = count

        cn_list.append(cn_dict)

    return cn_list


def atoms2graph(A, adj=None, scale=1.2, mic=True, radii='covalent'):
    """
    Convert ase.Atoms to networkx.Graph
    """
    G = nx.Graph(pbc=A.pbc, cell=A.cell)
    for idx, a in enumerate(A):
        G.add_node(idx, atom=a)
    if adj is None:
        adj = adj_matrix(A, scale=scale, mic=mic, radii=radii)
    bonds = bondlist(topodist_matrix(adj))
    G.add_edges_from(bonds)
    return G


def bondlist(dm, idx=None):
    """"
    Get bonds for given idx atoms.
    Return all bonds by default.
    """
    if len(dm) == 1:
        return []
    b = np.where(dm == 1)
    allbonds = np.array(b).T[(b[0] - b[1]) > 0]
    idx_set = set()
    if type(idx) in (int,):
        idx_set = {idx}
    elif type(idx) in (list, tuple):
        idx_set = set(idx)
    elif idx is None:
        return allbonds

    bonds = [bond.tolist() for bond in allbonds if set(bond).intersection(idx_set)]

    return bonds


def bondvalence(A, index=None, cutoff=None, only_neighbor=True, parameters=None):
    if type(index) in (int,):
        index = [index]
    if not index:
        index = range(len(A))

    if not cutoff:
        cutoff = 0.5 * A.cell.min()

    if not parameters:
        parameters = default_bv_parameter(set(A.get_atomic_numbers()))
        print("Bond valence parameters didn't defined, use default setting now.")

    vlist = []
    dist_matrix = A.get_all_distances(mic=True)
    if only_neighbor:
        G = atoms2graph(A, mic=True, scale=1.2)
        for idx in index:
            inum = G.nodes[idx]['atom'].number
            neighbors = list(G.neighbors(idx))
            distances = dist_matrix[idx, neighbors]
            vi = 0
            for jdx, neighbor in enumerate(neighbors):
                jnum = G.nodes[neighbor]['atom'].number
                rij = distances[jdx]
                if (inum, jnum) in parameters:
                    r0, b = parameters[(inum, jnum)]
                elif (jnum, inum) in parameters:
                    r0, b = parameters[(jnum, inum)]
                else:
                    print("Bond valence parameters aren't well defined: " + str((inum, jnum)))
                    return None

                vij = np.exp((r0 - rij) / b)
                vi += vij
            vlist.append(vi)
    else:
        print('Not implemented right now.')
        return None

    return vlist


def bond_distribution(A):
    """
    Bond Length distribution.
    :param A:
    :return:
    """
    result = {}
    G = atoms2graph(A, mic=True, scale=1.2)
    for idx in G.nodes():
        inum = G.nodes[idx]['atom'].number
        neighbors = list(G.neighbors(idx))
        distances = A.get_distances(idx, neighbors, mic=True)
        for jdx, neighbor in enumerate(neighbors):
            jnum = G.nodes[neighbor]['atom'].number
            rij = distances[jdx]
            if (inum, jnum) not in result:
                result[(inum, jnum)] = []
            result[(inum, jnum)].append(rij)
    return result


def cn_distribution(A):
    """
    Coordinate Number distribution.
    :param A:
    :return:
    """
    result = []
    G = atoms2graph(A, mic=True, scale=1.2)
    for idx in G.nodes():
        cn_dict = {}
        inum = G.nodes[idx]['atom'].number
        neighbors = list(G.neighbors(idx))
        for neighbor in neighbors:
            jnum = G.nodes[neighbor]['atom'].number
            if (inum, jnum) not in cn_dict:
                cn_dict[(inum, jnum)] = 0
            cn_dict[(inum, jnum)] += 1
        result.append(cn_dict)
    return result


def gav(A, index=None):
    if not index:
        index = range(len(A))
    # get all bondvalence
    bv = bondvalence(A)

    numbers_list = A.numbers
    numbers_set = set(numbers_list)
    vmax_dict = {}
    for number in numbers_set:
        vmax_dict[number] = max([v for num, v in zip(numbers_list, bv) if num == number])
    vmax_list = [vmax_dict[num] for num in numbers_list]

    G = atoms2graph(A)
    gav_list = []
    for idx in index:
        neighbors = list(G.neighbors(idx))
        vi = sum([bv[neighbor] / vmax_list[neighbor] for neighbor in neighbors])
        gav_list.append(vi)

    return gav_list


def atoms2spg(atoms):
    """
    Convert ASE Atoms object to spglib input cell format
    :param atoms: ASE Atoms object
    :return: spglib input cell format
    """
    lattice = np.array(atoms.get_cell().T, dtype='double', order='C')
    positions = np.array(atoms.get_scaled_positions(), dtype='double', order='C')
    numbers = np.array(atoms.get_atomic_numbers(), dtype='intc')
    return lattice, positions, numbers


def spg2atoms(cell):
    """
    Convert spglib input cell format to ASE Atoms object.
    :param cell: spglib input cell
    :return: ASE Atoms
    """
    atoms = ase.Atoms(cell=cell[0].T, scaled_positions=cell[1], numbers=cell[2], pbc=True)
    return atoms


def __gcd(a, b):
    """
    Get the co-prime factor of two positive integer
    """
    # Everything divides 0
    if a == 0 or b == 0:
        return 0

    # base case
    if a == b:
        return a

    # a is greater
    if a > b:
        return __gcd(a - b, b)

    return __gcd(a, b - a)


def coprime_factor(lst):
    """
    Get the co-prime factor of a list
    :param lst: list
    :return: int, co-prime factor
    """

    # remove duplicate
    lst = list(set(lst))
    # remove all zero
    lst = [i for i in lst if i != 0]
    if len(lst) == 0:
        return 1
    if len(lst) == 1:
        return lst[0]
    if len(lst) == 2:
        return __gcd(lst[0], lst[1])

    factor = []
    for a, b in itertools.combinations(lst, 2):
        factor.append(__gcd(a, b))

    if 1 in factor:
        return 1

    return coprime_factor(factor)


def refined_atoms(atoms):
    """
    Refine the crystal to minimal unit cell.
    :param atoms: ASE Atoms
    :return: ASE Atoms, minimal unit cell
    """
    cell = atoms2spg(atoms)
    pcell = spglib.find_primitive(cell)
    if pcell is None:
        pcell = spglib.refine_cell(cell)

    return spg2atoms(pcell)


def check_structure(surf, ads_atoms, criteria=0.8):
    """
    检查吸附结构是否存在键长过短的情况。
    """
    dist = get_distances(ads_atoms.positions, surf.positions, cell=surf.cell, pbc=surf.pbc)[1]
    ads_radii = np.array([[covalent_radii[i]] for i in ads_atoms.numbers])
    surf_radii = np.array([covalent_radii[i] for i in surf.numbers])
    common_dist = ads_radii + surf_radii
    ratio = dist / common_dist
    ratio_min = ratio.min()

    if ratio_min < criteria:
        ratio_argmin = ratio.argmin()
        ads_idx_mesh, surf_idx_mesh = np.meshgrid(range(len(ads_atoms)), range(len(surf_radii)))
        ratio_min_idx = (ads_idx_mesh.flat[ratio_argmin], surf_idx_mesh.flat[ratio_argmin])
        print("Warning: Atoms conflict between surface({}) and adsorbate({})! Check the structure!".format(
            ratio_min_idx[1], ratio_min_idx[0]
        ))
        print("         Their distance between them is {:.3f}, which is smaller than criteria {:.3f}".format(
            dist[ratio_min_idx[0], ratio_min_idx[1]],
            common_dist[ratio_min_idx[0], ratio_min_idx[1]] * criteria
        ))
        return False
    else:
        return True


def angle_wrap(a):
    """
    把角度折叠到 (-pi, pi] 的范围
    :param a:
    :return:
    """
    while True:
        if a > np.pi:
            a -= 2 * np.pi
        elif a <= -np.pi:
            a += 2 * np.pi
        else:
            break
    return a

def sort_pos(pos:np.ndarray) -> np.ndarray:
    npos = len(pos)
    indices = np.arange(npos)

    # 使用结构化数组进行多键排序
    # 创建一个结构化数组，包含x, y, z坐标
    dtype = [('x', float), ('y', float), ('z', float), ('index', int)]
    structured_array = np.zeros(npos, dtype=dtype)

    structured_array['x'] = pos[:, 0]
    structured_array['y'] = pos[:, 1]
    structured_array['z'] = pos[:, 2]
    structured_array['index'] = indices

    # 按照x, y, z的顺序排序
    sorted_struct = np.sort(structured_array, order=['x', 'y', 'z'])
    # 获取排序后的索引
    return sorted_struct['index']

def atoms_regulate(atoms:ase.Atoms, target_atoms:ase.Atoms=None) -> None:
    """
    将分子旋转对齐到 x、y、z。
    第一原则是旋转主轴 z轴
    如果没有旋转轴，或者有两个垂直的C2轴，默认是 第一主轴 x，第二主轴 y。
    如果 target_atoms 不是 None，旋转使得距离最小
    target_atoms 要求是已经 regulated 过了。
    """
    # com to 0,0,0
    atoms.set_center_of_mass(com=(0.0, 0.0, 0.0))
    if target_atoms is not None:
        pos0 = target_atoms.positions[sort_pos(target_atoms.positions)]
        dlist = []
        axes = list(zip(['x', '-x', 'x', '-x'], ['y', 'y', '-y', '-y']))
        atoms_list = []
        for x, y in axes:
            align_atoms(atoms, x, y)
            pos1 = atoms.positions[sort_pos(atoms.positions)]
            dlist.append(np.linalg.norm(pos1-pos0))
            atoms_list.append(atoms.copy())
        argmin = np.argmin(dlist)
        return atoms_list[argmin]
    else:
        align_atoms(atoms)
        return atoms.copy()

def align_atoms(atoms:ase.Atoms, xaxis='x', yaxis='y'):
    """
    From ase.geometry.distance.
    第一原则是旋转主轴 z轴
    如果没有旋转轴，或者有两个垂直的C2轴，默认是 第一主轴 x，第二主轴 y。
    """
    Is, Vs = atoms.get_moments_of_inertia(True)
    IV = list(zip(Is, Vs))
    IV.sort(key=lambda x: x[0])
    atoms.rotate(IV[0][1], xaxis)

    Is, Vs = atoms.get_moments_of_inertia(True)
    IV = list(zip(Is, Vs))
    IV.sort(key=lambda x: x[0])
    atoms.rotate(IV[1][1], yaxis)

    Cn_dict = get_Cn(atoms)
    if len(Cn_dict) > 0:
        main_axis_order = sorted(Cn_dict.items(), key=lambda x: x[1], reverse=True)[0]
        main_axis = main_axis_order[0]
        order = main_axis_order[1]
        if order == 2:
            if np.any([np.allclose(i,[0,0,1]) for i in Cn_dict.keys()]):
                return None
        else:
            if np.allclose(main_axis, [0,0,1]):
                return None
        atoms.rotate(main_axis, 'z')
    return None

def set_dihedrals(atoms: ase.Atoms,
                  dihedrals: dict) -> ase.Atoms:
    """
    设置多个二面角，不改变原来的结构
    :param atoms: ase.Atoms
    :param dihedrals:
    :return: new_atoms: ase.Atoms
    """
    new_atoms = atoms.copy()
    for d in dihedrals:
        new_atoms.set_dihedral(*d, angle=dihedrals[d]['value'], indices=dihedrals[d].get('mask'))
    return new_atoms