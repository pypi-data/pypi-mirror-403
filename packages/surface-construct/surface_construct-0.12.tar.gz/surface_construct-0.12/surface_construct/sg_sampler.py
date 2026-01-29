import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.distance import cdist
from sklearn.cluster import KMeans as Cluster
import random


def name2sampler(name):
    return globals()[name]


def addition_samples(sg_obj, size=None, probability=None, **kwargs):
    if 'seed' in kwargs:
        seed = kwargs['seed']
    else:
        seed = None
    if probability is None:
        probability = {
            "max_sigma": 0.2,  # 采样方法的概率
            "max_diversity": 0.8,
        }
    if size is None:
        size = 1

    # 归一化
    total = sum(probability.values())
    if total != 1.0:
        probability = {k: v / total for k, v in probability.items()}

    rng = np.random.default_rng(seed)
    method_list = rng.choice(list(probability.keys()), size=size, p=list(probability.values()))

    point_idx = np.array([], dtype=int)
    for method in method_list:
        method_lower = method.lower()
        if method_lower == 'max_sigma':
            sampling_obj = MaxSigmaSGSampler(sg_obj)
        elif method_lower == 'max_diversity':
            sampling_obj = MaxDiversitySGSampler(sg_obj)
        else:
            raise NotImplementedError
        point_idx = np.concatenate([point_idx, sampling_obj.samples(size=1, **kwargs)])  # 每种方法只采一个

    return point_idx


class SGSamplerBase:
    def __init__(self, sg_obj, **kwargs):
        self.sg_obj = sg_obj
        self.threshold = kwargs.get('threshold', 0.37)  # 0.37 is half of H-H bond
        self.weight = kwargs.get('weight', 1.0)  # 采样的几率，最后进行归一化处理
        self.kwargs = kwargs

    @property
    def _pop_size(self):
        return len(self.sg_obj.points)

    @property
    def _population(self):
        """
        默认的全体是 sg_obj.points 的 index
        :return:
        """
        return range(self._pop_size)

    def _append_sample_to_sg(self, point_idx=None):
        """
        将采样点加入到 sg_obj.sample_points 和相应的 vector

        :return:
        """
        if point_idx is None:
            point_idx = []
        elif type(point_idx) is int:
            point_idx = [point_idx]

        for p in point_idx:
            self.sg_obj.sample_idx = p

    def _samples(self, size, **kwargs):
        raise NotImplementedError

    def samples(self, size=1, **kwargs):
        result = []
        curr_size = size
        loop = 0
        while len(result) < size and loop < 10:
            point_idx = self._samples(size=curr_size, **kwargs)
            filtered_idx = self.exclude_too_close_sample(point_idx)
            self._append_sample_to_sg(point_idx=filtered_idx)
            result += filtered_idx
            curr_size = size - len(filtered_idx)
            loop += 1
        return result

    def exclude_too_close_sample(self, idx_list, threshold=None):
        if threshold is None:
            threshold = self.threshold
        if self.sg_obj.sample_idx is not None:
            unique_idx_list = [i for i in idx_list if i not in self.sg_obj.sample_idx]
            points = list(self.sg_obj.sample_points)
        else:
            unique_idx_list = idx_list[:]
            points = []
        new_idx_list = []
        for idx in unique_idx_list:
            p = self.sg_obj.points[idx]
            if len(points) == 0:
                points.append(p)
                new_idx_list.append(idx)
                continue
            tree = cKDTree(points)
            if len(tree.query_ball_point(x=p, r=threshold,p=2))==0:
                points.append(p)
                new_idx_list.append(idx)

        if len(new_idx_list) != len(idx_list):
            print(f"Exclude too close sample {set(idx_list)-set(new_idx_list)}")
        return new_idx_list

class KeyPointSGSampler(SGSamplerBase):
    """
    关键点采样，使用 vip_id
    """
    def _samples(self, **kwargs):
        sample_idx = self.sg_obj.unique_vip_id
        clusters = Cluster(n_clusters=len(sample_idx)).fit(self.sg_obj.vector)
        self.sg_obj._clusters = clusters
        return sample_idx

    def samples(self, size=None, **kwargs):
        point_idx = self._samples(**kwargs)
        filtered_idx = self.exclude_too_close_sample(point_idx)
        self._append_sample_to_sg(point_idx=filtered_idx)
        return filtered_idx

class RandomSGSampler(SGSamplerBase):
    """
    完全随机的选择点，仅用于测试，效率太低。
    """
    def __init__(self, sg_obj, **kwargs):
        super().__init__(sg_obj, **kwargs)
        if 'seed' in kwargs:
            self.seed = kwargs['seed']
        else:
            self.seed = None

    def _samples(self, size, **kwargs):
        idx = random.sample(self._population, size)
        return idx


class MaxSigmaSGSampler(SGSamplerBase):
    """
    对最大误差的点进行采样
    """
    def _samples(self, size, **kwargs):
        if 'energy' in self.sg_obj.grid_property:
            # 如果已经读入了一些能量，则返回误差最大的点
            sigma_array = self.sg_obj.grid_property['energy']
            sigma0 = sigma_array.max()
            idx_list = np.argwhere(sigma_array <= sigma0-0.1).flatten().tolist()
            idx = random.sample(idx_list, size)
            return idx
        else:
            raise "No energy for all population, pls do initial sampling first!"


