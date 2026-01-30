"""
Why we need this module?
Because most of vison operation is based on 2D-images (with shape (..., Nx, Ny)).
For our program, we use multi-dimension data, like 3D or 4D or 5D ... We need a
function accept (..., Nx, Ny) to process our (..., Nx, Ny, ...) data, here are
two solutions:
    1.  we to permute data, use the operator, then permute back. we add this kind of
        permutation process into every 2D operator.
    2.  design a general data axes permute function for any 2D operator
It will be much smarter for us to use solution 2 than solution 1.
"""
import functools
import math

from typing import Sequence, Union, Dict, List, Callable, Any

import numpy as np
import torch

from bixi.utils.torch_cast import numpy_torch_compatible, list_to_batch
from bixi.utils.collection_op import deep_map, deep_apply, forest2tree


def ordinal_index(length, index):
    """
    Example:
        3D shape, (-1) --> 2
        5D shape, (-1) --> 4
        5D shape, (-3) --> 2
    """
    return index if index >= 0 else length + index


def ordinal_indexes(length, indexes):
    """
    Example:
        5D shape, axis: (0,1,2,3,4)
        (-1,-2,0,1,2) -->  (4,3,0,1,2)
    """
    return [ordinal_index(length, idx) for idx in indexes]


def axes_to_last_order(ndim, axes_idx: Sequence[int]):
    """
    Generate axes order of move the axes specifed by `axes_idx` to last in a n-dimension axes,
    return indices can used to permute(array, indices) and inverse_indices can used
    to restore the data by permute(array, inverse_indices)
    eg.
        (Nb, Nx, Ny, Ntime) --move(2,3)--> (Nb, Ntime, Nx, Ny)
        (..., Nx, Ny, Ntime, Nslice) --move(-4,-3)--> (..., Ntime, Nslice, Nx, Ny)
        shape (1,2,3,4,5) --move(3,2)--> shape (1,2,5,4,3)
    """
    # convert reversed index to ordinal index
    axes_need_move = [(axis if axis >= 0 else ndim + axis) for axis in axes_idx]

    # generate forward-indices
    forward_indices = tuple([axis for axis in range(ndim) if axis not in axes_need_move] + axes_need_move)

    # generate inverse-indices
    inverse_indices = np.argsort(forward_indices).tolist()

    return forward_indices, inverse_indices


@numpy_torch_compatible(implementation='torch')
def index_select_batchop(data: torch.Tensor,
                         indexes: torch.Tensor,
                         dim: int):
    """
    Extract any data at specified axis over batches
    NOTE: the dimension won't change after this method
    :param data: [B, ..., axisX: size n, ...]
    :param indexes: [B, m (number of positions you want to extract at the axisX)], m <= n
    :param dim: the index of axisX
    :return: [B, ..., axisX: size indexes.shape[1], ...]
    """
    B = data.shape[0]

    # NOTE: torch.index_select will keep dimension, it will not break the dimension of input data
    extracted = torch.cat([
        torch.index_select(data[[batch_idx]], dim, indexes[batch_idx]) for batch_idx in range(B)
    ], dim=0)

    return extracted


_ARRAY = Union[torch.Tensor, np.ndarray]


