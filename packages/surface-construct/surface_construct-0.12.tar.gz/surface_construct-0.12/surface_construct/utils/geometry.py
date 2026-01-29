import itertools
import re

import numpy as np
from typing import Sequence
from scipy.spatial.transform import Rotation
from scipy.stats import qmc

def rotation_distance(r1:Rotation, r2:Rotation) -> np.ndarray:
    """最高效的旋转距离计算"""
    # 计算相对旋转
    r_rel = r2 * r1.inv()
    # 转换为旋转向量并计算范数（最快）
    rotvec = r_rel.as_rotvec()
    if rotvec.ndim == 1:
        return np.array([np.linalg.norm(rotvec)]) / 2.0
    else:
        return np.linalg.norm(rotvec, axis=1) /2.0

# === Dihedrals ========================================================================

def dih_grid(ndih:int, nangle:int, uniform=False) -> np.ndarray:
    """
    生成二面角格点。
    """
    if uniform:
        dih_arrays = [np.arange(0, 360, nangle) for i in range(ndih)]
        grid = np.array(list(itertools.product(*dih_arrays)))
    else:
        if ndih == 0:
            grid = np.asarray([])
        elif ndih == 1:
            grid = golden_ratio_sampling(nangle)
        elif ndih == 2:
            grid = fibonacci_sampling(nangle)
        elif ndih <= 20:
            grid = sobol_sampling(ndih, nangle)
        else:
            grid = lhs_sampling(ndih, nangle)
        grid = grid * 180 / np.pi
    return grid

def golden_ratio_sampling(n:int) -> np.ndarray:
    """
    1个二面角,黄金比例采样：数学证明的最优分布
    :param n:
    :return:
    """
    phi = (np.sqrt(5) - 1) / 2  # 黄金比例
    return np.array([(i * phi) % 1 for i in range(n)]) * 2 * np.pi

def fibonacci_sampling(n:int) -> np.ndarray:
    """
    2个二面角, Fibonacci螺旋：球面上的最优分布
    :param n:
    :return:
    """
    indices = np.arange(n)
    phi = np.pi * (3 - np.sqrt(5))  # 黄金角度
    y = 1 - (indices / (n - 1)) * 2
    radius = np.sqrt(1 - y**2)
    theta = phi * indices
    x = (np.cos(theta) * radius + 1) * np.pi
    y = (y + 1) * np.pi
    return np.vstack([x, y]).T

def halton_sampling_2d(n:int) -> np.ndarray:
    """
    2个二面角, Halton序列：低维表现优秀
    :param n:
    :return:
    """
    sampler = qmc.Halton(d=2, scramble=True)
    return sampler.random(n) * 2 * np.pi

def sobol_sampling(dim:int, n_samples:int) -> np.ndarray:
    """三个二面角以上,20个以下，Sobol序列采样"""
    sampler = qmc.Sobol(d=dim, scramble=True)
    return sampler.random(n_samples) * 2 * np.pi

def lhs_sampling(dim:int, n_samples:int) -> np.ndarray:
    """20个二面角以上,拉丁超立方体采样"""
    sampler = qmc.LatinHypercube(d=dim)
    return sampler.random(n_samples) * 2 * np.pi

# === Rotations ================================================================================

def estimate_rotation_samples(theta_avg_deg:float, point_group:str='C1', method:str="halton") -> int:
    """
    Estimate number of samples for molecule rotation space (SO(3)).

    Parameters:
        theta_avg_deg (float): desired average nearest-neighbor angle in degrees
        point_group:
        method (str): "optimal", "cvt", "halton", "random", "max_gap"

    Returns:
        int: recommended number of samples
    """
    if not (0 < theta_avg_deg <= 180):
        raise ValueError("theta_avg_deg must be in (0, 180]")

    theta = np.radians(theta_avg_deg)
    if 'Cinf' in point_group:  # whether it is a linear molecule
        N = int(4.0 / (theta**2))
    elif 'Dinf' in point_group:
        N = int(2.0 / (theta**2))
    elif 'Td' in point_group or 'Oh' in point_group: # TODO: 球形分子单独处理
        return 2
    else:
        constants = {
            "optimal": 2.0,
            "cvt": 18.0,
            "halton": 20.0,
            "random": 25.0,
            "max_gap": 100.0
        }
        if method not in constants:
            raise ValueError(f"method must be one of {list(constants.keys())}")
        match = re.search(r'[1-9]', point_group)
        nrot = int(match.group())
        if 'D' in point_group:
            nrot = nrot * 2
        N = constants[method] / (theta ** 3) / nrot
    return max(int(np.ceil(N)),2)

def quat_mult(q1:Sequence, q2:Sequence)->Sequence:
    """Hamilton product: q = q1 * q2 (both [w, x, y, z])"""
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    return np.array([
        w1*w2 - x1*x2 - y1*y2 - z1*z2,
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2
    ])

