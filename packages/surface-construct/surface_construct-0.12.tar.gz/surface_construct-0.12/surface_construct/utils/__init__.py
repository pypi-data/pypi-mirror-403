import itertools

import ase
import ase.geometry
import networkx as nx
import numpy as np
from scipy.spatial import ConvexHull, cKDTree
from skimage.measure import marching_cubes
from scipy.special import comb


MIN_HULL_ANGLE_COS = np.cos(np.pi * 30 / 180)

def hull_vertices(hull):
    hsimplices = hull.simplices
    hvertices = hull.vertices
    hnorms = hull.equations[:,0:-1]
    ndim = hsimplices.shape[1]
    vertices = []
    # 去掉 hull 的 simplices 的角度较大的点
    for i in hvertices:
        p0_facets_idx = np.argwhere(hsimplices == i)[:,0]
        p0_norms = hnorms[p0_facets_idx]
        cosangle = lambda a,b: a.dot(b) / (np.linalg.norm(a) * np.linalg.norm(b))
        # 求 i 凸点相邻的超平面的法向向量之间的夹角。如果存在夹角小于30度，即平面之间的夹角大于150度，则排除该点。反之，保留该点。
        norm_angle_cos = np.absolute([cosangle(a,b) for a,b in itertools.combinations(p0_norms, 2)])
        if np.sum(norm_angle_cos < MIN_HULL_ANGLE_COS) >= comb(ndim,2):
            vertices.append(i)

    return vertices


def calc_hull_vertices(v):
    shape = v.shape
    if len(shape) != 2:
        print(f"Warning: The vector should be 2D, however {len(shape)}D vector was provided!)")
        print("The Convex Hull Vertices won't be calculated.")
        return None
    if shape[1] > 5:
        print(f"Warning: The vector.shape[1]={shape[1]} is too large to be calculated!)")
        print("The Convex Hull Vertices won't be calculated.")
        return None
    try:
        print("Calculate Convex Hull Vertices ...")
        hull = ConvexHull(v)
        vertices = hull.vertices
        return vertices
    except ValueError:
        return None


def get_calc_info(calc=None):
    if calc is None:
        return {}
    calc_name = calc.name
    calc_para = dict()
    if calc_name in ('vasp',):
        calc_para['xc'] = calc.parameters['xc']
        calc_para['encut'] = calc.parameters['encut']

    calc_info = {
        'name': calc_name,
        'para': calc_para,
    }
    return calc_info


def extended_points(points, ncell, cell):
    ranges = [np.arange(-1 * p, p + 1) for p in ncell]
    hkls = np.array(list(itertools.product(*ranges)))
    hkls = np.concatenate([hkls, np.zeros([hkls.shape[0], 3-hkls.shape[1]], dtype=int)], axis=1)
    vrvecs = hkls @ cell
    super_points = np.concatenate(points + vrvecs[:, None], axis=0)
    return super_points

def extended_points_in_xy(points:np.ndarray, nx:int, ny:int, cell:np.ndarray):
    if nx==1 and ny==1:
        return points
    hkls = np.array([[ix,iy,0] for ix in range(nx) for iy in range(ny)])
    vrvecs = hkls @ cell
    super_points = np.concatenate(points + vrvecs[:, None], axis=0)
    return super_points


def get_distances(p1, p2=None, cutoff=10.0, cell=None, ncell=None, pbc=None, use_ase=False):
    """
    计算位点周围原子的距离，参考 ase.geometry.get_distances. 对于更大的体系使用 cDTree 来计算。
    :param pbc:
    :param p1: grid positions
    :param p2: atoms.positions
    :param cutoff: 截断半径，只考虑距离之内的距离，超过该距离的定为 np.inf
    :param cell:
    :param ncell: [nx, ny, nz]
    :param use_ase: 如果 use_ase is True，则使用 ase.geometry.get_distances，即周期性条件等价的原子只考虑一次
    :return:
    """
    if not use_ase:
        if ncell is None:
            ncell = [max([i,1]) for i in np.floor((cutoff * 2) / cell.lengths())]  # 至少拓展+1,-1, 保证边缘周期性
        for ip,p in enumerate(pbc):
            if not p:  # 如果不是周期性的，则不要重复
                ncell[ip] = 0
        if np.all(ncell==1):
            use_ase = True

    if use_ase:
        return ase.geometry.get_distances(p1, p2, cell, pbc)

    if p2 is None:
        p2 = p1.copy()

    p2 = extended_points(p2, ncell, cell)
    tree1 = cKDTree(p1, copy_data=True)
    tree2 = cKDTree(p2, copy_data=True)
    sdm = tree1.sparse_distance_matrix(tree2, max_distance=cutoff)
    dist = sdm.toarray()
    # set distance larger than cutoff to np.inf
    mask = dist==0
    dist[mask] = np.inf
    return None, dist


