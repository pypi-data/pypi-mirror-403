from __future__ import annotations
from typing import Callable, List, Dict
from warnings import warn
import numpy as np
import scipy.sparse as sp
from pandas import Series as pd_Series
from pandas import DataFrame as pd_DataFrame
from polars import Series as pl_Series
from polars import DataFrame as pl_DataFrame
from tqdm import tqdm


def spyce_normalize(fun: Callable) -> Callable:
    def inner(mat: np.ndarray, **kwargs):
        shape = mat.shape
        norm_mat = fun(mat, **kwargs)
        if not len(norm_mat.shape) == len(shape) or any(
                [dim != shape[i_dim] for i_dim, dim in enumerate(norm_mat.shape)]):
            raise ValueError("Normalization changed shape of matrix which is not permitted.")
        else:
            return norm_mat
    return inner


def convert_normalization(normalization: Callable | str | None = "centered_sum") -> Callable:
    """
    Convert string or callable to spyce normalization function to make sure dimension is
    not changed. If passed as string, the function must be pre-implemented. If passed
    as callable, we add decorator @spyce_normalize.

    :param Callable | str | None normalization: Normalization function. If callable, make sure
        that the dimension is not changed. The framework will prevent you to perform a 
        normalization that changes the dimensionality of a matrix.
        If passed as a string, you can pass one of the following

            - `none`: No normalization is performed
            - `max_norm`: Largest value for each cell is set to 1
            - `sum_norm`: The kmer histogram for each cell sums up to 1
            - `center_norm`: Each sample is centered 
            - `centered_sum`: Unit sum histogram per cell and centering per sample
            - `centered_max`: Maximum value set to 1 per cell and centering per sample 
            - `centered_uniform_sum`: Centered unit sum normalization with unit variance 
            - `centered_uniform_max`: Maximum value per cell set to 1, centered, and unit variance
            
        Unless you know what you're doing, choose `centered_sum`
    :return Callable: normalization function
    """
    if normalization is None:
        normalization_fun = no_norm
    elif isinstance(normalization, str):
        normalization = normalization.lower()
        if normalization == "none" or normalization == "no_norm":
            normalization_fun = no_norm
        elif normalization == "max_norm":
            normalization_fun = max_norm
        elif normalization == "sum_norm":
            normalization_fun = sum_norm
        elif normalization == "add_norm":
            normalization_fun = add_norm
        elif normalization == "center_norm":
            normalization_fun = center_norm
        elif normalization == "centered_sum":
            normalization_fun = centered_sum
        elif normalization == "centered_max":
            normalization_fun = centered_max
        elif normalization == "centered_uniform_sum":
            normalization_fun = centered_uniform_sum
        elif normalization == "centered_uniform_max":
            normalization_fun = centered_uniform_max
        else:
            raise ValueError("Normalization not understood. Choose between none | max_norm | "
                             "sum_norm | center_norm | centered_sum | centered_max | centered_uniform_sum | "
                             "centered_uniform_max.")
    elif callable(normalization):
        normalization_fun = spyce_normalize(normalization)
    else:
        raise ValueError("Normalization type not understood. Pass one of the following: none | str | callable.")
    return normalization_fun

def cscmat_division(
        mat: sp.lil_matrix | sp.csc_matrix,
        fun_str: str,
        axis: int | None = None,
        **kwargs
) -> sp.csc_matrix:
    """
    Helper function for sparse division
    """
    if fun_str.lower() == "sum":
        auxil_mat = sp.diags(1. / mat.sum(axis=axis).A.ravel())
    elif fun_str.lower() == "max":
        auxil_mat = sp.diags(1. / mat.max(axis=axis).A.ravel())
    else:
        raise ValueError("Function type not understood.")
    return sp.csc_matrix(auxil_mat.dot(mat))


@spyce_normalize
def no_norm(
    mat: np.ndarray | sp.lil_matrix | sp.csc_matrix,
    **kwargs
) -> np.ndarray | sp.lil_matrix | sp.csc_matrix:
    """
    Perform no normalization.

    :param np.ndarray | sp.lil_matrix | sp.csc_matrix mat: matrix to be normalized
    :param kwargs: Unused parameters.
    :return np.ndarray | sp.lil_matrix | sp.csc_matrix: Non-normalized matrix
    """
    return mat


