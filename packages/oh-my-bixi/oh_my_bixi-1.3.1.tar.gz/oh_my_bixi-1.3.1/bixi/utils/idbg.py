"""
Interactive Debugging Utilities. This module is designed to debug iteractively.
It can display the results directly using Jupyter Notebook or IPython environment.
In the environment that does not support GUI rendering, you can use `autosave.on()` to automatically intercept
 matplotlib commands and save them in disk.
"""
import collections.abc
import datetime
import functools
import inspect
import os
import time
import math

from typing import Sequence, Callable, Union, List, Optional

import numpy as np
import matplotlib
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

try:
    import torch
except:
    print("[WARNING] torch is not installed, some functions in bixi.utils.idbg may not work.")

try:
    from torchvision.utils import make_grid as _make_grid
except:
    print("[WARNING] torchvision is not installed, some functions in bixi.utils.idbg may not work.")

try:
    from scipy.spatial.transform import Rotation
except:
    print("[WARNING] scipy is not installed, some functions in bixi.utils.idbg may not work.")

from bixi.utils.torch_cast import numpy_torch_compatible

AUTOSAVE_DIRNAME = '.bixi/debug_figures'


class _AutoPlotSaver:
    """A singleton class to automatically save matplotlib plots.

    This class ensures that only one instance of _AutoPlotSaver exists and provides
    functionality to automatically save matplotlib plots to a specified directory
    whenever `plt.show` or `plt.Figure.show` is called.

    Attributes:
        autosave_directory (str): The directory where plots will be saved.
        _autosave (bool): The state indicating whether autosave is enabled.
        _original_func (dict): A dictionary storing the original `plt.show` and `plt.Figure.show` functions.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        # Singleton pattern to ensure only one instance of _AutoPlotSaver exists
        if cls._instance is None:
            cls._instance = super(_AutoPlotSaver, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.autosave_directory = AUTOSAVE_DIRNAME
        self._autosave = False
        self._original_func = dict(
            plt_show=plt.show,
            plt_figure_show=plt.Figure.show
        )

    def _save_fig(self, fig: plt.Figure = None):
        fig = fig or plt.gcf()
        filename = f'plot_{datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")}.png'
        filepath = os.path.join(self.autosave_directory, filename)
        os.makedirs(self.autosave_directory, exist_ok=True)
        fig.savefig(filepath)
        print(f"Figure saved into {filepath}")

    def _get_decorated(self, fn: Callable, fn_get_fig: Callable = None):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            if fn_get_fig is not None:
                fig = fn_get_fig(*args, **kwargs)
            else:
                fig = None
            self._save_fig(fig=fig)
            return fn(*args, **kwargs)

        return wrapper

    def __repr__(self):
        return f"AutoPlotSaver(autosave_directory={self.autosave_directory if self.autosave_directory else '(cwd)'}, state={self._autosave})"

    def on(self):
        self.state = True

    def off(self):
        self.state = False

    @property
    def state(self):
        return self._autosave

    @state.setter
    def state(self, value: bool):
        assert isinstance(value, bool)
        if not value == self._autosave:
            if value:
                plt.show = self._get_decorated(plt.show, fn_get_fig=None)
                plt.Figure.show = self._get_decorated(plt.Figure.show,
                                                      fn_get_fig=lambda *args, **kwargs: args[0])  # args[0] is self
            else:
                plt.show = self._original_func['plt_show']
                plt.Figure.show = self._original_func['plt_figure_show']
        self._autosave = value


# Create a singleton instance of _AutoPlotSaver
autosave = _AutoPlotSaver()


@numpy_torch_compatible(_implementation='numpy')
def save2npzfile(filepath: str, is_compressed=False, **data):
    if is_compressed:
        np.savez_compressed(filepath, **data)
    else:
        np.savez(filepath, **data)


@numpy_torch_compatible(_implementation='numpy')
def datahistshow(x, bins=50, dpi=100, figsize=(6.4, 4.8), suptitle=None, **hist_kwargs):
    data = x.reshape(-1)
    fig = plt.figure(dpi=dpi, figsize=figsize, constrained_layout=True)
    ax1 = plt.subplot()

    # Plot the histogram on ax1 (primary y-axis: counts)
    counts, bins, patches = ax1.hist(data, bins=bins, alpha=0.6, color='b')

    # Label for the first y-axis
    ax1.set_xlabel('Value')
    ax1.set_ylabel('Counts', color='b')
    ax1.tick_params(axis='y', labelcolor='b')
    ax1.grid(which='major', color='gray', linewidth=1.0)
    ax1.grid(which='minor', color='lightgray', linewidth=0.6)
    ax1.minorticks_on()

    # Create a secondary y-axis (normalized probabilities as percentages)
    ax2 = ax1.twinx()

    # Prepare the data for the secondary y-axis
    count_sum = counts.sum()

    # Adjust the second y-axis to represent percentages
    ax2.set_ylabel(f'Probability Percentage', color='r')
    ax2.tick_params(axis='y', labelcolor='r')

    # Create a customized FuncFormatter object to make the secondary y-axis be probabilities
    formatter = matplotlib.ticker.FuncFormatter(lambda count, pos: f"{(count / count_sum):.2%}")
    ax2.yaxis.set_major_formatter(formatter)

    if suptitle:
        plt.suptitle(suptitle)

    plt.hist(x.reshape(-1), bins=bins, **hist_kwargs)
    plt.show()
    plt.close('all')


@numpy_torch_compatible(_implementation='numpy')
def imgshow(im, cmap=None, dpi=100, figsize=(6.4, 4.8), cbar=True,
            suptitle: str = None,
            filename2save: str = None,
            **imshow_kwargs):
    """
    :param im: [H, W] or [H, W, C]
    """
    if isinstance(im, torch.Tensor):
        im = im.to('cpu').detach().cpu().numpy()

    plt.figure(dpi=dpi, figsize=figsize, constrained_layout=True)
    plt.imshow(im, cmap=cmap, **imshow_kwargs)
    if cbar:
        plt.colorbar()

    if suptitle:
        plt.suptitle(suptitle)
    if filename2save is not None:
        plt.savefig(filename2save)
    else:
        plt.show()
    plt.close('all')


@numpy_torch_compatible(_implementation='numpy')
def imgshow_complex(imgc, dpi=100, col_width=3, row_width=3,
                    suptitle: str = None,
                    filename2save: str = None):
    """
    :param imgc: [H, W] Complex
    """
    figsize = (4 * col_width, 1 * row_width)
    fig, axes = plt.subplots(1, 4, dpi=dpi, figsize=figsize)
    axes[0].imshow(imgc.real, cmap='gray')
    axes[0].set_title('real')
    axes[1].imshow(imgc.imag, cmap='gray')
    axes[1].set_title('imag')
    axes[2].imshow(np.abs(imgc), cmap='gray')
    axes[2].set_title('magnitude')
    axes[3].imshow(np.angle(imgc), cmap='hsv')
    axes[3].set_title('angle')

    if suptitle:
        plt.suptitle(suptitle)
    if filename2save is not None:
        fig.savefig(filename2save)
    else:
        plt.show()
    plt.close('all')


@numpy_torch_compatible(_implementation='numpy')
def imsshow(imgs: Sequence[str], titles: Sequence[str] = None,
            ncols: int = 5, dpi: int = 100,
            cmap: Union[str, Sequence[str]] = 'viridis',
            cbar: bool = False, is_ticks: bool = False,
            suptitle: str = None, grid_size: int = 3, suptitle_height=0.1,
            margin_ratio=0.01, subplot_pad: float = 1.5, n_images_max=50,
            filename2save=None,
            **imshow_kwargs):
    '''
    assume imgs is Sequence[ndarray[Nx, Ny, (optional) C=1/3/4]]
    '''
    num_imgs = len(imgs)

    if num_imgs > n_images_max:
        print(
            f"[WARNING] Too many images ({num_imgs}), clip to argument n_images_max({n_images_max}) for performance reasons.")
        imgs = imgs[:n_images_max]
        num_imgs = n_images_max

    if isinstance(cmap, list) and not isinstance(cmap, (str, bytes)):
        assert len(cmap) == len(imgs)
    else:
        cmap = [cmap, ] * num_imgs

    nrows = math.ceil(num_imgs / ncols)
    ncols = min(num_imgs, ncols)

    # compute the figure size, compute necessary size first, then add margin
    figsize = (ncols * grid_size, nrows * grid_size)
    suptitle_height = suptitle_height if suptitle else 0
    figsize = (figsize[0], figsize[1] + suptitle_height)
    suptitle_height_rel = suptitle_height / figsize[1]
    fig = plt.figure(dpi=dpi, figsize=figsize)

    for i in range(num_imgs):
        ax = plt.subplot(nrows, ncols, i + 1)
        aximage4cbar = ax.imshow(imgs[i], cmap=cmap[i], **imshow_kwargs)
        if titles:
            plt.title(titles[i])
        if cbar:
            # cax = fig.add_axes([ax.get_position().x1 + 0.01, ax.get_position().y0, 0.01, ax.get_position().height])
            # fig.colorbar(im, cax=cax)
            fig.colorbar(aximage4cbar, ax=ax)
        if not is_ticks:
            ax.set_xticks([])
            ax.set_yticks([])

    fig.tight_layout(h_pad=subplot_pad, w_pad=subplot_pad,
                     rect=(margin_ratio, margin_ratio,
                           1 - margin_ratio, (1 - suptitle_height_rel) * (1 - margin_ratio)))

    if suptitle:
        plt.suptitle(suptitle)
    if filename2save is not None:
        fig.savefig(filename2save)
    else:
        plt.show()
    plt.close('all')


@numpy_torch_compatible(_implementation='numpy')
def singalsshow(*, xs=None, ys=None, titles=None, ncols=None,
                dpi=100, cmap=None, cbar=False, is_ticks=True, suptitle=None,
                col_width=3, row_height=3, margin_ratio=0.1, n_max=50, filename2save=None):
    '''
    :param xs: Sequence[[N,]]
    :param ys: Sequence[[N,]]
    :param titles: Sequence[str]
    '''
    N = len(ys)
    if xs is None:
        xs = [np.arange(0, len(ys[0]))] * N
    if titles is None:
        titles = [''] * N
    assert len(xs) == len(ys) == len(titles)

    if N > n_max:
        print(
            f"[WARNING] Too many signals ({N}), clip to argument n_max({n_max}) for performance reasons.")
        xs = xs[:n_max]
        ys = ys[:n_max]
        titles = titles[:n_max]
        N = n_max

    if isinstance(cmap, Sequence):
        assert len(cmap) == len(xs)
    else:
        cmap = [cmap, ] * N

    if ncols is None:
        nrows, ncols = 1, 1
    else:
        nrows = math.ceil(N / ncols)
        # compute the figure size, compute necessary size first, then add margin
    figsize = (ncols * col_width, nrows * row_height)
    figsize = (figsize[0] * (1 + margin_ratio), figsize[1] * (1 + margin_ratio))
    fig, axes = plt.subplots(nrows, ncols, dpi=dpi, figsize=figsize, constrained_layout=True)

    if nrows * ncols == 1:
        axes = [axes] * N
    else:
        axes = axes.reshape(-1)

    for i, ax in enumerate(axes):
        if i < N:
            ax.plot(xs[i], ys[i])
            if titles:
                ax.set_title(titles[i])
            if cbar:
                plt.colorbar(ax=ax)
            if not is_ticks:
                ax.set_xticks([])
                ax.set_yticks([])
        else:
            ax.axis('off')

    if suptitle:
        plt.suptitle(suptitle)
    if filename2save is not None:
        fig.savefig(filename2save)
    else:
        plt.show()
    plt.close('all')


@numpy_torch_compatible(_implementation='numpy')
def pcviz(point_cloud, nrows=1, ncols=1, dim=-1, color=None,
          cmap='viridis', marker='o', marker_size=1, grid_size=3, dpi=100, suptitle=None,
          elev_range=(15, 90), azim_range=(0, 180)):
    """
    Visualize the point cloud using matplotlib.

    Args:
        point_cloud (array[*, 3: xyz, *]): Point cloud, e.g. [3 (dim=0), 128, 128] or [65536, 3 (dim=-1)] or [16, 3 (dim=1), 256, 256].
        nrows (int, optional): Number of rows of subplots (default: 1).
        ncols (int, optional): Number of columns of subplots (default: 1).
        dim (int, optional): Dimension of the point cloud coordinates to prediction (default: -1).
        color (array[*, 3: rgb, *], optional): Point cloud's colors (default: use depth colored by cmap).
        cmap (str, optional): Colormap for the plot (default: 'viridis').
        marker (str, optional): Marker style for the plot (default: 'o').
        grid_size (int, optional): Size of each subplot grid (default: 4).
        dpi (int, optional): Dots per inch for the figure (default: 100).
        suptitle (str, optional): Suptitle for the figure (default: None).
        elev_range (tuple, optional): Range of elevation angles for the subplots (default: (15, 90)).
        azim_range (tuple, optional): Range of azimuth angles for the subplots (default: (0, 180)).

    Returns:
        None
    """
    # Convert to numpy array and reshape to get 3D coordinates
    pc = np.moveaxis(point_cloud, dim, -1).reshape(-1, 3)  # Shape: [N_points, 3]

    if color is not None:
        color = np.moveaxis(color, dim, -1).reshape(-1, 3)  # Shape: [N_points, 3]
    else:
        # Calculate depth as the Euclidean distance from the origin (camera position)
        color = np.linalg.norm(pc, axis=1)

    # Create a figure with subplots
    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, subplot_kw={'projection': '3d'},
                             figsize=(ncols * grid_size, nrows * grid_size), dpi=dpi)
    axes = axes.flatten() if nrows * ncols > 1 else [axes]

    # Plot the points in each subplot with different views
    elevs = np.linspace(elev_range[0], elev_range[1], nrows)
    azims = np.linspace(azim_range[0], azim_range[1], ncols)
    for i, ax in enumerate(axes):  # type: int, Axes3D
        scatter_obj = ax.scatter(xs=pc[:, 0], ys=pc[:, 1], zs=pc[:, 2],
                                 c=color, cmap=cmap, marker=marker, s=marker_size)
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        row = i // ncols
        col = i % ncols
        ax.view_init(elev=elevs[row], azim=azims[col])
        ax.set_title(f'Elev: {elevs[row]}, Azim: {azims[col]}')

    # Adjust the position of the color bar
    fig.subplots_adjust(right=0.85)
    cbar_ax = fig.add_axes([0.9, 0.15, 0.02, 0.7])
    cbar = fig.colorbar(scatter_obj, cax=cbar_ax)
    cbar.set_label('Euclidean Norm of Coordinates')

    # Add suptitle
    if suptitle:
        fig.suptitle(suptitle)

    # Show the plot
    plt.tight_layout(rect=[0, 0, 0.88, 1])
    plt.show()

    # Close the figure
    plt.close(fig)


def make_grid_and_show(ims, nrow=5, cmap=None):
    B, C, H, W = ims.shape
    im = _make_grid(ims, nrow=nrow)
    fig_h, fig_w = nrow * 2 + 1, (B / nrow) + 1
    imgshow(im, cmap=cmap, rgb_axis=0, dpi=200, figsize=(fig_h, fig_w))


def int2preetyStr(num: int):
    s = str(num)
    remain_len = len(s)
    while remain_len - 3 > 0:
        s = s[:remain_len - 3] + ',' + s[remain_len - 3:]
        remain_len -= 3
    return s


def compute_num_params(module, is_trace=False):
    print(int2preetyStr(sum([p.numel() for p in module.parameters()])))
    if is_trace:
        for item in [f"[{int2preetyStr(info[1].numel())}] {info[0]}:{tuple(info[1].shape)}"
                     for info in module.named_parameters()]:
            print(item)


def coordinates_plot(coordinates, img_size=(192, 192)):
    im = np.zeros(img_size)
    N, D = coordinates.shape
    assert D == 2
    for i in range(N):
        im[coordinates[i, 0], coordinates[i, 1]] = 1
    imgshow(im)


def print_shapes(obj=None, indent='  ', truncate: int = None, title: str = None):
    """Recursively print the shape of obj
    :param obj: use parts of locals() at caller stack by default.
    """

    def _get_previous_locals(n: int):
        """identical to call locals() in the previous `n` function stack"""
        assert n > 0
        # Get current frame
        _frame = inspect.currentframe()
        for i in range(n):
            _frame = _frame.f_back
            if _frame is None:
                return None

        # Get locals()
        localdict = _frame.f_locals.copy()
        return localdict

    def _print(elem):
        if hasattr(elem, 'shape') and hasattr(elem, 'dtype'):
            digest = f"{elem.shape} ({elem.dtype}) "
            if (isinstance(elem, torch.Tensor) and torch.is_floating_point(elem)) or \
                    (isinstance(elem, np.ndarray) and (elem.dtype in {np.float32, np.float64})):
                # float type checking to avoid error or warnings when computing mean on integer or complex types
                if np.prod(elem.shape) == 1:
                    # directly print the value when the number of values is 1, otherwise error will occur when computing
                    # statistics on single value.
                    digest += str(elem)
                else:
                    digest += f"(min {elem.min():.3e}, max {elem.max():.3e}, mean {elem.mean():.3e}, std {elem.std():.3e}"
        else:
            elem_str = str(elem)
            if truncate is not None:
                elem_str.replace('\n', ' ')
                if len(elem_str) > truncate:
                    elem_str = elem_str[:truncate]
                    elem_str += '...'
            digest = f"<{type(elem)}> {elem_str}"
        digest = digest
        print(digest)

    def _dfs(c, n_indent=0):
        n_indent_child = n_indent + 1
        if isinstance(c, collections.abc.Mapping):
            print(f"<{type(c).__name__}>")
            for k, v in c.items():
                print(f"{indent * n_indent_child}+ '{k}': ", end='')
                _dfs(v, n_indent=n_indent_child)
        elif isinstance(c, (collections.abc.Sequence, collections.abc.Set)) and not isinstance(c, (str, bytes)):
            print(f"<{type(c).__name__}>")
            for i, v in enumerate(c):
                print(f"{indent * n_indent_child}- [{i}] ", end='')
                _dfs(v, n_indent=n_indent_child)
        else:
            _print(c)

    if obj is None:
        if title:
            print(title)

        caller_locals = _get_previous_locals(2)
        obj = {k: v for k, v in caller_locals.items() if
               not inspect.ismodule(v) and
               not inspect.isfunction(v) and
               not inspect.isbuiltin(v) and
               not inspect.isclass(v) and
               not (k.startswith('__') and k.endswith('__')) and
               not (k in {'self'})}
    _dfs(obj, n_indent=0)


@numpy_torch_compatible(_implementation='numpy')
def visualize_7dof_poses(poses: List[np.ndarray] = None,
                         cmap: Optional[str] = None,
                         azimuths: List[float] = [0, 30, 45, 60, 90],
                         elevations: List[float] = [0, 45, 90],
                         grid_size=4,
                         dpi=100,
                         # the ratio compared to the maximum axis length of the poses (tx, ty, tz)
                         camera_tick_scale=0.1
                         ):
    """

    Args:
        poses: List[num_poses * [tx, ty, tz, qx, qy, qz, qw]]

    Notes:
        For each poses, red/green/blue lines represent the x/y/z axes of the camera coordinate system.
    """

    def plot_camera_pose(ax: Axes3D,
                         trans3d: np.ndarray,
                         quaternion: np.ndarray,
                         color='k',
                         scale: float = 0.1):
        """Plot a camera at position t with orientation q (as quaternion)."""
        # Get rotation matrix (camera-to-world) from quaternion
        rot = Rotation.from_quat(quaternion).as_matrix()
        # Camera axes in camera coordinate system
        cam_axes = np.eye(3) * scale
        # Rotate axes, then translate
        # Assume rot is row-major, then we need a transpose
        cam_axes_world = rot @ cam_axes + trans3d.reshape(3, 1)
        # Plot camera center
        ax.scatter(*trans3d, color=color, marker='o')
        # Plot axes
        colors = ['r', 'g', 'b']
        for i in range(3):
            ax.plot(
                [trans3d[0], cam_axes_world[0, i]],
                [trans3d[1], cam_axes_world[1, i]],
                [trans3d[2], cam_axes_world[2, i]],
                c=colors[i]
            )

    if not isinstance(poses, np.ndarray):
        poses = np.array(poses)  # [num_views, 7]

    num_views = len(poses)
    """Example: List of camera poses
    poses = [
        [0, 0, 0, 0, 0, 0, 1],  # Identity rotation
        [1, 1, 1, 0, 0, 0.7071, 0.7071],  # 90 deg around z-axis
        # Add more poses as needed
    ]
    """

    scale_per_dim = poses[:, :3].max(axis=0) - poses[:, :3].min(axis=0)
    max_scale_dim = np.max(scale_per_dim)

    tick_scale = max_scale_dim * camera_tick_scale  # Scale for the camera axes
    tick_scale = tick_scale if tick_scale > 0 else 0.1  # Ensure scale is positive

    def _set_uniform_axis_limits(ax: Axes3D,
                                 # `+ camera_tick_scale * 2` to accommodate the extra extends of the camera axes
                                 limit_size: float = (max_scale_dim * (1 + camera_tick_scale * 2))
                                 ):
        xlim, ylim, zlim = ax.get_xlim(), ax.get_ylim(), ax.get_zlim()
        limits_xyz = np.array([xlim, ylim, zlim])  # [3 (x, y, z), 2 (min, max)]
        center_xyz = (limits_xyz[:, 1] + limits_xyz[:, 0]) / 2
        uniform_limits_xyz = np.stack(
            [center_xyz - limit_size / 2, center_xyz + limit_size / 2], axis=1
        )  # [3 (x, y, z), 2 (min, max)]
        ax.set_xlim(uniform_limits_xyz[0, :])
        ax.set_ylim(uniform_limits_xyz[1, :])
        ax.set_zlim(uniform_limits_xyz[2, :])
        ax.set_box_aspect([1, 1, 1])

    nrows, ncols = len(elevations), len(azimuths)
    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, subplot_kw={'projection': '3d'},
                             figsize=(ncols * grid_size, nrows * grid_size), dpi=dpi,
                             constrained_layout=True)
    axes = axes.flatten() if nrows * ncols > 1 else [axes]

    # prepare colors for each poses' marker
    if cmap is None:
        colors = ['k' for _ in range(num_views)]
    else:
        cmap_obj = plt.cm.get_cmap(cmap)
        cmap_indices = (np.linspace(0, 1, num_views) * cmap_obj.N).astype(np.int64)
        colors = [cmap_obj(i) for i in cmap_indices]

    for i, ax in enumerate(axes):  # type: int, Axes3D
        for pose, color in zip(poses, colors):
            t = np.array(pose[:3])
            q = np.array(pose[3:])
            plot_camera_pose(ax, t, q,
                             color=color,
                             scale=tick_scale)

        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')

        # Reset all axis limits to same scale
        _set_uniform_axis_limits(ax)

        row = i // ncols
        col = i % ncols
        ax.view_init(elev=elevations[row], azim=azimuths[col])
        ax.set_title(f'Elev: {elevations[row]}, Azim: {azimuths[col]}')

    plt.show()

    # Close the figure
    plt.close(fig)


def timeit(fn: Callable, *,
           n_rep: int = 10,
           n_warmup: int = 2) -> dict:
    counter = 0
    time_records = []
    while counter < n_rep + n_warmup:
        start_time = time.time()
        fn()
        end_time = time.time()
        if counter >= n_warmup:
            time_records.append(end_time - start_time)
        counter += 1

    time_avg = np.mean(time_records).item()
    time_std = np.std(time_records).item()

    base_power = 1.0
    unit = 's'
    if time_avg < 1e-3:
        base_power = 1e3
        unit = 'ms'
    elif time_avg < 1e-6:
        base_power = 1e6
        unit = 'us'
    elif time_avg < 1e9:
        base_power = 1e9
        unit = 'ns'

    print(f"Timeit over {n_rep} runs (after {n_warmup} warmup runs): "
          f"avg {time_avg * base_power:.3f} {unit}, std {time_std * base_power:.3f} {unit}")

    return time_avg, time_std