class MultidimBatchFormer(object):
    """
    Trace and check the specified dimension's size
    We Assume nonbatch_indices are CONTINUOUS indices or MANUALLY GIVEN the positions after operation.
    Otherwise, the position of batch axes in returned values are ambiguous
    Note:
            [*multidim_indices_left, *nonbatch_indices, *multidim_indices_right]
         -> [*front_indices, *nonbatch_indices]
         -> [N, *nonbatch_indices]
         -> [*front_indices, *nonbatch_indices]
         -> [*multidim_indices_left, *nonbatch_indices, *multidim_indices_right]
    """

    def __init__(self, multidim_positions: Sequence[int], multidim_positions_post: Sequence[int] = None):
        assert multidim_positions_post is None or len(multidim_positions_post) == len(multidim_positions)
        self.multidim_positions: List[int] = list(multidim_positions)
        self.multidim_positions_post = multidim_positions_post
        """
        The multidim_positions_post is multidim_positions by default, but the right part is represented in
         inverse indexing way to make sure it is not ambiguous. (example goes follow)

            Axes (batch_1, batch_2, op_1, op_2, ..., op_m, batch_3 ..., batch_n) can be partition into
                               left ^ right
                (batch_1, ..., batch_n) and (op_1, ..., op_m),
                (batch_1, batch_2) are left, can use ordinal indices to represent
                (batch_3, ..., batch_n) are right, **must** be represented by inversed way, because operation axes may
                disappeared in the returned values.

        Assertion: operation axes must be continued if multidim_positions_post is not manually given, 
            otherwise the position of batch axes in returned values are ambiguous to infer.
        """

        self.first_operation_index: int = (len(multidim_positions))
        self.batch_indices_front_placed: List[int] = list(range(len(multidim_positions)))

        self.dim2size: Dict[int, int] = None  # used to check each array's batch dimensions' sizes are same
        self.multidim_sizes: List[int] = None  # sizes of each multidims
        self.batched_size: int = None  # represent prod(multidim_sizes)

        self.is_dim_stored: bool = False
        self.is_no_batch: bool = len(multidim_positions) == 0

    def _store_dims(self, x: _ARRAY):
        shape = x.shape
        ndim = len(shape)
        multidim_positions = ordinal_indexes(ndim, self.multidim_positions)
        if self.multidim_positions_post is None and len(multidim_positions) != ndim:
            # When multidim_post_positions is not manually given, we need to check the continuity of operation axes
            # Special case: when multidim_positions covered all dimensions, there is no operation axes, it always valid
            operation_indices = set(range(ndim)) - set(multidim_positions)
            first_operation_index = min(operation_indices)
            multidim_positions = list(map(lambda i: i if i < first_operation_index else i - ndim,
                                          multidim_positions))
            assert len(operation_indices) == (max(operation_indices) - min(operation_indices) + 1), \
                f"Operation axes must be a series of continuous integers, got {operation_indices}. It is ambiguous " \
                f"to infer multidim_positions after operation. You can manually specify multidim_positions_post."

        if self.multidim_positions_post is None:
            # multidim_positions's right part are inverse now, it can be used to be the default post-positions
            self.multidim_positions_post = multidim_positions

        self.dim2size = {k: shape[k] for k in multidim_positions}
        self.multidim_sizes = list(self.dim2size.values())
        self.batched_size = math.prod(self.multidim_sizes)

        self.is_dim_stored = True

    def _check_tensor(self, x: _ARRAY):
        if not self.is_dim_stored:
            self._store_dims(x)
            return

        shape = x.shape
        for dim in self.dim2size:
            size = shape[dim]
            expect_size = self.dim2size[dim]
            if size != expect_size:
                raise RuntimeWarning(
                    f"Tensor's shape is different with expectation, "
                    f"expect {expect_size} size on dimension {dim} of shape {shape}, but got {size} instead"
                )

    def _moveaxes(self, x: _ARRAY, axes_src_indices, axes_dst_indices):
        if isinstance(x, np.ndarray):
            return np.moveaxis(x, axes_src_indices, axes_dst_indices)
        elif isinstance(x, torch.Tensor):
            return torch.moveaxis(x, axes_src_indices, axes_dst_indices)
        else:
            assert False

    def to_batched(self, x: _ARRAY) -> _ARRAY:
        if self.is_no_batch:
            return x

        self._check_tensor(x)
        x = self._moveaxes(x, self.multidim_positions, self.batch_indices_front_placed)  # [..., ...]
        x = x.reshape(self.batched_size, *x.shape[self.first_operation_index:])  # [N, ...]
        return x

    def to_multidim(self, x: _ARRAY) -> _ARRAY:
        if self.is_no_batch:
            return x

        assert self.is_dim_stored, "Uninitialized MultidimBatchFormer: at least a Tensor should be passed to " \
                                   "`.to_batched()`, otherwise no prior dimensionality information can be used."
        x = x.reshape(*self.multidim_sizes, *x.shape[1:])
        x = self._moveaxes(x, self.batch_indices_front_placed, self.multidim_positions_post)
        return x


