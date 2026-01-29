import ase
import numpy as np
from typing import Union, Sequence

from scipy.spatial import cKDTree

from surface_construct.utils import extended_points
from surface_construct.utils.atoms import set_dihedrals, atoms_regulate
from surface_construct import Adsorbate, SurfaceGrid


class AdsGridCombiner:
    def __init__(self, sg_obj:SurfaceGrid, ads_obj:Adsorbate, **kwargs):
        """
        :param sg_obj: 表面格点
        :param ads_obj: 吸附分子，包含Atoms，主轴，内坐标列表，根据这些参数可以得到分子坐标
        :param kwargs:
        """
        self.atoms = None
        self.sg_obj = sg_obj
        self.ads_obj = ads_obj
        self.kwargs = kwargs
        if self.sg_obj.atoms.calc is not None:
            self.calc = self.sg_obj.atoms.calc
        else:
            if self.ads_obj.atoms.calc is not None:
                self.calc = self.ads_obj.atoms.calc
            else:
                self.calc = None

    @property
    def info(self):
        info = [self.sg_obj.info, self.ads_obj.info]
        return '\n'.join(info)

    def get_atoms(self, sidx:int, cidx:Union[int, None]=None,
                  ridx:Union[int, None]=None, dp_idx:int=None, **kwargs) -> Union[ase.Atoms, None]:
        """
        将分子设置 dihedrals（C空间）、rotation （R空间）然后将分子的结合点（dock_point）
            放置于site（S空间）上，根据需要调整 z （Z空间）。
        分子内坐标 dihedrals = {indice:{value:v, mask:[i,j,k]}}
        若不用调整 z，则设置 zmax=site[-1]，放入 kwargs
        :param sidx: 格点序号
        :param cidx:
        :param ridx:
        :param dp_idx:
        :return: 组合后的 Atoms
        """
        xyz = self.sg_obj.points[sidx]
        dih_value, rotation, dock_point = None, None, None
        if cidx is not None:
            dih_value = self.ads_obj.dihedral_grid[cidx]
        if ridx is not None:
            rotation = self.ads_obj.rotation_grid[ridx]
        if dp_idx is None and len(self.ads_obj.dock_points) > 0:
            dp_idx = 0
        if dp_idx is not None:
            dock_point = self.ads_obj.dock_points[dp_idx]
        # 改变分子构象 and then rotate
        ads_atoms = self.docking(
            dih_value=dih_value,
            rotation=rotation,
            xyz=xyz,
            dock_point=dock_point,
        )
        if kwargs.get('opt_z', False):
            # get_z 去更新 ads_atoms 的坐标
            ads_atoms = self._opt_z(ads_atoms, dock_point=dock_point, zmax=kwargs.get('zmax', None))
            if not ads_atoms:
                return None

        atoms = self.sg_obj.atoms.copy()
        atoms += ads_atoms
        atoms.calc = self.calc
        self.atoms = atoms
        return atoms

    def _opt_z(self, ads_atoms:ase.Atoms,
               dock_point:int=None,
               conflict:float=None,
               zmax:float=None,
               ):
        """
        由于分子可能会与表面冲突，调整分子的高度可以避免
        TODO： 事实上调整的是沿着格点法向向量的距离 xyz = xyz0 + r×d
        :return:
        """
        # 该方法仅仅适用于 slab 体系，不适合 cluster 体系
        # 先找到grid 的最大值点，分子的最小值点，然后把分子的COM 移动到距离5A以上的点
        # 根据 ads 不同的原子类型，计算每个原子需要移动的z值，取最小的值。-> 应该不需要，用最简单的办法解决就行
        max_rsub = max(self.sg_obj.rsub)
        if conflict is None:
            conflict = max_rsub + 0.5  # 分子与表面距离宁肯稍微大一些，不要太小。TODO: 使用距离矩阵判断，考虑元素影响
        if zmax is None:
            if dock_point is None:  # 默认是范德华作用，单原子不需要调整（也无需dock point）
                posz = ads_atoms.positions[:,2]
                zmax = self.sg_obj.rads + max_rsub + (max(posz)-min(posz))/2.0 #
            else:
                zmax = (self.sg_obj.rads+max_rsub) * 0.5  # 键长的1.5倍
        surf_atoms = self.sg_obj.atoms
        surf_tree = cKDTree(extended_points(surf_atoms.positions, (1, 1, 0), surf_atoms.cell))
        test_atoms = ads_atoms.copy()
        delta_z = 0.05 # 每次递增 0.05
        n_delta = 1
        while delta_z*n_delta <= zmax:
            test_atoms.positions[:,2] += delta_z
            overlap = surf_tree.query_ball_point(test_atoms.positions, conflict, p=2).tolist()
            len_overlap = sum(list(map(len, overlap)))
            if len_overlap != 0:
                n_delta += 1
            else:
                print(f"Update adsorbate by adding z {delta_z*n_delta} to avoid conflict to surface.")
                return test_atoms

        print("Cannot find z value for adsorbate without conflict!")
        return False

    def docking(self, xyz:np.ndarray=np.array([0.,0.,0.]),
                dih_value:Sequence=None,
                rotation:Sequence=None,
                dock_point:int=None) -> ase.Atoms:
        from scipy.spatial.transform import Rotation as R

        atoms = self.ads_obj.atoms.copy()
        constraints = atoms.constraints.copy()  # 需要先消除限制，因为会影响set_com 和旋转
        atoms.constraints = []
        if dih_value is not None:
            dih_dict = self.ads_obj.get_dihedrals(dih_value=dih_value)
            atoms = set_dihedrals(self.ads_obj.atoms,dih_dict)
            atoms_regulate(atoms)
        else:
            atoms = self.ads_obj.atoms.copy()

        if dock_point is not None:  # move atoms dock point to 0
            atoms.positions -= dock_point

        if rotation is not None:  # rotate atoms at dock point
            atoms.positions = R.from_quat(rotation, scalar_first=True).apply(atoms.positions)

        atoms.positions += xyz # move atoms
        atoms.constraints = constraints  # 重新找回 constraints
        return atoms

    def get_vip_rot(self)->Sequence:
        # TODO: 根据各种不同位点的采样结果，进行能量分析，排除截断以上的旋转，得到较优的旋转空间
        return []


