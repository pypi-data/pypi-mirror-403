from typing import Callable, Iterable, Sequence, Union, Optional
import numpy as np
from numpy._typing import DTypeLike
from array_like_generic import *
try:
    from scipy.special import gamma
finally: pass


def apply_from_axis(func: Callable, arr: np.ndarray, axis = 0, otypes: Iterable[DTypeLike] = None):
    '''
    Select an axis of an `numpy.ndarray` and apply a function.
    '''
    slices = (slice(None, None, None),) * (axis)
    if len(otypes) > 1:
        return tuple(np.array(item, dtype=otypes[i]) for i, item in enumerate(zip(*[func(arr[slices + (i,)]) for i in range(arr.shape[axis])])))
    elif len(otypes) == 1:
        return np.array([func(arr[slices + (i,)]) for i in range(arr.shape[axis])], otypes[0], copy=False)
    else:
        [func(arr[slices + (i,)]) for i in range(arr.shape[axis])]


def map_range(
    array: np.ndarray,
    interval: Sequence[int] = (0, 1),
    axis: Union[int, Sequence[int], None] = None,
    dtype: np.dtype = None,
    scalar_default: ScalarDefault = ScalarDefault.max,
    eps: float = 1e-6
):
    min_value: np.ndarray = np.min(array, axis=axis, keepdim=True)
    max_value: np.ndarray = np.max(array, axis=axis, keepdim=True)
    max_min_difference = max_value - min_value
    max_min_equal_mask = max_min_difference == 0
    max_min_difference[max_min_equal_mask] = 1
    array = array - min_value
    array[np.broadcast_to(max_min_equal_mask, array.shape)] = np.asarray(scalar_default_value(scalar_default, eps)).astype(array.dtype)
    return (array / max_min_difference * (interval[1] - interval[0]) + interval[0]).astype(dtype)


def map_ranges(
    array: np.ndarray,
    intervals: Sequence[Sequence[int]] = [(0, 1)],
    axis: Union[int, Sequence[int], None] = None,
    dtype: Optional[np.dtype] = None,
    scalar_default: ScalarDefault = ScalarDefault.max,
    eps: float = 1.e-6
):
    min_value: np.ndarray = np.min(array, dims=axis, keepdims=True)
    max_value: np.ndarray = np.max(array, dims=axis, keepdims=True)
    max_min_difference = max_value - min_value
    max_min_equal_mask = max_min_difference == 0
    max_min_difference[max_min_equal_mask] = 1
    normed = (array - min_value) / max_min_difference
    normed[np.broadcast_to(max_min_equal_mask, array.shape)] = np.asarray(scalar_default_value(scalar_default, eps)).astype(array.dtype)
    def generator():
        for interval in intervals:
            yield (normed * (interval[1] - interval[0]) + interval[0]).astype(dtype)
    return tuple(*generator())


def linspace_at(index, start, stop, num):
    common_difference = np.array((stop - start) / (num - 1), copy=False)
    index = np.array(index, copy=False)
    return start + common_difference * index.reshape([*index.shape] + [1] * len(common_difference.shape))


def linspace_cumprod_at(index, start, stop, num):
    start = np.array(start, copy=False)
    stop = np.array(stop, copy=False)
    common_difference = (stop - start) / (num - 1)
    index = np.array(index, copy=False)
    result_index_prefix = (slice(None),) * len(index.shape)
    n = index + 1
    n_shape = n.shape
    result = np.zeros((*n.shape, *common_difference.shape))
    zero_common_difference_mask = common_difference == 0
    left_required_shape, right_required_shape = broadcast_required_shape(start[zero_common_difference_mask].shape, n_shape)
    n = n.reshape(right_required_shape)
    result[combine_mask_index(result_index_prefix, zero_common_difference_mask)] = np.power(start[zero_common_difference_mask].reshape(left_required_shape), n)
    sequence_with_zero_mask = np.zeros_like(zero_common_difference_mask)
    nonzero_common_difference_mask = common_difference != 0
    sequence_with_zero_mask[nonzero_common_difference_mask] = (start[nonzero_common_difference_mask]) % common_difference[nonzero_common_difference_mask] == 0
    sequence_with_zero_mask[nonzero_common_difference_mask] &= (np.sign(start[nonzero_common_difference_mask]) != np.sign(common_difference[nonzero_common_difference_mask]))
    del nonzero_common_difference_mask
    result[combine_mask_index(result_index_prefix, sequence_with_zero_mask)] = 0
    first_divided_mask = np.logical_not(sequence_with_zero_mask | zero_common_difference_mask)
    del zero_common_difference_mask
    del sequence_with_zero_mask
    first_divided = np.full(common_difference.shape, np.nan)
    first_divided[first_divided_mask] = start[first_divided_mask] / common_difference[first_divided_mask]
    first_divided_gt_eq_zero_mask = first_divided > 0
    left_required_shape, right_required_shape = broadcast_required_shape(common_difference[first_divided_gt_eq_zero_mask].shape, n_shape)
    n = n.reshape(right_required_shape)
    result[combine_mask_index(result_index_prefix, first_divided_gt_eq_zero_mask)] = np.power(common_difference[first_divided_gt_eq_zero_mask].reshape(left_required_shape), n) * gamma(first_divided[first_divided_gt_eq_zero_mask].reshape(left_required_shape) + n) / gamma(first_divided[first_divided_gt_eq_zero_mask].reshape(left_required_shape))
    del first_divided_gt_eq_zero_mask
    first_divided_lt_zero_mask = first_divided < 0
    left_required_shape, right_required_shape = broadcast_required_shape(common_difference[first_divided_lt_zero_mask].shape, n_shape)
    n = n.reshape(right_required_shape)
    result[combine_mask_index(result_index_prefix, first_divided_lt_zero_mask)] = np.power(-common_difference[first_divided_lt_zero_mask].reshape(left_required_shape), n) * gamma(-first_divided[first_divided_lt_zero_mask].reshape(left_required_shape) + 1) / gamma(-first_divided[first_divided_lt_zero_mask].reshape(left_required_shape) - n + 1)
    return result


def permute(array: np.ndarray, axes: Sequence[int]):
    return np.transpose(array, axes)


def full_transpose(arr: np.ndarray):
    return np.transpose(arr, np.arange(len(arr.shape))[::-1])