import logging
import traceback

try:
    from bixi.appcore import Workspace, WorkspaceAppMixin
    from bixi.cli import run_partial_typer
except Exception as e:
    logging.error(f"Failed to import bixi: {e}" + '\n' + \
                  traceback.format_exc() + '\n' + \
                  '(Note: Bixi initialization failed, but you may still be able to use some parts of the package.')
