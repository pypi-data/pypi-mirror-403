import glob
import os
import shutil
import time
from typing import List, Tuple, Dict, Annotated

import pandas as pd
import typer
from bixi.appcore import Workspace

app = typer.Typer()
app.callback()(lambda: None)  # Placeholder for the main app callback to ensure 1st argument of app is command


def find_workspace_dir(dirpath_glob: str, **requirements) -> Dict[str, str]:
    """Find the workspace metadata based on name or id regex."""
    possible_dirpaths = glob.glob(dirpath_glob)
    filepath2metadata = {}
    for p in possible_dirpaths:
        filepath2metadata.update(Workspace.query_workspace_metadata(
            search_root=p, **requirements
        ))
    return filepath2metadata


@app.command()
def wandb_sync(
        dirpath_glob: str = typer.Argument(..., help="Glob pattern to find workspace directories."),
        workspace_rootpath: Annotated[str, typer.Option('...', metavar='TEXT', help="Root path for the workspace directories.")] = os.getcwd()
) -> None:
    """
    Synchronize WandB runs in the specified workspace directories.
    """
    metadata_tosync = []
    all_wandb_dirpaths = glob.glob(os.path.join(workspace_rootpath, "wandb", '*'))
    filepath2metadata = find_workspace_dir(dirpath_glob)

    for filepath_i in filepath2metadata:
        ws_dirpath = os.path.dirname(filepath_i)
        ws_id = filepath2metadata[filepath_i]['id']
        for wandb_dirpath in all_wandb_dirpaths:
            if wandb_dirpath.endswith(ws_id):
                metadata_i = {
                    'id':        ws_id,
                    'name':      filepath2metadata[filepath_i]['name'],
                    'workspace': ws_dirpath,
                    'wandb':     wandb_dirpath
                }
                metadata_tosync.append(metadata_i)

    df_metadata = pd.DataFrame(metadata_tosync)

    # display all data frame and let user to confirm
    typer.echo(f"The following {len(df_metadata)} metadata will be synchronized:")
    typer.echo(df_metadata.to_string(index=False))
    if typer.confirm("Do you want to proceed with the synchronization?"):
        for _, row in df_metadata.iterrows():
            os.system(f"wandb sync {row['wandb']}")
        typer.echo("WandB synchronization completed.")
    else:
        typer.echo("WandB synchronization aborted.")


@app.command()
def archive(
        dirpath_glob: str = typer.Argument(..., help="Glob pattern to find workspace directories."),
        workspace_rootpath: Annotated[str, typer.Option('...', metavar='TEXT', help="Root path for the workspace directories.")] = None,
        output_dirpath: Annotated[str, typer.Option('...', metavar='TEXT', help="Output path for the archive.")] = None
) -> None:
    """
    Archive the specified workspace directories.
    """
    workspace_rootpath = workspace_rootpath or os.getcwd()
    output_dirpath = output_dirpath or os.path.join(os.getcwd(), '_archives', time.strftime("%Y%m%d-%H%M%S"))

    metadata_tosync = []
    filepath2metadata = find_workspace_dir(dirpath_glob)
    all_wandb_dirpaths = glob.glob(os.path.join(workspace_rootpath, "wandb", '*'))

    for filepath_i in filepath2metadata:
        ws_dirpath = os.path.dirname(filepath_i)
        ws_id = filepath2metadata[filepath_i]['id']
        wandb_dirpath = None
        for wandb_dirpath_i in all_wandb_dirpaths:
            if wandb_dirpath_i.endswith(ws_id):
                wandb_dirpath = wandb_dirpath_i
                break

        metadata_i = {
            'id':        ws_id,
            'name':      filepath2metadata[filepath_i]['name'],
            'workspace': ws_dirpath,
            'wandb':     wandb_dirpath
        }
        metadata_tosync.append(metadata_i)

    df_metadata = pd.DataFrame(metadata_tosync)

    # display all data frame and let user to confirm
    typer.echo(f"The following {len(df_metadata)} metadata will be archived:")
    typer.echo(df_metadata.to_string(index=False))
    if typer.confirm("Do you want to proceed with the archiving?"):
        os.makedirs(output_dirpath, exist_ok=True)
        for _, row in df_metadata.iterrows():
            dirpaths_tomove = [row['workspace'], row['wandb']]
            for p in dirpaths_tomove:
                if p is not None:
                    shutil.move(p, output_dirpath)
        typer.echo("Archiving completed.")
    else:
        typer.echo("Archiving aborted.")


if __name__ == '__main__':
    app()
