"""
Set of Plotting Utility Functions
"""
import numpy as np
import matplotlib.pyplot as plt
from typing import Union


def plot_2d(
    data: np.ndarray,
    axis_stride: int,
    max_xlen: int,
    max_ylen: int,
    xlabel: str,
    ylabel: str,
    title: str,
    save_path: str,
) -> np.ndarray:
    """
    Plot's the Pruning Mask of Sparse Weight (2D) `data`, and returns path of saved plot.
    Also, returns the estimated prune mask.

    Args:
        data (np.ndarray): Sparse Weight Matrix (2-D)
        axis_stride (int): Plot Figure Axis Stride
        max_xlen (int): Maximum number of samples to plot along x-axis
        max_ylen (int): Maximum number of samples to plot along y-axis
        xlabel (str): X-Axis Title
        ylabel (str): Y-Axis Title
        title (str): The figure Title
        save_path (str): Path to Save the Plot

    Returns:
        `np.ndarray`: The Prune Mask of the Weight Matrix
    """
    data = np.where(abs(data[0:max_xlen, 0:max_ylen]) > 0, 1, 0)

    plt.imshow(data, cmap="viridis")
    plt.colorbar()

    # Set axis stride
    plt.xticks(np.arange(0, data.shape[1], axis_stride))
    plt.yticks(np.arange(0, data.shape[0], axis_stride))

    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.savefig(save_path, bbox_inches="tight")

    # Show the plot
    plt.show()
    return data


def plot_1d(
    data: np.ndarray,
    axis_stride: int,
    max_xlen: int,
    xlabel: str,
    ylabel: str,
    title: str,
    save_path: str,
) -> np.ndarray:
    """
    Plot's the Pruning Mask of Sparse Weight (1D) `data`, and returns path of saved plot.
    Also, returns the estimated prune mask.

    Args:
        data (np.ndarray): Sparse Weight Matrix (1-D)
        axis_stride (int): Plot Figure Axis Stride
        max_xlen (int): Maximum number of samples to plot along x-axis
        xlabel (str): X-Axis Title
        ylabel (str): Y-Axis Title
        title (str): The figure Title
        save_path (str): Path to Save the Plot

    Returns:
        `np.ndarray`: The Prune Mask of the Weight Matrix
    """
    data = np.where(abs(data[0:max_xlen]) > 0, 1, 0)

    plt.plot(data)

    # Set axis stride
    plt.xticks(np.arange(0, data.shape[0], axis_stride))

    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.savefig(save_path, bbox_inches="tight")

    # Show the plot
    plt.show()
    return data


def plot_prune_mask(
    data: np.ndarray,
    axis_stride: int = 4,
    max_xlen: int = 24,
    max_ylen: int = 24,
    title: str = "title",
    save_path: str = "foo.png",
    skip_bias: bool = True,
    shape_mode="ip_x_op",
) -> Union[None, np.ndarray]:
    """
    Plot's the Pruning Mask of Sparse Weight (2D or 1D) `data`, and returns path of saved plot.
    Also, returns the estimated prune mask.

    Args:
        data (np.ndarray): Sparse Weight Matrix (1-D/ 2-D)
        axis_stride (int): Plot Figure Axis Stride
                              Default: 4
        max_xlen (int): Maximum number of samples to plot along x-axis
                           Default: 24
        max_ylen (int): Maximum number of samples to plot along y-axis
                           Default: 24
        title (str): The figure Title
                        Default: 'title'
        save_path (str): Path to Save the Plot
                            Default: 'foo.png'
        skip_bias (bool): If True, Skip Plotting Bias Prune Masks
                             Default: True

    Returns:
        Union[None, `np.ndarray`]: The Prune Mask of the Weight Matrix
                                       None if `data` was Bias, and skip_bias=True
    """
    ndims = len(data.shape)
    if ndims == 1:
        # Bias Tensors. Skip plotting if skip_bias == True
        bias_ret_val = (
            None
            if skip_bias
            else plot_1d(
                data=data,
                axis_stride=axis_stride,
                max_xlen=max_xlen,
                xlabel="Output Channels",
                ylabel="Mask",
                title=title,
                save_path=save_path,
            )
        )
        return bias_ret_val

    # If Conv1D (kernel_size, input_channels, output_channels) or Conv 2D (kernel_x, kernel_y, input_channels, output_channels)
    # Flatten the weight matrix, to get a Dense Matrix of shape (kernel_x * kernel_y * input_channels, output_channels)
    data = data.reshape(-1, data.shape[-1])

    if shape_mode == "ip_x_op":
        # `data` default: (IP_CHANNEL x OP_CHANNEL)
        # But, plot_2d expects `data` to be (OP_CHANNEL x IP_CHANNEL)
        data = data.T

    # Dense Weights
    return plot_2d(
        data=data,
        axis_stride=axis_stride,
        max_xlen=max_xlen,
        max_ylen=max_ylen,
        xlabel="Input Channels",
        ylabel="Output Channels",
        title=title,
        save_path=save_path,
    )
