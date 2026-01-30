import functools
import inspect
import re
import os
import logging
import glob
import datetime
import sys
import uuid
import traceback
from enum import Enum
from copy import deepcopy
from dataclasses import dataclass, field, asdict
from bixi.utils.distributed import get_distributed_rank
from omegaconf import DictConfig, OmegaConf
from typing import Callable, Dict, Any, Union, Iterable, Mapping, Tuple, List, Optional, Annotated

import yaml
import typer

from bixi.utils.collection_op import flatten_dict
from bixi.utils.config import compose_from_source
from bixi.utils.record import initialize_logging
from bixi.utils.reflect import extract_function_table, regularize_function_table


@dataclass
class Workspace:
    """Data structure of experiment state and file management.
    It is a wrapper of a directory, and all files related to the experiment should be stored in this directory.
    This directory is called a workspace, and identified by a metadata file (workspace.yaml) associated by a unique id.

    Args:
        prefix: (mandatory) directory path for storing the app running workspaces (i.e. many similar workspaces)
        name: (mandatory) name for an experiment in a prefix(i.e. a single unique experiment in a prefix)

    Note:
        - `id` is unique for every experiment workspace. And `prefix/name` are suggested to be unique.
        - use `ws.relpath(...)` to get path for saving.
        - use `ws[...]` to get or set metadata.

    To create a workspace:
        1. Create a Workspace object with prefix and name
        2. (Optional) Set metadata using `ws[...]`
        3. (Optional) Call `ws.setup_workspace()` to create the workspace directory and save metadata

    To reload a workspace:
        1. Call `Workspace.restore_workspace(...)` to search for the workspace directory and load metadata
            Note: It is okay to change the prefix or name or workspace location, but the id must be the same.
            Note: Even if you change workspace location, the prefix and name does not change.
    """

    # ==== Mandatory Fields ========================================================
    prefix: str
    name: str
    id: str = field(default=None)  # will be generated in __post_init__, only prefix and name must be given in creation
    # ==============================================================================

    # ==== (Auto-generated) Private Fields =========================================
    _metadata_filepath: str = field(default=None)
    _rootpath: str = field(default=None)
    _metadata: dict = field(default_factory=dict)
    # ==============================================================================

    ID_NUM_DIGITS = 6
    """ ID does not need to be too long, so we truncate it for convenience.
    It won't be an issue since we use timestamp as prefix, and it will be unique if you don't create
    too many workspaces at a single timestamp, and truncated UUID is enough for most of deep 
    learning experiments. If you have a very high demand for uniqueness, you can set it to 32, which
    is the default UUID4 length, and it will guarantee uniqueness.    
    """
    WORKSPACE_METADATA_FILENAME = 'bixi_workspace.yaml'
    """ The name of the metadata file that stores the workspace information.
    The folder that contains this file is a workspace root directory. If you organize your workspaces
    in a directory, it is hightly recommended to use the same name for the metadata file.
    """
    PROTECTED_METADATA_KEYS = {'id', 'prefix', 'name'}
    """The protected keys that should not be modified by the user of workspace objects."""

    def __post_init__(self):
        """Initialize newly created workspace information"""
        if self.id is None:  # only initialize when id is not set (not resuming a workspace)
            utc_timestamp_created = datetime.datetime.now(datetime.timezone.utc).timestamp()
            workspace_id = self._generate_uuid(utc_timestamp_created, num_uuid_digits=self.ID_NUM_DIGITS)
            initial_dirname = f"{workspace_id[:16]}_{self.name}"  # truncate the id to avoid too long directory name
            initial_rootpath = os.path.abspath(os.path.join(self.prefix, initial_dirname))
            initial_metadata_filepath = os.path.join(initial_rootpath, self.WORKSPACE_METADATA_FILENAME)

            self.id = workspace_id
            self._metadata['utc_timestamp_created'] = utc_timestamp_created
            self._metadata['prefix'] = self.prefix
            self._metadata['name'] = self.name
            self._metadata['id'] = self.id
            self._init_around_metadata_filepath(initial_metadata_filepath)

    def _init_around_metadata_filepath(self, metadata_filepath: str):
        """
        Infer workspace metadata filepath related attributes. This function will be called both at
        the first-time initialization and when restoring a workspace. Note that when you restore a
        workspace from changed location, the attributes will be updated to the new location except
        for the `prefix` and `name` attributes.
        """
        metadata_filepath = os.path.abspath(metadata_filepath)
        self._metadata_filepath = metadata_filepath
        self._rootpath = os.path.dirname(self._metadata_filepath)

    @property
    def rootpath(self):
        return self._rootpath

    @staticmethod
    def _generate_uuid(utc_timestamp: float, num_uuid_digits: int = None) -> str:
        """Generate a UTC time prefixed UUID string.
        Examples:
            20210910T123456Z3d651e042ce3438e8e31f18538d9566d
            20241104T033841Z52ae8ffa0d2c4861bc775c8975670139
            ^-UTC timestamp ^-UUID-v4

        Args:
            utc_timestamp: UTC timestamp in seconds since epoch
            num_uuid_digits: number of truncated digits for UUID,
                default is None, which means 32 digits, Note: UUID-v4 is always 32 digits
                If you set less than 32, it will be truncated to the specified number of digits.
                If you set higher than 32, it will be padded with 0s to 32 digits.

        Returns:
            str: a string of UTC timestamp and UUID-v4
        """
        # Field-1: Get the current UTC time, format it in the compact style
        utc_time = datetime.datetime.fromtimestamp(utc_timestamp, datetime.timezone.utc)
        utc_timestamp_str = utc_time.strftime('%Y%m%dT%H%M%S') + 'Z'

        # Field 2: UUID-v4
        uuid_hex = uuid.uuid4().hex

        if num_uuid_digits is not None:
            if num_uuid_digits <= 32:
                uuid_hex = uuid_hex[:num_uuid_digits]
            else:
                uuid_hex = uuid_hex.ljust(num_uuid_digits, '0')

        return f"{utc_timestamp_str}{uuid_hex}"

    def create_workspace(self, exist_ok: bool = False):
        """Create the workspace directory and save the metadata file.
        The workspace is designed to be either temporarily used (not persisted) or permanently used
        (persisted). Once persisted, the workspace directory and metadata file will be created.

        Args:
            exist_ok: whether to ignore if the directory already exists. Default is False.
                If True, it will skip directory creation if it already exists. This can be
                useful when you want to setup workspace in non-primary processes in distributed
                settings.
        """
        if os.path.isdir(self.rootpath) and not exist_ok:
            raise RuntimeWarning(
                f"Workspace {self.rootpath} already existed. Try to restore the workspace instead."
            )

        os.makedirs(self.rootpath, exist_ok=exist_ok)
        self._save_metadata()
        logging.info('Workspace initialized at:', self.rootpath)

    def relpath(self, *relative_paths: str):
        """Compute relative path from the workspace root path."""
        return os.path.join(self.rootpath, *relative_paths)

    def __getitem__(self, item):
        return self._metadata[item]

    def __setitem__(self, key, value):
        if key in self.PROTECTED_METADATA_KEYS:
            logging.warning(f"You are trying to set a reserved key '{key}' in workspace metadata. ")

        try:
            _ = repr(value)  # we don't care about the repr value, just check if it is serializable
        except Exception as e:
            logging.error(f"Cannot set unserializable object as workspace metadata: {e}")
            raise e
        self._metadata[key] = value  # set value instead of value_repr can keep dict structure
        self._save_metadata()

    def _save_metadata(self):
        if self.is_created:
            # Only save when the workspace is saved
            with open(self._metadata_filepath, 'w') as f:
                yaml.dump(self._metadata, f)

    @staticmethod
    def query_workspace_metadata(search_root: str = None, **requirements) -> Dict[str, dict]:
        """Search for workspaces under the `search_root` directory that satisfies requirements.

        Args:
            search_root: root directory for finding workspace file, use current working directory as the default.
            requirements: keyword argument for matching workspace, e.g.: id=..., prefix=..., name=...
                Note that field of type `str` can use regex to match, i.e. prefix=r'^vision\.cifar10\..+$'

        Returns:
            A list of workspace metadata dictionaries that satisfied the requirements.
        """

        def _filter(metadata: dict) -> bool:
            for k, v in requirements.items():
                if not v:  # ignore None or empty string
                    continue
                if k not in metadata:
                    return False
                if isinstance(v, str) and re.fullmatch(v, metadata[k]) is None:
                    return False
                elif metadata[k] != v:
                    return False
            return True

        search_root = search_root if search_root is not None else os.getcwd()
        all_filepaths = glob.glob(os.path.join(search_root, f'**/{Workspace.WORKSPACE_METADATA_FILENAME}'),
                                  recursive=True)
        filepath2metadata = {}
        for filepath in all_filepaths:
            with open(filepath, mode='r') as f:
                metadata = yaml.safe_load(f)

            if _filter(metadata):
                filepath2metadata[filepath] = metadata

        return filepath2metadata

    @staticmethod
    def restore_workspace(search_root: str = None, **workspace_queries) -> 'Workspace':
        """Search for a valid workspace and restore it. The searching result must contain a unique workspace,
        otherwise an error will be raised.
        """
        filepath2metadata = Workspace.query_workspace_metadata(search_root=search_root, **workspace_queries)
        n_found = len(filepath2metadata)
        if n_found != 1:
            raise RuntimeError(f"Invalid workspace query {workspace_queries} at searching directory {search_root}: " +
                               (f"Too many workspace metadata entries: {filepath2metadata}."
                                if n_found > 1 else "No workspace metadata entries found."))
        filepath, metadata = next(iter(filepath2metadata.items()))

        # Create an instance
        logging.info(f"Restoring workspace from {filepath}")
        ws = Workspace(prefix=metadata['prefix'], name=metadata['name'], id=metadata['id'])
        ws._init_around_metadata_filepath(filepath)
        ws._metadata = metadata
        logging.info(f"Workspace restored at {ws.rootpath}")
        return ws

    @property
    def is_created(self) -> bool:
        """Whether the workspace directory has been created."""
        return os.path.isdir(self.rootpath)


