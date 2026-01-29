import numpy as np


def no_weight(v, **kwargs):
    return v


def linear_weight(v, **kwargs):
    r0 = kwargs['r0']
    if 'rc' in kwargs:
        rc = kwargs['rc']
    else:
        rc = 3 * r0

    w = (rc - v) / (rc - r0)
    w[w > 1.0] = 1.0
    w[w < 0.0] = 0.0
    v_w = w
    return v_w


def vb_r_weight(v, **kwargs):
    r0 = kwargs['r0']
    if 'b' not in kwargs:
        b = 0.618 # 较大的数值衰减较慢，能够将更远的原子作用考虑进来。不建议大于此数
    else:
        b = kwargs['b']
    weight = np.exp((r0 - v) / b)
    #weight[weight > 1.0] = 1.0
    v_w = v / r0 * weight
    return v_w


def vb_weight(v, **kwargs):
    r0 = kwargs['r0']
    if 'b' not in kwargs:
        b = 1.0  # 较大的数值衰减较慢，能够将更远的原子作用考虑进来
    else:
        b = kwargs['b']
    weight = np.exp((r0 - v) / b)
    #weight[weight > 1.0] = 1.0
    v_w = weight
    return v_w


def reciprocal_weight(v, **kwargs):
    """Relate to Coulumb interaction
    Need charge for each atom.
    TODO: add charge option.
    Calculate each pairs between q and q_ads.
    q = kwargs.get('charge',0.1)
    q_ads = kwargs.get('charge_ads',1)
    q 可以使用 CHELG 方法快速计算。
    """
    r0 = kwargs['r0']
    v_w = r0 / v
    return v_w

# TODO: vdw 相互作用项

# TODO: 总的加和是 valent + coulumb + vdw，或者三者的合并

def reciprocal_square_weight(v, **kwargs):
    return reciprocal_weight(v, **kwargs) ** 2