class MinEnergySGSampler(SGSamplerBase):
    """
    对最大误差的点进行采样
    """
    def _samples(self, size, **kwargs):
        if 'energy' in self.sg_obj.grid_property:
            E_array = self.sg_obj.grid_property['energy']
            # 如果已经读入了一些能量，则返回能量最低的点 (<0.1eV 以内，然后随机选一个)
            E0 = E_array.min()
            idx_list = np.argwhere(E_array <= E0+0.1).flatten().tolist()
            idx = random.sample(idx_list, size)
            return idx
        else:
            raise "No energy for all population, pls do initial sampling first!"


class InitialSGSampler(SGSamplerBase):
    """
    结合使用 KeyPointSampling 和 MaxDiversitySampling
    """
    def _samples(self, size=None, **kwargs):
        # 先进行 KeyPoint sampling，数量不够再进行 Max diversity sampling
        vip_idx = self.sg_obj.unique_vip_id
        if size is None:
            size = len(vip_idx)

        if size == len(vip_idx):
            # 已经排除了距离过近的点，而且已经加入到了sg_obj
            sample_idx = KeyPointSGSampler(self.sg_obj, **self.kwargs).samples(**kwargs)
        elif size < len(vip_idx):
            print(f"The initial sampling size {size} is smaller than the number of key points {len(vip_idx)}.")
            sample_idx = random.sample(vip_idx, size)
            self._append_sample_to_sg(point_idx=sample_idx)
        else:
            sample_idx = KeyPointSGSampler(self.sg_obj, **self.kwargs).samples(**kwargs)
            while len(sample_idx) < size:
                adding_sample = MaxDiversitySGSampler(self.sg_obj).samples(size=size-len(sample_idx),**kwargs)
                sample_idx = np.concatenate([sample_idx, adding_sample])
        return sample_idx

    def samples(self, size=1, **kwargs):
        return self._samples(size=size, **kwargs)


class MaxDiversitySGSampler(SGSamplerBase):
    """
    对当前采样结构差异最大的点进行采样
    基本思路是这样的：
        * 重新进行聚类，
        * 判断已经采样点属于的类别，找出没有点的类别，空类
        * 如果空类不止一个，比较这些空类中心与旧点的距离，选择距离最大的点。
    """
    def _samples(self, size, center=True, **kwargs):
        """
        :param size:
        :param center: 是否取中心。如果不是，则取能量最小值的点。如果没有能量则报错。
        :param kwargs:
        :return:
        """
        # 判断是否有过往的采样点，如果没有，调用 InitialSampling
        if len(self.sg_obj.sample_idx) == 0:
            clusters = Cluster(n_clusters=size).fit(self.sg_obj.vector)
            virgin = list(set(clusters.labels_))
        else:
            cluster_size = len(self.sg_obj.sample_idx) + size
            nvirgin = 0
            larger_clusters = None
            larger_virgin = None
            virgin = None
            clusters = None
            # 如果等于则停止，并保存 cluster
            while nvirgin != size:
                # 以 len(sample_idx) + size 作为新的聚类的size
                clusters = Cluster(n_clusters=cluster_size).fit(self.sg_obj.vector)
                labels = clusters.labels_[self.sg_obj.sample_idx]
                labels_set = set(labels)
                virgin = set(range(cluster_size)) - labels_set
                nvirgin = len(virgin)
                # 判断分类以后空类数目与size的大小
                # 如果大于size，则减小size，并记录空类的数目
                if nvirgin > size:
                    cluster_size -= 1
                    larger_clusters = clusters
                    larger_virgin = virgin
                # 如果小于 size 则增大size，检查上一个size是否有记录，如果有记录则使用上个size 的记录。从中随机选择size个点作为采样点。
                elif nvirgin < size:
                    cluster_size += 1
                    if larger_clusters is not None:
                        clusters = larger_clusters
                        virgin = larger_virgin
                        break
        # 从 virgin 里面选取 size 个点
        cluster_idx = random.sample(list(virgin), size)
        if (not center) and 'energy' not in self.sg_obj.grid_property:
            center = True
            print("Warning: Can't get cluster minimum energy, use cluster center instead!")
        if center:
            # 取中心位置的格点
            centers = clusters.cluster_centers_[cluster_idx]
            center_dist = cdist(centers, self.sg_obj.vector)  # 计算每个点到中心的距离
            point_idx = np.argmin(center_dist, axis=-1)
        else:
            # 取这些 clusters 中能量最小值点
            point_idx = []
            for c_id in cluster_idx:
                p_idx = np.arange(len(self.sg_obj.points))[clusters.labels_ == c_id]
                # 求这些点的能量最小值
                p_energy = self.sg_obj.grid_energy[p_idx]
                point_idx.append(p_idx[p_energy.argmin()])
        # assign cluster to sg_obj
        self.sg_obj._clusters = clusters
        return point_idx


class NewtonSGSampler(SGSamplerBase):
    """
    沿着受力方向进行采样
    """

    def _samples(self, size, **kwargs):
        raise NotImplementedError


class RandomWalk(SGSamplerBase):
    """
    从给定点出发随机行走进行采样
    """
    def _samples(self, size, **kwargs):
        raise NotImplementedError


class SystematicSGSampler(SGSamplerBase):
    """
    等距采样。主要用于测试。
    """
    def _samples(self, size, **kwargs):
        if 'start' in kwargs:
            start = kwargs['start']
        else:
            start = random.randint(0, self._pop_size)
        stop = self._pop_size
        indices = list(range(start, stop)) + list(range(0, start))
        step = int(self._pop_size / size)
        point_idx = [indices[i + n * step] for n, i in enumerate(range(size))]

        return point_idx
