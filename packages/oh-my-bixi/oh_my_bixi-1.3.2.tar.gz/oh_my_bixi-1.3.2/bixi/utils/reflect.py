import importlib
import inspect
import sys

from collections import abc
from typing import List, Any, Dict, Callable, Optional, Union, Iterable, Mapping

from omegaconf import DictConfig, OmegaConf
import hydra


def regularize_function_table(
        functions: Union[Callable, Iterable[Callable], Mapping[str, Callable]],
        underscore_or_hyphen='_'
) -> Dict[str, Callable]:
    """
    Convert a function or a list of functions to a dictionary of name to function mapping.

    Args:
        functions: A function or a collection of functions to be regularized.
        underscore_or_hyphen: Normalize the function names to use either underscores or hyphens.

    Returns:
        Dict[str, Callable]: A dictionary of name to function mapping.
    """
    if isinstance(functions, Mapping):
        name2func = functions

    else:
        # single function -> a list of function -> name to function mapping
        functions = [functions] if isinstance(functions, Callable) else functions  # Ensure it is Iterable
        name2func = {fn.__name__: fn for fn in functions}

    if underscore_or_hyphen == '-':
        name2func = {k.replace('_', '-'): v for k, v in name2func.items()}
    elif underscore_or_hyphen == '_':
        name2func = {k.replace('-', '_'): v for k, v in name2func.items()}
    else:
        raise ValueError('underscore_or_hyphen must be either "_" or "-"')

    return name2func


def extract_function_table(x: object, only_public=True) -> Dict[str, Callable]:
    """
    Return a dictionary of the method names and the corresponding functions of an object or a class.
    For a class, only staticmethod or classmethod are extracted (normal methods are unbounded).
    For an object instance, all methods are extracted (staticmethod, classmethod, and bounded normal method).

    Args:
        x (object): The object or class to extract methods from.
        only_public (bool): Whether to only include public methods (not starting with '_').
    """
    pred_only_public = (lambda k: not k.startswith('_')) if only_public else (lambda k: True)

    is_class = isinstance(x, type)
    cls = x if is_class else type(x)
    customized_name2func = {k: v for k, v in cls.__dict__.items() if pred_only_public(k)}
    if is_class:
        # Only staticmethod or classmethod is viable for a type (normal methods are unbounded)
        # Use attributes from the instance so that the methods are unwrapped
        name2func = {k: getattr(x, k) for k, v in customized_name2func.items() if
                     isinstance(v, (staticmethod, classmethod))}
    else:
        # use attributes from the instance so that the methods are bounded
        name2func = {k: getattr(x, k) for k, v in customized_name2func.items() if inspect.isfunction(v)}
    return name2func


def dynamic_import(module_path: str, attr_path: Optional[str] = None) -> Any:
    """Dynamically import a module or an attribute from a module.

    Args:
        module_path (str): The dot-separated path of the module to import.
        attr_path (str, optional): The dot-separated path of the attribute within the module to import. Defaults to None.

    Returns:
        The imported module or attribute.
    """

    def _recursive_getattr(obj, attr_path_list: list):
        attr, *remains = attr_path_list
        if not remains:
            return getattr(obj, attr)
        return _recursive_getattr(getattr(obj, attr), remains)

    try:
        # Check whether the module is already imported, import the module otherwise
        module = sys.modules.get(module_path) or importlib.import_module(module_path)

        if attr_path:
            # Retrieve the attribute from the module
            return _recursive_getattr(module, attr_path.split('.'))

    except ImportError as e:
        raise ImportError(f"Module '{module_path}' could not be imported: {e}")
    except AttributeError as e:
        raise ImportError(f"Attribute '{attr_path}' not found in module '{module_path}': {e}")

    return module


def omega_instantiate(cfg: DictConfig, *args, **kwargs) -> Any:
    """Instantiate a DictConfig for OmegaConf, similar to hydra.utils.instantiate but simpler.
    Support attributed extraction by specifying _target_ as module.path/attribute.path
    """
    target_key: str = '_target_'
    is_recursive: bool = cfg.get('_recursive_', True)
    config_args: List[Any] = cfg.get('_args_', [])

    target_path = cfg[target_key]
    if '/' in target_path:
        attribute = dynamic_import(*target_path.split('/'))
        return attribute
    else:
        factory = dynamic_import(*target_path.rsplit('.', 1))
        config_kwargs = {}
        for k, v in cfg.items():
            if k != target_key:
                if is_recursive and isinstance(v, DictConfig) and target_key in v:
                    v = omega_instantiate(v, *args, **kwargs)
                config_kwargs[k] = v
        return factory(*args, *config_args, **kwargs, **config_kwargs)


def _omegaconf_resolver_import(path: str):
    paths = path.split('/')
    assert len(paths) in {1, 2}  # either module_path or module_path/attribute_path
    module_path = paths[0]
    attr_path = paths[1] if len(paths) > 1 else None
    return dynamic_import(module_path, attr_path)


def hydra_instantiate(cfg: abc.Mapping, *args, _convert_="partial", **kwargs) -> Any:
    """Instantiate a DictConfig for Hydra, with additional resolver supports.
    Check reference: [Resolvers — OmegaConf 2.4.0.dev3 documentation]( https://omegaconf.readthedocs.io/en/latest/custom_resolvers.html#clear-resolver )
    Args:
        cfg: The configuration to instantiate. Must contain a '_target_' key.
        _convert_: str: The conversion mode for hydra.utils.instantiate.
            use "partial" to convert only ListConfig/DictConfig args to list/dict
    """
    resolvers = {
        'bixi.import': _omegaconf_resolver_import
    }
    for name, fn in resolvers.items():
        if not OmegaConf.has_resolver(name):
            OmegaConf.register_new_resolver(name, fn)
    obj = hydra.utils.instantiate(cfg, *args, _convert_=_convert_, **kwargs)
    return obj
