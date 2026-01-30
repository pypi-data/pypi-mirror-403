import dataclasses
from typing import Sequence, Callable, Any, Union, Tuple, Optional, List, Mapping, Iterable

import collections.abc
from copy import deepcopy


def deep_update(base: collections.abc.MutableMapping,
                updator: collections.abc.Mapping) -> collections.abc.MutableMapping:
    updated = deepcopy(base)
    for k, v in updator.items():
        if (isinstance(base.get(k, None), collections.abc.MutableMapping)
                and isinstance(v, collections.abc.Mapping)):
            updated[k] = deep_update(base[k], v)
        else:
            updated[k] = v
    return updated


def _default_is_leaf(tree):
    if isinstance(tree, str):  # special case: normally we don't consider str as collection, though it is a Sequence
        return True
    elif isinstance(tree, (collections.abc.Mapping, collections.abc.Set, collections.abc.Sequence)):
        return False
    else:
        return True


def _is_namedtuple(obj: object) -> bool:
    # https://github.com/pytorch/pytorch/blob/v1.8.1/torch/nn/parallel/scatter_gather.py#L4-L8
    return isinstance(obj, tuple) and hasattr(obj, "_asdict") and hasattr(obj, "_fields")


def _is_dataclass_instance(obj: object) -> bool:
    # https://docs.python.org/3/library/dataclasses.html#module-level-decorators-classes-and-functions
    return dataclasses.is_dataclass(obj) and not isinstance(obj, type)


_TreeType = Union[collections.abc.Mapping, collections.abc.Sequence]


def deep_map(
        function: Callable[[Any], Any],
        data: _TreeType,
        dtype: Union[type, Tuple[type, ...]],
        *,
        wrong_dtype: Optional[Union[type, Tuple[type, ...]]] = None,
        is_include_none: bool = True,
        fn_is_leaf: Optional[Callable[[Any], bool]] = None
) -> _TreeType:
    """
    Recursively applies a function to all elements of a certain dtype.

    Args:
        data: The collection to apply the function to.
        dtype: The given function will be applied to all elements of this dtype.
        function: The function to apply.
        wrong_dtype: The given function won't be applied if this type is specified and the given collections
            is of the `wrong_dtype` even if it is of type `dtype`.
        is_include_none: Whether to include an element if the output of `function` is `None`.
        fn_is_leaf: User-defined terminator in advance, used when the data is matched with dtype.

    Returns:
        The collection with the function applied to all elements of the specified dtype.


    Note:
        The matching rules (and orders) are:
        1. if matched with wrong_dtype -> Identical data (not applied)
        2. if not matched with dtype -> Identical data (not applied)
        3. if matched with dtype
            3.1 fn_is_leaf is None -> Apply function
            3.2 fn_is_leaf is not None, and it returns True -> Apply function
                fn_is_leaf is not None, and it returns False -> Identical data (not applied)

    """
    if isinstance(data, dtype) and (fn_is_leaf is None or fn_is_leaf(data)) \
            and (wrong_dtype is None or not isinstance(data, wrong_dtype)):
        return function(data)

    elem_type = type(data)
    if isinstance(data, collections.abc.Mapping):
        out = []
        for k, v in data.items():
            v = deep_map(function, v, dtype, wrong_dtype=wrong_dtype, is_include_none=is_include_none, fn_is_leaf=fn_is_leaf)
            if is_include_none or v is not None:
                out.append((k, v))
        if isinstance(data, collections.defaultdict):
            return elem_type(data.default_factory, collections.OrderedDict(out))
        return elem_type(out)

    is_namedtuple = _is_namedtuple(data)
    is_sequence = isinstance(data, collections.abc.Sequence) and not isinstance(data, (str, bytes))
    if is_namedtuple or is_sequence:
        out = []
        for d in data:
            v = deep_map(function, d, dtype, wrong_dtype=wrong_dtype, is_include_none=is_include_none, fn_is_leaf=fn_is_leaf)
            if is_include_none or v is None:
                out.append(v)
        return elem_type(*out) if is_namedtuple else elem_type(out)

    # data is neither of dtype, nor collection, then leave it without any processing
    return data