def quat_conjugate(q:Sequence)->Sequence:
    """Return conjugate of unit quaternion"""
    w, x, y, z = q
    return np.array([w, -x, -y, -z])

def quat_norm(q:Sequence)->Sequence:
    return q / np.linalg.norm(q)

# ----------------------------
# 1. 生成 SO(3) 中的 Halton 样本（通过 Hopf fibration）
# ----------------------------

def halton_so3_hopf(n:int)->Sequence:
    """
    Generate n quasi-uniform samples in SO(3) using Halton + Hopf fibration.
    Returns: array of shape (n, 4) unit quaternions [w, x, y, z]
    """
    sampler = qmc.Halton(d=3, scramble=False)
    u = sampler.random(n)  # (n, 3), each in [0,1)

    quats = []
    for u1, u2, u3 in u:
        # Hopf coordinates
        alpha = np.arcsin(np.sqrt(u1))          # ∈ [0, π/2]
        beta  = 2 * np.pi * u2                  # ∈ [0, 2π)
        gamma = 2 * np.pi * u3                  # ∈ [0, 2π)

        w = np.cos(alpha) * np.cos(beta)
        x = np.cos(alpha) * np.sin(beta)
        y = np.sin(alpha) * np.cos(gamma)
        z = np.sin(alpha) * np.sin(gamma)
        q = np.array([w, x, y, z])
        q = quat_norm(q)  # numerical safety
        quats.append(q)
    return np.array(quats)

# ----------------------------
# 2. 商空间轨道距离
# ----------------------------

def orbit_distance(q1:Sequence, q2:Sequence, sym_quats:Sequence)->float:
    """
    Compute min_{h in G} angle between q1 and q2 * h
    Returns: angular distance in radians ∈ [0, π/2]
    """
    max_abs_dot = 0.0
    for h in sym_quats:
        q2h = quat_mult(q2, h)  # compose rotation: apply symmetry after q2
        dot = abs(np.dot(q1, q2h))  # |<q1, q2h>|, accounts for q ~ -q
        if dot > max_abs_dot:
            max_abs_dot = dot
    # Clamp to [-1, 1] for safety
    max_abs_dot = np.clip(max_abs_dot, 0.0, 1.0)
    return np.arccos(max_abs_dot)

def orbit_distance2(q1:Sequence, q2:Sequence, sym_quats:Sequence):
    r_symm = Rotation.from_quat(sym_quats, scalar_first=True)
    r1 = Rotation.from_quat(q1, scalar_first=True)
    dists = [rotation_distance(r1, ir2)
             for iq2 in q2
             for ir2 in Rotation.from_quat(iq2, scalar_first=True)*r_symm]
    return np.min(dists,axis=0)

def fibonacci_sphere(n_samples):
    """
    Generate n_samples points uniformly on the unit sphere S^2.
    Reference: Gonzalez (2010), "Measurement of areas on a sphere using Fibonacci and latitude–longitude lattices"
    """
    if n_samples <= 0:
        return np.empty((0, 3))

    indices = np.arange(0, n_samples, dtype=float) + 0.5
    phi = np.arccos(1 - 2 * indices / n_samples)  # polar angle ∈ [0, π]
    theta = np.pi * (1 + np.sqrt(5)) * indices  # golden angle spiral

    x = np.cos(theta) * np.sin(phi)
    y = np.sin(theta) * np.sin(phi)
    z = np.cos(phi)

    return np.stack([x, y, z], axis=1)


def canonical_antipodal(v):
    """
    Map vector v to canonical representative in RP^2:
    Choose sign so that:
      1. z > 0, OR
      2. z == 0 and x > 0, OR
      3. z == 0, x == 0 and y >= 0
    """
    v = v / np.linalg.norm(v)
    x, y, z = v

    if z < -1e-12:
        return -v
    elif abs(z) < 1e-12:
        if x < -1e-12:
            return -v
        elif abs(x) < 1e-12:
            if y < -1e-12:
                return -v
    return v

def point2quat(points, axis=np.array([0., 0., 1.])) -> np.ndarray:
    qlist = []
    for point in points:
        # 使用四元数方法更稳定
        v1 = axis  # 参考方向：默认z轴
        v2 = point / np.linalg.norm(point)

        if np.allclose(v1, v2) :
            q = np.array([0., 0., 0., 1.])
        elif np.allclose(v1, -v2):
            q = np.array([1., 0., 0., 0.])
        else:
            # 计算旋转四元数
            dot = np.dot(v1, v2)
            cross = np.cross(v1, v2)
            w = 1 + dot
            x, y, z = cross
            q = np.array([x, y, z, w])
        qlist.append(q / np.linalg.norm(q))
    return np.asarray(qlist)