@spyce_normalize
def max_norm(
    mat: np.ndarray | sp.lil_matrix | sp.csc_matrix,
    **kwargs
) -> np.ndarray | sp.lil_matrix | sp.csc_matrix:
    """
    Normalize such that the maximum value in each row is set to 1.

    :param np.ndarray | sp.lil_matrix | sp.csc_matrix mat: matrix to be normalized
    :param kwargs: Unused parameters.
    :return np.ndarray | sp.lil_matrix | sp.csc_matrix: Normalized matrix
    """
    if isinstance(mat, np.ndarray):
        return mat / mat.max(axis=1).reshape(-1, 1)
    else:
        return cscmat_division(mat, "max", axis=1)


@spyce_normalize
def sum_norm(
    mat: np.ndarray | sp.lil_matrix | sp.csc_matrix,
    **kwargs
) -> np.ndarray | sp.lil_matrix | sp.csc_matrix:
    """
    Normalize to unit sum per row.

    :param np.ndarray | sp.lil_matrix | sp.csc_matrix mat: matrix to be normalized
    :param kwargs: Unused parameters.
    :return np.ndarray | sp.lil_matrix | sp.csc_matrix: Normalized matrix
    """
    if isinstance(mat, np.ndarray):
        return mat / mat.sum(axis=1).reshape(-1, 1)
    else:
        return cscmat_division(mat, "sum", axis=1)

@spyce_normalize
def center_norm(
    mat: np.ndarray | sp.lil_matrix | sp.csc_matrix,
    use_median: bool = False,
    **kwargs
) -> np.ndarray | sp.lil_matrix | sp.csc_matrix:
    """
    Center matrix along columns.

    :param np.ndarray | sp.lil_matrix | sp.csc_matrix mat: matrix to be normalized
    :param bool use_median: If `True`, use the median for centering instead of mean.
    :param kwargs: Unused parameters.
    :return np.ndarray | sp.lil_matrix | sp.csc_matrix: Normalized matrix
    """
    if use_median and isinstance(mat, np.ndarray):
        norm_mat = mat - np.median(mat, axis=0)
    else:
        norm_mat = mat - mat.mean(axis=0).reshape(1, -1)
    # if not isinstance(mat, np.ndarray):
    #     norm_mat = sp.csc_matrix(norm_mat)
    return norm_mat


@spyce_normalize
def add_norm(
    mat: np.ndarray | sp.lil_matrix | sp.csc_matrix,
    bias:  np.ndarray | sp.lil_matrix | sp.csc_matrix | float | int,
    **kwargs
):
    """
    Add a constant value to the matrix.

    :param np.ndarray | sp.lil_matrix | sp.csc_matrix mat: matrix to be normalized
    :param np.ndarray | sp.lil_matrix | sp.csc_matrix bias: Adjust matrix by this bias
    :return np.ndarray | sp.lil_matrix | sp.csc_matrix: Normalized matrix
    """
    if isinstance(bias, int) or isinstance(bias, float):
        return mat + bias
    else:
        return mat + bias.reshape(1, -1)


@spyce_normalize
def centered_sum(
    mat: np.ndarray | sp.lil_matrix | sp.csc_matrix,
    use_median: bool = False,
    **kwargs
) -> np.ndarray | sp.lil_matrix | sp.csc_matrix:
    """
    Centered unit sum normalization. Perform unit sum normalization before centering.

    :param np.ndarray | sp.lil_matrix | sp.csc_matrix mat: matrix to be normalized
    :param bool use_median: If `True`, use the median for centering instead of mean.
    :param kwargs: Unused parameters.
    :return np.ndarray | sp.lil_matrix | sp.csc_matrix: Normalized matrix
    """
    norm_mat = sum_norm(mat)
    return center_norm(norm_mat, use_median=use_median)


@spyce_normalize
def centered_max(
    mat: np.ndarray | sp.lil_matrix | sp.csc_matrix,
    use_median: bool = False,
    **kwargs
) -> np.ndarray | sp.lil_matrix | sp.csc_matrix:
    """
    Centered maximum value normalization. Perform maximum value normalization before centering.

    :param np.ndarray | sp.lil_matrix | sp.csc_matrix mat: matrix to be normalized
    :param bool use_median: If `True`, use the median for centering instead of mean.
    :param kwargs: Unused parameters.
    :return np.ndarray | sp.lil_matrix | sp.csc_matrix: Normalized matrix
    """
    norm_mat = max_norm(mat)
    return center_norm(norm_mat, use_median=use_median)