def deep_apply(
        func: Callable[[Any, List[str]], Any],
        tree: _TreeType,
        fn_is_leaf=_default_is_leaf
) -> None:
    """
    Traverse through `tree` (a single leaf or a collection composed by tuple/dict/list),
    any elements in list/tuple/dict or the value of non-collections' type will be replaced by func(x).

    Args:
        func: A function that takes two parameters as input (leaf_node: Any, path_to_leaf_node: List[str]) -> new_leaf.
        tree: The tree structure to traverse.
        fn_is_leaf: A function to determine if a node is a leaf. Defaults to _default_is_leaf.
    """

    def _traverse(subtree, path):
        nonlocal func, fn_is_leaf
        subtree_type = type(subtree)
        if isinstance(subtree, collections.abc.Mapping):
            for key, value in subtree.items():
                _dfs(value, path=path + [(subtree_type, key)])
        elif isinstance(subtree, collections.abc.Set):
            for idx, elem in enumerate(subtree):
                _dfs(elem, path=path + [(subtree_type, idx)])
        elif isinstance(subtree, collections.abc.Sequence):  # use Sequence, not Iterable for semantic correctness
            for idx, elem in enumerate(subtree):
                _dfs(elem, path=path + [(subtree_type, idx)])
        else:
            raise RuntimeError(f"Unsupported collection type: {subtree_type}")

    def _dfs(subtree, path):
        nonlocal func, fn_is_leaf
        if fn_is_leaf(subtree):
            elem = subtree
            elem_result = func(elem, path)
            return elem_result
        else:
            tree_transformed = _traverse(subtree, path=path)
            return tree_transformed

    transformed_tree = _dfs(tree, path=[])
    return transformed_tree


def flatten_dict(d: dict, sep: str = '.') -> dict:
    """Flattens a nested dictionary, using a specified separator for keys.

    Args:
        d (collections.abc.Mapping): The dictionary to flatten.
        sep (str): The separator to use for concatenating keys. Defaults to '.'.

    Returns:
        collections.abc.Mapping: A flattened dictionary with concatenated keys.

    Example:
        >>> flatten_dict({
        ...     'name': 'Steven',
        ...     'candy': [(1, 2, 5)],
        ...     'infos': {'age': 20}
        ... })
        {
            'name': 'Steven',
            'candy': [(1, 2, 5)],
            'infos.age': 20
        }
    """

    def _flatten(d: collections.abc.Mapping, parent_key='') -> List[Tuple[str, Any]]:
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, collections.abc.Mapping):
                items.extend(_flatten(v, new_key))
            else:
                items.append((new_key, v))
        return items

    elem_type = type(d)
    return elem_type(_flatten(d))


_STRING_CALSSES = (str, bytes)


def _fn_not_tree(x):
    is_tree = \
        isinstance(x, collections.abc.Mapping) or \
        isinstance(x, collections.abc.Sequence) and not isinstance(x, _STRING_CALSSES)
    return not is_tree


def forest2tree(
        forest: Sequence[_TreeType],
        *,
        fn_is_leaf: Callable[[Any], bool] = _fn_not_tree,
        fn_combine_leaves: Callable[[Sequence[_TreeType]], _TreeType] = list
) -> _TreeType:
    """
    Combine a list of trees into a single tree with combined leaves.

    Args:
        forest (Sequence[Any]): A list of trees (nested structures) to combine.
        fn_is_leaf (Callable[[Any], bool]): Function to determine if a node is a leaf. Defaults to _fn_not_tree.
        fn_combine_leaves (Callable[[Sequence[Any]], Any]): Function to combine leaves. Defaults to list.

    Returns:
        Any: A single tree with combined leaves.

    Raises:
        RuntimeError: If the forest is empty or if the trees do not have identical structures.
        TypeError: If the input type is not supported.
    """
    if len(forest) == 0:
        raise RuntimeError("The forest is empty. Cannot combine an empty sequence of trees.")

    tree = forest[0]
    TreeType = type(tree)

    # reach leaf, combine sequence
    if fn_is_leaf(tree) or isinstance(tree, _STRING_CALSSES):
        return fn_combine_leaves(forest)

    # if not leaf, them we assert all the trees are same type
    if not all(isinstance(t, TreeType) for t in forest):
        raise RuntimeError(f"All trees must be of type {TreeType}. Found types: {[type(t) for t in forest]}")

    if isinstance(tree, collections.abc.Mapping):
        return {key: forest2tree([d[key] for d in forest], fn_is_leaf=fn_is_leaf, fn_combine_leaves=fn_combine_leaves)
                for key in tree}

    # use Sequence instead of Iterable because array is Iterable, and dealing them is too complicated
    elif isinstance(tree, collections.abc.Sequence):
        # check to make sure that the elements have consistent size
        elem_size = len(tree)
        if not fn_is_leaf(tree) and (not all(len(c) == elem_size for c in forest)):
            # varying lengths in leaves is tolerant, but the structure lengths is unacceptable
            raise RuntimeError('Each branch in the list of trees should be of equal size')
        combined_seq = [forest2tree(t, fn_is_leaf=fn_is_leaf, fn_combine_leaves=fn_combine_leaves)
                        for t in zip(*forest)]

        # matching for namedtuple
        if isinstance(tree, tuple) and hasattr(tree, '_fields'):
            return TreeType(*combined_seq)
        else:
            return combined_seq

    raise TypeError(f"Unsupported type: {TreeType}")
