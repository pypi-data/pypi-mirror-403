"""
需要手动定义 sg_obj，ads_obj

combiner 的使用方式：__init__(sg, ads),  调用 combiner.get_atoms(**kwargs)
optimizer 使用方式：兼容 ase.optimizer, 调用 optimizer.run(fmax=0.1, steps=100)
sampler 使用方式：[{'size':1,  # 采样大小
                  'surface': "Sampler1",   # 表面采样方法
                  'weight': (w1, w2),  # 表面采样方法的权重
                  'seed': None,  # 随机采样的随机数
                  },  # 第一步采样,
                   ...,   # 第二、三 、... 采样
                 ]
"""
import datetime
import itertools
import os
import numpy as np
from scan_ts import FixAtomsComXY

from .taskbase import TaskBase
from ..sg_sampler import name2sampler


class SurfaceSiteSampleTask(TaskBase):
    """
    表面位点的采样任务：对adsorbate 的二面角和旋转进行完全采样，得到最低的能量对应的结构
    输入：复合结构构造器（表面结构，分子的结构），优化器（普通优化，过渡态优化，计算器），采样器
        上一步运行的 pkl（可选）
    输出：分布图，grid 和 sample 采样的文件，如果有数据库则放到数据库中

    """
    pkl_content = ['combiner']
    def __init__(self, combiner=None, optimizer=None, sampler=None, **kwargs):
        """

        :param combiner:
        :param optimizer: ase.optimizer, 默认 None 即不优化, fmax=0.1, steps=100
        :param sampler:
        :param kwargs: {'optimizer':None, other kwargs}  需要把 optimizer的参数单独出来，因为它的参数比较固定
        """
        # 初始化
        super().__init__(**kwargs)
        # 如果存在 hist_pkl 则读入相关信息 combiner, optimizer。后面保存 pkl 文件的名字，也是 hist_pkl.
        self.optimizer = optimizer
        self.sampler = sampler
        if os.path.isfile(self.hist_pkl):
            self.from_pkl()
            self.sg_obj = self.combiner.sg_obj
            if len(self.sg_obj.calculated_sample) > 0 and len(self.sg_obj.grid_property) == 0:
                self.sg_obj.fit()
        else:
            self.combiner = combiner
            self.sg_obj = combiner.sg_obj
            if self.sg_obj.points is None:
                self.sg_obj.initialize()
            self.to_pkl()  # 保存当前状态

        if self.sampler is None:
            self.sampler = [{'surface':'KeyPointSGSampler'}]  # 默认关键点采样

        # 这些全局变量用来保存临时信息
        self.atoms = None
        self.grid_idx = None
        self.stime = datetime.datetime.now()

        self.print_task_info()

    def print_task_info(self):
        msg = [f"Starting task {self.__class__.__name__} at "
               f"{datetime.datetime.ctime(self.stime)}.\n",
               self.sg_obj.info,
               self.combiner.ads_obj.info]
        if self.optimizer is None:
            msg.append(f"Optimizer: None")
        else:
            msg.append(f"Optimizer: {self.optimizer.__name__}")
        # TODO: calculator 信息
        msg.append(f"Sampling Method: ")
        for i, s in enumerate(self.sampler):
            msg.append(f"  The {i+1}-th sampler:")
            msg.append(f"    Size: {s.get('size')}")
            msg.append(f"    Surface Sampler: {s.get('surface')}")
            msg.append(f"    Surface Sampler weight: {s.get('weight',1.0)}")
        msg.append("Other kwargs:")
        for k,v in self.kwargs.items():
            msg.append(f'    {k} : {v}')

        msg.append("\nResult:")
        msg.append("       time   sample_idx     x       y        z      E0/eV   converged")
        self.log('\n'.join(msg)+'\n')

    def irun(self,grid_idx=None, **kwargs):
        # 采样单元运行
        self.grid_idx = grid_idx
        if self.combiner.ads_obj.dihedral_delta is None:
            cidx_list = [None]
        else:
            cidx_list = range(len(self.combiner.ads_obj.dihedral_grid))
        if self.combiner.ads_obj.rotation_delta is None:
            ridx_list = [None]
        else:
            ridx_list = range(len(self.combiner.ads_obj.rotation_grid))
        if len(self.combiner.ads_obj.dock_points)==0:
            dp_list = [None]
        else:
            dp_list = range(len(self.combiner.ads_obj.dock_points))
        crd_comb = itertools.product(cidx_list, ridx_list, dp_list)
        e0_list = []
        atoms_list = []
        for cidx,ridx,dp_idx in crd_comb:
            atoms = self.combiner.get_atoms(sidx=grid_idx,
                                            cidx=cidx,
                                            ridx=ridx,
                                            dp_idx=dp_idx,
                                            opt_z=True)
            if atoms is None:
                continue
            if self.optimizer is not None:
                # 设置 constraint
                fixed_idx = list(range(len(self.sg_obj.atoms), len(atoms)))
                atoms.set_constraint([FixAtomsComXY(fixed_idx)] + atoms.constraints)
                opt_kwargs = self.kwargs.get('optimizer',dict())
                output_name = f"opt_{grid_idx}-{cidx or 0}-{ridx or 0}-{dp_idx or 0}"
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
            else:
                converged = True
            if converged:
                e0_list.append(atoms.get_potential_energy())
                atoms_list.append(atoms.copy())

        if len(e0_list) == 0:
            e0 = np.nan
            converged = False  # re-define converged
        else:
            converged = True
            e0_min_idx = np.argmin(e0_list)
            e0 = e0_list[e0_min_idx]
            atoms = atoms_list[e0_min_idx]

        # 打印信息到 log file：
        used_time = (datetime.datetime.now() - self.stime).seconds
        h = used_time // 3600
        m = (used_time % 3600) // 60
        s = (used_time % 60)
        x, y, z = self.sg_obj.points[grid_idx]
        msg = (f"SAMPLE {h:02}:{m:02}:{s:02} {grid_idx:7} "
               f"{x:8.3f} {y:8.3f} {z:8.3f} {e0:.4f}  {str(converged)[0]}")  # TODO: 将信息写入单独的一个文件 sample_energy.dat
        self.log(msg+'\n')
        # 输出 优化完的结构
        if converged:
            atoms.write(f"atoms_{grid_idx}.traj")
            # 更新 sg_obj
            self.sg_obj.set_energy(grid_idx, e0)
            self.to_pkl()
            # 是否画图？
            if kwargs.get('fit', False):
                self.sg_obj.fit()
                self.sg_obj.plot_energy()
                self.sg_obj.plot_sigma()
        else:
            self.sg_obj.del_sample(grid_idx)

    def run(self):
        for isampler in self.sampler:
            size = isampler.get("size", 1)
            sg_sampler = isampler.get("surface")
            if type(sg_sampler) in (tuple, list) and len(sg_sampler) == 1:
                sg_sampler = sg_sampler[0]
            if type(sg_sampler) == str:
                sg_sampler_obj = name2sampler(sg_sampler)
                if sg_sampler in ('InitialSGSampler', 'KeyPointSGSampler'):  # 一次性采N样，其余都是一次一个点
                    sg_samples = sg_sampler_obj(self.sg_obj).samples(size)
                    msg = f"  Start initial sampling with {len(sg_samples)} points."
                    self.log(msg+'\n')
                    for grid_idx in sg_samples:
                        if grid_idx == sg_samples[-1]:
                            self.irun(grid_idx, fit=True)
                        else:
                            self.irun(grid_idx, fit=False)
                else:
                    for i in range(size):
                        grid_idx = sg_sampler_obj(self.sg_obj).samples(size=1)
                        self.irun(grid_idx, fit=True)
            elif type(sg_sampler) in (tuple, list):
                msg = f"  Appending sampling with {size} points."
                self.log(msg+'\n')
                loop = 0
                while loop < size:
                    weight = isampler.get("weight", [1] * len(sg_sampler))
                    seed = isampler.get("seed")
                    # 归一化权重
                    total = sum(weight)
                    weight = [v / total for v in weight]
                    rng = np.random.default_rng(seed)
                    sampler_name = rng.choice(sg_sampler, size=1, p=weight)[0]
                    msg = f"    Next sampling is by {sampler_name} method."
                    self.log(msg+'\n')
                    sampler = name2sampler(sampler_name)
                    grid_idx_list = sampler(self.sg_obj).samples(size=1)
                    if len(grid_idx_list) > 0:
                        self.irun(grid_idx_list[0], fit=True)
                        loop += 1

        msg = f"\nSampling complete with {len(self.sg_obj.sample_idx)} sampled points in total."
        self.log(msg+'\n')