@spyce_normalize
def centered_uniform_sum(
    mat: np.ndarray | sp.lil_matrix | sp.csc_matrix,
    use_median: bool = False,
    use_std: bool = True,
    **kwargs
) -> np.ndarray | sp.lil_matrix | sp.csc_matrix:
    """
    Centered unit sum with unit spread. Perform centered unit sum normalization before transforming to unit spread.

    :param np.ndarray | sp.lil_matrix | sp.csc_matrix mat: matrix to be normalized
    :param bool use_median: If `True`, use the median for centering instead of mean.
    :param bool use_std: If `True`, normalize over standard deviation instead of variance.
    :param kwargs: Unused parameters.
    :return np.ndarray | sp.lil_matrix | sp.csc_matrix: Normalized matrix
    """
    norm_mat = centered_sum(mat, use_median=use_median)
    if isinstance(mat, np.ndarray):
        spread_fun = np.std if use_std else np.var
        spread = spread_fun(norm_mat, axis=0).reshape(1, -1)
        spread[spread == 0.] = 1.
        return norm_mat / spread
    else:
        warn("Can only unify spread for dense matrices safely. No division is performed.")
        return norm_mat

@spyce_normalize
def centered_uniform_max(
    mat: np.ndarray | sp.lil_matrix | sp.csc_matrix,
    use_median: bool = False,
    use_std: bool = True,
    **kwargs
) -> np.ndarray | sp.lil_matrix | sp.csc_matrix:
    """
    Centered unit sum with unit spread. Perform centered max value normalization before transforming to unit spread.

    :param np.ndarray | sp.lil_matrix | sp.csc_matrix mat: matrix to be normalized
    :param bool use_median: If `True`, use the median for centering instead of mean.
    :param bool use_std: If `True`, normalize over standard deviation instead of variance.
    :param kwargs: Unused parameters.
    :return np.ndarray | sp.lil_matrix | sp.csc_matrix: Normalized matrix
    """
    norm_mat = centered_max(mat, use_median=use_median)
    if isinstance(mat, np.ndarray):
        spread_fun = np.std if use_std else np.var
        spread = spread_fun(norm_mat, axis=0).reshape(1, -1)
        spread[spread == 0.] = 1.
        return norm_mat / spread
    else:
        warn("Can only unify spread for dense matrices safely. No division is performed.")
        return norm_mat

