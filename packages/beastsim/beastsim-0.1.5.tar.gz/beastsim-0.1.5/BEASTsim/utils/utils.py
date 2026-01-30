import os
from tqdm import tqdm
from anndata import AnnData
from typing import List, Optional, Tuple, Union, Dict
from numpy import ndarray
from pandas import DataFrame, Series, isna, notna
from pathlib import Path

from BEASTsim.beast_data import BEAST_Data

def _save_data(data: Dict[str, Union[DataFrame, Series]], filename: str):
    """Save the normalized benchmark results to a file."""
    from pickle import dump
    with open(filename, "wb") as f:
        dump(data, f)

def _load_data(filename: str) -> Dict[str, Union[DataFrame, Series]]:
    """Load the normalized benchmark results from a file."""
    from pickle import load
    with open(filename, "rb") as f:
        return load(f)

def _normalize_benchmark_results(data: Dict[str, Union[DataFrame, Series]], min=None, max=None) -> Dict[str, Union[DataFrame, Series]]:
    from pandas import concat, Series
    # Convert all Series to DataFrames for consistent processing
    data = {key: (df.to_frame() if isinstance(df, Series) else df) for key, df in data.items()}

    # Concatenate all data for row-wise min-max normalization
    combined_data = concat(data.values(), axis=1)

    row_min = combined_data.min(axis=1, skipna=True) if min is None else Series(min, index=combined_data.index)
    row_max = combined_data.max(axis=1, skipna=True) if max is None else Series(max, index=combined_data.index)

    row_range = row_max - row_min
    row_range[row_range == 0] = 1  # Prevent division by zero for constant rows

    # Normalize data
    normalized_data = {
        key: (df.iloc[:, 0] - row_min) / row_range
        for key, df in data.items()
    }

    # Fill NaN values with 0
    normalized_data = {key: df.fillna(0) for key, df in normalized_data.items()}



    # Filter out rows where all values are identical across benchmarks
    filtered_indices = (combined_data.nunique(axis=1) > 1)
    normalized_data = {key: df[filtered_indices] for key, df in normalized_data.items()}

    # Convert back to Series if original input was a Series
    normalized_data = {
        key: df.iloc[:, 0] if isinstance(data[key], Series) else df
        for key, df in normalized_data.items()
    }

    return normalized_data

def _merge_results(data: List[Dict[str, Series]], score_title: str) -> Dict[str, Series]:
    from collections import defaultdict
    from pandas import concat

    merged_results = defaultdict(lambda: Series(dtype="float64"))  # Initialize empty Series

    for benchmark_result in data:  # Each benchmark's result is a dict
        for sim_name, scores in benchmark_result.items():
            merged_results[sim_name] = concat([merged_results[sim_name], scores])

    merged_results = {k: v.rename(score_title) for k, v in merged_results.items()}
    return merged_results

def _clean(attributes: List[str], fields: List[str], data):
    for attr in attributes:
        for field in fields:
            if field in getattr(data.data, attr, {}):
                del getattr(data.data, attr)[field]

def _use_ground_truth(use_ground_truth: str, real: BEAST_Data, sim_data: List[BEAST_Data]) -> Optional[List[BEAST_Data]]:
    from copy import deepcopy
    def _create_copy(name_suffix: str) -> BEAST_Data:
        copied_data = deepcopy(real)
        copied_data.name = f"{name_suffix}-{real.name}"
        copied_data.is_simulated = True
        if name_suffix == "Variance":
            if "centroids" in copied_data.data.uns:
                _clean(attributes=["obs"], fields=["cell_type"], data=copied_data)
                _clean(attributes=["uns"], fields=["centroids"], data=copied_data)
                _clean(attributes=["obsm"], fields=["cell_type_distribution"], data=copied_data)
            elif "voxelized_subdata" in copied_data.data.uns:
                _clean(attributes=["uns"], fields=["voxelized_subdata"], data=copied_data)
            _clean(attributes=["var"], fields=["q_val", "p_val"], data=copied_data)
        return copied_data

    if not real.copied:
        if use_ground_truth.lower() == 'real':
            sim_data.append(_create_copy(name_suffix="GT"))
        elif use_ground_truth.lower() == 'variance':
            sim_data.append(_create_copy(name_suffix="Variance"))
        elif use_ground_truth.lower() == 'both':
            sim_data.append(_create_copy(name_suffix="GT"))
            sim_data.append(_create_copy(name_suffix="Variance"))
        else:
            return None
    else:
        return None
    real.copied = True
    return sim_data

def _replace_nan_with_zero(obj):
    import math
    if isinstance(obj, list):
        return [_replace_nan_with_zero(x) for x in obj]  # Recursively process lists
    elif isinstance(obj, float) and math.isnan(obj):
        return 0  # Replace NaN with 0
    else:
        return obj  # Keep everything else unchanged


def _unwrap_array(array):
    """
    Unwraps the input if it's a list or array with a single element that itself is an array.

    Args:
        array (Any): Possibly wrapped array.

    Returns:
        Unwrapped array.
    """
    import numpy as np

    if isinstance(array, list) and len(array) == 1 and isinstance(array[0], (list, np.ndarray)):
        return array[0]
    elif isinstance(array, np.ndarray) and array.ndim == 1 and len(array) == 1 and isinstance(array[0], np.ndarray):
        return array[0]
    else:
        return array


def _format_name_html(name: str, max_length: int = 15) -> str:
    """
    Formats a string by replacing underscores with spaces, preserving existing capitalization,
    capitalizing words only if they start with a lowercase letter, and inserting <br>
    when the name exceeds a certain length.

    Args:
        name (str): The input string to format.
        max_length (int): The maximum length before inserting a <br>.

    Returns:
        str: The formatted string with appropriate capitalization and <br> for long names.
    """
    import textwrap

    # Replace underscores with spaces
    formatted_name = " ".join(
        word.capitalize() if word and word[0].islower() else word
        for word in name.replace("_", " ").split()
    )

    # Insert <br> if the string is too long
    return "<br>".join(textwrap.wrap(formatted_name, max_length))

def _cluster_cell_distributions(cell_distributions: DataFrame, k_start: int = 2, k_end: int = 10,
                                weights: dict = {"silhouette": 0.5, "davies": 0.5}, seed: int = 42) -> \
