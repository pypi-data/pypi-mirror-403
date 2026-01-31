import collections
import concurrent.futures
import hashlib
import random
import re
import os
from copy import deepcopy
from typing import Sequence, Callable, Optional, Any, Dict
import unicodedata

from bixi.utils.reflect import dynamic_import


def slugify(value: str, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')


def seed_all(seed: int, is_deterministic: bool = False):
    """Seed everything

    Args:
        seed: seed value
        is_deterministic: whether to ensure deterministic CUDA behavior in the cost of computing efficiency
    """

    def _import_or_none(package: str):
        try:
            return dynamic_import(package)
        except Exception:
            return None

    random.seed(seed)
    numpy = _import_or_none('numpy')
    if numpy is not None:
        numpy.random.seed(seed)
    torch = _import_or_none('torch')
    if torch is not None:
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        if is_deterministic and torch is not None:
            torch.backends.cudnn.deterministic = True


class RegexMatchingSet(object):
    """A set-like object that matches strings against a list of regular expressions."""

    def __init__(self, expressions: Sequence[str]):
        """Initializes REMatchingSet with a list of regular expressions.

        Args:
            expressions (Sequence[str]): A sequence of regular expression strings.
        """
        pattern_composed = '|'.join([f"({expr})" for expr in expressions])
        self.re_pattern = re.compile(pattern_composed)
        self._raw_expressions = expressions

    def __contains__(self, identifier: str) -> bool:
        mo = self.re_pattern.fullmatch(identifier)
        return mo is not None

    def __repr__(self) -> str:
        return f"REMatchingSet{{{self.re_pattern.pattern}}}"


class LRU(collections.OrderedDict):
    """Limit size, evicting the least recently looked-up key when full.

    This class extends `collections.OrderedDict` to implement a Least Recently Used (LRU) cache.
    """

    def __init__(self, max_size=128, *args, **kwargs):
        """Initializes the LRU cache with a specified maximum size.

        Args:
            max_size (int): The maximum size of the cache. Defaults to 128.
        """
        self.max_size = max_size
        super().__init__(*args, **kwargs)

    def __getitem__(self, key):
        value = super().__getitem__(key)
        self.move_to_end(key)
        return value

    def __setitem__(self, key, value):
        if key in self:
            self.move_to_end(key)
        super().__setitem__(key, value)
        if len(self) > self.max_size:
            oldest = next(iter(self))
            del self[oldest]


class CachedRandomAccess(collections.UserDict):
    """A dictionary interface for any random access mapping with caching.

    This class provides a dictionary-like interface for accessing elements
    using a provided function, with optional caching (LRU) to improve performance
    for repeated accesses.
    """

    def __init__(self, fn_access: Callable, max_size: int = -1):
        """Initializes the CachedRandomAccess with a function and optional cache size.

        Args:
            fn_access (Callable): A function that takes an index and returns the corresponding element.
            max_size (int): The maximum size of the cache. If -1, caching is disabled. Defaults to -1.
        """
        super().__init__()
        if max_size > 0:
            self.data = LRU(max_size=max_size)
        self.fn_access = fn_access

    def __getitem__(self, key):
        if key in self.data:
            return self.data[key]
        else:
            elem = self.fn_access(key)
            self.data[key] = elem
            return elem


def salted_seed(seed: int, salt: str, num_digits: Optional[int] = None) -> int:
    """Generate a salted seed using a hash function.
    Args:
        seed (int): The seed value.
        salt (str): The salt string.
        num_digits (Optional[int], optional): The number of digits to return. Defaults to all digits.
    """
    # Convert the seed to a string and concatenate with the salt
    seed_str = str(seed) + salt

    # Create a SHA-256 hash of the concatenated string
    hash_obj = hashlib.sha256(seed_str.encode())

    # Convert the hash to an integer and return it
    seed = int(hash_obj.hexdigest(), 16)

    if num_digits is not None:
        seed = seed % (10 ** num_digits)

    return seed


class AsyncExecutor:
    def __init__(self, max_workers=None):
        self._max_workers = max_workers
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self._futures = set()  # Track all submitted tasks

    def submit(self, fn: Callable, *args, _is_deepcopy_args: bool = True, **kwargs):
        """Submit a function to the executor.
        Args:
            fn (Callable): The function to execute
            _is_deepcopy_args: Whether to capture the values (deepcopy) of the arguments. Default to True to keep
                consistency between normal blocking execution and asynchronous execution. Turn off to avoid copying
                overhead when you are sure that the arguments are not mutable.
        Returns:
            concurrent.futures.Future: The future object representing the execution of the function
        """
        if _is_deepcopy_args:
            args = deepcopy(args)
            kwargs = deepcopy(kwargs)
        future = self._executor.submit(fn, *args, **kwargs)
        self._futures.add(future)
        future.add_done_callback(lambda f: self._futures.discard(f))  # Auto-remove completed futures
        return future

    def wait_all(self, timeout=None):
        """Wait for all pending tasks to complete.

        Args:
            timeout (float, optional): The maximum number of seconds to wait. If None, wait indefinitely.

        Returns:
            tuple: A tuple containing two sets: (done_futures, not_done_futures)
        """
        futures_to_wait = set(self._futures)  # Create a copy of the set
        if not futures_to_wait:
            return set(), set()

        return concurrent.futures.wait(futures_to_wait, timeout=timeout)

    def shutdown(self, wait=True):
        self._executor.shutdown(wait=wait)
        self._futures.clear()

    def __del__(self):
        self.shutdown(wait=True)


def wandb_resumable_init(
    wandb_step: Optional[int] = None,
    wandb_id: Optional[str] = None,
    wandb_project: Optional[str] = None,
    wandb_name: Optional[str] = None,
    wandb_group: Optional[str] = None,
    wandb_config: Optional[Dict[str, Any]] = None,
    rewind_mode: bool = False,
):
    """
    Initialize a W&B run with consistent semantics across:
      - online resume (non-rewind)
      - online rewind (resume_from)
      - offline logging (segment + append-at-sync-time)

    Why this helper exists
    ----------------------
    W&B has two distinct "continue a run" mechanisms:
      1) resume=... with id=...
         - Standard resume: continues from the last logged step if the run exists.
         - Options include "must", "allow", "never", "auto".
         - Docs: resume options and behavior are described in W&B "Resume a run" and init() reference.
      2) resume_from="RUN_ID?_step=K"
         - Rewind: truncates history at step K and continues logging from there.
         - This feature is gated/private preview and may be disabled on your deployment.

    Offline mode considerations
    ---------------------------
    In offline mode (WANDB_MODE=offline / dryrun), W&B saves logs locally and later you upload via `wandb sync`.
    In practice, users commonly see that `resume` is ignored in offline mode, so we avoid relying on it.
    If you need "one logical run" across multiple offline segments, the recommended approach is:
      - Log each segment offline with the same `wandb_id` (run id).
      - Later, upload segments using `wandb sync --append --id <wandb_id> <path>`.
        (See `wandb sync --append` and `wandb sync --id` CLI options.)

    How `wandb_step` is interpreted
    -----------------------------------
    - wandb_step is None:
        Evaluation/attach-to-run intent.
        - Online: use resume="must" (fail if the run id does not exist).
        - Offline: cannot truly attach to a remote run while offline; we start an offline segment
          with the given id (no resume flags), intended to be appended during `wandb sync`.

    - wandb_step <= 0:
        New run intent.
        - Always start a new run (no resume flags).
        - If wandb_id is None, we generate a new id so callers can checkpoint it.

    - wandb_step > 0:
        Training resumption intent.
        - Online + rewind_mode=True: use resume_from=f"{wandb_id}?_step={wandb_step}" (rewind).
          This will fail fast if rewind is not enabled on your deployment.
        - Online + rewind_mode=False: use resume="allow" (resume if exists; else create with that id).
        - Offline: start a new offline segment with the same id (no resume flags).
          Merge later with `wandb sync --append --id`.

        Note that rewind_mode is only accessible when online, as rewind is a server-side operation.
        wandb has a offical plan to support offline rewind in the future, but as of 2026-01 it is 
        not available.

    Parameters passed to wandb.init
    -------------------------------
    We pass only one of {resume, resume_from} because W&B disallows combining them.

    Args
    ----
    wandb_step (Optional[int]): Current wandb_step value, or None for evaluation attach.
    wandb_id (Optional[str]): W&B run ID. Required for attach/resume; generated if absent for new runs.
    wandb_project (Optional[str]): W&B project name.
    wandb_name (Optional[str]): W&B run name.
    wandb_group (Optional[str]): W&B group name.
    wandb_config (Optional[Dict[str, Any]]): W&B config dictionary.
    rewind_mode (bool): Whether to use rewind (resume_from) when resuming.

    Returns
    -------
    wandb.Run

    Raises
    ------
    ValueError / RuntimeError with an actionable message if:
      - wandb_id is missing when required
      - rewind_mode is requested while offline
      - wandb.init fails (including "rewind not enabled" server errors)
    """
    try:
        import wandb
        from wandb.errors import CommError, UsageError
    except ImportError as e:
        raise ImportError("wandb is not installed. Please install wandb to use this function.") from e

    # Infer offline-ish mode from env. (Caller may also explicitly set wandb.init(mode=...) elsewhere;
    # this helper does not override that.)
    env_mode = (os.environ.get("WANDB_MODE") or "").strip().lower()
    is_offline = env_mode in {"offline", "dryrun"}

    # Validate / generate wandb_id when appropriate
    if wandb_step is None:
        # Evaluation attach intent: requires a known run id
        if not wandb_id:
            raise ValueError(
                "wandb_resumable_init: wandb_step=None (evaluation attach) requires wandb_id."
            )
    elif wandb_step <= 0:
        # New run: generate id if absent so it can be stored in checkpoints
        if not wandb_id:
            wandb_id = wandb.util.generate_id()
    else:
        # wandb_step > 0 : resume intent
        if not wandb_id:
            raise ValueError(
                "wandb_resumable_init: wandb_step>0 (resume) requires wandb_id."
            )

    # Decide resume strategy
    resume: Optional[str] = None
    resume_from: Optional[str] = None

    if wandb_step is None:
        if is_offline:
            # Offline cannot truly "attach" to a remote run; create an offline segment to be appended at sync time.
            resume = None
        else:
            resume = "must"

    elif wandb_step <= 0:
        # New run
        resume = None
        resume_from = None

    else:
        # wandb_step > 0
        if rewind_mode:
            if is_offline:
                raise RuntimeError(
                    "wandb_resumable_init: rewind_mode=True requested but WANDB_MODE indicates offline/dryrun. "
                    "Rewind (resume_from) is server-side; run online or disable rewind_mode."
                )
            resume_from = f"{wandb_id}?_step={int(wandb_step)}"
        else:
            if is_offline:
                # Offline: do not rely on resume (often ignored); create a new offline segment with the same id.
                resume = None
            else:
                resume = "allow"

    # Build init kwargs, excluding None values.
    init_kwargs: Dict[str, Any] = {}
    if wandb_project is not None:
        init_kwargs["project"] = wandb_project
    if wandb_name is not None:
        init_kwargs["name"] = wandb_name
    if wandb_group is not None:
        init_kwargs["group"] = wandb_group
    if wandb_config is not None:
        init_kwargs["config"] = wandb_config

    # If using resume_from, it already encodes the source run id; we don't need to pass id.
    if resume_from is not None:
        init_kwargs["resume_from"] = resume_from
    else:
        init_kwargs["id"] = wandb_id
        if resume is not None:
            init_kwargs["resume"] = resume

    # Single init call; fail fast with clean diagnostics
    try:
        return wandb.init(**init_kwargs)
    except CommError as e:
        msg = str(e)
        if rewind_mode and ("rewind" in msg.lower() or "rewinding runs is not enabled" in msg.lower()):
            raise RuntimeError(
                "wandb_resumable_init: rewind requested (resume_from) but the server rejected it.\n"
                "This typically means your W&B deployment/project does not have 'rewind' enabled.\n"
                "Fix: set rewind_mode=False (use normal resume) or ask your W&B admins/support to enable rewind."
            ) from e
        raise RuntimeError(
            "wandb_resumable_init: communication error during wandb.init.\n"
            f"  WANDB_MODE={env_mode or '(unset)'}\n"
            f"  wandb_step={wandb_step}\n"
            f"  rewind_mode={rewind_mode}\n"
            f"  init_kwargs_keys={sorted(init_kwargs.keys())}"
        ) from e
    except UsageError as e:
        raise RuntimeError(
            "wandb_resumable_init: invalid wandb.init arguments.\n"
            f"  WANDB_MODE={env_mode or '(unset)'}\n"
            f"  wandb_step={wandb_step}\n"
            f"  rewind_mode={rewind_mode}\n"
            f"  init_kwargs_keys={sorted(init_kwargs.keys())}"
        ) from e


# =========================================================
# Global thread pool
# =========================================================
_global_executor = None
_DEFAULT_POOLSIZE = 8


def get_global_executor(max_workers=None) -> AsyncExecutor:
    global _global_executor, _DEFAULT_POOLSIZE
    if max_workers is None:
        max_workers = _DEFAULT_POOLSIZE
    if _global_executor is None:
        _global_executor = AsyncExecutor(max_workers=max_workers)
    return _global_executor
