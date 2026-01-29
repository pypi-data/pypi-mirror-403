import datetime

import ase.io
import numpy as np
from ase import Atoms
from ase.constraints import FixAtoms, dict2constraint
from .sitesampling import SurfaceSiteSampleTask

def update_fixatoms_index(atoms:Atoms, idx:int):
    c_list = []
    for c in atoms.constraints:
        if isinstance(c, FixAtoms):
            dct = c.todict()
            dct['kwargs']['indices'] = [i+idx for i in dct['kwargs']['indices']]
            new_c = dict2constraint(dct)
            c_list.append(new_c)
    return c_list

def get_topo_id(A,nl=None):  # 替代老的
    from ase.geometry.analysis import Analysis as ase_Analysis
    from surface_construct.utils.atoms import topodist_matrix, topo_identity
    analysis = ase_Analysis(A, nl=nl)
    adj_matrix = analysis.adjacency_matrix[0].toarray()
    dm = topodist_matrix(adj_matrix)
    ids = topo_identity(dm)
    return ids

class AFMTask(SurfaceSiteSampleTask):

    def irun(self,grid_idx=None, **kwargs):
        # 采样单元运行
        self.grid_idx = grid_idx
        x,y,z = self.sg_obj.points[grid_idx]
        dock_point = self.combiner.ads_obj.dock_points[0]  # tip must define the dock_point
        dz_range = (np.linspace(2.0,0.75,self.kwargs.get('nz',10)) *
                    (max(self.sg_obj.rsub)+self.sg_obj.rads))  # from far to near
        z0 = max(self.sg_obj.atoms.positions[:,2])
        e0_list = []
        dz_list = []
        atoms_list = []
        ads_topo_id0 = self.combiner.ads_obj.topo_id
        for dz in dz_range:
            ads_atoms = self.combiner.docking(
                xyz=[x,y,z0+dz],
                dock_point=dock_point,
            )
            atoms = self.sg_obj.atoms.copy()
            atoms += ads_atoms
            atoms.calc = self.combiner.calc

            if self.optimizer is not None:
                # 设置 constraint
                idx0 = len(self.sg_obj.atoms)
                new_constraint = (update_fixatoms_index(self.combiner.ads_obj.atoms, idx0)
                                  + atoms.constraints)
                atoms.constraints = new_constraint
                opt_kwargs = self.kwargs.get('optimizer',dict())
                output_name = f"opt_{grid_idx}-{dz:.2f}"
                if 'logfile' not in opt_kwargs:
                    opt_kwargs['logfile'] = f"{output_name}.log"
                if 'trajectory' not in opt_kwargs:
                    opt_kwargs['trajectory'] = f"{output_name}.traj"
                if 'fmax' in opt_kwargs:
                    fmax = opt_kwargs.pop('fmax')
                else:
                    fmax = 0.1
                if 'steps' in opt_kwargs:
                    steps = opt_kwargs.pop('steps')
                else:
                    steps = 100
                opt = self.optimizer(atoms, **opt_kwargs)
                converged = opt.run(fmax=fmax, steps=steps)
                if converged:
                    new_ads_atoms = atoms[len(self.sg_obj.atoms):]
                    topo_id = get_topo_id(new_ads_atoms,nl=self.combiner.ads_obj.nl)
                    if topo_id != ads_topo_id0:
                        msg=f"Warning: The connectivity of tip is broken for dz={dz}"
                        self.log(msg+'\n')
                        converged = False
            else:
                converged = True

            if converged:
                e0=atoms.get_potential_energy()
                e0_list.append(e0)
                dz_list.append(dz)
                atoms_list.append(atoms.copy())

        if len(e0_list) == 0:
            e0 = np.nan
            converged = False  # re-define converged
        else:
            converged = True
            e0_min_idx = np.argmin(e0_list)
            e0 = e0_list[e0_min_idx]
            dz = dz_list[e0_min_idx]
            z = z0 + dz

        # 打印信息到 log file：
        used_time = (datetime.datetime.now() - self.stime).seconds
        h = used_time // 3600
        m = (used_time % 3600) // 60
        s = (used_time % 60)
        msg = (f"SAMPLE {h:02}:{m:02}:{s:02} {grid_idx:7} "
               f"{x:8.3f} {y:8.3f} {z:8.3f} {e0:.4f}  {str(converged)[0]}")
        self.log(msg+'\n')
        # 输出 优化完的结构
        if converged:
            ase.io.write(f"atoms_{grid_idx}.traj", atoms_list)
            # 更新 sg_obj
            self.sg_obj.set_energy(grid_idx, e0)
            for iz, ie in zip(dz_list, e0_list):
                self.sg_obj.set_property(grid_idx, ie, key=iz)
            self.to_pkl()
            # 是否画图？
            if kwargs.get('fit', False):
                self.sg_obj.fit()
                self.sg_obj.plot_energy()
        else:
            self.sg_obj.del_sample(grid_idx)