tuple[List[tuple[int, float]], List[List[float]]]:
    """
    Perform KMeans clustering on cell type distributions and output cluster centroids.
    The optimal number of clusters is selected using silhouette score and Davies Bouldin index.

    Args:
        cell_distributions (DataFrame): Pandas DataFrame where rows are cells and columns are cell type distributions.
        k_start (int): The starting number of clusters for KMeans.
        k_end (int): The ending number of clusters for KMeans.
        weights (dict): Weights for the different clustering evaluation metrics (silhouette, davies).
        seed (int): Random seed for reproducibility.

    Returns:
        tuple: A tuple containing the ranking of the number of clusters based on the weighted sum and
               the centroids of the best KMeans model.
    """
    from sklearn.cluster import KMeans
    from numpy import log
    def _run_kmeans(k_start: int, k_end: int, data: ndarray, random_state: int = 42) -> List[KMeans]:
        """
        Run KMeans clustering for a range of cluster numbers and return the trained models.

        Args:
            k_start (int): The starting number of clusters (inclusive).
            k_end (int): The ending number of clusters (inclusive).
            data (ndarray): The dataset to be clustered.
            random_state (int, optional): The random seed for reproducibility. Default is 42.

        Returns:
            list: A list of trained KMeans models, one for each number of clusters in the specified range.
        """
        models = []
        for k in range(k_start, k_end + 1):
            kmeans = KMeans(n_clusters=k, init="k-means++", random_state=random_state)
            kmeans.fit(data)
            models.append(kmeans)
        return models

    def _calc_silhouette(k_start: int, k_end: int, models: List[KMeans], data: ndarray) -> List[tuple[int, float]]:
        """
        Calculate the silhouette scores for a range of clusters and return them sorted from best to worst.

        Args:
            k_start (int): The starting number of clusters (inclusive).
            k_end (int): The ending number of clusters (inclusive).
            models (list): A list of trained KMeans models corresponding to the cluster range.
            data (ndarray): The dataset used for clustering.

        Returns:
            list: A list of tuples where each tuple contains:
                  - The number of clusters (k).
                  - The silhouette score for that clustering.
                  The list is sorted in descending order by silhouette score.
        """
        from sklearn.metrics import silhouette_score
        s_scores = []
        ks = list(range(k_start, k_end + 1))
        for k, model in list(zip(ks, models)):
            s_score = silhouette_score(data, model.labels_)
            s_scores.append((k, s_score))
        s_scores = sorted(s_scores, key=lambda x: x[1], reverse=True)
        return s_scores

    def _calc_davies_bouldin(k_start: int, k_end: int, models: List[KMeans], data: ndarray) -> List[
        tuple[int, float]]:
        """
        Calculate the Davies-Bouldin Index (DBI) for a range of clusters and return them sorted from best to worst.

        Args:
            k_start (int): The starting number of clusters (inclusive).
            k_end (int): The ending number of clusters (inclusive).
            models (list): A list of trained KMeans models corresponding to the cluster range.
            data (ndarray): The dataset used for clustering.

        Returns:
            list: A list of tuples where each tuple contains:
                  - The number of clusters (k).
                  - The Davies-Bouldin Index for that clustering.
                  The list is sorted in ascending order by DBI score.
        """
        from sklearn.metrics import pairwise_distances
        from numpy import array, mean, inf, linalg

        dbi_scores = []
        ks = list(range(k_start, k_end + 1))

        for k, model in zip(ks, models):
            labels = model.labels_
            centroids = array([data[labels == i].mean(axis=0) for i in range(k)])

            scatter = []
            for i in range(k):
                cluster_points = data[labels == i]
                dist = pairwise_distances(cluster_points, [centroids[i]])
                scatter.append(mean(dist))

            db_index = 0.0
            for i in range(k):
                max_ratio = -inf
                for j in range(k):
                    if i != j:
                        inter_cluster_dist = linalg.norm(centroids[i] - centroids[j])
                        ratio = (scatter[i] + scatter[j]) / inter_cluster_dist
                        max_ratio = max(max_ratio, ratio)
                db_index += max_ratio

            dbi_scores.append((k, db_index / k))

        dbi_scores = sorted(dbi_scores, key=lambda x: x[1])

        return dbi_scores

    if not isinstance(cell_distributions, ndarray):
        data = cell_distributions.to_numpy()
    else:
        data = cell_distributions

    models = _run_kmeans(k_start=k_start, k_end=k_end, data=data, random_state=seed)

    # Silhouette
    s_scores = _calc_silhouette(k_start=k_start, k_end=k_end, models=models, data=data)
    s_scores = [(k, (score - min(s_scores, key=lambda x: x[1])[1]) / (
            max(s_scores, key=lambda x: x[1])[1] - min(s_scores, key=lambda x: x[1])[1])) for k, score in s_scores]

    # Davies Bouldin
    dbi_scores = _calc_davies_bouldin(k_start=k_start, k_end=k_end, models=models, data=data)
    dbi_scores = [(k, 1 - (score - min(dbi_scores, key=lambda x: x[1])[1]) / (
            max(dbi_scores, key=lambda x: x[1])[1] - min(dbi_scores, key=lambda x: x[1])[1])) for k, score in
                  dbi_scores]

    weights = {k: v / sum(weights.values()) for k, v in weights.items()} # Normalize the weights

    weighted_sums = []
    for k in range(k_start, k_end + 1):
        sil_score = dict(s_scores).get(k, 0)
        davies_score = dict(dbi_scores).get(k, 0)

        weighted_sum = (weights["silhouette"] * sil_score) + \
                       (weights["davies"] * davies_score)

        weighted_sums.append((k, weighted_sum))

    # Ranking (higher is better)
    ranking = sorted(weighted_sums, key=lambda x: x[1], reverse=True)

    best_k = ranking[0][0]
    best_kmeans = models[best_k - k_start]
    centroids = best_kmeans.cluster_centers_

    return ranking, centroids

def _find_project_root(start_path, marker="BEASTsim"):
    """
    Traverse upwards to find the project root directory.
    """
    current_dir = start_path
    while current_dir != os.path.dirname(current_dir):
        if marker in os.listdir(current_dir):
            return current_dir
        current_dir = os.path.dirname(current_dir)
    return None

def _trunc(values, decs=0):
    from numpy import trunc
    return trunc(values * 10 ** decs) / (10 ** decs)

def _num_of_types(adata):
    return len(adata.obs['cell_type'].astype('category').cat.categories)

def _init_dir(path):
    os.makedirs(path, exist_ok=True)

def _cpm(x: ndarray, log: bool = False) -> ndarray:
    """
    Transforms the exact count matrix into the Counts Per Million (CPM) matrix, which may be used according to
    preferance in several benchmarks instead of the raw data

    Args:
        x (ndarray): Input array of counts where rows represent genes and columns represent samples.

        log (bool): If True, applies a log2 transformation to the CPM values after calculation. Default is False.

    Returns:
        ndarray: An array of CPM values. If log is True, returns log2-transformed CPM values.
    """
    from numpy import log2, array
    if log:
        r = log2(1e+6 * x / x.sum(axis=0) + 1)
    else:
        r = 1e+6 * x / x.sum(axis=0)
    return array(r)


def _build_statistical_dataframe(simulated_data: list, real_data=None, names: list[str] = []) -> DataFrame:
    from numpy import isscalar
    dict = {}
    if real_data is not None:
        dict = {"Real": real_data}
    for i, method_name in enumerate(names):
        if isscalar(simulated_data[i]):
            simulated_data[i] = [simulated_data[i]]  # Wrap scalar in list
        elif isinstance(simulated_data[i], (list, ndarray)):
            # Ensure it's already iterable, nothing to change
            pass
        else:
            # Handle other cases if necessary
            raise ValueError(f"Unexpected data type for simulated_data[{i}]: {type(simulated_data[i])}")
        dict[method_name] = simulated_data[i]
    df = DataFrame(dict)
    return df

def _init_colors(method_names):
    method_colors = {"Real": "blue"}
    colors = ["green", "red", "orange", "pink", "yellow"]
    for i, method_name in enumerate(method_names):
        if method_name != "Real":
            method_colors[method_name] = colors[i]
    return method_colors