def batchop_along_axes(batch_axes: Sequence[int], func: Callable,
                       *args, batch_axes_postop: Sequence[int] = None, **kwargs):
    """ Apply `func` on the given axes of the Tensors in its args and kwargs
    Args:
        batch_axes: the dimension indexes be stacked and applied by the func,
            we assume all Tensors (both in arguments and returned Tensors) has the `batch_axes` dimensions,
            and they share same sizes
        func: a batch-operation supported function (all arguments and returned Tensors have the shape like [N, ...]),
            independent N times operations are operated along the following dimensions
        args: placement arguments of function
        batch_axes_postop: batch_axes' index positions after operations. To avoid ambiguity, expect operation axes to
            be continuous if  the argument is not given
        kwargs: keyword arguments of function

    Example:
        f([N, H, W], [N, C, H, W], kwarg_example=[N, T]) -> ([N, 1], {'extra': [N, 16, 16]})

        ```
            def foo(arg1, arg2, *, kwarg):
                N1, N2, N3 = arg1.shape[0], arg2.shape[0], kwarg.shape[0]
                N = N1
                assert N == N2 and N == N3
                return (torch.zeros(N, 1), {'extra': torch.zeros(N, 16, 16)})

            B1, B2, B3 = 1, 20, 2
            C, T, H, W = 3, 15, 128, 128
            arg1 = torch.randn(B1, B2, H, W, B3)
            arg2 = torch.randn(B1, B2, C, H, W, B3)
            arg3 = torch.randn(B1, B2, T, B3)
            out = batchop_along_axes((0, 1, -1), foo, arg1, arg2, kwarg=arg3)

            self.assertEqual((B1, B2, 1, B3), out[0].shape)
            self.assertEqual((B1, B2, 16, 16, B3), out[1]['extra'].shape)
        ```
    """
    batch_former = MultidimBatchFormer(batch_axes, batch_axes_postop)

    args = deep_map(batch_former.to_batched, args, (torch.Tensor, np.ndarray))
    kwargs = deep_map(batch_former.to_batched, kwargs, (torch.Tensor, np.ndarray))
    ret_vals = func(*args, **kwargs)
    ret_vals = deep_map(batch_former.to_multidim, ret_vals, (torch.Tensor, np.ndarray))
    return ret_vals


class VirtualVectorizingWrapper(object):
    def __init__(self, func):
        self.func = func
        self.to_list = lambda xs: [x for x in xs]

    def _array_list2batch(self, xlist: List[Union[_ARRAY, Any]]) -> Union[_ARRAY, Any]:
        if isinstance(xlist[0], torch.Tensor):
            return torch.stack(xlist)
        elif isinstance(xlist[0], np.ndarray):
            return np.stack(xlist)
        elif isinstance(xlist[0], (int, float)):
            return np.array(xlist)
        else:
            raise xlist

    def _peak_batch_size(self, args_collection):
        batchsize_list = []

        def _get_batchsize(x, _):
            nonlocal batchsize_list
            if isinstance(x, (torch.Tensor, np.ndarray)):
                batch_size = x.shape[0]
                batchsize_list.append(batch_size)
            return x

        deep_apply(_get_batchsize, args_collection)
        if len(batchsize_list) == 0:
            # indicate there is no arrays
            return None
        elif len(batchsize_list) > 1 and len(set(batchsize_list)) != 1:
            raise RuntimeError(f"The first dimensions of all arrays expected to be equally length batch dimension, "
                               f"but got unequal batch-sizes: {batchsize_list}")
        else:
            # all the batchsize are same, just return the first one
            return batchsize_list[0]

    def args_iter(self, *args, **kwargs):
        batch_size = self._peak_batch_size([args, kwargs])
        if batch_size is None:
            yield (args, kwargs)
        else:
            for i in range(batch_size):
                args_i = deep_map(lambda xs: xs[i, ...], args, (torch.Tensor, np.ndarray))
                kwargs_i = deep_map(lambda xs: xs[i, ...], kwargs, (torch.Tensor, np.ndarray))
                yield (args_i, kwargs_i)

    def __call__(self, *args, **kwargs):
        retval_list = []
        for (args_i, kwargs_i) in self.args_iter(*args, **kwargs):
            retval = self.func(*args_i, **kwargs_i)
            retval_list.append(retval)
        retvals = forest2tree(retval_list)

        # numpy's stupid empty shape () is not recognized as np.ndarray
        # luckily, it can be recognized as (int, float) types
        retvals = deep_map(list_to_batch, retvals, list, fn_is_leaf=lambda xs: len(xs) >= 1 and isinstance(xs[0], (torch.Tensor, np.ndarray, int, float)))
        return retvals


def loop_vmap(func) -> Callable:
    """ A vamp replacement for numpy and torch, automatically lopping over the first dimensions of every
    np.ndarray and torch.Tensor then compose them together.

    Decorate function to make a function like:
        take [*some_axes] and output [*any_axes] to support multiple of input
        i.e. take [N, *some_axes] and output [N, *any_axes]
    Requirements:
        all arguments and returned value's structure must be consistent
    """
    vfunc = VirtualVectorizingWrapper(func)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        batched_retvals = vfunc(*args, **kwargs)
        return batched_retvals

    return wrapper