@spyce_normalize
def normalize_over_ord_vec(
    mat: np.ndarray | sp.lil_matrix | sp.csc_matrix | sp.csr_matrix | pd_DataFrame | pl_DataFrame,
    vec: List | np.ndarray | pl_Series | pd_Series,
    normalization: Callable | str | None = "centered_sum",
    vec_param: Dict | None = None,
    **kwargs
) -> np.ndarray | sp.lil_matrix | sp.csc_matrix:
    """
    Normalize over arbitrary vector with ordinal values. The passed normalization is then applied per value in ordinal vector.

    :param np.ndarray | sp.lil_matrix | sp.csc_matrix mat: matrix to be normalized
    :param List | np.ndarray | pl_Series | pd_Series vec: Labels/categories used to group rows for normalization
    :param Callable | str | None normalization: Type of normalization performed
    :param Dict | None vec_param: If passed, provide specific parameters for ordinal values in `vec`. The parameters
        must be provided as a dictionary. The layout of the `vec_param` parameter is:
        ```
        {
            "label1_in_vec": {"param1": param1_1, "param2": param2_1},
            ...
            "labeln_in_vec": {"param1": param1_n, "param2": param2_n},
        }
        ```
        where you need to replace the names and values according to your function. If `None`, no label specific parameters
        are used. 
    :param kwargs: Keyword arguments passed to the normalization function
    :return np.ndarray | sp.lil_matrix | sp.csc_matrix: Normalized matrix
    """
    if isinstance(vec, list):
        vec = np.array(vec).reshape(-1)
    if isinstance(vec, pl_Series) or isinstance(vec, pd_Series):
        vec = vec.to_numpy()
    if not isinstance(vec, np.ndarray):
        raise ValueError("Vector type not understood. Please pass `vec` as one of the following: "
                         "list | np.ndarray | polars Series | pandas Series.")
    vec = vec.reshape(-1)
    if vec.shape[0] != mat.shape[0]:
        raise ValueError("Vector length (%d) is unequal matrix length (%d). Note that vectors are flattened, "
                         "and the first matrix axis must be cell entries." % (vec.shape[0], mat.shape[0]))
    
    norm_fun = convert_normalization(normalization=normalization)
    cols, index = None, None
    if isinstance(mat, np.ndarray) or isinstance(mat, pd_DataFrame) or isinstance(mat, pl_DataFrame):
        norm_mat = np.zeros_like(mat)
        if isinstance(mat, pd_DataFrame):
            cols, index = mat.columns, mat.index
            mat = mat.to_numpy()
        elif isinstance(mat, pl_DataFrame):
            cols = mat.columns
            mat = mat.to_numpy()
    elif isinstance(mat, sp.lil_matrix):
        norm_mat = sp.lil_matrix(shape=mat.shape, dtype=mat.dtype)
    elif isinstance(mat, sp.csc_matrix):
        norm_mat = sp.csc_matrix(shape=mat.shape, dtype=mat.dtype)
    elif isinstance(mat, sp.csr_matrix):
        norm_mat = sp.csr_matrix(shape=mat.shape, dtype=mat.dtype)
    else:
        raise ValueError("Matrix type not understood. Please convert matrix to one of the following: "
                         "np.ndarray | scipy.sparse.lil_matrix | scipy.sparse.csc_matrix | scipy.sparse.csr_matrix.")
    
    for vec_val in np.unique(vec):
        mask = vec == vec_val 
        if vec_param is not None:
            if vec_val in vec_param:
                label_param = vec_param[vec_val]
            else:
                raise ValueError("`vec_param` is passed but no parameters are provided for label %s" % vec_val)
        else:
            label_param = {}
        norm_mat[mask] = norm_fun(mat[mask], **label_param, **kwargs)

    if cols is not None and index is not None:  # only set for pandas
        norm_mat = pd_DataFrame(norm_mat, index=index, columns=cols)
    elif cols is not None and index is None:  # only set for polars
        norm_mat = pl_DataFrame(norm_mat, schema=cols, orient="row")
    return norm_mat


@spyce_normalize
def harmony_correct(
    mat: np.ndarray | sp.lil_matrix | sp.csc_matrix,
    target_vec: np.ndarray | pl_Series | pd_Series | List,
    sigma: float = .3,
    max_iter: int = 20,
    theta: float | None = None,
    lamb: float | None = None,
    nclust: float | None = None,
    tau: float | None = 0.,
    block_size: float = 0.05, 
    max_iter_kmeans: int = 20,
    epsilon_cluster: float = 1e-5,
    epsilon_harmony: float = 1e-4, 
    **kwargs
) -> np.ndarray:
    """
    Batch or species correction using Harmony

    :param np.ndarray | sp.lil_matrix | sp.csc_matrix mat: matrix to be normalized
    :param List | np.ndarray | pl_Series | pd_Series target_vec: Labels/categories used for Harmony correction
    :param float sigma: Force by which soft-clusters are corrected. 
        The lower the value, the larger the correction.
    :param int max_iter: Maximum iterations
    :param float | None theta: Harmony theta parameter
    :param float | None lamb: Harmony lambda parameter
    :param int | None nclust: Number of clusters
    :param float tau: Harmony tau parameter
    :param float block_size: Harmony block size parameter
    :param int max_iter_kmeans: Maximum number of sklearn kmeans iterations
    :param float epsilon_cluster: Harmony epsilon cluster parameter
    :param float epsilon_harmony: Harmony epsilon harmony parameter
    :param kwargs: Unused parameters
    :return np.ndarray | sp.lil_matrix | sp.csc_matrix: Normalized matrix
    """
    import harmonypy
    if isinstance(target_vec, pl_Series):
        target_vec = target_vec.to_pandas()

    # assume that matrix is passed either dense or sparse
    if not isinstance(mat, np.ndarray):    
        mat = mat.A

    # run_harmony doesn't accept **kwargs. We need to set them specifically to allow 
    # other kwargs non related to harmony to be passed
    return harmonypy.run_harmony(
        mat,
        pd_DataFrame({"batch": target_vec}),
        "batch",
        sigma=sigma,
        max_iter_harmony=max_iter,
        theta=theta,
        lamb=lamb,
        nclust=nclust,
        tau=tau,
        block_size=block_size,
        max_iter_kmeans=max_iter_kmeans,
        epsilon_cluster=epsilon_cluster,
        epsilon_harmony=epsilon_harmony
    ).Z_corr.T