def _find_closest_points_distance(adata, x_col="X", y_col="Y"):
    from numpy import inf, linalg
    # Extract coordinates
    coords = adata.obs[[x_col, y_col]].to_numpy()

    # Compute pairwise distances
    num_points = coords.shape[0]
    min_distance = inf

    for i in range(num_points):
        for j in range(i + 1, num_points):
            dist = linalg.norm(coords[i] - coords[j])
            if dist < min_distance:
                min_distance = dist

    return min_distance

def _calc_cell_type_neighborhoods(datasets, ct):
    from collections import namedtuple
    from numpy import sort, unique, append, argsort, diff, max, zeros, where, sum

    nh_list = []
    cell_types = []
    cell_types_n = []
    for i, ST in enumerate(datasets):
        x = ST.obs.X.values
        y = ST.obs.Y.values
        ## TODO: GET CELLTYPES USING CELL2LOCATION

        if i == 0:
            cell_types = sort(unique(ct[i]))
            cell_types_n = append(cell_types, "empty")

        sorted_indices = argsort(x)

        sorted_x = x[sorted_indices]
        sorted_y = y[sorted_indices]
        sorted_ct = ct[sorted_indices]

        min_x = min(sorted_x)
        min_y = min(sorted_y)

        sorted_x = sorted_x - min_x
        sorted_y = sorted_y - min_y

        unqiue_x = unique(sorted_x)
        dist_x = max(diff(unqiue_x))

        unqiue_y = unique(sorted_y)
        dist_y = max(diff(unqiue_y)) * 2

        dict = {}
        PointSetWithInteger = namedtuple(
            "PointSetWithInteger", ["neighbors", "cell_type"]
        )
        for idx, (x1, y1, ct) in tqdm(
            enumerate(zip(sorted_x, sorted_y, sorted_ct))
        ):
            points = []
            for jdx, (x2, y2) in enumerate(zip(sorted_x, sorted_y)):
                if x1 == x2 and y1 == y2:
                    continue
                if abs(x1 - x2) <= dist_x and abs(y1 - y2) <= dist_y:
                    points.append((x2, y2))
            dict[(x1, y1)] = PointSetWithInteger(set(points), ct)

        n_ct = len(unique(sorted_ct))
        ct_dist = zeros(n_ct)
        for key, val in dict.items():
            cell_type = val.cell_type
            idx = where(cell_types_n == cell_type)[0][0]
            ct_dist[idx] += 1
        ct_dist /= sum(ct_dist)

        nh_dist = zeros((n_ct, n_ct + 1))
        for key, val in dict.items():
            cell_type = val.cell_type
            idx = where(cell_types_n == cell_type)[0][0]
            neighbors = val.neighbors
            for neighbor in neighbors:
                n_cell_type = dict[neighbor].cell_type
                jdx = where(cell_types_n == n_cell_type)[0][0]
                nh_dist[idx][jdx] += 1
            nh_dist[idx][n_ct] += 6 - len(neighbors)

        for i in range(len(nh_dist)):
            nh_dist[i] /= sum(nh_dist[i])

        nh_list.append(nh_dist)
    return nh_list, cell_types, cell_types_n


def _calculate_ks(gt, pred):
    from scipy.stats import ks_2samp

    statistic, pvalue = ks_2samp(gt.flatten(), pred.flatten())
    return statistic, pvalue


def _init_spot_size(dataset):
    import math
    min_dist = math.inf
    for data in dataset:
        dist = _find_closest_points_distance(data)
        if dist < min_dist:
            min_dist = dist
    spot_size = min_dist * 0.75
    return spot_size


def _cluster_cells_into_pseudospots(adata, n_spots=500, cell_type_keys=['cell_type', 'cell_type_distribution']):
    """
    Clusters single cells into pseudo-spots and attaches a spot-level AnnData object at .uns['voxelized_subdata'].

    Mimics Visium-style spatial transcriptomics by k-means clustering the 2-D
    cell coordinates, then summing gene counts within each cluster (“pseudo-spot”).
    Centroid coordinates, per-spot cell counts, and optional cell-type
    compositions are calculated and stored.

    The resulting spot-level dataset is placed in
    `adata.uns['voxelized_subdata']`, while the original AnnData gains
    `obs['pseudo_spot']` labels and an updated `.obsm['spatial']` matrix.

    Parameters
    ----------
    adata : AnnData
        Single-cell expression object containing per-cell X/Y coordinates
        in `obs['X']` and `obs['Y']`.
    n_spots : int, default 500
        Number of k-means clusters (i.e. pseudo-spots) to generate.
    cell_type_keys : list[str], default ['cell_type', 'cell_type_distribution']
        Two keys to look for cell-type information:
        1. `obs[cell_type_keys[0]]` – categorical cell-type labels.
        2. `obsm[cell_type_keys[1]]` – per-cell probability/fraction vectors.
        The second key is preferred; if absent, the categorical labels are
        one-hot–encoded and aggregated to spot-level proportions.

    Returns
    -------
    AnnData
        The same `adata` object, augmented with:
        * `obs['pseudo_spot']` : cluster label for each cell.
        * `obsm['spatial']`    : n_cells × 2 array of X/Y coordinates
                                 (overwritten/created).
        * `uns['voxelized_subdata']` : new AnnData whose
          ├─ obs rows represent pseudo-spots
          ├─ X/Y stored in `.obsm['spatial']` and copied to `obs['X']`,`obs['Y']`
          ├─ `.X` (or `.layers['counts']`) holds summed gene counts
          ├─ `obs['cell_counts']` gives contributing cell numbers
          └─ `.obsm['cell_type_distribution']` (optional) stores per-spot
             cell-type fractions.

    Notes
    -----
    * K-means is initialised with `random_state=42` for reproducibility.
    * If `x_bin`/`y_bin` columns exist, their means (instead of raw X/Y) are
      used for spot centroids, enabling compatibility with pre-binned data.
    * Each row of the spot-level cell-type distribution sums to 1; NaNs
      (possible only for empty spots) are replaced with 0.
    """
    from pandas import get_dummies
    from sklearn.cluster import KMeans
    from numpy import vstack
    adata.obsm['spatial'] = vstack([adata.obs['X'].values, adata.obs['Y'].values]).T
    spatial_coords = adata.obsm['spatial']
    kmeans = KMeans(n_clusters=n_spots, random_state=42).fit(spatial_coords)
    adata.obs['pseudo_spot'] = kmeans.labels_
    clustered_expression = adata.to_df().groupby(adata.obs['pseudo_spot']).sum()
    clustered_expression.index = clustered_expression.index.astype(str)
    pseudo_spot_coords = (
        adata.obs.groupby("pseudo_spot")[["x_bin", "y_bin"]].mean().values
        if "x_bin" in adata.obs and "y_bin" in adata.obs
        else adata.obs.groupby("pseudo_spot")[["X", "Y"]].mean().values
    )
    cell_counts = adata.obs["pseudo_spot"].value_counts().sort_index()
    if cell_type_keys[1] in adata.obsm:
        ctd_df = DataFrame(adata.obsm[cell_type_keys[1]], index=adata.obs.index)
        aggregated_ctd = ctd_df.groupby(adata.obs["pseudo_spot"]).mean().values
    elif cell_type_keys[0] in adata.obs:
        print(f'No cell type distribution found under name {cell_type_keys[1]}. Trying categorical cell types.')
        one_hot_ctd = get_dummies(adata.obs[cell_type_keys[0]]).reindex(columns=adata.obs[cell_type_keys[0]].cat.categories, fill_value=0)
        aggregated_ctd = one_hot_ctd.groupby(adata.obs["pseudo_spot"]).sum()
        aggregated_ctd = (aggregated_ctd.T / aggregated_ctd.sum(axis=1)).T.fillna(0).values
    else:
        print(
            f'No cell type distribution found under name {cell_type_keys[1]}. No categorical cell types found under name {cell_type_keys[0]}')
        aggregated_ctd = None
    new_adata = AnnData(clustered_expression)
    new_adata.obsm['spatial'] = pseudo_spot_coords
    new_adata.obs["X"] = new_adata.obsm["spatial"][:, 0]
    new_adata.obs["Y"] = new_adata.obsm["spatial"][:, 1]
    new_adata.obs['cell_counts'] = cell_counts.values
    if aggregated_ctd is not None:
        new_adata.obsm['cell_type_distribution'] = aggregated_ctd
    adata.uns['voxelized_subdata'] = new_adata
    return adata