def iso_surface(grids, dist_array, level=0):
    verts, faces, normals, values = marching_cubes(dist_array, level=level, allow_degenerate=False)
    grid_x, grid_y, grid_z = grids
    verts = np.asarray(verts, dtype=int)
    unique_verts = np.unique(verts, axis=0)  # exclude some repeat points
    points = np.asarray([grid_x[unique_verts[:, 0], unique_verts[:, 1], unique_verts[:, 2]],
                         grid_y[unique_verts[:, 0], unique_verts[:, 1], unique_verts[:, 2]],
                         grid_z[unique_verts[:, 0], unique_verts[:, 1], unique_verts[:, 2]]]).T

    return points, faces, normals


def rattle(positions, stdev=0.001, rng=None, seed=None):
    """Rattle the grid to make the vector distribution more smooth.
    Adapt from ase.Atoms.rattle
    """
    if seed is not None and rng is not None:
        raise ValueError('Please do not provide both seed and rng.')
    if rng is None:
        if seed is None:
            seed = 42
        rng = np.random.RandomState(seed)
    return positions + rng.normal(scale=stdev, size=positions.shape)


def furthest_sites(points, n):
    # return the n sites that covers the max volume
    assert n < len(points)
    combs = list(itertools.combinations(range(len(points)), n))
    volumes = []
    if n==2:
        for c in combs:
            volumes.append(np.linalg.norm(points[c[0]] - points[c[1]]))
    elif n>2:
        for c in combs:
            pp = [points[i] for i in c]
            volumes.append(ConvexHull(pp).volume)
    idx = combs[np.argmax(volumes)]
    return idx


def get_graph_core(G, gmin=1):
    Gsub = G.copy()
    old_G = Gsub.copy()
    while Gsub.order() >= gmin and nx.is_connected(Gsub):
        old_G = Gsub.copy()
        degree = np.array(old_G.degree())
        max_degree = np.max(degree[:,1])
        min_degree = np.min(degree[:,1])
        avg_degree = (max_degree+min_degree)/2
        core_nodes = (degree[:,0])[np.argwhere(degree[:,1] > avg_degree)].flatten()
        Gsub = old_G.subgraph(core_nodes)

    return old_G

def wrap_grid(pos, cell):
    if len(pos) == 1:
        return pos
    p0 = pos[0]
    wrapped_pos = pos[:]
    for idx, p in enumerate(pos[1:]):
        v = p - p0
        wp, _ = ase.geometry.find_mic(v,cell)
        wrapped_pos[idx+1] = p0 + wp
    return wrapped_pos

def filter_index_label(index_label, index_dict):
    # 根据规则需要合并位点类型
    # 规则一：同时包含三配位和四配位（或者更高配位），只保留最高的配位类型
    reverse_dict = {v:k for k,v in index_dict.items()}
    new_index_label = np.array(index_label)
    new_index_dict = index_dict.copy()
    for k,v in index_dict.items():
        if len(v) > 3:
            for n in range(3,len(v)):
                for comb in itertools.combinations(v, n):
                    if comb in reverse_dict:
                        old_idx = reverse_dict[comb]
                        if old_idx in new_index_label:
                            new_index_label[new_index_label==old_idx] = k
                            del new_index_dict[old_idx]
    return new_index_label.tolist(), new_index_dict