@spyce_normalize
def icp(
    mat: np.ndarray | sp.lil_matrix | sp.csc_matrix,
    target_vec:  np.ndarray | pl_Series | pd_Series | List,
    subset_frac: float = .6,
    tol: float = 1e-2,
    max_iter: int = 50,
    verbosity: int = 0,
    verbosity_indent: str = "",
    **kwargs
) -> np.ndarray | sp.lil_matrix | sp.csc_matrix:
    """
    Batch or species correction iterative closest point normalization as modified point-set registration transform.

    :param np.ndarray | sp.lil_matrix | sp.csc_matrix mat: matrix to be normalized
    :param List | np.ndarray | pl_Series | pd_Series target_vec: Labels/categories used for Harmony correction
    :param float subset_frac: Reduce run time by performing correction on subset
    :param float tol: Tolerance value. When update step lower than tolerance, stop ICP
    :param int max_iter: Maximum iterations
    :param int verbosity: Verbosity level
    :param str verbosity_indent: Prefix for output.
    :param kwargs: Unused parameters
    :return np.ndarray | sp.lil_matrix | sp.csc_matrix: Normalized matrix
    """
    from scipy.optimize import least_squares
    from sklearn.neighbors import KDTree
    def translation_cost(t_, mat1_, mat2_):
        return norm_fun((mat1_ - t_.reshape(1, -1)) - mat2_)
    
    if not 0 < subset_frac < 1.:
        raise ValueError("Subsampling fraction must be between 0 and 1")
    
    if isinstance(target_vec, pl_Series) or isinstance(target_vec, pd_Series):
        target_vec = target_vec.to_numpy()
    elif isinstance(target_vec, list):
        target_vec = np.array(target_vec)

    if isinstance(mat, sp.lil_matrix) or isinstance(mat, sp.csc_matrix):
        norm_fun = sp.linalg.norm
        trf_mat = sp.csc_matrix(shape=mat.shape)
    else:
        norm_fun = np.linalg.norm
        trf_mat = np.zeros_like(mat)
    src_mat = mat[~target_vec]
    dst_mat = mat[target_vec]
    # use point-set registration transform
    # find jointly correspondance between between data points of the two sets
    # and the corresponding transformation
    # intialize translational vector
    t_vec = src_mat.mean(axis=0).reshape(1, -1)
    difference = np.inf
    kdtree = KDTree(dst_mat)  
    epoch_iter = tqdm(
        range(max_iter), total=max_iter, desc="%sICP progress. Difference: inf."  % verbosity_indent
    ) if verbosity > 0 else range(max_iter) 
    for _ in epoch_iter:
        if verbosity > 0:
            epoch_iter.set_description(desc="%sICP progress. Difference: %.6f"  % (verbosity_indent, difference))

        subset_mat = src_mat[
            np.random.choice(src_mat.shape[0], replace=False, size=int(subset_frac * src_mat.shape[0]))
        ]
        t_mat = subset_mat - t_vec
        closest_match = np.zeros_like(t_mat)
        for i_m, m in enumerate(t_mat):
            closest_match[i_m] = dst_mat[kdtree.query(m.reshape(1, -1), return_distance=False)[0]]

        t_vec = least_squares(translation_cost, x0=t_vec.flatten(), args=(subset_mat, closest_match)).x
        t_vec = t_vec.reshape(1, -1)

        difference = norm_fun((subset_mat - t_vec) - closest_match)
        if difference <= tol:
            if verbosity > 0:
                print("%sFound registration, early stopping." % verbosity_indent)
            break

    trf_mat[~target_vec] = src_mat - t_vec
    trf_mat[target_vec] = dst_mat
    return trf_mat