#HELPER FUNCTION 1
# Assumption: SCE.var, SRT.var and SCE.obs_names, SRT.obs_names have matching genes, but maybe in a different order
# This function checks these assumptions, non-matching elements result in an error, matching elements
# with different order result in a copy of input anndata objects reordered so that they match
def _reorder_mtx(adata_real: AnnData, adata_sim: AnnData, intersect_genes: bool = False) -> Tuple[AnnData, AnnData]:
    """
    Reorders two AnnData objects according to a mutually matching gene order.
    Parameters:
        adata_real (AnnData): The first input AnnData object, typically containing real gene expression data.
        adata_sim (AnnData): The second input AnnData object, typically containing simulated gene expression data.
        intersect_genes (bool): If False, raises an error when the gene sets do not exactly match.
                                If True, only common genes are retained and reordered.
    Returns:
        Tuple[AnnData, AnnData]: The two AnnData objects with matching gene orders (optionally subsetted genes in case of mismatch).
    """
    from numpy import intersect1d
    df_real = adata_real.copy()
    df_sim = adata_sim.copy()
    genes_real = df_real.var['gene_id'].values
    genes_sim = df_sim.var['gene_id'].values
    mtx_sim = df_sim.X
    common_genes, gene_idx_real, gene_idx_sim = intersect1d(genes_real, genes_sim, return_indices=True)
    if len(gene_idx_sim) != mtx_sim.shape[1] and not intersect_genes:
        raise ValueError('Some gene names occur only in one of the datasets')
    else:
        df_sim = df_sim[:, gene_idx_sim].copy()
        df_real = df_real[:, gene_idx_real].copy()
        return df_real, df_sim

#HELPER FUNCTION 2
# This function transforms the locations of spatial data into a bounding square along x and y with side length = scale
# Should be called before grid transformation according to use (e.g, 1 if no rotation, scale 1/sqrt(2) if we rotate)
def _square_normalize(adata: AnnData, scale: float = 1) -> AnnData:
    """
    Normalizes the spatial coordinates (X, Y) of an AnnData object so that they fit within a square bounding box.

    Parameters:
        adata (AnnData): Input AnnData object with 2D spatial (X, Y) coordinates stored in 'obs' under keys 'X' and 'Y' respectively.
        scale (float): Desired size of the square's sides (default is 1).
                       For example, use 1 for full normalization or 1/√2 if a rotation will follow to make sure they stay inside [0,1]^2.
    Returns:
        AnnData: A new AnnData object with normalized spatial coordinates for the cells.
    """
    from numpy import min, max
    normalized = adata.copy()
    x = normalized.obs['X'].values
    y = normalized.obs['Y'].values
    Tx = scale * (x - min(x)) / (max(x) - min(x)) + (1 - scale) / 2
    Ty = scale * (y - min(y)) / (max(y) - min(y)) + (1 - scale) / 2
    normalized.obs['X'] = Tx
    normalized.obs['Y'] = Ty
    return normalized

