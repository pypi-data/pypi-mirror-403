"""
EasyViz: A flexible visualization library for creating complex, nested matplotlib visualizations
    without explicit layout specifications.

Architecture:
------------
The module is organized into two main component types:
1. Visualization Items (VItemBase derivatives):
   - ImageVItem: Displays image data with customizable appearance
   - LambdaVItem: Executes arbitrary plotting functions on an axis
   - Others ...

2. Panel (Container):
   - Arranges visualization items in a grid layout
   - Supports nested panels for complex hierarchical layouts
   - Handles automatic positioning and spans
   - Provides helper methods (hstack, vstack) for common arrangements

Examples:
---------
# Simple image grid
p = Panel(
    ImageVItem(np.random.rand(128, 128), 'gray', title='Image 1'),
    ImageVItem(np.random.rand(128, 128), 'viridis', title='Image 2'),
    ImageVItem(np.random.rand(128, 128), 'plasma', title='Image 3'),
    ncols=3, title="Image Grid"
)
fig = p.to_matplotlib_figure()
fig.show()

# Non-uniform layout with spans
p = Panel(
    ImageVItem(np.random.rand(128, 128), 'gray', title='Regular'),
    ImageVItem(np.random.rand(128, 256), 'viridis', span=(1, 2), title='Double-width'),
    ImageVItem(np.random.rand(256, 128), 'plasma', span=(2, 1), title='Double-height'),
    ncols=3, title="Mixed Spans"
)
fig = p.to_matplotlib_figure()
fig.show()

# Nested panels
p = Panel(
    Panel(
        ImageVItem(np.random.rand(128, 128), 'gray'),
        ImageVItem(np.random.rand(128, 128), 'gray'),
        ncols=2, title="Nested Panel"
    ),
    LambdaVItem(lambda ax: ax.plot([0, 1], [0, 1]), title="Custom Plot"),
    ncols=2, title="Root Panel"
)
fig = p.to_matplotlib_figure()
fig.show()

# Horizontal stacking (or vertical stacking using Panel.vstack)
p = Panel.hstack(
    ImageVItem(np.random.rand(128, 128), 'gray', title='Left'),
    ImageVItem(np.random.rand(128, 128), 'gray', title='Center'),
    ImageVItem(np.random.rand(128, 128), 'gray', title='Right'),
    title="Horizontal Stack"
)
fig = p.to_matplotlib_figure()
fig.show()
"""
from __future__ import annotations
from typing import List, Optional, Dict, Tuple, Any, Union, Callable
import matplotlib as mpl
import matplotlib.axes
import matplotlib.gridspec
import matplotlib.figure
import matplotlib.pyplot as plt
import numpy as np


# -----------------------------------------------------------------------------
# VItemBase is the abstract base for leaf Visualization items.
# -----------------------------------------------------------------------------
class VItemBase:
    """Base visualization item (leaf node) for plotting.

    NOTE:
        - All location parameters are specified with (0, 0) as the top-left corner.
        - The span parameter is specified as (row span, col span).
    """

    def __init__(
            self,
            location: Optional[Tuple[int, int]] = None,
            span: Optional[Tuple[int, int]] = None,
    ) -> None:
        """
        Args:
            location (Optional[Tuple[int, int]]): (row, col) starting location (top-left is (0, 0)).
            span (Optional[Tuple[int, int]]): (row span, col span) dimensions.
        """
        self.location: Optional[Tuple[int, int]] = location
        self.span: Optional[Tuple[int, int]] = span  # (row span, col span)

    def draw_axis(self, ax: mpl.axes.Axes) -> None:
        """Draw the visualization item on the given axes.

        Args:
            ax (mpl.axes.Axes): The matplotlib axes on which to draw.
        """
        raise NotImplemented


