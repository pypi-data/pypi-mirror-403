import collections.abc
import functools
import re
import typing
from typing import Union, List, Sequence, Callable

import numpy as np
import torch
from torch import nn

from bixi.utils.collection_op import deep_apply, deep_map


def numpy_torch_compatible(*,
                           _implementation: str = 'numpy',
                           _is_output_conversion=True):
    """
    Decorator to make a function compatible with both NumPy and PyTorch tensors.

    This decorator ensures that the input arguments and return values of the decorated function are either all
    NumPy arrays or all PyTorch tensors, based on the specified implementation. It converts the input arguments
    to the specified type before calling the function and converts the return values back to the original type
    if the `_is_output_conversion` option is enabled.

    Args:
        _implementation (str): Specifies the target implementation, either 'numpy' or 'torch'.
        _is_output_conversion (bool): If True, ensures that the return values are converted back to the original type.

    Returns:
        Callable: The decorated function with type compatibility for NumPy and PyTorch.
    """

    def _type_detecting(args, kwargs):
        is_exist_ndarray = False
        is_exist_Tensor = False

        def _detector(x, path):
            nonlocal is_exist_ndarray, is_exist_Tensor
            if isinstance(x, np.ndarray):
                is_exist_ndarray = True
            if isinstance(x, torch.Tensor):
                is_exist_Tensor = True

        deep_apply(func=_detector, tree=args)
        deep_apply(func=_detector, tree=kwargs)

        return is_exist_ndarray, is_exist_Tensor

    def _torch_comply_numpy(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            _, is_exist_Tensor = _type_detecting(args, kwargs)
            if is_exist_Tensor:
                args = deep_map(torch_to_numpy, args, torch.Tensor)
                kwargs = deep_map(torch_to_numpy, kwargs, torch.Tensor)
            ret_vals = func(*args, **kwargs)
            if _is_output_conversion and is_exist_Tensor:
                ret_vals = deep_map(numpy_to_torch, ret_vals, np.ndarray)
            return ret_vals

        return wrapper

    def _numpy_comply_torch(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            is_exist_ndarray, _ = _type_detecting(args, kwargs)
            if is_exist_ndarray:
                args = deep_map(numpy_to_torch, args, np.ndarray)
                kwargs = deep_map(numpy_to_torch, kwargs, np.ndarray)
            ret_vals = func(*args, **kwargs)
            if _is_output_conversion and is_exist_ndarray:
                ret_vals = deep_map(torch_to_numpy, ret_vals, torch.Tensor)
            return ret_vals

        return wrapper

    assert _implementation in {'numpy', 'torch'}
    if _implementation == 'numpy':
        return _torch_comply_numpy
    elif _implementation == 'torch':
        return _numpy_comply_torch
    else:
        raise ValueError("Invalid implementation specified. Choose either 'numpy' or 'torch'.")


class _NoOpContext:
    def __enter__(self): pass

    def __exit__(self, type, value, traceback): pass


def cast_dtype_inside(src_dtypes: Sequence[torch.dtype], dst_dtype: torch.dtype, *,
                      return_dtype: torch.dtype = None,
                      context_manager: typing.ContextManager = _NoOpContext()) -> Callable:
    """
    Decorator that automatically casts any torch.Tensor arguments from src_dtypes to dst_dtype
    before calling the function, and converts the tensor outputs from dst_dtype back to the original dtype.
    This can be useful for ensuring that the function operates on tensors of a specific dtype.

    Args:
        src_dtypes: A sequence of dtypes that will be cast to dst_dtype.
        dst_dtype: The dtype to cast to inside the function. i.e. function will work on this dtype.
        return_dtype: The dtype to which the output tensors will be cast back.
            If None, the first input dtype will be used.
        context_manager: A context manager that will be used during the function execution.
            e.g. torch.autocast(device_type='cuda', enabled=False)
    """
    src_dtypes = set(src_dtypes)

    def decorator(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal return_dtype
            _return_dtype = return_dtype

            def _cast_input(x: torch.Tensor):
                nonlocal _return_dtype, src_dtypes
                if x.dtype in src_dtypes:
                    if _return_dtype is None:
                        _return_dtype = x.dtype
                    return x.to(dst_dtype)
                return x

            def _cast_output(x: torch.Tensor):
                if _return_dtype is not None and x.dtype != _return_dtype:
                    return x.to(_return_dtype)
                return x

            with context_manager:
                args_cast = deep_map(_cast_input, args, torch.Tensor)
                kwargs_cast = deep_map(_cast_input, kwargs, torch.Tensor)
                result = func(*args_cast, **kwargs_cast)
                result_cast = deep_map(_cast_output, result, torch.Tensor)

            return result_cast

        return wrapper

    return decorator


bf16_to_fp32_decorator = cast_dtype_inside(
    src_dtypes=[torch.bfloat16],
    dst_dtype=torch.float32,
    context_manager=torch.autocast(device_type='cuda', enabled=False)
)
"""
A workaround patch some operations that does not support bfloat16. 
Simply decorate them and their input tensors will be casted to fp32 automatically.
"""


def cast_dtype_inside_module(*modules: nn.Module,
                             src_types: Sequence[torch.dtype],
                             dst_type: torch.dtype) -> tuple:
    """
    Modify modules' forward function to cast input tensors from src_types to dst_type, and cast them back to one of src_types.
    This is useful for patching existing modules without modifying their source code.

    Returns:
        modules (Tuple[nn.Module ...]) that forward function be decorated.
    """
    no_autocast_context = torch.autocast(device_type='cuda', enabled=False)
    dtype_caster = cast_dtype_inside(src_dtypes=src_types, dst_dtype=dst_type, context_manager=no_autocast_context)
    for m in modules:
        if isinstance(m, nn.Module):
            m.forward = dtype_caster(m.forward)
    return modules


def torch_to_numpy(x: torch.Tensor):
    if isinstance(x, torch.Tensor):
        if x.requires_grad:
            x = x.detach()

        if x.get_device() != -1:
            x = x.cpu()  # make sure move to cpu

        # transform un-normal types into the highest precision (usually mixed precision like bf16, tf32)
        if torch.is_floating_point(x) and not (x.dtype == torch.float32 or x.dtype == torch.float64):
            x = x.to(torch.float64)

        return x.numpy()
    else:
        return x


def numpy_to_torch(x: np.ndarray):
    if isinstance(x, np.ndarray):
        return torch.from_numpy(x)
    else:
        return x


def to_numpy_vector(x: Union[torch.Tensor, np.ndarray, int, float]):
    """
    Convert array/tensor/int/float to (-1) shape number vector
    """
    if isinstance(x, torch.Tensor):
        return torch_to_numpy(x).astype(np.float64).reshape(-1)
    elif isinstance(x, np.ndarray):
        return x.astype(np.float64).reshape(-1)
    elif isinstance(x, (int, float)):
        return np.array([x], dtype=np.float64).reshape(-1)
    else:
        raise RuntimeError(f'Unsupported type {type(x)}')


def to_python_number(x: Union[torch.Tensor, np.ndarray, int, float]):
    if isinstance(x, torch.Tensor):
        x = x.detach().cpu().numpy().reshape(-1).item()
        return x
    elif isinstance(x, np.ndarray):
        x = x.reshape(-1).item()
        return x
    elif isinstance(x, (int, float)):
        return x
    else:
        raise RuntimeError(f'Unsupported type {type(x)}')


def batch_to_list(x: Union[torch.Tensor, np.ndarray, str, bytes]) -> List[Union[torch.Tensor, np.ndarray, str, bytes]]:
    """
    Convert a batch of samples representation into a list of samples
    """
    if isinstance(x, (torch.Tensor, np.ndarray)):
        batch_size = x.shape[0]
        xlist = [x[i, ...] for i in range(batch_size)]
    elif isinstance(x, (str, bytes)):  # tackle special case: list('str') -> ['s', 't', 'r'] is not what we expected
        return x
    elif isinstance(x, collections.abc.Sequence):  # list, tuple, ...
        xlist = list(x)
    else:
        raise RuntimeError(f'Unsupported type {type(x)}')
    return xlist


def list_to_batch(xlist: List[Union[torch.Tensor, np.ndarray, int, float]]) -> Union[torch.Tensor, np.ndarray]:
    """
    Convert a list of arrays/tensors (have same shape) or Numbers to a batch with new axis at front position
    """
    if isinstance(xlist[0], torch.Tensor):
        return torch.stack(xlist)
    elif isinstance(xlist[0], np.ndarray):
        return np.stack(xlist)
    elif isinstance(xlist[0], (int, float)):
        return np.array(xlist)
    else:
        raise RuntimeError(f'Unsupported type {type(xlist)}')


def regularize_batched_tensor(
        x: Union[torch.Tensor, Sequence[float], Sequence[int], float, int],
        batch_size: int,
        dtype=torch.float32,
        device=None
):
    """ Reprocess float/int/sequence into batched tensor. It replicate [...] into [B, ...]
    Examples:
        [] -> [B,]
        [1] -> [B, 1]
        [16, 16] -> [B, 16, 16]
    """
    # Transform into tensor
    if not isinstance(x, torch.Tensor):
        x = torch.tensor(x, dtype=dtype, device=device)

    # Add batch dimension and replicate
    x = x.unsqueeze(0)
    x = x.repeat(batch_size, *([1] * (x.ndim - 1)))

    return x


def extract_state_dict(state_dict: dict, *, prefix: str = None, is_rename_matched=True) -> dict:
    """
    :param state_dict: a dict represented in Dict[str, Union[torch.Tensor, ...]]
    :param prefix: a str to match any key start with the prefix in dict
    :param is_rename_matched: if True, keys in the returned state_dict will remove the prefix
    :return: a subset of the input state_dict
    """
    pattern = re.compile(rf"^{prefix}(?P<content>.+)$")
    new_state_dict = {}
    for key in state_dict:
        m = pattern.fullmatch(key)
        if m is not None:
            if is_rename_matched:
                new_key = m.groupdict()['content']
            else:
                new_key = key
            new_state_dict[new_key] = state_dict[key]
    return new_state_dict