#HELPER FUNCTION 3
# This function adds expression matrix with only svgs to anndata, should be performed before grid_tranforms.
# Should use genes=None, threshold=1, if one wants every gene.
def _add_svg_matrix(adata_real: AnnData, adata_sim: AnnData, GP_real: Optional[list] = None,
                   GP_sim: Optional[ndarray] = None, alpha: float = 0.05, threshold: float = 0.5,
                   genes: Optional[ndarray] = None, intersect_genes: bool = True,
                   only_abundance1: bool = True, only_abundance2: bool = False) -> Tuple[AnnData, AnnData]:
    """
    Adds a spatially variable gene (SVG) expression matrix to the .obsm slot of both real and simulated AnnData objects.

    This should be called prior to grid transformations. Filters genes based on SVG significance (usually based on SpatialDE) and expression abundance.

    Parameters:
        adata_real (AnnData): Real gene expression data.
        adata_sim (AnnData): Simulated gene expression data.
        GP_real (Optional[ndarray]): Gene-Probability double vector for real data (2D array: gene IDs and p-values). Defaults to None.
        GP_sim (Optional[ndarray]): Gene-Probability double vector for simulated data (2D array: gene IDs and p-values). Defaults to None.
        alpha (float): Significance threshold for SVG detection (default: 0.05).
        threshold (float): Maximum proportion of cells in which a gene may be expressed to be retained.
        genes (Optional[ndarray]): Specific set of genes to include. If None, automatically intersect SVGs from both sets.
        intersect_genes (bool): Whether to require exact matching of genes before processing (via `reorder_mtx`).
        only_abundance1 (bool): If True, binarizes expression for filtering.
        only_abundance2 (bool): If True, filters using binarized presence only (disregards abundance).
    Returns:
        Tuple[AnnData, AnnData]: The input AnnData objects with `.obsm['SVG']` populated.
    """
    from numpy import vstack, zeros, intersect1d, sum, max, newaxis, array
    adata_real, adata_sim = _reorder_mtx(adata_real, adata_sim, intersect_genes=intersect_genes)
    gene_names_real = adata_real.var['gene_id'].values
    gene_names_sim = adata_sim.var['gene_id'].values
    if GP_real is None:
        GP_real = vstack((gene_names_real, zeros(len(gene_names_real))))
    else:
        GP_real = GP_real
    if GP_sim is None:
        GP_sim = vstack((gene_names_sim, zeros(len(gene_names_sim))))
    else:
        GP_sim = GP_sim
    if genes is not None:
        genes = genes
    else:
        genes = None

    def _SVG_significance_test(GP, alpha=0.05, versions = True):
        if versions:
            GP = tuple(array(gp) for gp in GP)
            keep = GP[1] <= alpha

            result = tuple(gp[keep] for gp in GP)
        else:
            keep = GP[1] <= alpha
            result = GP[:, keep]
        return result

    def _get_common_indices(genes):
        common_indices_real = intersect1d(gene_names_real, genes, return_indices=True)[1]
        common_indices_sim = intersect1d(gene_names_sim, genes, return_indices=True)[1]
        if len(common_indices_real) != len(common_indices_sim):
            raise ValueError('Some of the given genes appear in only one of the datasets')
        return common_indices_real, common_indices_sim

    def _remove_above_threshold(SVG_matrix_real, SVG_matrix_sim, threshold=1, only_abundance1=True,
                               only_abundance2=False):
        M = SVG_matrix_real.shape[0]
        if only_abundance1:
            if only_abundance2:
                SVG_matrix_real_copy = SVG_matrix_real.copy()
                SVG_matrix_real_copy = (SVG_matrix_real_copy > 0).astype(int)
                keep = sum(SVG_matrix_real_copy, axis=0) / M <= threshold
            else:
                keep = sum(SVG_matrix_real, axis=0) / M <= threshold
        else:
            keep = sum(SVG_matrix_real, axis=0) / max(sum(SVG_matrix_real, axis=0)) <= threshold
        return SVG_matrix_real[:, keep], SVG_matrix_sim[:, keep]

        adata_real.obsm['SVG'] = SVG_matrix_real
        adata_sim.obsm['SVG'] = SVG_matrix_sim
        return adata_real, adata_sim

    SVG_real, SVG_sim = _SVG_significance_test(GP_real,alpha=alpha), _SVG_significance_test(GP_sim, alpha=alpha)
    common_genes = intersect1d(SVG_real[0], SVG_sim[0])
    if genes is None:
        common_indices_real, common_indices_sim = _get_common_indices(genes=common_genes)
    else:
        common_indices_real, common_indices_sim = _get_common_indices(genes=genes)

    if only_abundance1:
        SVG_matrix_real = (adata_real.X[:, common_indices_real] > 0).astype(int)
        SVG_matrix_sim = (adata_sim.X[:, common_indices_sim] > 0).astype(int)
    else:
        SVG_matrix_real = adata_real.X[:, common_indices_real]
        SVG_matrix_real = SVG_matrix_real * (1 / sum(SVG_matrix_real, axis=1))[:, newaxis]
        SVG_matrix_sim = adata_sim.X[:, common_indices_sim]
        SVG_matrix_sim = SVG_matrix_sim * (1 / sum(SVG_matrix_sim, axis=1))[:, newaxis]
    SVG_matrix_real, SVG_matrix_sim = _remove_above_threshold(SVG_matrix_real, SVG_matrix_sim,
                                                             threshold=threshold,
                                                             only_abundance1=only_abundance1,
                                                             only_abundance2=only_abundance2)
    adata_real.obsm['SVG'] = SVG_matrix_real
    adata_sim.obsm['SVG'] = SVG_matrix_sim
    return adata_real, adata_sim

#HELPER FUNCTION 4
# This function performs the grid transformation. It creates a new anndata object with new 'region_coordinates' and
# 'Region_ID' indices, 'neighbours' for neighbour coordinates, 'cell_type_distribution', 'ETD', 'SVG' distributions and 'cell_counts'
# inside regions
# Input anndata should already contain cell types 'adata.obs['cell_type']' and matrix for only svgs
# 'adata.obs['SVG']'. If CTD=True 'adata.obs['cell_type']' categorical CTs are used to create distribution vectors,
# otherwise if CTD=False adata.obsm['cell_type_distribution'] distribution vectors are used.
def _grid_transform(adata: AnnData, CTD: bool = True, gridsize: int = 4, show: bool = False,
                   figsize: int = 16, SVGD: bool = True) -> AnnData:
    """
    Performs a grid transformation on spatial data and returns a new AnnData object summarizing spatial features per grid region instead of cells.

    Parameters:
        adata (AnnData): Input AnnData object containing cell-level data with:
                         - adata.obs['cell_type']: categorical labels or
                         - adata.obsm['cell_type_distribution']: precomputed distributions
                         - adata.obsm['SVG']: spatially variable gene matrix
        CTD (bool): If True, use categorical cell types; if False, use precomputed cell type distributions.
        gridsize (int): Number of grid divisions along one axis (effective grid is (gridsize+2)^2 including borders, but borders are usually removed later).
        show (bool): If True, plots the grid overlay and cell counts to visualize the transformation.
        figsize (int): Size of the plot if show=True.
        SVGD (bool): If False, binarizes the SVG matrix across the grid.

    Returns:
        AnnData: A new AnnData object where each observation corresponds to a grid region with aggregated features.
    """
    from numpy import zeros, floor, sum, float32, array
    from pandas import get_dummies
    expMtx = adata.X.T
    N = expMtx.shape[0]
    M = expMtx.shape[1]
    k = gridsize
    gridsize = gridsize + 2
    if CTD:
        if 'cell_type' in adata.obs:
            CT = adata.obs['cell_type']
            ctMtx = (get_dummies(CT).astype(int)).values
        elif 'cell_type_distribution' in adata.obsm and CTD:
            ValueError("Provided data has no categorical cell types under .obs['cell_type'] in order to force use of categorical cell types.")
        else:
            ValueError("Provided data has no categorical cell types or cell type distributions under .obs['cell_type'] and .obsm['cell_type_distribution'] respectively.")
    else:
        if isinstance(adata.obsm['cell_type_distribution'], DataFrame):
            ctMtx = adata.obsm['cell_type_distribution'].values
        else:
            ctMtx = adata.obsm['cell_type_distribution']
    svgMtx = adata.obsm['SVG']
    m = ctMtx.shape[1]
    s = svgMtx.shape[1]
    x = adata.obs['X'].values
    y = adata.obs['Y'].values
    Txy = array([x, y]).T
    TexpMtx = zeros((N, k ** 2))
    TexpMtx_with_outside = zeros((N, gridsize ** 2))
    TctMtx = zeros((k ** 2, m + 1))
    TsvgMtx = zeros((k ** 2, s))
    TctMtx_with_outside = zeros((gridsize ** 2, m + 1))
    TsvgMtx_with_outside = zeros((gridsize ** 2, s))
    ETDMtx_with_outside = zeros((gridsize ** 2, 2))
    ETDMtx_with_outside[:, 1] = 1
    Tr = 1 + floor(k * Txy).astype(int)
    cell_counts_with_outside = zeros(gridsize ** 2)
    borders = array([(i - 1) / k for i in range(gridsize + 1)])
    grid_mid_points = [[(i - 0.5) / k, (j - 0.5) / k] for j in range(gridsize) for i in range(gridsize)]
    region_coordinates = array([[i, j] for j in range(gridsize) for i in range(gridsize)])
    region_indices = array([c[0] + gridsize * c[1] for c in region_coordinates])
    neighbours = array([[int(i - 1), int(i + 1), int(i + gridsize), int(i - gridsize), int(i + gridsize - 1),
                            int(i + gridsize + 1), int(i - gridsize + 1), int(i - gridsize - 1)] for i in
                           region_indices])
    for index, value in enumerate(Tr):
        if value[0] == k + 1:
            value[0] = k
        if value[1] == k + 1:
            value[1] = k
    for index, value in enumerate(Tr):
        cell_counts_with_outside[value[0] + value[1] * gridsize] += 1
    for index, value in enumerate(Tr):
        TexpMtx_with_outside[:, value[0] + value[1] * gridsize] += expMtx[:, index]
        if cell_counts_with_outside[value[0] + value[1] * gridsize] != 0:
            TsvgMtx_with_outside[value[0] + value[1] * gridsize, 0:s] += svgMtx[index] * 1 / (
            cell_counts_with_outside[value[0] + value[1] * gridsize])
            TctMtx_with_outside[value[0] + value[1] * gridsize, 0:m] += ctMtx[index] * 1 / (
            cell_counts_with_outside[value[0] + value[1] * gridsize])
            ETDMtx_with_outside[value[0] + value[1] * gridsize, 0] = 1
            ETDMtx_with_outside[value[0] + value[1] * gridsize, 1] = 0
        else:
            TctMtx_with_outside[value[0] + value[1] * gridsize, m] = 1
    if not SVGD:
        TsvgMtx_with_outside = (TsvgMtx_with_outside > 0).astype(int)

    for i in range(TctMtx_with_outside.shape[0]):
        if sum(TctMtx_with_outside[i]) == 0:
            TctMtx_with_outside[i, m] = 1
    # TODO: Save it instead of showing it
    if show:
        import matplotlib.pyplot as plt
        plt.figure(figsize=(figsize, figsize))
        plt.plot(x, y, '.', markersize=6, color='red')
        for i, p in enumerate(grid_mid_points):
            plt.text(p[0], p[1], str(cell_counts_with_outside[i]), fontsize=figsize, ha='center', weight="bold")
        for v in borders:
            plt.axvline(x=v, color='black', linestyle='--')
        for u in borders:
            plt.axhline(y=u, color='black', linestyle='--')
        plt.show()

    region_data = DataFrame(columns=['Region_ID', 'X', 'Y', 'm'])
    region_data['Region_ID'] = region_indices
    # for i in range(TctMtx_with_outside.shape[1]):
    #    region_data[str(i)] = TctMtx_with_outside[:,i]
    region_data['X'] = region_coordinates[:, 0]
    region_data['Y'] = region_coordinates[:, 1]
    genes = DataFrame(columns=['gene_id'])
    genes['gene_id'] = adata.var.index
    genes.index = adata.var.index

    result = AnnData(X=TexpMtx_with_outside.T.astype(float32), obs=region_data, var=genes)
    result.obsm['cell_type_distribution'] = TctMtx_with_outside
    # print(TctMtx_with_outside.shape)
    result.obsm['SVG'] = TsvgMtx_with_outside
    result.obsm['ETD'] = ETDMtx_with_outside
    result.obsm['neighbours'] = neighbours
    result.obs['cell_counts'] = cell_counts_with_outside
    result.k = k
    return result