# -----------------------------------------------------------------------------
# Panel is the container that arranges children into a grid layout.
# -----------------------------------------------------------------------------
class Panel:
    """A Panel arranges its children into a grid layout.

    It supports both explicitly positioned children and those automatically
    allocated via a packing algorithm. The children can be either Panels (for nesting)
    or leaf visualization items derived from VItemBase.

    NOTE:
        - All location parameters are specified using (0, 0) as the top-left corner.
        - The span parameter is specified as (row span, col span). For child Panels,
          if span is not provided, its effective span is its own layout size.
    """

    def __init__(
            self,
            *children: Union[Panel, VItemBase],
            ncols: int = 1,
            title: Optional[str] = None,
            location: Optional[Tuple[int, int]] = None,
            span: Optional[Tuple[int, int]] = None,
            **kwargs: Any,
    ) -> None:
        """
        Args:
            *children (Union[Panel, VItemBase]): Child panels or visualization items to be arranged.
            ncols (int): Number of columns in the grid layout.
            location (Optional[Tuple[int, int]]): (row, col) starting location in the parent grid.
            span (Optional[Tuple[int, int]]): (row span, col span) dimensions in the parent grid.
                Note: this span is relative to the parent panel's GridSpec.
                  For example, a three level panel like:
                    0. Top level, grid (2, 2), size 2x2 inches
                    1. Middle level, span (1, 1), grid (2, 2), size 1x1 inches per grid
                    2. Bottom level, span (1, 1), grid (1, 1), size 0.5x0.5 inches per grid
            **kwargs: Additional layout kwargs (e.g., 'wspace', 'hspace') for GridSpec.
        """
        self.children: List[Union[Panel, VItemBase]] = list(children)
        self.ncols = ncols
        self.title = title
        self.location: Optional[Tuple[int, int]] = location
        self.span: Optional[Tuple[int, int]] = span  # (row span, col span)
        self.kwargs4gridspec: Dict[str, Any] = kwargs  # for GridSpecFromSubplotSpec

    @staticmethod
    def get_effective_span(x: Union[Panel, VItemBase]) -> Tuple[int, int]:
        if x.span is not None:
            return x.span
        elif isinstance(x, Panel):
            # For child panels, default span is its own computed layout size.
            return x.compute_layout()
        elif isinstance(x, VItemBase):
            # For leaf nodes, the default span is (1, 1).
            return (1, 1)
        else:
            raise ValueError(f"Unknown child type: {type(x)}. Must be Panel or VItemBase.")

    def _allocate_positions(
            self,
    ) -> Tuple[List[Tuple[Union[Panel, VItemBase], int, int, int, int]], int]:
        """
        Allocate grid positions for children.

        The allocation algorithm proceeds in three stages:
          0. First, check that all children's spans fit within panel width.
          1. Then, pre-compute the effective span for each child. For a child Panel,
             if no explicit span is provided, its effective span is its computed layout size.
             For leaf nodes, the default span is (1, 1).
          2. Process children with explicit locations and check for overlaps.
          3. Process children without explicit locations using a packing algorithm.

        The allocation algorithm proceeds in two stages:
          1. First, we pre-compute the effective span for each child. For a child Panel,
             if no explicit span is provided, its effective span is its computed layout size.
             For leaf nodes, the default span is (1, 1).
          2. Then, we process:
             - Children with an explicit location: reserve their requested block (and
               check for overlaps).
             - Children without explicit locations: scan row by row (in a packing fashion)
               for the first available contiguous block that can fully accommodate the child's span.
               We use Python's `all()` function to ensure that the entire candidate block is free.

        Returns:
            Tuple[List[Tuple[Union[Panel, VItemBase], int, int, int, int]], int]:
                - A list of allocations, each defined as a tuple:
                  (child, allocated_row, allocated_col, row span, col span)
                - The total number of grid rows needed.
        """
        allocated: List[Tuple[Union[Panel, VItemBase], int, int, int, int]] = []
        occupied: set[Tuple[int, int]] = set()

        # Precompute the effective span for each child.
        effective_spans: List[Tuple[Union[Panel, VItemBase], Tuple[int, int]]] = []
        for child in self.children:
            eff_span = self.get_effective_span(child)

            # Check that all children fit within panel width
            if eff_span[1] > self.ncols:
                raise ValueError(
                    f"Child with span {eff_span} exceeds panel width {self.ncols}."
                )
            effective_spans.append((child, eff_span))

        # Separate children with explicit locations from those without.
        explicit_children: List[Tuple[Union[Panel, VItemBase], Tuple[int, int]]] = []
        implicit_children: List[Tuple[Union[Panel, VItemBase], Tuple[int, int]]] = []
        for child, eff_span in effective_spans:
            if child.location is not None:
                explicit_children.append((child, eff_span))
            else:
                implicit_children.append((child, eff_span))

        # Stage 1: Process children with explicit locations.
        for child, child_span in explicit_children:
            r, c = child.location  # explicit location (top-left is (0, 0))
            if c + child_span[1] > self.ncols:
                raise ValueError(
                    f"Child with explicit location {child.location} and span {child_span} "
                    f"exceeds panel width {self.ncols}."
                )
            # Reserve cells and check for overlaps.
            for i in range(child_span[0]):
                for j in range(child_span[1]):
                    cell = (r + i, c + j)
                    if cell in occupied:
                        raise ValueError(
                            f"Overlap detected for child at location {child.location} with span {child_span}."
                        )
                    occupied.add(cell)
            allocated.append((child, r, c, child_span[0], child_span[1]))

        # Stage 2: Process children without explicit locations.
        for child, child_span in implicit_children:
            allocated_flag = False
            row = 0
            while not allocated_flag:
                for col in range(self.ncols - child_span[1] + 1):
                    # Check that the candidate block is fully free.
                    if all(
                            (row + i, col + j) not in occupied
                            for i in range(child_span[0])
                            for j in range(child_span[1])
                    ):
                        # Reserve the block.
                        for i in range(child_span[0]):
                            for j in range(child_span[1]):
                                occupied.add((row + i, col + j))
                        allocated.append((child, row, col, child_span[0], child_span[1]))
                        allocated_flag = True
                        break  # Block found; break out of the column loop.
                if not allocated_flag:
                    row += 1

        total_rows = max(r + rs for (_, r, _, rs, _) in allocated)
        allocated.sort(key=lambda tup: (tup[1], tup[2]))  # sort by row then col
        return allocated, total_rows

    def compute_layout(self) -> Tuple[int, int]:
        """
        Compute and return the grid layout for this panel.

        Returns:
            Tuple[int, int]: A tuple (total_rows, ncols) representing the layout dimensions.
        """
        if not self.children:
            raise ValueError("Panel must have at least one child.")
        _, total_rows = self._allocate_positions()
        return total_rows, self.ncols

    def draw(
            self,
            parent_fig: Union[mpl.figure.Figure, mpl.figure.SubFigure],
            parent_gs: Union[mpl.gridspec.GridSpec, mpl.gridspec.SubplotSpec]
    ) -> None:
        """
        Draw the panel on the given matplotlib figure and gridspec.

        The method first allocates positions for children, then for each allocated child:
          - If the child is a Panel, create a subfigure with a nested gridspec and call its draw method.
          - If the child is a leaf (an instance of VItemBase), create an axis in the allocated cell(s)
            and call its draw_axis method.
        Mixed usage (Panels and leaf nodes) is allowed.

        Args:
            parent_fig (mpl.figure.Figure): The matplotlib figure or subfigure.
            parent_gs (mpl.gridspec.GridSpec): The gridspec allocated for this panel.
        """
        if not self.children:
            raise ValueError("Panel must have at least one child.")

        allocated, total_rows = self._allocate_positions()

        panel_gs = parent_gs[:, :].subgridspec(
            total_rows,
            self.ncols,
            **self.kwargs4gridspec
        )

        for (child, row, col, rs, cs) in allocated:
            cell_subspec = panel_gs[row: row + rs, col: col + cs]
            if isinstance(child, Panel):
                # For nested Panels, create a subfigure and nested gridspec.
                subfig = parent_fig.add_subfigure(subplotspec=cell_subspec)
                child_nrows, child_ncols = child.compute_layout()
                child_gs = mpl.gridspec.GridSpec(
                    child_nrows,
                    child_ncols,
                    figure=subfig,
                    **child.kwargs4gridspec
                )
                child.draw(subfig, child_gs)

                if child.title:
                    subfig.suptitle(child.title)

            elif isinstance(child, VItemBase):
                # For leaf nodes, create an axis and call draw_axis.
                ax = parent_fig.add_subplot(cell_subspec)
                child.draw_axis(ax)
            else:
                # Fallback: if the child is of an unknown type.
                ax = parent_fig.add_subplot(cell_subspec)
                ax.text(0.5, 0.5, "Leaf drawing not implemented", ha="center", va="center")
                ax.set_xticks([])
                ax.set_yticks([])

    def to_matplotlib_figure(self, inch_per_unit: int = 2, **kwargs4gridspec) -> mpl.figure.Figure:
        """
        Create and return a matplotlib Figure from this panel.

        Args:
            inch_per_unit (int): Size of each grid cell in inches.
            **kwargs4gridspec: Passed to GridSpec for layout adjustments.

        Returns:
            mpl.figure.Figure: The assembled figure.
        """
        nrows, ncols = self.compute_layout()
        figsize = (ncols * inch_per_unit, nrows * inch_per_unit)
        fig = plt.figure(constrained_layout=True, figsize=figsize)
        root_gs = mpl.gridspec.GridSpec(nrows, ncols, figure=fig, **kwargs4gridspec)

        if self.title:
            fig.suptitle(self.title)

        self.draw(fig, root_gs)

        return fig

    @classmethod
    def vstack(cls, *children: Union[Panel, VItemBase], **kwargs) -> Panel:
        """
        Create a vertical stack of panels or visualization items.
        This factory method avoid the need to specify the number of columns.
        """
        max_width = max(
            cls.get_effective_span(child)[1] for child in children
        )
        return cls(*children, ncols=max_width, **kwargs)

    @classmethod
    def hstack(cls, *children: Union[Panel, VItemBase], **kwargs) -> Panel:
        """
        Create a horizontal stack of panels or visualization items.
        This factory method avoid the need to specify the number of columns.
        """
        sum_width = sum(
            cls.get_effective_span(child)[1] for child in children
        )
        return cls(*children, ncols=sum_width, **kwargs)


