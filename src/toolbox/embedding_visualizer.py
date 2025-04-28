import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler, MinMaxScaler, normalize



def _apply_normalization(
    X: np.ndarray,
    method: str = None
) -> np.ndarray:
    """
    Apply feature-wise or sample-wise normalization to X.

    Parameters:
        X (np.ndarray): Array of shape (n_samples, n_features).
        method (str, optional): One of {None, "zscore", "minmax", "l2"}. Defaults to None.

    Returns:
        np.ndarray: Normalized array.
    """
    if method is None:
        return X
    m = method.lower()
    if m == "zscore":
        scaler = StandardScaler()
        return scaler.fit_transform(X)
    if m == "minmax":
        scaler = MinMaxScaler()
        return scaler.fit_transform(X)
    if m == "l2":
        return normalize(X, norm="l2")
    raise ValueError(f"Unknown normalization method: {method!r}")

def compute_PCA(
    signal: np.ndarray,
    n_cmp: int = 2,
    feature: np.ndarray = None,
    feature_label: str = "Feature",
    normalization: str = None,
    plot: bool = True,
) -> np.ndarray:
    """
    Compute PCA for the given signal (with optional normalization) and plot.

    Parameters:
        signal (np.ndarray): Input data of shape (n_samples, n_features).
        n_cmp (int): Number of principal components. Defaults to 2.
        feature (np.ndarray, optional): Values for coloring. If None, no color.
        feature_label (str): Label for color bar. Defaults to "Feature".
        normalization (str, optional): "zscore", "minmax", or None. Defaults to None.
        plot (bool): Whether to display the scatter plot. Defaults to True.

    Returns:
        np.ndarray: Transformed data after PCA.
    """
    # Normalize features if requested
    X = _apply_normalization(signal, normalization)

    pca = PCA(n_components=n_cmp)
    P = pca.fit_transform(X)

    if plot:
        if n_cmp == 2:
            plt.figure(figsize=(8, 6))
            if feature is None:
                plt.scatter(P[:, 0], P[:, 1], alpha=0.7)
            else:
                norm = mcolors.Normalize(vmin=np.min(feature), vmax=np.max(feature))
                plt.scatter(P[:, 0], P[:, 1], c=feature, cmap="viridis", norm=norm, alpha=0.7)
                plt.colorbar(label=feature_label)
            plt.grid(True)
            plt.xlabel("Component 1")
            plt.ylabel("Component 2")
            plt.title(f"PCA ({n_cmp} Components) — norm={normalization}")
            plt.show()
        elif n_cmp == 3:
            fig = plt.figure(figsize=(8, 6))
            ax = fig.add_subplot(111, projection="3d")
            if feature is None:
                sc = ax.scatter(P[:, 0], P[:, 1], P[:, 2], alpha=0.7)
            else:
                norm = mcolors.Normalize(vmin=np.min(feature), vmax=np.max(feature))
                sc = ax.scatter(P[:, 0], P[:, 1], P[:, 2], c=feature, cmap="viridis", norm=norm, alpha=0.7)
                cbar = plt.colorbar(sc, ax=ax)
                cbar.set_label(feature_label)
            ax.set_xlabel("Component 1")
            ax.set_ylabel("Component 2")
            ax.set_zlabel("Component 3")
            plt.title(f"PCA ({n_cmp} Components) — norm={normalization}")
            plt.show()
        else:
            raise ValueError("Plotting only supported for 2 or 3 components.")
    return P


def compute_TSNE(
    X: np.ndarray,
    feature: np.ndarray = None,
    feature_label: str = "Feature",
    normalization: str = None,
    plot: bool = True,
    **tsne_kwargs
) -> np.ndarray:
    """
    Compute t-SNE (with optional normalization) and plot.

    Parameters:
        X (np.ndarray): Input data, shape (n_samples, …).
        feature (np.ndarray, optional): Values for coloring. If None, no color.
        feature_label (str): Label for color bar. Defaults to "Feature".
        normalization (str, optional): "zscore", "minmax", or None. Defaults to None.
        plot (bool): Whether to display the scatter plot. Defaults to True.
        **tsne_kwargs: Additional args for sklearn.manifold.TSNE.

    Returns:
        np.ndarray: 2D t-SNE embedding.
    """
    # Flatten and replace NaNs
    X_flat = X.reshape(X.shape[0], -1)
    X_flat = np.nan_to_num(X_flat)

    # Normalize if requested
    X_proc = _apply_normalization(X_flat, normalization)

    tsne = TSNE(n_components=2, random_state=42, **tsne_kwargs)
    X_embedded = tsne.fit_transform(X_proc)

    if plot:
        plt.figure(figsize=(8, 6))
        if feature is None:
            plt.scatter(X_embedded[:, 0], X_embedded[:, 1], alpha=0.7)
        else:
            plt.scatter(X_embedded[:, 0], X_embedded[:, 1], c=feature, cmap="jet", alpha=0.7)
            plt.colorbar(label=feature_label)
        plt.xlabel("Dimension 1")
        plt.ylabel("Dimension 2")
        plt.title(f"t-SNE — norm={normalization}")
        plt.show()

    return X_embedded