def load_benchmarking_results(folder: str) -> dict:
    """
    Loads pickled benchmark result objects from a folder and organizes them into a nested dictionary.
    Parameters:
        folder (str): Path to the folder containing .pkl files. The expected file path format is name - data - genefiltering - BiologicalSignalsBenchmark-anything.pkl
    Returns:
        dict: Nested dictionary structured as data[dataset][method][benchmark] = loaded_object.
    """
    from pathlib import Path
    import pickle as pkl

    folder_path = Path(folder)
    data: dict = {}

    for pkl_path in folder_path.glob("*.pkl"):
        parts = [p.strip() for p in pkl_path.stem.split(" - ")]
        if len(parts) < 4:
            raise ValueError(f"Unexpected filename format: {pkl_path.name}")

        dataset = parts[1]
        method = parts[2]
        benchmark = parts[3].split("-")[0]

        obj = _load_pickle(pkl_path)

        data.setdefault(dataset, {}).setdefault(method, {})[benchmark] = obj

    return data

def summarize_benchmark_results(
    nested_results: dict,
    average_rank: bool,
    *,
    similarity_benchmark: str = "SimilarityBenchmark",
    similarity_global_metrics: tuple[str, ...] = ("CT_Global", "SVG_Global"),
    similarity_local_metrics: tuple[str, ...] = ("CT_Local", "SVG_Local"),
    rank_benchmarks: tuple[str, ...] = ("BiologicalSignalsBenchmark", "DataPropertyBenchmark"),
) -> tuple[dict, dict]:
    """
    Computes per-dataset, per-method summaries for multiple benchmark types.
    Parameters:
        nested_results (dict): Nested dictionary structured as data[dataset][method][benchmark] = scores/object.
        average_rank (bool): If True, compute mean rank across metrics per method. If False, compute mean score.
        similarity_benchmark (str): Benchmark name used for similarity scoring (default: "SimilarityBenchmark").
        similarity_global_metrics (tuple[str, ...]): Metrics retained for the global similarity view.
        similarity_local_metrics (tuple[str, ...]): Metrics retained for the local similarity view.
        rank_benchmarks (tuple[str, ...]): Benchmarks to treat as "rank-like" (no metric subsetting applied).
    Returns:
        Tuple[dict, dict]:
            - avg_scores: avg_scores[dataset][method][benchmark] = dict(method->value),
              where value is either rank/avg_rank or average score depending on average_rank.
            - sim_scores: sim_scores[dataset][method][SimilarityBenchmark] = (rank_dict, avg_score_dict)
              computed from the LOCAL similarity metrics (always raw mean scores, not avg-rank).
    """
    avg_scores: dict = {}
    sim_scores: dict = {}

    choice_idx = 0 if average_rank else 1

    for dataset_name, dataset_dict in nested_results.items():
        for method_name, method_dict in dataset_dict.items():
            for benchmark_name, scores in method_dict.items():

                if benchmark_name in rank_benchmarks:
                    rank_dict, avg_dict = compute_method_summary(scores, average_rank=average_rank)
                    avg_scores.setdefault(dataset_name, {}).setdefault(method_name, {})[benchmark_name] = (
                        [rank_dict, avg_dict][choice_idx]
                    )
                    continue

                if benchmark_name == similarity_benchmark:
                    filtered_global = {
                        k: _subset_metrics(v, similarity_global_metrics) for k, v in scores.items()
                    }
                    rank_dict, avg_dict = compute_method_summary(filtered_global, average_rank=average_rank)
                    avg_scores.setdefault(dataset_name, {}).setdefault(method_name, {})[benchmark_name] = (
                        [rank_dict, avg_dict][choice_idx]
                    )

                    filtered_local = {
                        k: _subset_metrics(v, similarity_local_metrics) for k, v in scores.items()
                    }
                    sim_scores.setdefault(dataset_name, {}).setdefault(method_name, {})[benchmark_name] = (
                        compute_method_summary(filtered_local, average_rank=False)
                    )
                    continue

                raise ValueError(f"{benchmark_name} is not a valid benchmark type")

    return avg_scores, sim_scores