# -----------------------------------------------------------------------------
# Implementation of concrete VItemBase leaf nodes.
# -----------------------------------------------------------------------------
class ImageVItem(VItemBase):
    """Visualization item for displaying an image."""

    def __init__(
            self,
            image: np.ndarray,
            cmap: Optional[str] = None,
            title: Optional[str] = None,
            location: Optional[Tuple[int, int]] = None,
            span: Optional[Tuple[int, int]] = None,
            **kwargs: Any,
    ) -> None:
        """
        Args:
            image (np.ndarray): The image data in numpy convention ([H, W, C=3/4] or [H, W])
            cmap (Optional[str]): Colormap (if applicable).
            location (Optional[Tuple[int, int]]): (row, col) starting location.
            span (Optional[Tuple[int, int]]): (row span, col span) dimensions.
            **kwargs: Additional keyword arguments passed to imshow.
        """
        super().__init__(location, span)
        self.image = image
        self.cmap = cmap
        self.title = title
        self.imshow_kwargs = kwargs

    def __repr__(self):
        return f"ImageVItem(title={self.title}, image_shape={self.image.shape})"

    def draw_axis(self, ax: mpl.axes.Axes) -> None:
        """Display the image on the given axes."""
        ax.imshow(self.image, cmap=self.cmap, **self.imshow_kwargs)

        if self.title:
            ax.set_title(self.title)

        ax.set_xticks([])
        ax.set_yticks([])


