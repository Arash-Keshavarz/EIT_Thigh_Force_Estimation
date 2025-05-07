import numpy as np
import matplotlib.pyplot as plt
import os
from os.path import join
from glob import glob
from tqdm import tqdm
from sklearn.decomposition import PCA
import seaborn as sns


def z_score(data, print_info: bool = True):
    mean = np.mean(data)
    std  = np.std(data)

    if print_info:
        print(f"   before: mean={mean:.3f}, std={std:.3f}")

    data_z = (data - mean) / std

    if print_info:
        print(f"   after:  mean={np.mean(data_z):.3f}, std={np.std(data_z):.3f}")

    return data_z



def load_data(
    P_list: list,
    z_score_norm: str = "global", 
    path: str = None,
    print_info: bool = True,
):
    """
    Load EIT and torque data with optional normalization methods:
      - "none":             no z-scoring at all
      - "global":           one global z-score over the entire X array (default)
      - "participant":      each participant's time series z-scored independently
      - "participant_meanfree": remove each participant's mean then global z-score
    """
    if print_info:
        print("Loading participants:", P_list)
        print("Normalization method:", z_score_norm)

    X, Y, P = [], [], []

    for Ps in tqdm(P_list, total=len(P_list), desc="Loading data"):
        Xs, Ys, Ps_list = [], [], []
        folder = join(path, Ps)
        files  = sorted(glob(join(folder, "*.npz")))
        if not files:
            print(f"⚠️  No files for {Ps} in {folder}")
            continue

        for file in files:
            data = np.load(file, allow_pickle=True)
            Xs.append(np.abs(data["eit"]))
            Ys.append(data["torque"])
            Ps_list.append(Ps)

        Xs = np.array(Xs)  # shape (n_samples, ...)
        # per-participant methods
        if z_score_norm == "participant":
            if print_info: print(f"P{Ps}: participant z-scoring")
            Xs = z_score(Xs, print_info)
        elif z_score_norm == "participant_meanfree":
            if print_info: print(f"P{Ps}: mean-free → global z-scoring")
            Xs_mean = np.mean(Xs, axis=0)
            Xs      = z_score(Xs - Xs_mean, print_info)

        # else: "none" or "global" → leave Xs raw for now

        X.extend(Xs)
        Y.extend(Ys)
        P.extend(Ps_list)

    X = np.array(X)
    Y = np.array(Y)
    P = np.array(P)

    # flatten each sample to 1D
    if X.ndim > 2:
        n_samples = X.shape[0]
        X = X.reshape(n_samples, -1)   # now (n_samples, 256*256)
        
    # global z-scoring, if requested
    if z_score_norm == "global":
        if print_info: print("Applying GLOBAL z-score to entire dataset")
        X = z_score(X, print_info)

    return X, Y, P




def plot_pca_by_participant(X, P, method_name, output_dir="PCA_outputs", show_plot: bool = True, show_legend: bool = True):
    """
    Projects the data using PCA and creates a scatter plot of the first two components,
    coloring each point by participant ID with maximally distinct colors.
    Optionally shows the legend.
    """
    if X.size == 0:
        print(f"❌ Skipping PCA for '{method_name}' — No data")
        return

    # PCA projection
    pca    = PCA(n_components=2)
    X_pca  = pca.fit_transform(X)
    varrat = pca.explained_variance_ratio_

    # Prepare maximally distinct colors
    unique_parts = np.unique(P)
    n_parts      = len(unique_parts)
    # Use tab20, Set3, or hsv palette depending on number of participants
    colors = sns.color_palette("hsv", n_parts)

    plt.figure(figsize=(8, 6))
    for idx, p in enumerate(unique_parts):
        mask = (P == p)
        plt.scatter(
            X_pca[mask, 0], X_pca[mask, 1],
            color=[colors[idx]],
            label=f"{p}",
            alpha=0.8,
            edgecolor='k',
            linewidth=0.5,
            s=60
        )

    # Title & labels
    plt.title(
        f"PCA ({method_name})",
        fontsize=18, pad=12
    )
    plt.xlabel(f"PC1({varrat[0]:.2f})", fontsize=14)
    plt.ylabel(f"PC2({varrat[1]:.2f})", fontsize=14)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)

    # Legend outside (optional)
    if show_legend:
        leg = plt.legend(
            title="Participant",
            bbox_to_anchor=(1.02, 1),
            loc='upper left',
            fontsize=10,
            title_fontsize=12,
            frameon=True
        )
        leg.get_frame().set_edgecolor('gray')

    plt.tight_layout()

    # Save & show
    os.makedirs(output_dir, exist_ok=True)
    save_path = join(output_dir, f"PCA_scatter_{method_name.replace(' ','_')}.png")
    plt.savefig(save_path, format="png", dpi=300)
    print(f"✅ Saved PCA scatter: {save_path}")

    if show_plot:
        plt.show()
    plt.close()