def compute_method_summary(
    per_method_scores: dict,
    *,
    average_rank: bool,
    skip_methods: tuple[str, ...] = ("GT-real_spatial", "GT-real-st", "GT-real_st"),
    name_separator: str = "_",
    special_refs: Optional[dict] = None,
) -> tuple[dict, dict]:
    """
    Aggregates per-metric scores per method into (rank-like summary, mean-score summary).
    Parameters:
        per_method_scores (dict): Mapping {method_name: score_container}.
        average_rank (bool): If True, compute mean rank across metrics per method (lower is better).
                             If False, rank methods by their mean score (higher is better).
        skip_methods (tuple[str, ...]): Method keys to skip entirely.
        name_separator (str): Separator used to split method naming for canonicalization.
        special_refs (dict | None): Optional mapping {method: ref} to override inferred ref.
    Returns:
        Tuple[dict, dict]:
            - If average_rank is False: ({method: rank_of_mean_score}, {method: mean_score})
            - If average_rank is True:  ({method: mean_rank_across_metrics}, {method: mean_score})
    """
    import pandas as pd

    if special_refs is None:
        special_refs = {"spatialcoGCN": "rf"}

    series_by_method: dict[str, "pd.Series"] = {}

    for raw_name, scores in per_method_scores.items():
        if raw_name in skip_methods:
            continue

        canonical = _normalize_method_name(
            raw_name,
            separator=name_separator,
            special_refs=special_refs,
        )
        series_by_method[canonical] = _as_series(scores)

    scores_df = pd.DataFrame(series_by_method).T
    mean_score = scores_df.mean(axis=1, skipna=True)

    if not average_rank:
        rank_of_mean = mean_score.rank(ascending=False, method="min").astype(int)
        return rank_of_mean.to_dict(), mean_score.to_dict()

    ranks_per_metric = scores_df.rank(axis=0, ascending=False, method="average")
    avg_rank = ranks_per_metric.mean(axis=1, skipna=True)
    return avg_rank.to_dict(), mean_score.to_dict()


def build_raw_table(results: dict, benchmark_name: str = "SimilarityBenchmark") -> "object":
    """
    Builds a wide table of raw similarity scores (0..1) for each dataset-tool column.
    Parameters:
        results (dict): Nested dict results[dataset][tool][benchmark] = object.
        benchmark_name (str): Which benchmark key to extract (default: "SimilarityBenchmark").
    Returns:
        pandas.DataFrame: Table with raw scores and summary columns:
            - OverallSimilarity: row-wise mean of raw columns
            - AvgRank: mean of within-column ranks
            - OverallRank: rank of AvgRank (lower is better)
    """
    import pandas as pd

    raw_by_col: dict[str, "pd.Series"] = {}
    rank_by_col: dict[str, "pd.Series"] = {}

    for dataset, tools in results.items():
        for tool, benches in tools.items():
            if benchmark_name not in benches:
                continue

            col = f"{dataset}_{tool}"
            raw = pd.Series(_extract_raw_dict(benches[benchmark_name]), dtype=float)

            raw_by_col[col] = raw
            rank_by_col[col] = raw.rank(ascending=False, method="min").astype("Int64")

    df_raw = pd.DataFrame(raw_by_col)
    df_rank = pd.DataFrame(rank_by_col)

    df_raw["OverallSimilarity"] = df_raw.mean(axis=1, skipna=True)
    df_raw["AvgRank"] = df_rank.mean(axis=1, skipna=True)
    df_raw["OverallRank"] = df_raw["AvgRank"].rank(ascending=True, method="min").astype(int)

    return df_raw.sort_values(["OverallRank", "AvgRank"])


def build_similarity_category_table(
    results: dict,
    benchmark_name: str = "SimilarityBenchmark",
    *,
    thresholds: tuple[float, float] = (0.4, 0.8),
    labels: tuple[str, str, str] = ("Low", "Medium", "High"),
) -> "object":
    """
    Builds a wide table of categorical similarity labels for each dataset-tool column.
    Parameters:
        results (dict): Nested dict results[dataset][tool][benchmark] = object.
        benchmark_name (str): Which benchmark key to extract (default: "SimilarityBenchmark").
        thresholds (Tuple[float, float]): (medium_threshold, high_threshold).
        labels (Tuple[str, str, str]): (low_label, medium_label, high_label).
    Returns:
        pandas.DataFrame: Table with categorical entries and summary columns:
            - OverallSimilarityCategory: category of row-wise mean raw similarity
            - AvgRank: mean of within-column ranks computed from raw values
            - OverallRank: rank of AvgRank (lower is better)
    """
    import pandas as pd

    med_thr, high_thr = thresholds
    low_label, med_label, high_label = labels

    def categorize(s: "pd.Series") -> "pd.Series":
        out = pd.Series(pd.NA, index=s.index, dtype="object")
        out[s > high_thr] = high_label
        out[(s > med_thr) & (s <= high_thr)] = med_label
        out[s <= med_thr] = low_label
        return out

    raw_by_col: dict[str, "pd.Series"] = {}
    cat_by_col: dict[str, "pd.Series"] = {}
    rank_by_col: dict[str, "pd.Series"] = {}

    for dataset, tools in results.items():
        for tool, benches in tools.items():
            if benchmark_name not in benches:
                continue

            col = f"{dataset}_{tool}"
            raw = pd.Series(_extract_raw_dict(benches[benchmark_name]), dtype=float)

            raw_by_col[col] = raw
            cat_by_col[col] = categorize(raw)
            rank_by_col[col] = raw.rank(ascending=False, method="min").astype("Int64")

    df_raw = pd.DataFrame(raw_by_col)
    df_cat = pd.DataFrame(cat_by_col)
    df_rank = pd.DataFrame(rank_by_col)

    df_cat["OverallSimilarityCategory"] = categorize(df_raw.mean(axis=1, skipna=True))
    df_cat["AvgRank"] = df_rank.mean(axis=1, skipna=True)
    df_cat["OverallRank"] = df_cat["AvgRank"].rank(ascending=True, method="min").astype(int)

    return df_cat.sort_values(["OverallRank", "AvgRank"])


# -------------------------
# Internal helpers (private)
# -------------------------

def _extract_raw_dict(obj: object) -> dict:
    import pandas as pd  # only for isinstance checks in _as_series caller; harmless here

    if isinstance(obj, tuple) and len(obj) == 2:
        return obj[1]
    if isinstance(obj, dict):
        return obj
    raise TypeError(f"Unsupported format: {type(obj)}")


def _as_series(scores: object) -> "object":
    import pandas as pd

    if isinstance(scores, pd.DataFrame):
        if "KDE_Score" in scores.columns:
            s = scores["KDE_Score"].copy()
            s = (5 + s) / 5
            return s
        return scores.squeeze()

    if isinstance(scores, pd.Series):
        return scores

    return pd.Series(scores)


def _subset_metrics(obj: object, metrics: tuple[str, ...]) -> object:
    if hasattr(obj, "loc") and hasattr(obj, "index"):
        idx = obj.index.intersection(metrics)
        return obj.loc[idx].squeeze()
    return obj


def _normalize_method_name(raw_name: str, *, separator: str, special_refs: dict) -> str:
    parts = [p.strip() for p in raw_name.split(separator)]
    method = parts[0]

    if method in special_refs:
        ref = special_refs[method]
    else:
        ref = parts[1] if len(parts) > 1 else "na"
        ref = "rb" if ref == "rfb" else ref

    return f"{method}-{ref}"