def sample_linear_mol(n_samples, homonuclear:bool=False) -> np.ndarray:
    if n_samples <= 1:
        return np.array([[1.0, 0.0, 0.0, 0.0]])
    if homonuclear:
        n_directions = 0
        n_initial = max(int(n_samples * 2.2), 10)
        while n_directions < n_samples:
            full_sphere = fibonacci_sphere(n_initial)
            canonical_points = np.array([canonical_antipodal(v) for v in full_sphere])
            rounded = np.round(canonical_points, decimals=10)
            uniq = np.unique(rounded.view([('', rounded.dtype)] * 3)).view(rounded.dtype).reshape(-1, 3)
            directions = uniq[:n_samples]
            n_directions = len(directions)
            n_initial *= 2
    else:
        directions = fibonacci_sphere(n_samples)

    return point2quat(directions)

# ----------------------------
# 3. 最远点采样（FPS）在商空间 SO(3)/G
# ----------------------------

def sample_rotations_with_symmetry(avg_deg:float=45, point_group:str='C1',
                                   sym_quats:Sequence=np.array([[1.0, 0.0, 0.0, 0.0]]),
                                   pool_size_factor:int=10
                                   )->Sequence:
    """
    Sample n_samples rotations in SO(3)/G using Halton + FPS.

    Parameters:
        avg_deg (float): average rotation angle in degrees
        point_group (str): molecule point group
        sym_quats (np.ndarray): shape (g, 4), (w,x,y,z), symmetry group as unit quaternions.
        pool_size_factor (int): how many times larger the Halton pool is vs n_samples

    Returns:
        np.ndarray: shape (n_samples, 4), sampled unit quaternions
    """
    n_samples = estimate_rotation_samples(avg_deg, point_group)
    if point_group in ['C1', 'Cs', 'Ci']:
        print(f"The rotation samples without any rotation symmetry: {n_samples}")
    else:
        print(f"The rotation samples before symmetry: {estimate_rotation_samples(avg_deg)}")
        print(f"The {point_group} symmetry reduces to {n_samples} samples")

    if 'Cinf' in point_group:
        return sample_linear_mol(n_samples, homonuclear=False)
    elif 'Dinf' in point_group:
        return sample_linear_mol(n_samples, homonuclear=True)
    else:
        pool_size = max(n_samples * pool_size_factor, 1000)
        print(f"Generating Halton pool of {pool_size} points...")
        pool = halton_so3_hopf(pool_size)

        selected_indices = []
        min_distances = np.full(pool_size, np.inf)

        # Start with random first point
        first_idx = np.random.randint(pool_size)
        selected_indices.append(first_idx)
        min_distances[first_idx] = 0.0

        print("Running farthest point sampling in quotient space...")
        for i in range(1, n_samples):
            min_distances = orbit_distance2(pool, pool[selected_indices], sym_quats)
            # Select farthest point
            next_idx = np.argmax(min_distances)
            selected_indices.append(next_idx)
            print(f"  Selected {i+1}/{n_samples} samples")
        return pool[selected_indices]


def view_samples(quats:Sequence, save_path=None) ->None:
    """
    Example:

    :param quats:
    :return:
    """
    import matplotlib.pyplot as plt
    rotations = Rotation.from_quat(quats, scalar_first=True)  # 直接传入 (N, 4) 数组

    # 定义要旋转的基准向量（例如分子主轴）
    base_vector = np.array([1.0, 0.0, 0.0])  # shape (3,)

    # 应用所有旋转：结果形状为 (N, 3)
    rotated_vectors = rotations.apply(base_vector)

    # ----------------------------
    # 3D 散点图可视化
    # ----------------------------

    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')

    # 绘制单位球面（可选，增强视觉效果）
    u = np.linspace(0, 2 * np.pi, 50)
    v = np.linspace(0, np.pi, 25)
    x_sphere = np.outer(np.cos(u), np.sin(v))
    y_sphere = np.outer(np.sin(u), np.sin(v))
    z_sphere = np.outer(np.ones_like(u), np.cos(v))
    ax.plot_surface(x_sphere, y_sphere, z_sphere, color='lightgray', alpha=0.2, linewidth=0)

    # 绘制采样方向
    ax.scatter(
        rotated_vectors[:, 0],
        rotated_vectors[:, 1],
        rotated_vectors[:, 2],
        c='red',
        s=30,
        alpha=0.8
    )

    # 设置图形属性
    ax.set_xlim([-1, 1])
    ax.set_ylim([-1, 1])
    ax.set_zlim([-1, 1])
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title(f'Rotated Directions on Sphere ({len(rotated_vectors)} samples)')
    ax.set_box_aspect([1,1,1])  # equal aspect

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()