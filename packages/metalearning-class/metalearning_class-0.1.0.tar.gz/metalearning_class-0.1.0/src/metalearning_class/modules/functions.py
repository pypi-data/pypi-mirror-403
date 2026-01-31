# useful functions

import matplotlib.pyplot as plt
from si_prefix import si_format
import metalearning_class.modules.functions as f
import os


def make_file_name(
    batch_size, patience, epochs_used, loss, isgen=False, current_gen=None
):
    """
    Create a short standardized filename identifying a training run.

    Parameters
    ----------
    batch_size : int
        Batch size used in the run.
    patience : int
        Early-stopping patience used.
    epochs_used : int
        Number of epochs (or epochs used) in the run.
    loss : str
        Loss function name (e.g. "mean_squared_error").
    isgen : bool, optional
        If True, append generation info. Default: False.
    current_gen : int, optional
        Generation index if `isgen` is True.

    Returns
    -------
    str
        A compact filename, e.g. "BS32_pat10_ep100" or "BS32_pat10_ep100_gen3".

    Examples
    --------
    >>> make_file_name(32, 10, 100, "mean_squared_error")
    'BS32_pat10_ep100'
    """

    gen_info = "_gen" + str(current_gen) if isgen else ""

    fname = (
        "BS"
        + str(batch_size)
        + "_pat"
        + str(patience)
        + "_ep"
        + str(epochs_used)
        + gen_info
    )
    return fname


def make_dir_name(
    theme,
    extra_dirs=None,
):
    """
    Build a directory path under the `results/` folder using a theme and optional subfolders.

    Parameters
    ----------
    theme : str
        Top-level theme name (e.g. "heatsense_test").
    extra_dirs : list of str, optional
        Additional subdirectory names to append in order.

    Returns
    -------
    str
        Path string, for example "results/heatsense_test/BS32_pat10_ep100".

    Examples
    --------
    >>> make_dir_name("heatsense_test", ["BS32_pat10_ep100"])
    'results/heatsense_test/BS32_pat10_ep100'
    """

    dir_name = "results/" + theme

    if extra_dirs:
        for extra_dir in extra_dirs:
            dir_name += "/" + extra_dir

    return dir_name


def short_loss_name(loss):
    """
    Map common long loss names to short acronyms.

    Parameters
    ----------
    loss : str
        Loss name (e.g. "mean_squared_error", "mean_absolute_error").

    Returns
    -------
    str
        Short label for the loss, for example "MSE" or "MAE".
        Returns "uknown" if loss is not recognized.

    Examples
    --------
    >>> short_loss_name("mean_squared_error")
    'MSE'
    """

    if loss == "mean_absolute_error":
        return "MAE"
    elif loss == "mean_squared_error":
        return "MSE"
    elif loss == "mean_absolute_percentage_error":
        return "MAPE"
    elif loss == "mean_squared_logarithmic_error":
        return "MSLE"
    else:
        return "uknown"


def plot_loss(
    dir_name,
    history,
    batch_size,
    patience,
    epochs_used,
    peak_memory,
    file_name,
    theme,
    loss,
    isgen=False,
    current_gen=None,
):
    """
    Plot and save training and validation loss curves.

    Parameters
    ----------
    dir_name : str
        Directory path where the plot will be saved (must exist).
    history : keras.callbacks.History or object with `history` attribute
        Training history containing `history['loss']` and `history['val_loss']`.
    batch_size : int
        Batch size used in the run (used only for plot annotation).
    patience : int
        Early-stopping patience used (used only for plot annotation).
    epochs_used : int
        Number of epochs used (for annotation).
    peak_memory : str
        Formatted peak memory string (e.g., "12.3 MiB") for annotation.
    file_name : str
        Output filename (without extension). The function will save to
        `{dir_name}/{file_name}.png`.
    theme : str
        Theme string used to build graph title.
    loss : str
        Loss name (to annotate and convert to short name).
    isgen : bool, optional
        Whether the plot corresponds to a genetic generation. Default: False.
    current_gen : int, optional
        Current generation index (used if isgen True).

    Returns
    -------
    None

    Raises
    ------
    KeyError
        If `history.history` does not contain 'loss' or 'val_loss' keys.

    Notes
    -----
    - The directory `dir_name` should exist (caller usually calls os.makedirs(dir_name, exist_ok=True)).
    - The function writes a PNG file at `{dir_name}/{file_name}.png`.

    Examples
    --------
    >>> plot_loss(dir_name="results/heatsense_test",
    ...           history=ml.history,
    ...           batch_size=32,
    ...           patience=10,
    ...           epochs_used=50,
    ...           peak_memory="12.3 MiB",
    ...           file_name="BS32_pat10_ep50",
    ...           theme="heatsense_test",
    ...           loss="mean_squared_error")
    """

    min_loss = str(round(min(history.history["loss"]), 3))
    min_val_loss = str(round(min(history.history["val_loss"]), 3))

    last_loss = str(round(history.history["loss"][-1], 3))
    last_val_loss = str(round(history.history["val_loss"][-1], 3))

    n_gen_info = " gen" + str(current_gen) if isgen else ""

    graph_info = (
        theme
        + " BS"
        + str(batch_size)
        + " Pat"
        + str(patience)
        + " Eps"
        + str(epochs_used)
        + n_gen_info
        + " "
        + peak_memory
        + " loss"
        + f.short_loss_name(loss)
    )

    # summarize history for loss
    plt.figure()
    plt.plot(history.history["loss"])
    plt.plot(history.history["val_loss"])
    plt.title(graph_info)

    plt.ylabel("loss")
    plt.xlabel("epoch")
    plt.legend(["train: " + min_loss, "test: " + min_val_loss], loc="upper left")

    plt.savefig(dir_name + "/" + file_name + ".png")