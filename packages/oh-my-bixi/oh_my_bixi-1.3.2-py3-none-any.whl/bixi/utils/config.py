import inspect
import uuid
from contextlib import contextmanager
from dataclasses import is_dataclass
from pathlib import Path
from typing import Sequence, Optional, Union, Type, TypeVar, overload

import hydra
from hydra import compose, initialize, initialize_config_dir
from hydra.core.config_store import ConfigStore
from hydra.core.global_hydra import GlobalHydra
from omegaconf import DictConfig

T = TypeVar("T")


def _clear_hydra() -> None:
    # Allow multiple compositions in the same process
    try:
        GlobalHydra.instance().clear()
    except Exception:
        pass


def _supports_version_base() -> bool:
    # Feature-detect instead of version parsing
    return "version_base" in inspect.signature(initialize).parameters


@contextmanager
def _init_ctx(config_dir: Optional[str] = None):
    """
    Context manager that initializes Hydra with or without version_base,
    depending on the installed Hydra version.
    """
    if _supports_version_base():
        if config_dir is None:
            with initialize(version_base=None):
                yield
        else:
            with initialize_config_dir(config_dir=config_dir, version_base=None):
                yield
    else:
        if config_dir is None:
            with initialize():
                yield
        else:
            with initialize_config_dir(config_dir=config_dir):
                yield


def _store_structured_node(node: object, name_hint: Optional[str] = None) -> str:
    """
    Store a dataclass type or instance in the ConfigStore and return a unique name.
    """
    cs = ConfigStore.instance()
    base = name_hint or getattr(node, "__name__", node.__class__.__name__)
    unique_name = f"{base}_{uuid.uuid4().hex[:8]}"
    cs.store(name=unique_name, node=node)
    return unique_name


PathLike = Union[str, Path]


@overload
def compose_from_source(
    source: PathLike, overrides: Sequence[str] = ...
) -> DictConfig: ...
@overload
def compose_from_source(
    source: Type[T], overrides: Sequence[str] = ...
) -> DictConfig: ...
@overload
def compose_from_source(source: T, overrides: Sequence[str] = ...) -> DictConfig: ...


def compose_from_source(
    source: Union[PathLike, Type[T], T],
    overrides: Sequence[str] = (),
) -> DictConfig:
    """
    Compose a Hydra DictConfig from:
      - a YAML file path (source: str | Path),
      - a dataclass type (source: Type[T]),
      - a dataclass instance (source: T).

    Args:
        source: The source of the configuration.
        overrides: The overrides to apply to the configuration.

    Returns:
        A Hydra DictConfig.

    Raises:
        TypeError: If the source is not a path, a dataclass type, or a dataclass instance.
    """
    _clear_hydra()
    ov = list(overrides)

    # Case 1: YAML path
    if isinstance(source, (str, Path)):
        p = Path(source).resolve()
        config_dir = str(p.parent)
        config_name = p.stem  # no file extension
        with _init_ctx(config_dir=config_dir):
            return compose(config_name=config_name, overrides=ov)

    # Case 2/3: dataclass type or instance
    if not is_dataclass(source):
        raise TypeError(
            "source must be a path, a dataclass type, or a dataclass instance"
        )

    name = _store_structured_node(source)
    with _init_ctx(config_dir=None):
        return compose(config_name=name, overrides=ov)