def _force_typer_to_use_command(typer_app: typer.Typer):
    """
    If there is **only a single** command()`, Typer will automatically use it as the main CLI application.
    This function is a workaround to force Typer to use command option even if it has only one command by adding a
    dummy callback. Ref: https://typer.tiangolo.com/tutorial/commands/one-or-multiple/#one-command-and-one-callback
    """
    typer_app.callback()(lambda: None)


class PartialTyper(typer.Typer):
    _process_partial_argv: List[str] = None
    """This is used to cache the argv that has been consumed by the sub-command.    
    We don't directly use `sys.argv` to avoid modifying the original `sys.argv` in the Typer app.
    Since some other applications may rely on the original `sys.argv` for their own CLI parsing.
    
    Notes:
        The initial value is None, which means no argv has been consumed yet.
        
        Note that this is a class variable, so it is shared across all instances of PartialTyper in the
        same process.
    """

    @property
    def argv(self) -> List[str]:
        if PartialTyper._process_partial_argv is None:
            return sys.argv
        else:
            # Return a copy of the cached argv to avoid modification
            return deepcopy(PartialTyper._process_partial_argv)

    @argv.setter
    def argv(self, argv: List[str]):
        assert isinstance(argv, list) and isinstance(argv[0], str)
        PartialTyper._process_partial_argv = deepcopy(argv)

    def __init__(self, entry: Union[Callable, Iterable[Callable], Mapping[str, Callable]], *args,
                 consume_argv: str = 'before', underscore_to_hyphen=False, hyphen_underscore_sensitive=False, **kwargs):
        """
        Build an app instance from a CLI interface automatically derived from `entry` using Typer.
        This Typer CLI can be used as a standalone script or as a library. It can read PARTIAL `argv` instead
        of the full `argv`, allowing subsequent programs to directly use `argv` for new CLI. This utility is useful
        when chaining a series of CLI programs together in a single script.

        Args:
            entry: A (list of) callable object(s), each of them will be used as a sub-command
            consume_argv: when to consume argv that already used for sub-command, so that the following program can
                directly use argv for a new CLI. value must be one of:
                - 'before': before sub-command calling
                - 'after': after sub-command calling
                - None: no argv consuming, keep argv unchanged
            underscore_to_hyphen: whether to regularize the function name to comply with Typer style
                by replacing '_' with '-' in the command name.
            hyphen_underscore_sensitive: whether names are `-` or `_` sensitive.
                If False, this CLI will preprocess all hyphens and underscores in input names (both function, argument,
                and option names) into the same character.

        Warning:
            We assume `--help` always be closely followed the command name
        """
        context_settings = kwargs.pop('context_settings', {})

        if not hyphen_underscore_sensitive:
            context_settings['token_normalize_func'] = (
                (lambda x: x.replace('_', '-')) if underscore_to_hyphen else (lambda x: x.replace('-', '_'))
            )

        super().__init__(*args, add_completion=False, context_settings=context_settings, **kwargs)

        name2func = regularize_function_table(entry, underscore_or_hyphen=('-' if underscore_to_hyphen else '_'))

        self._reset_state()

        for name_i, fn_i in name2func.items():
            # Define a factory function to capture fn_i correctly,
            # functools.wraps can preserve the original function's signature and metadata. This helps Typer correctly
            # generate the command-line interface based on the function's parameters.
            def make_command(fn):
                @functools.wraps(fn)
                def command_wrapper(ctx: typer.Context, *args, **kwargs):
                    nonlocal consume_argv
                    unused_args = ctx.args  # Capture the unparsed arguments
                    if consume_argv == 'before':
                        self._update_argv(unused_args)

                    retval = fn(*args, **kwargs)

                    if consume_argv == 'after':
                        self._update_argv(unused_args)
                    return retval

                # Typer use signature to distribute arguments, we need to let the signature be same as wrapped fn, which
                # has one more argument `ctx`
                sig = inspect.signature(fn)
                new_params = (
                    [inspect.Parameter("ctx", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=typer.Context)]
                    + list(sig.parameters.values())
                )
                new_sig = sig.replace(parameters=new_params)
                command_wrapper.__signature__ = new_sig
                return command_wrapper

            # Create the command function using the factory
            command_fn = make_command(fn_i)

            # Register the command function with the Typer app
            self.command(name_i, context_settings={"allow_extra_args": True,
                         "ignore_unknown_options": True})(command_fn)

        if len(name2func) <= 1:
            _force_typer_to_use_command(self)

    def _reset_state(self):
        self._state_num_popped_help = 0
        self._state_is_help_exit = False

    def _update_argv(self, unused_argv: List[str]):
        """Method for updating argv to only include the unparsed arguments."""
        num_unused_argv = len(unused_argv) + self._state_num_popped_help
        current_commands = self.argv[1:]
        used_commands, unused_commands = current_commands[:-num_unused_argv], current_commands[-num_unused_argv:]
        # Update argv to only include the unparsed arguments, so that other codes can be unchanged
        self.argv = [self.argv[0]] + unused_commands

    def __call__(self, *args, **kwargs):
        # Prepare the command-line arguments (excluding the script name)
        args4app = self.argv[1:]

        # Note: Because we don't know how many arguments are consumed by this partial command,
        # to avoid taking `--help` argument that belong to the subsequent command, we simply assume
        # that `--help` is always the **FIRST** argument of the command.
        # So, if any `--help` argument is presented in the 3rd and following position of the command,
        # it will be removed from the args4app. (But don't worry, they will be added back to argv
        # in _update_argv after the command parsing)
        # This is also a limitation of this implementation.
        while '--help' in args4app:
            help_index = args4app.index('--help')
            if help_index <= 1:
                self._state_is_help_exit = True
                break
            else:
                args4app.pop(help_index)
                self._state_num_popped_help += 1

        # Run the Typer app, capturing the result and handling exceptions
        fn_return = None
        try:
            fn_return = super().__call__(
                args4app,
                *args,
                standalone_mode=False,  # Prevent Typer from exiting the script
                **kwargs,
            )
        except SystemExit:
            # Handle normal exit quietly
            pass
        except Exception as e:
            # Handle other exceptions
            logging.error(f"Exception occurred while executing command: {e}")
            raise e

        if self._state_is_help_exit:
            exit(0)  # exit if user query '--help'

        self._reset_state()
        return fn_return


