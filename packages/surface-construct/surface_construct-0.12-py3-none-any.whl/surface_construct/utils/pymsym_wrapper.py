from typing import List, Dict

import numpy as np
import pymsym
import ase

from scipy.spatial.transform import Rotation as _Rotation

def get_point_group(atoms:ase.Atoms) -> str:
    """
    Get point group symbol.
    :param atoms:
    :return:
    """
    return pymsym.get_point_group(atoms.numbers.tolist(), atoms.positions.tolist())

def get_point_group_number(atoms:ase.Atoms) -> int:
    """
    Get point group number.
    :param atoms:
    :return:
    """
    return pymsym.get_symmetry_number(atoms.numbers.tolist(), atoms.positions.tolist())

def get_pure_rotations(atoms:ase.Atoms) -> List:
    """
    Get pure rotations matrix.
    :param atoms:
    :return:
    """
    ctx = _build_context(atoms)
    pure_rotations = [_Rotation.identity()]
    if ctx is not None:
        for op in ctx.symmetry_operations:
            if op.type == 1:
                # 构造 scipy Rotation
                angle = op.power/op.order * np.pi * 2.0
                uvect = np.asarray(op.vector)
                rotation = _Rotation.from_rotvec(uvect*angle)
                pure_rotations.append(rotation)
    return pure_rotations

def get_Cn(atoms:ase.Atoms) -> Dict:
    ctx = _build_context(atoms)
    Cn_dict = dict()
    if ctx is not None:
        for op in ctx.symmetry_operations:
            if op.type == 1:
                axis = tuple(np.around(op.vector,5))
                if axis in Cn_dict:
                    if op.order > Cn_dict[axis]:
                        Cn_dict[axis] = op.order
                else:
                    Cn_dict[axis] = op.order
    return Cn_dict

def _build_context(atoms:ase.Atoms) -> pymsym.Context:
    msym_elements = list()
    for i in atoms:
        msym_elements.append(pymsym.Element(name=i.symbol, coordinates=i.position.tolist()))

    msym_basis_functions = list()
    for element in msym_elements:
        bfs = [pymsym.RealSphericalHarmonic(element=element, n=2, l=1, m=m, name=f"p{m + 1}") for m in (-1, 0, 1)]
        element.basis_functions = bfs
        msym_basis_functions += bfs

    with pymsym.Context(elements=msym_elements, basis_functions=msym_basis_functions) as ctx:
        try:
            _ = ctx.find_symmetry()
        except Exception:
            ctx = None
        return ctx