class ImageOverlayVItem(VItemBase):
    """Visualization item for displaying an image overlaying on another image."""

    def __init__(
            self,
            image_base: np.ndarray,
            image_top: np.ndarray,
            *,
            alpha: float = 0.5,
            cmap_base: str = 'gray',
            cmap_top: str = 'magma',
            title: Optional[str] = None,
            location: Optional[Tuple[int, int]] = None,
            span: Optional[Tuple[int, int]] = None,
            **kwargs: Any,
    ) -> None:
        """
        Args:
            image_base (np.ndarray): The background image in numpy convention ([H, W, C=3/4] or [H, W])
            image_top (np.ndarray): The top image to overlay in numpy convention ([H, W, C=3/4] or [H, W])
            alpha (float): Transparency level for the heatmap.
            cmap_base (str): Colormap for the base image.
            cmap_top (str): Colormap for the heatmap.
            location (Optional[Tuple[int, int]]): (row, col) starting location.
            span (Optional[Tuple[int, int]]): (row span, col span) dimensions.
            **kwargs: Additional keyword arguments for imshow.
        """
        super().__init__(location, span)
        self.image_base = image_base
        self.image_top = image_top
        self.alpha = alpha
        self.cmap_base = cmap_base
        self.cmap_top = cmap_top
        self.imshow_kwargs = kwargs
        self.title = title

    def __repr__(self):
        return f"HeatmapOverlayVItem(title={self.title}, base_image_shape={self.image_base.shape}, top_image_shape={self.image_top.shape})"

    def draw_axis(self, ax: mpl.axes.Axes) -> None:
        """Display the base image and overlay the heatmap on the given axes."""
        # Plot the base image.
        ax.imshow(self.image_base, cmap=self.cmap_base, **self.imshow_kwargs)

        # Overlay the heatmap.
        ax.imshow(self.image_top, cmap=self.cmap_top, alpha=self.alpha, **self.imshow_kwargs)

        ax.set_xticks([])
        ax.set_yticks([])

        if self.title:
            ax.set_title(self.title)


class LambdaVItem(VItemBase):
    """Visualization item that uses a user-defined function to draw on the axis."""

    def __init__(
            self,
            plot_func: Callable[[mpl.axes.Axes], None],
            title: Optional[str] = None,
            location: Optional[Tuple[int, int]] = None,
            span: Optional[Tuple[int, int]] = None,
    ) -> None:
        """
        Args:
            plot_func (Callable[[mpl.axes.Axes], None]): A function that takes an axes instance and performs plotting.
            location (Optional[Tuple[int, int]]): (row, col) starting location.
            span (Optional[Tuple[int, int]]): (row span, col span) dimensions.
        """
        super().__init__(location, span)
        self.plot_func = plot_func
        self.title = title

    def __repr__(self):
        return f"LambdaOverlayVItem(title={self.title}, fn={self.plot_func})"

    def draw_axis(self, ax: mpl.axes.Axes) -> None:
        """Delegate drawing to the user-supplied calllable."""
        self.plot_func(ax)

        if self.title:
            ax.set_title(self.title)