class WorkspaceAppMixin(object):
    """An application utility for managing workspace-centried runs.
    This is a mixin class that provide basic template of:
        1. using config to manage application settings,
        2. using workspace to manage application files,
        3. and optionally using logging/config-recording/other features.
        
    A run is defined by a workspace and related saved files inside the workspace.
    """

    CONFIG_FILENAME = 'config.yaml'  # default config filename to be saved in the workspace
    LOGGING_FORMAT = '[%(asctime)s] %(name)s - %(levelname)s: %(message)s'

    def __init__(self,
                 *args,
                 # capture keyword arguments
                 config: DictConfig = None,
                 workspace: Workspace = None,
                 **kwargs):
        """
        Args:
            config: (optional) configuration dictionary.
                Access via `self.cfg`
            workspace: (optional) workspace object. 
                No workspace nor logging file nor config saving will be used if not provided.
                Access via `self.ws`
        """
        super().__init__(*args, **kwargs)  # Mixin: forward unused arguments
        self.ws: Workspace = workspace  # all files related to this app running should be stored in this workspace dir
        self.cfg: DictConfig = config

    def workspace_init(self, *,
                       rank: Optional[int] = None,
                       is_create_workspace: bool = True,
                       is_init_logging: bool = True,
                       is_save_config: bool = True,
                       ):
        """ Initialize the workspace (persistent directory for storing files related to this run) and logging.

        Args:
            rank: distributed rank for multi-processing usage. Default is None (no rank info).
            is_create_workspace: whether to create the workspace persistency directory (in the main process).
                Default is True.
            is_init_logging: whether to initialize logging (across all processes). Default is True.
            is_save_config: whether to save the config file in the workspace (in the main process).
                Default is True.

        Warnings:
            This method does not designed to be fully distributed-safe. You need to ensure main process (rank 0)
            goes first before other processes in distributed setting. The ideal usage is:
                1. main process calls this method first
                2. other processes call this method after main process finished
        """
        is_main_process = (rank == 0 or rank is None)

        # Workspace create involves directory creation, only main process should do it to avoid race condition
        if is_create_workspace and is_main_process:
            if self.ws is None:
                raise ValueError("workspace is None, cannot create workspace.")
            if not self.ws.is_created:
                self.ws.create_workspace(exist_ok=(not is_main_process))

        ws_is_persistent = (self.ws is not None) and self.ws.is_created

        # Logging initialization can be done across all processes
        if is_init_logging:
            log_filepath = self.ws.relpath('logging.log') if self.ws is not None else None
            initialize_logging(log_filepath=log_filepath, rank=rank)

        # Save config involves file writing, only main process should do it to avoid duplicate writing
        if is_save_config and is_main_process:
            if not ws_is_persistent:
                raise ValueError("workspace is None or not created, cannot save config.")

            if self.cfg is not None:  # config must be provided
                cfg_filepath = self.ws.relpath(self.CONFIG_FILENAME)
                cfg_yaml_string = yaml.dump(OmegaConf.to_container(self.cfg))

                is_config_already_saved = os.path.exists(cfg_filepath)
                if is_config_already_saved:
                    logging.warning(f"Config file already exists at {cfg_filepath}, not overwriting.")
                else:
                    with open(cfg_filepath, 'w') as f:
                        f.write(cfg_yaml_string)

        logging.info(f"bixi AppMixin initialized. "
                     f"Workspace rootpath: {self.ws.rootpath if ws_is_persistent else 'N/A'}")

    @classmethod
    def default_prefix(cls):
        """compute class hierarchy as the default prefix:
        <father_module_name>.<class_name>
        """
        # cls.__module == '__main__' will happen when calling in interactive mode
        father_module_path = cls.__module__ if (hasattr(cls, '__module__') and cls.__module__ != '__main__') else ''
        module_path = (father_module_path + '.' if father_module_path else '') + cls.__name__
        return module_path

    @property
    def entries(self) -> Dict[str, Callable]:
        """Get public (not start with '_') method that directly defined the App class (not including the parents)
        as the default entry points.
        """
        return extract_function_table(self)

    def run_exec(self, command: str,
                 *,
                 entry: Optional[Union[Callable, Iterable[Callable], Mapping[str, Callable]]] = None,
                 globals_: Optional[Dict[str, Any]] = None,
                 locals_: Optional[Dict[str, Any]] = None
                 ):
        entry = entry or extract_function_table(self)
        name2func = regularize_function_table(entry)
        safe_globals: Dict[str, Any] = globals_ or {}
        safe_locals: Dict[str, Any] = name2func
        safe_locals.update(locals_ or {})

        # Execute the command string
        try:
            exec(command, safe_globals, safe_locals)
        except Exception as e:
            logging.error(f"Exception occurred while executing command: {e}")
            traceback.print_exc()
            raise

    class ResumePolicy(str, Enum):
        """Controls workspace resumption behavior for `workspace_app_launch`."""

        NEW = "new"
        AUTO = "auto"
        RESUME = "resume"

    @classmethod
    def workspace_app_launch(
            cls,
            # Workspace identification parameters
            ws_id: Annotated[Optional[str], typer.Option(
                help="The unique ID of an existing workspace to restore.",
            )] = None,
            ws_searchpath: Annotated[Optional[str], typer.Option(
                help="Root directory to search for workspace (used with ws_id).",
            )] = None,
            name: Annotated[Optional[str], typer.Option(
                help="Name of the experiment (used for workspace identification or creation).",
            )] = None,
            prefix: Annotated[Optional[str], typer.Option(
                help="Prefix of the experiment (used with name for workspace identification or creation). "
                "Default is `cls.default_prefix()`, which is the module and class name of the App class."
            )] = None,

            # Config parameters
            config_filepath: Annotated[Optional[str], typer.Option(
                help="The path of the config file.",
            )] = None,
            config_overrides: Annotated[Optional[List[str]], typer.Option(
                ..., '-opt',
                help="The overrides for the config. "
                "e.g. 'ddp.num_devices=1', 'training.training_iterations=100'"
            )] = None,

            # Execution parameters
            command: Annotated[Optional[str], typer.Option(
                help="The command to execute, e.g. 'train(0); summarize()'",
            )] = None,

            # Resume control parameter
            resume: Annotated[ResumePolicy, typer.Option(
                help="Workspace policy: 'new' (always create a new workspace), "
                "'auto' (resume a unique existing workspace if possible, else create a new one), "
                "'resume' (force resume a unique existing workspace, error if not found).",
            )] = ResumePolicy.AUTO):
        """Unified interface for experiment management.

        This method provides a single entry point for experiment lifecycle management,
        with explicit control over whether to create a new workspace or restore an existing one.

        Workspace Resolution Logic:
        1. If ws_id is provided:
           - Use ws_id + ws_searchpath to restore the workspace
           - ws_searchpath defaults to current working directory if not provided
           - If resume='new', raise error (cannot create new experiment with ws_id)
        2. If ws_id is not provided but name is provided:
           - If resume='resume': search for existing workspace, raise error if not found
           - If resume='new': create new workspace, raise error if cannot create
           - If resume='auto': resume if a unique workspace exists, otherwise create new
        3. If neither ws_id nor name is provided:
           - Raise an error as workspace cannot be identified

        Config Loading Logic:
        1. If config_filepath is provided:
           - Load base config from config_filepath
        2. If config_filepath is not provided:
           - For restored workspaces: load config from workspace/config.yaml
            - For new workspaces: use None as config object

        Note:
            When resuming an existing workspace and `config_filepath` is provided, the app will use
            the config loaded from `config_filepath` (with overrides), and will not overwrite the
            existing workspace `config.yaml`. This can be confusing; sugessting to omit `config_filepath`
            to load the workspace config instead when resuming.

        Warnings:
            "new" workspace does not means it will setup automatically. You need to call 
            `ws.setup_workspace()` manually. This design allows user to flexibly setup workspace
            in distributed or highly parallel setting.

        Raises:
            ValueError: If neither ws_id nor name is provided
            RuntimeError: If workspace restoration fails, multiple workspaces match the criteria,
                         or resume parameter conflicts with workspace identification method
        """
        config_overrides = config_overrides or []

        if isinstance(resume, cls.ResumePolicy):
            resume_policy = resume
        elif isinstance(resume, str):
            try:
                resume_policy = cls.ResumePolicy(resume.lower())
            except ValueError as e:
                raise ValueError(
                    "Invalid resume policy. Expected one of: 'new', 'auto', 'resume'."
                ) from e
        else:
            raise TypeError(
                "resume must be a ResumePolicy (or one of: 'new', 'auto', 'resume')."
            )

        # ===== Step 1: Workspace Resolution =====
        is_new_workspace = False
        ws_searchpath = ws_searchpath or os.getcwd()

        if ws_id is not None:
            # Case 1: Restore workspace by ID
            if resume_policy == cls.ResumePolicy.NEW:
                raise RuntimeError("Cannot create new experiment when using ws_id. Use 'name' parameter instead.")

            logging.info(f"Restoring workspace with ID: {ws_id}")
            ws = Workspace.restore_workspace(ws_searchpath, id=ws_id)
            logging.info(f"Successfully restored workspace: {ws.rootpath}")

        elif name is not None:
            # Case 2: Handle workspace by name + prefix based on resume parameter
            prefix = prefix or cls.default_prefix()

            if resume_policy == cls.ResumePolicy.NEW:
                # Always create a new workspace
                logging.info(f"Creating new workspace with name: {name}, prefix: {prefix}")
                try:
                    ws = Workspace(prefix=prefix, name=name)
                    is_new_workspace = True
                    logging.info(f"Successfully created new workspace: {ws.rootpath}")
                except Exception as e:
                    raise RuntimeError(f"Failed to create new workspace with name '{name}' and prefix '{prefix}': {e}")

            elif resume_policy == cls.ResumePolicy.RESUME:
                matches = Workspace.query_workspace_metadata(ws_searchpath, name=name, prefix=prefix)
                if len(matches) == 0:
                    raise RuntimeError(
                        f"Failed to resume workspace with name '{name}' and prefix '{prefix}': "
                        f"no workspace metadata entries found under {ws_searchpath}."
                    )
                if len(matches) > 1:
                    raise RuntimeError(
                        f"Failed to resume workspace with name '{name}' and prefix '{prefix}': "
                        f"found {len(matches)} matches. Pass ws_id to disambiguate."
                    )
                logging.info(f"Resuming workspace with name: {name}, prefix: {prefix}")
                ws = Workspace.restore_workspace(ws_searchpath, name=name, prefix=prefix)
                logging.info(f"Successfully resumed workspace: {ws.rootpath}")

            elif resume_policy == cls.ResumePolicy.AUTO:
                matches = Workspace.query_workspace_metadata(ws_searchpath, name=name, prefix=prefix)
                if len(matches) == 0:
                    logging.info(
                        "Auto-resume found no workspace; creating a new workspace with "
                        f"name: {name}, prefix: {prefix}"
                    )
                    ws = Workspace(prefix=prefix, name=name)
                    is_new_workspace = True
                    logging.info(f"Successfully created new workspace: {ws.rootpath}")
                elif len(matches) == 1:
                    logging.info(f"Auto-resume found a unique workspace; resuming name: {name}, prefix: {prefix}")
                    ws = Workspace.restore_workspace(ws_searchpath, name=name, prefix=prefix)
                    logging.info(f"Successfully resumed workspace: {ws.rootpath}")
                else:
                    raise RuntimeError(
                        f"Auto-resume found {len(matches)} workspaces for name '{name}' and prefix '{prefix}'. "
                        "Pass ws_id to disambiguate or use resume='new' to force creating a new workspace."
                    )

            else:
                raise AssertionError(f"Unhandled resume policy: {resume_policy}")

        else:
            # Case 3: Neither ws_id nor name provided
            raise ValueError("Either 'ws_id' or 'name' must be provided to identify the workspace")

        # ===== Step 2: Config Loading =====
        if not is_new_workspace and config_filepath is not None:
            ws_config_filepath = os.path.join(ws.rootpath, cls.CONFIG_FILENAME)
            logging.warning(
                f"Resuming an existing workspace, but `config_filepath` was provided. "
                f"The app will use the config loaded from `{config_filepath}` (with overrides), "
                f"and will not overwrite `{ws_config_filepath}`. "
                f"If this is not desired, omit `config_filepath` to load the workspace config instead."
            )

        if config_filepath is not None:
            # Load base config from config directory
            logging.info(f"Loading config from: {config_filepath}")
            config: DictConfig = compose_from_source(config_filepath, config_overrides)

        else:
            # Load config from workspace (only valid for restored workspaces)
            if not is_new_workspace:
                # This is a restored workspace, load config from workspace
                config_filepath = os.path.join(ws.rootpath, cls.CONFIG_FILENAME)
                if not os.path.exists(config_filepath):
                    raise FileNotFoundError(f"Config file not found in workspace: {config_filepath}")
                logging.info(f"Loading config from workspace: {config_filepath}")
                config: DictConfig = compose_from_source(config_filepath, config_overrides)
            else:
                config = None  # No config provided for this new workspace
                logging.info("No config_filepath provided for this new workspace; using None as config.")

        # ===== Step 3: App Instantiation and Execution =====
        # Set workspace metadata for new workspaces
        if is_new_workspace:
            # This is a new workspace, set up metadata
            if config is not None:
                flattened_config = flatten_dict(OmegaConf.to_container(config))  # type: ignore
            else:
                flattened_config = {}
            ws['flattened_config'] = flattened_config

        # Instantiate app
        app = cls(config=config, workspace=ws)

        # Execute command if provided
        if command is not None:
            logging.info(f"Executing command: {command}")
            app.run_exec(command=command, entry=app.entries)

        return app
