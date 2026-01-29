from typing import Dict, List

import numpy as np
import spglib

from surface_construct.utils.atoms import atoms2spg

"""
Example:
from ase.build import molecule

# H2O 分子，返回 C2v 点群
h2o = molecule('H2O')
dataset = get_symmetry_dataset(h2o)
rots = get_pure_rotations(h2o)
symmetry_summary(dataset)

# 苯分子，返回点群 Pmmm，这是错误的。
# 正确的应该是 D6h，错误的原因可能是因为 spglib 是针对晶体体系的，结果依赖于晶胞形状。
# 建议使用 pymsym 库
ben = molecule('C6H6')
dataset = get_symmetry_dataset(ben)
rots = get_pure_rotations(ben)
symmetry_summary(dataset)

"""

def get_symmetry_dataset(atoms, symprec: float = 1e-2) -> Dict:
    """
    使用spglib分析分子对称性. from Deepseek.
    """
    newatoms = atoms.copy()
    newatoms.cell = np.eye(3) * 20
    spgcell = atoms2spg(newatoms)
    dataset = spglib.get_symmetry_dataset(spgcell, symprec=symprec)
    if dataset is None:
        raise Exception("Could not get symmetry dataset.")
    dataset['symprec'] = symprec
    return dataset

def symmetry_summary(dataset) -> None:
    """
    打印对称性分析摘要. From Deepseek
    """
    # 提取纯旋转操作
    pure_rotations = extract_pure_rotations(dataset)
    # 计算点群
    point_group = _get_detailed_point_group(dataset, pure_rotations)
    symmetry_info = {
        'dataset': dataset,
        'pointgroup_symbol': dataset['pointgroup'],
        'international_symbol': dataset['international'],
        'pure_rotations': pure_rotations,
        'n_pure_rotations': len(pure_rotations),
        'equivalent_atoms': dataset['equivalent_atoms'],
        'detailed_point_group': point_group,
        'symmetry_operations': len(dataset['rotations'])
    }
    print("\n" + "=" * 60)
    print("分子对称性分析结果")
    print("=" * 60)
    print(f"点群符号 (spglib): {symmetry_info['pointgroup_symbol']}")
    print(f"国际符号: {symmetry_info['international_symbol']}")
    print(f"Schoenflies符号: {symmetry_info['detailed_point_group']['schoenflies']}")
    print(f"总对称操作数: {symmetry_info['symmetry_operations']}")
    print(f"纯旋转操作数: {symmetry_info['n_pure_rotations']}")

    if symmetry_info['pure_rotations']:
        print("\n旋转轴分析:")
        for i, axis in enumerate(symmetry_info['detailed_point_group']['rotation_axes']):
            order = symmetry_info['detailed_point_group']['rotation_orders'][i]
            print(f"  轴 {i + 1}: 方向={axis}, 阶数={order}")


def extract_pure_rotations(dataset: Dict) -> List[np.ndarray]:
    """
    从spglib数据集中提取纯旋转操作. from Deepseek.
    """
    pure_rotations = []

    for rot, trans in zip(dataset['rotations'], dataset['translations']):
        # 检查是否是纯旋转（无平移）
        if np.allclose(trans, [0, 0, 0], atol=dataset['symprec']):
            # 检查是否是有效旋转（行列式接近1）
            if np.abs(np.linalg.det(rot) - 1.0) < dataset['symprec']:
                pure_rotations.append(rot)
    return pure_rotations

def get_pure_rotations(atoms, symprec: float = 1e-2) -> List:
    dataset = get_symmetry_dataset(atoms, symprec)
    pure_rotations = extract_pure_rotations(dataset)
    return pure_rotations


def _get_detailed_point_group(dataset: Dict, pure_rotations):
    """
    获取详细的点群信息. from Deepseek.
    """
    pg_symbol = dataset['pointgroup']

    # 常见点群的旋转阶数
    point_group_info = {
        'symbol': pg_symbol,
        'schoenflies': _to_schoenflies(pg_symbol),
        'rotation_axes': _analyze_rotation_axes(pure_rotations, dataset['symprec']),
        'rotation_orders': _get_rotation_orders(pure_rotations, dataset['symprec'])
    }

    return point_group_info


def _analyze_rotation_axes(rotations, symprec):
    """
    分析旋转轴. from Deepseek.
    """
    axes = []

    for rot in rotations:
        if np.allclose(rot, np.eye(3), atol=symprec):
            continue

        # 从旋转矩阵提取旋转轴
        axis = _extract_rotation_axis(rot, symprec)
        if axis is not None:
            # 归一化并去重
            axis = axis / np.linalg.norm(axis)
            is_new = True
            for existing_axis in axes:
                if (np.allclose(axis, existing_axis, atol=0.1) or
                        np.allclose(axis, -existing_axis, atol=0.1)):
                    is_new = False
                    break
            if is_new:
                axes.append(axis)

    return axes


def _extract_rotation_axis(rotation_matrix, symprec):
    """
    从旋转矩阵提取旋转轴. from Deepseek.
    """
    # 计算特征值和特征向量
    eigvals, eigvecs = np.linalg.eig(rotation_matrix)

    # 找到特征值为1的特征向量
    for i, eigval in enumerate(eigvals):
        if np.isclose(eigval, 1.0, atol=symprec):
            axis = np.real(eigvecs[:, i])
            return axis

    return None


def _get_rotation_orders(rotations, symprec):
    """
    获取旋转操作的阶数. from Deepseek.
    """
    orders = []

    for rot in rotations:
        if np.allclose(rot, np.eye(3), atol=symprec):
            orders.append(1)
            continue

        # 计算阶数（最小n使得R^n = I）
        current = rot.copy()
        order = 1

        while not np.allclose(current, np.eye(3), atol=symprec):
            current = current @ rot
            order += 1
            if order > 12:  # 防止无限循环
                break

        orders.append(order)

    return orders


def _to_schoenflies(pointgroup_symbol: str) -> str:
    """
    转换为Schoenflies符号. From Deepseek.
    """
    conversion = {
        '1': 'C1', '2': 'C2', '3': 'C3', '4': 'C4', '6': 'C6',
        '222': 'D2', '32': 'D3', '422': 'D4', '622': 'D6',
        '23': 'T', '432': 'O', '-43m': 'Td', 'm-3m': 'Oh',
        '2/m': 'C2h', '4/m': 'C4h', '6/m': 'C6h',
        'mmm': 'D2h', '4/mmm': 'D4h', '6/mmm': 'D6h',
        '3m': 'C3v', '-3m': 'D3d', '-62m': 'D3h',
        'm': 'Cs', '-1': 'Ci', '-3': 'S6', '-4': 'S4',
    }
    return conversion.get(pointgroup_symbol, pointgroup_symbol)