def prepare_correlation_correction(
    kmer_hist: np.ndarray | sp.lil_matrix | sp.csc_matrix,
    species_vec: List | np.ndarray | pl_Series | pd_Series,
    ct_vec: List | np.ndarray | pl_Series | pd_Series,
    target_species: str,
    verbosity: int = 0
) -> Dict:
    """
    Preparation funtion for normalization via correlation. Determines distance of annotated cell type to 
    most similar cell type in a target species and adjusts the mean values such that their centers superimpose.
    This function should be passed directly to the `set_normalization` function, and it shouldn't be necessary 
    for you to use it independently.

    :param np.ndarray | sp.lil_matrix | sp.csc_matrix kmer_hist: KMer histogram over all cells
    :param  List | np.ndarray | pl_Series | pd_Series species_vec: Species vector identifies which to which species
        a cell belongs to. It has the same number of entries as the number of rows in the KMer histogram. 
    :param  List | np.ndarray | pl_Series | pd_Series ct_vec: Cell type vector identifies which to which cell type
        or label a cell belongs to. It has the same number of entries as the number of rows in the KMer histogram. 
    :param str target_species: Name of the target species to which other species need to be corrected to
    :param int verbosity: Verbosity level.
    :return Dict: Returns a dictionary containing the `ord_vec` parameter required for the `normalize_over_ord_vec`
        function, and for each cell type and species a bias term that is used for moving the cell type to the target
        species.
    """
    import scipy.stats as st
    def _convert_vec(vec):
        if isinstance(vec, list):
            vec = np.array(vec).reshape(-1)
        elif isinstance(vec, pl_Series):
            vec = vec.to_pandas()
        elif isinstance(vec, np.ndarray):
            vec = pd_Series(vec)
        return vec
    
    # convert vector
    species_vec = _convert_vec(species_vec)
    ct_vec = _convert_vec(ct_vec)
    if not isinstance(kmer_hist, np.ndarray):
        kmer_hist = np.array(kmer_hist.A)

    # create dictionary with mean k-mers per cell type an cell type
    mean_ct_vec = {
        species: np.zeros((len(ct_vec.unique()), kmer_hist.shape[1]))
        for species in species_vec.unique()
    }

    ct_iter = enumerate(np.sort(ct_vec.unique()))
    if verbosity > 0:
        ct_iter = tqdm(ct_iter, desc="Prepare normalization", total=len(ct_vec.unique()))
    for i_ct, ct in ct_iter:
        ct_mask = (ct_vec == ct).to_numpy()
        for species in species_vec.unique():
            species_mask = (species == species_vec).to_numpy() 
            if not (ct_mask & species_mask).any():
                continue
                
            # calculate mean
            mean_ct_vec[species][i_ct] = kmer_hist[ct_mask & species_mask].mean(axis=0)

    # calculate adjustment to target species based on correlation
    vec_params = {}
    species_iter = mean_ct_vec.keys()
    if verbosity > 0:
        species_iter = tqdm(species_iter, desc="Adjust species", total=len(mean_ct_vec))
    for species in species_iter:
        for i_sct, sct_vec in enumerate(mean_ct_vec[species]):
            sct = np.sort(ct_vec.unique())[i_sct]
            vec_params["%s_%s" % (species, sct)] = {}
            # no adjustment to target species
            if species == target_species:
                vec_params["%s_%s" % (species, sct)]["bias"] = np.zeros(kmer_hist.shape[1])
                continue

            #if no variability, no correlation can be computed
            if sct_vec.std() < np.finfo("float32").eps: continue
            
            # determine correlation to best cell type in target
            best_corr, best_ct = -np.inf, -1
            for i_tct, tct_vec in enumerate(mean_ct_vec[target_species]):
                if tct_vec.std() < np.finfo("float32").eps: continue
                # compute spearman correlation
                corr = st.spearmanr(sct_vec, tct_vec, axis=0).statistic
                if corr > best_corr:
                    best_corr = corr
                    best_ct = i_tct
    
            # adjustment
            if not np.isinf(best_corr) or best_ct < 0:
                vec_params["%s_%s" % (species, sct)]["bias"] = (mean_ct_vec[target_species][best_ct] - sct_vec).reshape(1, -1)
    # return adjustment + order vec
    return {
        "vec_param": vec_params,
        "ord_vec": pd_Series(species_vec).astype("string") + "_" + pd_Series(ct_vec).astype("string")
    }