def _load_pickle(path: Path):
    from pickle import load as pickle_load

    with open(path, "rb") as fh:
        return pickle_load(fh)

def load_benchmark_runs(directory: Path, pattern: str) -> list:
    files = sorted(directory.glob(pattern))
    return [_load_pickle(p) for p in files]

def _as_series(value: object, key: str) -> Series:
    if isinstance(value, Series):
        return value
    if isinstance(value, DataFrame):
        if value.shape[1] != 1:
            raise ValueError(f"{key} has {value.shape[1]} columns; expected 1.")
        return value.iloc[:, 0]
    raise TypeError(f"{key} has unsupported type {type(value)} (expected Series or 1-col DataFrame)")

def _validate_run_dict(run: dict, where: str) -> None:
    if not isinstance(run, dict) or len(run) == 0:
        raise ValueError(f"{where}: run is empty or not a dict")
    bad = {k: type(v) for k, v in run.items() if not isinstance(v, Series)}
    if bad:
        raise ValueError(f"{where}: non-Series values found: {bad}")


def remap_run_keys(run: dict, key_mapper) -> dict:
    return {key_mapper(k): v for k, v in run.items()}

def _set_metrics_nan(scores: Series, metric_names: list) -> Series:
    if not metric_names:
        return scores
    s = scores.copy()
    for metric in metric_names:
        if metric in s.index:
            s.loc[metric] = float("nan")
    return s

def normalize_scores_affine(
    raw_run: dict,
    *,
    offset: float,
    scale: float,
    nan_metrics_by_method: Optional[dict] = None,
    method_from_key=None,
) -> dict:
    if method_from_key is None:
        method_from_key = lambda k: k.split("_", 1)[0]

    out = {}
    for raw_key, raw_value in raw_run.items():
        method = method_from_key(raw_key)
        s = _as_series(raw_value, raw_key)

        if nan_metrics_by_method and method in nan_metrics_by_method:
            s = _set_metrics_nan(s, nan_metrics_by_method[method])

        out[raw_key] = offset + (s / scale)
    return out

def select_metrics(raw_run: dict, metrics: list) -> dict:
    out = {}
    for raw_key, raw_value in raw_run.items():
        s = _as_series(raw_value, raw_key)
        out[raw_key] = s.reindex(metrics)
    return out

def build_rank_matrices(runs: list, higher_is_better: bool = True, avg_rank_col: str = "AvgRank") -> list:
    ascending = not higher_is_better
    rank_mats = []

    for i, run in enumerate(runs):
        _validate_run_dict(run, where=f"build_rank_matrices[{i}]")

        score_df = DataFrame(run).T
        rank_df = score_df.rank(axis=0, ascending=ascending, method="average")
        rank_df[avg_rank_col] = rank_df.mean(axis=1)
        rank_df = rank_df.sort_values(avg_rank_col)

        rank_mats.append(rank_df)

    return rank_mats

def count_adjacent_wins(rank_matrices: list, method_order: list, avg_rank_col: str = "AvgRank") -> DataFrame:
    rows = []
    for better, worse in zip(method_order[:-1], method_order[1:]):
        wins = 0
        n = 0

        for df in rank_matrices:
            if better not in df.index or worse not in df.index or avg_rank_col not in df.columns:
                continue

            r_better = df.at[better, avg_rank_col]
            r_worse = df.at[worse, avg_rank_col]

            if isna(r_better) or isna(r_worse) or r_better == r_worse:
                continue

            n += 1
            if r_better < r_worse:
                wins += 1

        rows.append((better, wins, n))

    return DataFrame(rows, columns=["Method", "BetterThanNext", "OutOf"]).set_index("Method")

def _format_p_value(p: float) -> str:
    if isna(p):
        return "NA"
    return "< 0.001" if p < 0.001 else f"{p:.3f}"

def add_pairwise_binomial_stats(counts: DataFrame, alpha: float = 0.05) -> DataFrame:
    from scipy.stats import binomtest

    df = counts.copy()
    m = len(df)

    def p_value(wins: int, total: int) -> float:
        if total == 0:
            return float("nan")
        return binomtest(wins, total, p=0.5, alternative="greater").pvalue

    df["p_raw_numeric"] = [p_value(w, n) for w, n in zip(df["BetterThanNext"], df["OutOf"])]
    df["p_adj_numeric"] = (df["p_raw_numeric"] * m).clip(upper=1.0)
    df["Significant"] = df["p_adj_numeric"] < alpha

    df["p_raw"] = df["p_raw_numeric"].apply(_format_p_value)
    df["p_adj"] = df["p_adj_numeric"].apply(_format_p_value)

    return df[["BetterThanNext", "OutOf", "p_raw", "p_adj", "Significant"]]


def _classify_similarity(avg_similarity: float, low_thr: float, high_thr: float) -> str:
    if isna(avg_similarity):
        return float("nan")
    if avg_similarity <= low_thr:
        return "low"
    if avg_similarity <= high_thr:
        return "medium"
    return "high"


def similarity_class_per_run(
    sim_runs: list,
    metric_names: list,
    low_thr: float = 0.4,
    high_thr: float = 0.8,
) -> list:
    out = []
    for i, run in enumerate(sim_runs):
        _validate_run_dict(run, where=f"similarity_class_per_run[{i}]")
        score_df = DataFrame(run).T
        avg_sim = score_df[metric_names].mean(axis=1)
        out.append(avg_sim.apply(lambda x: _classify_similarity(x, low_thr=low_thr, high_thr=high_thr)))
    return out


def similarity_class_counts(sim_class_runs: list) -> DataFrame:
    records = []
    for run_series in sim_class_runs:
        for method, cls in run_series.items():
            if notna(cls):
                records.append((method, cls))

    long_df = DataFrame(records, columns=["Method", "Class"])
    return (
        long_df.groupby(["Method", "Class"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=["low", "medium", "high"], fill_value=0)
    )


def similarity_expected_category_test(
    sim_class_runs: list,
    expected_category: dict,
    alpha: float = 0.05,
    p_null: float = 1 / 3,
) -> DataFrame:
    from scipy.stats import binomtest

    rows = []
    for method, expected in expected_category.items():
        wins = 0
        n = 0

        for run_series in sim_class_runs:
            if method not in run_series:
                continue
            cls = run_series.loc[method]
            if isna(cls):
                continue
            n += 1
            if cls == expected:
                wins += 1

        p_raw = float("nan") if n == 0 else binomtest(wins, n, p=p_null, alternative="greater").pvalue
        rows.append({"Method": method, "InExpectedCategory": wins, "OutOf": n, "p_raw_numeric": p_raw})

    df = DataFrame(rows).set_index("Method")
    m = len(df)

    df["p_adj_numeric"] = (df["p_raw_numeric"] * m).clip(upper=1.0)
    df["Significant"] = df["p_adj_numeric"] < alpha

    df["p_raw"] = df["p_raw_numeric"].apply(_format_p_value)
    df["p_adj"] = df["p_adj_numeric"].apply(_format_p_value)

    return df[["InExpectedCategory", "OutOf", "p_raw", "p_adj", "Significant"]]