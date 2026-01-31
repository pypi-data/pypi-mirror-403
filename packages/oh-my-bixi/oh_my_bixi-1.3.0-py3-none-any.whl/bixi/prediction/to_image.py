import io
import math

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import pyplot as plt


def fig2ndarray(fig: plt.Figure, **kwargs4savefig) -> np.ndarray:
    """
    Convert matplotlib figure to numpy ndarray
    Returns:
        np.ndarray: [H, W, C]
    """
    io_buf = io.BytesIO()
    fig.savefig(io_buf, format='raw', **kwargs4savefig)

    io_buf.seek(0)
    data = np.frombuffer(io_buf.getvalue(), dtype=np.uint8)
    image_array = data.reshape(int(fig.bbox.bounds[3]), int(fig.bbox.bounds[2]), -1)
    io_buf.close()

    return image_array
