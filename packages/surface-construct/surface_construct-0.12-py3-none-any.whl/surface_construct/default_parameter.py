# 设置默认参数
import numpy as np
from ase.calculators.vasp import Vasp
grid_interval = 0.1  # angstrom, 格点的间距
Nsample = 10  # 第一次采样的点
Niter = 20  # 最大迭代次数
calc = Vasp(
    ibrion=-1,
    nsw=0,
    lwave=True,
    lcharg=False,
    xc='PBE',
    kpts=(1, 1, 1),
    encut=400,
    setups='recommended',
    ncore=4,
    gamma=True,
    nelm=200,
    algo='fast',
    ismear=0,
    sigma=0.05,
    ediffg=-0.03,
    ediff=1e-4,
    prec='normal',
    lreal='Auto',
    ispin=1)

fmax = 0.1  # 结构优化 force 的收敛标准
max_steps = 100  # 优化最大步数
max_error = 0.01  # 表面采样的收敛标准
radii_type = 'covalent_radii'  # 半径选项：'vdw_radii'，'covalent_radii'
radii_factor = 1.1  # 原子半径系数
scan_type = 'optimization'  # 扫描类型：'optimization'，'transition_state'
plot_property = ['energy', ]  # 输出图片的内容，可选内容：'energy', 'z', 'phi', 'theta',
# '-1, -2' (-1，-2 原子键长），'-1, -2, -3' （键角），'-1, -2, -3, -4' 二面角
# 作图就意味着要拟合，就可以尝试预测
predict_property = []  # 可选内容：'z', 'phi', 'theta',
# '-1, -2' (-1，-2 原子键长），'-1, -2, -3' （键角），'-1, -2, -3, -4' 二面角
sampleproperty = dict()  # 对性质进行采样 key:list，可选 key 内容: 'phi_x', 'theta'
if scan_type == 'transition_state':
    # 只对初始 Nsample 个点进行全部采样，接下来的点使用预测值, 不再扫描。
    sampleproperty['phi_x'] = np.linspace(0, 2 * np.pi, 3, endpoint=False)
# 采样方法
sampling_method = {
    "max_sigma": 0.5,  # 采样方法概率
    "max_diversity": 0.5,
}
include_vertex = False  # initial sampling 是否包含 vertex 点
E_reference = 0.0  # 一般是基底加上吸附分子的能量，也可以自定义。默认为 0.0
