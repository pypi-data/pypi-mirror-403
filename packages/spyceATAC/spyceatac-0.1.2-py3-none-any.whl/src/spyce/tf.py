from __future__ import annotations
import os
from typing import List, Dict, Callable, Tuple
from itertools import product
import warnings
import numpy as np
import anndata as ad
import scipy.sparse as sp
import scipy.stats as st
from sklearn.decomposition import PCA
import pandas as pd
import polars as pl
from gimmemotifs.motif import read_motifs
from gimmemotifs.config import DIRECT_NAME, INDIRECT_NAME
from Bio.Seq import Seq
from tqdm import tqdm

from spyce.kmerMatrix import KMerClass, KMerMatrix
from spyce.constants import DNA_ALPHABET
from spyce.utils import fetch_async_result, seq_to_int, nozero_kmer_to_idx
from spyce.normalize import convert_normalization, harmony_correct
import multiprocessing


def chi2_pwm_convolve_diff(pwm1: np.ndarray, pwm2: np.ndarray, thresh: float = .95, min_conv: int = 4) -> float:
    """
    Computes similarity between two convoluting TFBS motifs given PWM using chi-squared significant test.
    Determines the number of positions that are significantly similar or dissimilar, dependening
    on the set threshold. Metric taken and adapted from https://doi.org/10.1186/1471-2105-6-237

    :param np.ndarray pwm1: PWM of first motif
    :param np.ndarray pwm2: PWM of second motif
    :param float thresh: p-value threshold used for defining whether the pwm at a given position is 
        sufficiently similar. For example, if the threshold is set to 0.95, it measures significant
        similarity. The distance is therefore the fraction of positions that are not significantly similar.
        If the threshold is set to 0.05, the measure represent significant dissimilarity. The
        distance is the fraction of positions that are significantly different.
    :param int min_conv: Minimum overlap between the motifs.
    :return float: Difference between motif1 and 2 based on their PWMs 
    """
    # get shorter pwm
    shorter_pwm, longer_pwm = (pwm1, pwm2) if pwm1.shape[0] < pwm2.shape[0] else (pwm2, pwm1)
    min_size = shorter_pwm.shape[0]
    max_size = longer_pwm.shape[0]
    # make sure probabilities sum up to one
    pwm1 /= pwm1.sum(axis=1).reshape(-1, 1)
    pwm2 /= pwm2.sum(axis=1).reshape(-1, 1)
    dist_list = []
    # convolute the two pwms
    for lag in range(min_conv, pwm1.shape[0] + pwm2.shape[0] - (min_conv + 1)):
        # get end of longer pwm
        cropped_longer = longer_pwm[-np.minimum(lag, max_size)
                                    :-(lag - min_size) if (lag - min_size) > 0 else None]
        # get beginning of shorter pwm
        cropped_shorter = shorter_pwm[
            np.maximum(0, lag - longer_pwm.shape[0])
            :np.minimum(lag, min_size)]
        
        # chi squared significance test whether observed frequencies match given distribution.
        # note that chisquare is asymmetric. As the definition of observation and distribution is
        # arbitrary, we perform both sides
        chisq_1 = np.nan_to_num(st.chisquare(cropped_shorter, cropped_longer, axis=1).pvalue, nan=1.)
        chisq_2 = np.nan_to_num(st.chisquare(cropped_longer, cropped_shorter, axis=1).pvalue, nan=1.)
        
        # take the maximum probability out of the two chi squared tests.
        # this indicates probability that the pwms are different at a given position.
        # look how many are larger than threshold on average given the size of the motif.
        # if threshold is 0.95, this represents the probability that they are significantly similar
        # if threshold is 0.05, this respresents probability that they are significantly dissimilar
        dist_list.append((np.maximum(chisq_1, chisq_2) >= thresh).mean())    
    # the larger max(dist_list), the more similar are motifs. Average of p-values ranges [0, 1].
    # as dissimilarity metrc, we compute 1 - max(dist_list
    return 1. - max(dist_list)


def chi2_pwm_diff(pwm1: np.ndarray, pwm2: np.ndarray, thresh: float = .95) -> float:
    """
    Computes similarity between two TFBS motifs given PWM using chi-squared significant test.
    Determines the number of positions that are significantly similar or dissimilar, dependening
    on the set threshold. Metric taken and adapted from https://doi.org/10.1186/1471-2105-6-237

    :param np.ndarray pwm1: PWM of first motif
    :param np.ndarray pwm2: PWM of second motif
    :param float thresh: p-value threshold used for defining whether the pwm at a given position is 
        sufficiently similar. For example, if the threshold is set to 0.95, it measures significant
        similarity. The distance is therefore the fraction of positions that are not significantly similar.
        If the threshold is set to 0.05, the measure represent significant dissimilarity. The
        distance is the fraction of positions that are significantly different.
    :return float: Difference between motif1 and 2 based on their PWMs 
    """
    # get shorter pwm
    shorter_pwm, longer_pwm = (pwm1, pwm2) if pwm1.shape[0] < pwm2.shape[0] else (pwm2, pwm1)
    # make sure probabilities sum up to one
    shorter_pwm /= shorter_pwm.sum(axis=1).reshape(-1, 1)
    longer_pwm /= longer_pwm.sum(axis=1).reshape(-1, 1)
    dist_list = []
    # move shorter motif along larger motif and compare significant differences
    for lag in range(0, longer_pwm.shape[0] - shorter_pwm.shape[0] + 1):
        # crop larger motif to same size
        cropped_pwm = longer_pwm[lag:lag + shorter_pwm.shape[0]]
        # chi squared significance test whether observed frequencies match given distribution.
        # note that chisquare is asymmetric. As the definition of observation and distribution is
        # arbitrary, we perform both sides
        chisq_1 = np.nan_to_num(st.chisquare(cropped_pwm, shorter_pwm, axis=1).pvalue, nan=1.)
        chisq_2 = np.nan_to_num(st.chisquare(shorter_pwm, cropped_pwm, axis=1).pvalue, nan=1.)
        # take the maximum probability out of the two chi squared tests.
        # this indicates probability that the pwms are different at a given position.
        # look how many are larger than threshold on average given the size of the motif.
        # if threshold is 0.95, this represents the probability that they are significantly similar
        # if threshold is 0.05, this respresents probability that they are significantly dissimilar
        dist_list.append((np.maximum(chisq_1, chisq_2) >= thresh).mean())    
    # the larger max(dist_list), the more similar are motifs. Average of p-values ranges [0, 1].
    # as dissimilarity metrc, we compute 1 - max(dist_list)
    return 1. - max(dist_list)


def motif_kmer_score(
        ppm: np.ndarray,
        k: int = 6,
        alphabet: List[str] = DNA_ALPHABET,
        return_dense: bool = True,
        rm_zeros: bool = False,
        use_thresh: bool = False,
        min_prob: float | None = None,
        collapse_fun: Callable = np.maximum,
        consensus_thresh: float = .0,
        equalize_counter: bool = True
) -> np.ndarray | sp.lil_matrix:
    """
    Helper function that returns kmer probability scores for a given transcription factor when provided with
    a position probability matrix. This is called during parallel processing.

    :param np.ndarray ppm: Position probability matrix
    :param int k: K-mer size
    :param List[str] alphabet: Letters in k-mer alphabet
    :param bool return_dense: If set, return dense numpy array instead of sparse matrix
    :param bool rm_zeros: If set, remove reverse complements if `equalize_counter=True`. For example,
        assuming `k=3`, `AAT` and `ATT` (the reverse complement) would both contain the same value.
        They can be removde to save memory. Note, however, that in many use cases, it is easier to keep
        them.
    :param bool use_thresh: If set, probability values for a k-mer to be present in motif must be larger
        than `min_prob`, or are set to zero.
    :param float | None min_prob: If set and `use_thresh`, use this value as minimum probability for k-mer
        being present in motif, otherwise set to zero. If `None`, and `use_thresh=True` set
        `min_prob = k * .25**k`.
    :param Callable collapse_fun: Probability of `k` tuples are multiplied per position. `collapse_fun`
        defines how the position-specific information is combined with the position-oblivious k-mer histogram
        representation. For example, you can add them all together (by passing for example `np.add`, or you
        keep only the maximum value (by passing for example `np.maximum`). The passed callable must accept
        to parameters, the first is the k-mer histogram computed up to the n-th position, and the probility
        of finding the `k`-tuple at positon `n+1`. Default is `np.add`. 
    :param float consensus_thresh: Minimum probability for a nucleotide to be present in order to be included into k-mer
        probability, otherwise set to zero.
    :param bool equalize_counter: If set to `True`, treat forward and reverse complement kmer as the same kmer and add
        probability to both entries. If `rm_zeros=True`, add only to first alphabetical k-mer. That
        means values for `GCGT` are added to the histogram values for `ACGC` if `rm_zeros=True`.
    :return np.ndarray | sp.lil_matrix: Numpy array or sparse matrix depending on whether `return_dense` is
        set to true.
    """
    motif_kmer_total = np.zeros((1, len(alphabet)**k))
    if min_prob is None:
        min_prob = k * .25**k
    for i in range(0, ppm.shape[0] - k + 1):
        to_idx = np.minimum(k + i,  ppm.shape[0])
        # get all kmer combinations for these positions as indices in ppm
        col_idc = np.array(list(product(np.arange(len(alphabet)), repeat=(to_idx - i))))
        row_idc = np.tile(np.arange(i, to_idx), reps=col_idc.shape[0])
        kmer_ppm = ppm[row_idc.flatten(), col_idc.flatten()].reshape(-1, (to_idx - i))
        kmer_ppm[kmer_ppm < consensus_thresh] = 0.

        # multiply position probabilities per kmer
        motif_kmer_total[0, np.arange(len(alphabet)**(to_idx - i))] = collapse_fun(
            motif_kmer_total[0, np.arange(len(alphabet)**(to_idx - i))],
            np.prod(kmer_ppm, axis=1)
        )
    
    if equalize_counter:
        # account for the fact that the annotation could also occur for the reversed strand
        equalized_kmer_counter = {}
        # sort alphabetically
        for kmer in product(alphabet, repeat=k):
            kmer = "".join(kmer)
            rev_kmer = str(Seq(kmer).reverse_complement())
            # make sure order is alphabetical
            if rm_zeros:
                save_kmer = kmer if kmer < rev_kmer else rev_kmer
                idx = seq_to_int(kmer, alphabet=alphabet)
                equalized_kmer_counter[save_kmer] = motif_kmer_total[0, idx] + equalized_kmer_counter.get(rev_kmer, 0)
            else:
                if kmer in equalized_kmer_counter or rev_kmer in equalized_kmer_counter:
                    continue
                idx = seq_to_int(kmer, alphabet=alphabet)
                rev_idx = seq_to_int(rev_kmer, alphabet=alphabet)
                equalized_kmer_counter[kmer] = motif_kmer_total[0, idx] + motif_kmer_total[0, rev_idx]
                equalized_kmer_counter[rev_kmer] = motif_kmer_total[0, idx] + motif_kmer_total[0, rev_idx]
    else:
        equalized_kmer_counter = dict(zip(
            ["".join(kmer) for kmer in product(alphabet, repeat=k)],
            motif_kmer_total.reshape(-1)
        ))

    kmer_list, n_kmer = zip(*sorted(equalized_kmer_counter.items(), key=lambda _: _[0]))
    # convert present kmers to unique numerical value
    if rm_zeros:
        kmer_idx_dict = nozero_kmer_to_idx(alphabet=alphabet, k=k)
        kmer_idx = [kmer_idx_dict[kmer] for kmer in kmer_list]
    else:
        kmer_idx = [seq_to_int(kmer, alphabet) for kmer in kmer_list]
    # set kmer histogram values
    motif_kmer = np.zeros(max(kmer_idx_dict.values()) + 1 if rm_zeros else len(alphabet)**k, dtype="float")
    motif_kmer[kmer_idx] = n_kmer

    if equalize_counter:
        motif_kmer /= 2.

    if use_thresh:
        motif_kmer[motif_kmer < min_prob] = 0.

    motif_kmer = motif_kmer.reshape(1, -1)
    return sp.coo_matrix(motif_kmer).reshape(1, -1) if not return_dense else motif_kmer


def motifs_to_kmer(
        k: int = 6,
        alphabet: List[str] = DNA_ALPHABET,
        db_name: str = "CIS-BP",
        return_dense: bool = False,
        include_indirect: bool = True,
        n_jobs: int = 1,
        rm_zeros: bool = True,
        use_thresh: bool = False,
        min_prob: float | None = None,
        collapse_fun: Callable = np.add,
        normalization: Callable | str | None = "none",
        consensus_thresh: float = .0,
        equalize_counter: bool = True,
        pca_transform: PCA | None = None,
        verbosity: int = 0,
        verbosity_indent: str = "",
) -> KMerMatrix:
    """
    Convert transcription factor binding motifs from a data base to a k-mer matrix which is 
    returned as and AnnData object (rather than a KMer object).

    :param int k: k-mer size
    :param List[str] alphabet: k-mer alphabet
    :param str db_name: transcription factor binding site motif data base name. Choose a motif supported
        by the gimmemotifs library, which are CIS-BP | ENCODE | factorbook | HOCOMOCOv11_HUMAN |
        HOCOMOCOv11_MOUSE | HOMER | IMAGE | JASPAR[2018 | 2020][_vertebrates | _plants | _insects | _fungi 
        _nematodes | _urochordata]
    :param bool return_dense: If set, use a dense numpy array instead a sparse matrix
    :param bool include_indirect: also include motifs for which there is only computational support
    :param int n_jobs: Number of processes used
    :param bool rm_zeros: If set, remove reverse complements if `equalize_counter=True`. For example,
        assuming `k=3`, `AAT` and `ATT` (the reverse complement) would both contain the same value.
        They can be removde to save memory. Note, however, that in many use cases, it is easier to keep
        them.
    :param bool use_thresh: If set, probability values for a k-mer to be present in motif must be larger
        than `min_prob`, or are set to zero.
    :param float | None min_prob: If set and `use_thresh`, use this value as minimum probability for k-mer
        being present in motif, otherwise set to zero. If `None`, and `use_thresh=True` set
        `min_prob = k * .25**k`.
    :param Callable collapse_fun: Probability of `k` tuples are multiplied per position. `collapse_fun`
        defines how the position-specific information is combined with the position-oblivious k-mer histogram
        representation. For example, you can add them all together (by passing for example `np.add`, or you
        keep only the maximum value (by passing for example `np.maximum`). The passed callable must accept
        to parameters, the first is the k-mer histogram computed up to the n-th position, and the probility
        of finding the `k`-tuple at positon `n+1`. Default is `np.add`. 
    :param str | Callable | None normalization: normalization function. Can be either a user defined callable;
        or one of the following:

        - None or `none`: no normalization
        - `max_norm`: normalize every cell by its maximum value
        - `sum_norm`: normalize every cell by its sum
        - `centered_sum`: normalize every cell by its sum and then center every histogram value
        - `centered_max`: normalize every cell by its maximum value and then center every histogram value
        - `centered_uniform_sum`: normalize every cell by its sum and then center every histogram value with
            uniform variance
        - `centered_uniform_max`: normalize every cell by its maximum value and then center every histogram value with
            uniform variance    

    :param float consensus_thresh: Minimum probability for a nucleotide to be present in order to be included into k-mer
        probability, otherwise set to zero.
    :param bool equalize_counter: If set to `True`, treat forward and reverse complement kmer as the same kmer and add
        probability to both entries. If `rm_zeros=True`, add only to first alphabetical k-mer. That
        means values for `GCGT` are added to the histogram values for `ACGC` if `rm_zeros=True`.
    :param PCA | None pca_transform: sklearn PCA object. If passed, perform dimensionality reduction on pre-trained PCA
    :param int verbosity: verbosity level
    :param str verbosity_indent: indentation string added before printout
    :return KMerMatrix: k-mer histrogram matrix as KMerMatrix object
    """
    with multiprocessing.get_context("spawn").Pool(n_jobs) as pool:
        if verbosity > 0:
            print("Fetch motifs from %s" % db_name)
        tf_motifs = read_motifs(db_name)
        motif_jobs = []
        if verbosity > 0:
            print("Prepare motif k-mers.")

        tf_iter = tqdm(
            tf_motifs,
            total=len(tf_motifs),
            desc="Compute TF probability"
        ) if verbosity > 0 else tf_motifs

        motif_name_dict = {}
        motif_results = []
        for motif in tf_iter:
            # get ppm 
            ppm = motif.ppm
            # get motif name
            factor_name = motif.factors[DIRECT_NAME]
            indirect_name = motif.factors[INDIRECT_NAME]
            if len(factor_name) == 0 and len(indirect_name) == 0:
                factor_name = motif.id
            elif len(factor_name) > 0:
                factor_name = factor_name[0] 
            else:
                if include_indirect:
                    factor_name = indirect_name[0]
                else:
                    continue
            motif_name_dict[motif.id] = factor_name
            if n_jobs > 1:
                # create job
                motif_jobs.append((motif.id, pool.apply_async(
                    motif_kmer_score, args=(
                        ppm, 
                        k, 
                        alphabet,
                        return_dense,
                        rm_zeros,
                        use_thresh,
                        min_prob,
                        collapse_fun,
                        consensus_thresh,
                        equalize_counter
                    ))))
            else:
                motif_results.append((motif.id, motif_kmer_score(
                            ppm, 
                            k, 
                            alphabet,
                            return_dense,
                            rm_zeros,
                            use_thresh,
                            min_prob,
                            collapse_fun,
                            consensus_thresh,
                            equalize_counter
                        )))

                
        if n_jobs > 1:
            # fetch completed jobs   
            pbar = tqdm(
                total=len(tf_motifs),
                desc="%sFetch motif kmers" % verbosity_indent
            ) if verbosity > 0 else None
            motif_results = fetch_async_result(motif_jobs, process_bar=pbar)
        stack_lib = np if return_dense else sp
        motif_id_list = []
        kmer_list = []
        for motif_id, kmer in sorted(motif_results, key=lambda x: x[0]):
            motif_id_list.append(motif_id)
            kmer_list.append(kmer)
        # create var name list, which are the factor IDs
        if rm_zeros:
            kmer_seq_list = list(sorted(nozero_kmer_to_idx(alphabet=alphabet, k=k).keys()))
        else:
            kmer_seq_list = product(alphabet, repeat=k)
        kmer_tuple_list = []
        for kmer_seq in kmer_seq_list:
            kmer_tuple_list.append((seq_to_int(kmer_seq, alphabet=alphabet), "".join(kmer_seq)))
        
        # create anndata object
        motif_kmer_mat = stack_lib.vstack(kmer_list)
        motif_kmer = KMerMatrix(
            kmer_hist=motif_kmer_mat,
            barcodes=pd.Series(motif_id_list),
            k=k,
            normalization=normalization
        )
        if pca_transform is not None:
            motif_kmer.dr = {}
            motif_kmer.dr["ext_pca"] = pca_transform.transform(motif_kmer.kmer_hist)
        return motif_kmer


def data_set_motif_score(
        kmer_obj: KMerClass,
        motif_kmer: KMerClass,
        use_kmer_dr: str | None = None,
        use_motif_dr: str | None = None,
        norm: Callable | str | None = None,
        norm_vec: pd.Series | pl.Series | np.ndarray | List | None = None,
        harmony_vec: pd.Series | pl.Series | np.ndarray | List | None = None,
        collapse_fun: str | Callable = "sum",
        verbosity: int = 0,
        verbosity_indent: str = "",
        **kwargs
) -> pd.DataFrame:
    """
    Compute motif score based on data set to obtain a matrix cell x TFBS motif.

    :param KMerClass kmer_obj: KMer object 
    :param KMerClass motif_kmer: Motif kmer histogram as KMerClass object. Should be created using the 
        function `motifs_to_kmer`
    :param str | None use_kmer_dr: Use a particular dimensionality reduced KMer representation saved under
        `kmer_obj.dr[use_kmer_dr]`.
    :param str | None use_motif_dr: Use a particular dimensionality reduced TFBS representation saved under
        `motif_kmer.dr[use_motif_dr]`.
    :param Callable | str | None norm: Normalize TFBS data using a spyce normalization function.
    :param pd.Series | pl.Series | np.ndarray | List | None norm_vec: Normalization vector. The function iterates over the unique values,
        creates a mask for them, and applies the `norm` function to each sub-matrix independently. If `None` is passed, no normalization is
        performed.
    :param pd.Series | pl.Series | np.ndarray | List | None harmony_vec: If set, perform Harmony batch correction over these value.
        Disable by setting this value to `None`.
    :param str | Callable collapse_fun: Define how the TFBS motif KMer probabilities are combined with
        the data after the k-mer histograms were multiplied. This obtains a TFBS-specific kmer 
        probability score per cell (a surrogate for the probability that the TFBS motif is present with a given
        k-mer in the data). `collapse_fun` defines how these k-mer specific TBFS probability scores are then aggregated to provide single
        score per TFBS motif. You can pass either a string (choose between `mean` | `max` | `min`) or a Callable.
        Note that the callable must aggregate over the kmer axis, which is `axis=1` per default.
    :param int verbosity: Verbosity level
    :param str verbosity_indent: Indentation string added before printout
    :params kwargs: Other keyword parameters passed to Harmony.
    :return pd.DataFrame: pandas dataframe containing the TF scoring in a matrix cells x motifs
    """
    tf_kmer_list = []
    if use_motif_dr is None:
        if not isinstance(motif_kmer.kmer_hist, np.ndarray):
            motif_data = sp.coo_matrix(motif_kmer.kmer_hist) 
            multiply_fun = sp.coo_matrix.multiply
        else:
            motif_data = motif_kmer.kmer_hist
            multiply_fun = np.multiply
    else:
        motif_data = motif_kmer.dr[use_motif_dr]
        multiply_fun = np.multiply

    if use_kmer_dr is None:
        iterator = tqdm(
            kmer_obj, 
            desc="%sCalculate motif score for data set" % verbosity_indent
        ) if verbosity > 0 else kmer_obj
    else:
        iterator = tqdm(
            kmer_obj.dr[use_kmer_dr], 
            desc="%sCalculate motif score for data set" % verbosity_indent
        ) if verbosity > 0 else kmer_obj.dr[use_kmer_dr]
    norm = convert_normalization(norm)
    
    # simple matrix operation
    # use row wise iteration for printout 
    for kmer in iterator:   
        expand_mat = multiply_fun(motif_data, kmer.reshape(1, -1))
        if isinstance(collapse_fun, Callable):
             tf_kmer_list.append(collapse_fun(expand_mat))
        else:
            if collapse_fun.lower() == "mean" or collapse_fun.lower() == "sum":  
                summed_val = expand_mat.sum(axis=1).reshape(-1, 1)
                if collapse_fun.lower() == "mean":
                    div = (expand_mat.sum(axis=0) > 0).sum()
                    if div == 0:
                        div = 1.
                    tf_kmer_list.append(summed_val / div)
                else:
                    tf_kmer_list.append(summed_val)
            elif collapse_fun.lower() == "max":
                tf_kmer_list.append(expand_mat.max(axis=1).reshape(-1, 1))
            elif collapse_fun.lower() == "min":
                tf_kmer_list.append(expand_mat.min(axis=1).reshape(-1, 1))
            else:
                raise NotImplementedError("The passed aggregation function is not implemented. Please pass your own "
                                          "callable (remember to aggregate over the kmer axis, axis=1 per default); or "
                                          "pass one of the following strings: `mean` | `max` | `min`.")

    stack_lib = np if isinstance(tf_kmer_list[0], np.ndarray) else sp
    data_mat = stack_lib.hstack(tf_kmer_list).T
    index = kmer_obj.barcodes
    cols = motif_kmer.barcodes
    if (data_mat.sum(axis=1) == 0).any():
        warnings.warn("Found cells with zero enrichment for all TFBS motifs. "
                      "Those cells are removed to avoid problems with further downstream correction procedures.")
        norm_vec = norm_vec[data_mat.sum(axis=1) > 0]
        harmony_vec = harmony_vec[data_mat.sum(axis=1) > 0]
        index = index[data_mat.sum(axis=1) > 0]
        data_mat = data_mat[data_mat.sum(axis=1) > 0]

    if (data_mat.sum(axis=0) == 0).any():
        warnings.warn("Found TFBS motifs that aren't present in any cell. " 
                      "Those TFBS motifs are removed to avoid problems with further downstream correction procedures.")
        cols = cols[data_mat.sum(axis=0) > 0]
        data_mat = data_mat[:, data_mat.sum(axis=0) > 0]

    if norm_vec is not None:
        if isinstance(norm_vec, pl.Series) or isinstance(norm_vec, pd.Series):
            norm_vec = norm_vec.to_numpy()
        elif isinstance(norm_vec, list):
            norm_vec = np.array(norm_vec)
        elif isinstance(norm_vec, np.ndarray):
            pass
        else:
            raise ValueError("`norm_vec` must be of type pl.Series | pd.Series | np.ndarray | List. "
                             "You passed a `norm_vec` of type %s" % type(norm_vec))
        if not isinstance(data_mat, np.ndarray):
            data_mat = data_mat.tocsr()

        for nval in np.unique(norm_vec):
            norm_mask = nval == norm_vec
            data_mat[norm_mask] = norm(data_mat[norm_mask], **kwargs)
    
    if harmony_vec is not None:
        data_mat = harmony_correct(data_mat, target_vec=harmony_vec, verbosity=verbosity - 1, **kwargs)
    
    # create dataframe
    cell_tf_mat = pd.DataFrame(
        data_mat if isinstance(data_mat, np.ndarray) else data_mat.A,
        index=index,
        columns=cols
    )
    return cell_tf_mat


def sig_test_beta(
        frg_sample: np.ndarray,
        bkg_sample: np.ndarray | float,
        motif_vec: pl.Series | pd.Series | np.ndarray | List,
        alternative: str = "greater",
        fdr_control: str = "bh",
        verbosity: int = 0,
        verbosity_indent: str = ""
) -> pl.DataFrame:
    """
    Compare TFBS scores of a foreground to a single background value (such as a score predicted over the all accessible regions/
    the entire genome) using a beta distribution. More precisely, fit TFBS scores to beta distribution and evaluate whether a 
    single (background) value is outside a confidence interval. 
    Note that this requires the scores to be properly normalised to yield a reasonable distribution.
    This method is experimental and should only be taken with a pinch of salt.

    :param np.ndarray frg_sample: Foreground data to which the beta distribution is approximated
    :param np.ndarray | float bkg_sample: Background value. This value is tested what the probability is that
        the value is part of the foreground data
    :param pl.Series | pd.Series | np.ndarray | List motif_vec: List with TFBS motif names
    :param str alternative: Test alternative. Choose between `greater` | `less` | `two-sided`.
    :param str fdr_control: Define algorithm for false discover rate control. Choose between `bh` | `by` | `none`
    :param int verbosity: Verbosity level
    :param str verbosity_indent: Indentation string added before printout
    :return pl.DataFrame: Return polars data frame with enrichment, p-value, and fdr per TFBS.
    """
    if isinstance(bkg_sample, float):
        bkg_sample = np.array([bkg_sample])
        frg_sample = frg_sample.reshape(-1, 1)
    if bkg_sample.shape[0] != frg_sample.shape[1] != motif_vec.shape[0]:
        raise ValueError("The number of background samples must match the number of columns in the foreground sample "
                         "and the number of motifs in `motif_vec`")
    sample_iter = zip(frg_sample.T, bkg_sample)
    if verbosity > 0:
        sample_iter = tqdm(
            sample_iter, 
            total=bkg_sample.shape[0],
            desc="%sCalulate beta significance" % verbosity_indent
        )
    pval_l, diff_l = [], []
    for frgs, bkgv in sample_iter:
        beta_params = st.beta.fit(frgs)
        diff_l.append(np.median(frgs) - bkgv)
        survival = st.beta(*beta_params).sf(bkgv)
        if alternative.lower() == "greater":
            pval = np.minimum(2 * (1. - survival), 1.)
        elif alternative.lower() == "lower" or alternative.lower() == "less":
            pval = np.minimum(2 * survival, 1.)
        elif alternative.lower() == "two-sided":
            pval = 2 * np.minimum(survival, 1. - survival)
        else:
            raise ValueError("Alternative not understood. Pass one of the following: `greater` | `less` | `two-sided`")
        pval_l.append(pval)

    pval_fdr = np.full_like(pval_l, fill_value=np.nan)
    if fdr_control is not None:
        if fdr_control.lower() != "none":
            if verbosity > 1:
                print("Apply %s FDR control" % fdr_control)
            pval_fdr = st.false_discovery_control(
                pval_l,
                method=fdr_control
            )
            
    return pl.DataFrame({
        "name": motif_vec,
        "absolute diff": diff_l,
        "p-value": pval_l,
        "fdr": pval_fdr
    })

def sig_tscore_test(
        frg_sample: np.ndarray,
        bkg_sample: np.ndarray | float,
        motif_vec: pl.Series | pd.Series | np.ndarray | List,
        alternative: str = "greater",
        fdr_control: str = "bh",
        verbosity: int = 0,
        verbosity_indent: str = ""
):
    """
    Compare TFBS scores of a foreground to a single background value (such as a score predicted over the all accessible regions/
    the entire genome) using a Student-t distribution. More precisely, we evaluate the difference between TFBS scores and
    a single (background), which should be t-distributed when the TFBS distribution is sufficiently close to normal. 
    Note that this requires the scores to be properly normalised to yield a reasonable distribution.
    This method is experimental and should only be taken with a pinch of salt.

    :param np.ndarray frg_sample: Foreground data to which we measure the difference to the backround. Data is expected to
        be close to normally distributed.
    :param np.ndarray | float bkg_sample: Background value. It is tested whether values in the forground sample are significantly
        different from the mean.
    :param pl.Series | pd.Series | np.ndarray | List motif_vec: List with TFBS motif names
    :param str alternative: Test alternative. Choose between `greater` | `less` | `two-sided`.
    :param str fdr_control: Define algorithm for false discover rate control. Choose between `bh` | `by` | `none`
    :param int verbosity: Verbosity level
    :param str verbosity_indent: Indentation string added before printout
    :return pl.DataFrame: Return polars data frame with enrichment, p-value, and fdr per TFBS.
    """
    if isinstance(bkg_sample, float):
        bkg_sample = np.array([bkg_sample])
        frg_sample = frg_sample.reshape(-1, 1)
    if bkg_sample.shape[0] != frg_sample.shape[1] != motif_vec.shape[0]:
        raise ValueError("The number of background samples must match the number of columns in the foreground sample "
                         "and the number of motifs in `motif_vec`")
    sample_iter = zip(frg_sample.T, bkg_sample)
    if verbosity > 0:
        sample_iter = tqdm(
            sample_iter, 
            total=bkg_sample.shape[0],
            desc="%sCalulate beta significance" % verbosity_indent
        )
    pval_l, diff_l = [], []
    for frgs, bkgv in sample_iter:
        frg_mean = frgs.mean()
        frg_std = frgs.std()
        diff_l.append(frg_mean - bkgv)
        t_x = (bkgv - frg_mean) / frg_std
        survival = st.t(df=frgs.shape[0] - 1).sf(t_x) 
        if alternative.lower() == "greater":
            pval = np.minimum(2 * (1. - survival), 1.)
        elif alternative.lower() == "lower" or alternative.lower() == "less":
            pval = np.minimum(2 * survival, 1.)
        elif alternative.lower() == "two-sided":
            pval = 2 * np.minimum(survival, 1. - survival)
        else:
            raise ValueError("Alternative not understood. Pass one of the following: `greater` | `less` | `two-sided`")
        pval_l.append(pval)

    pval_fdr = np.full_like(pval_l, fill_value=np.nan)
    if fdr_control is not None:
        if fdr_control.lower() != "none":
            if verbosity > 1:
                print("Apply %s FDR control" % fdr_control)
            pval_fdr = st.false_discovery_control(
                pval_l,
                method=fdr_control
            )
            
    return pl.DataFrame({
        "name": motif_vec,
        "absolute diff": diff_l,
        "p-value": pval_l,
        "fdr": pval_fdr
    })

def sig_test_over_total_background(
       kmer_obj: KMerClass,
       motif_kmer: KMerMatrix,
       total_bkg_kmer: KMerClass,
       ct_vec: pd.Series | pl.Series | np.ndarray | List | None = None,
       norm: Callable | str | None = "sum_norm",
       norm_vec: pd.Series | pl.Series | np.ndarray | List | None = None,
       harmony_vec: pd.Series | pl.Series | np.ndarray | List | None = None,
       collapse_fun: str | Callable = "sum",
       alternative: str = "greater",
       sig_test: str = "t",
       fdr_control: str | None = "bh",
       verbosity: int = 0,
       verbosity_indent: str = "",
       **kwargs
) -> Dict[str, pl.DataFrame] | pl.DataFrame:
    """
    Perform signficance test using a non-normalized `kmer_obj` and the k-mer histogram over all 
    features and peaks (background). Significance is tested by calculating a beta distribution over
    the foreground values (ie. normalized probabilities mulitplied by a constant) and the probability of the 
    background value. Please pass a non-normalized `kmer_obj` and normalize using `sum_norm`. This only valid
    when using a single-species.
    This method is experimental and should only be taken with a pinch of salt.

    :param KMerClass kmer_obj: KMer data object
    :param KMerMatrix motif_kmer: KMer matrix of motifs.
    :param KMerClass total_bkg_kmer: KMer object representing k-mer histogram/scores over all accessible regions.
    :param pd.Series | pl.Series | np.ndarray | List | None ct_vec: Vector with cell type labels. Size matches
        number of cells in KMer object
    :param Callable | str | None norm: Normalization applied to TFBS scores
    :param pd.Series | pl.Series | np.ndarray | List | None norm_vec: Normalization vector indicating groups of cells
        that are normalized together (for example for centering).
    :param pd.Series | pl.Series | np.ndarray | List | None harmony_vec: Vector with cell labels that are used
        for the harmony correction.
    :param str | Callable collapse_fun: Aggregation function used for collapsing the TFBS scores over k-mers
    :param str alternative: Alternative for significance test. Choose between `greater` | `less` | `two-sided`
    :param str sig_test: Significance test to perform. Choose between `t` | `beta`.
    :param str fdr_control: Type of control applied to account for false discovery rate.
    :param int verbosity: Verbosity level
    :param str verbosity_indent: Indentation string added before printout
    :param kwargs: Other keywords that are passed the motif score function
    :return Dict[str, pl.DataFrame] | pl.DataFrame: If `ct_vec` is passed, return an enrichment table per cell type, 
        otherwise return results directly (containing name, absolute difference, p-value and q-value for TFBS).
    """
    
    
    if norm_vec is None:
        norm_vec = np.ones(kmer_obj.shape[0])

    if sig_test.lower() == "t":
        sig_fun = sig_tscore_test
    elif sig_test.lower() == "beta":
        sig_fun = sig_test_beta
    else:
        raise ValueError("`sig_test` not understood. Please pass one of the following: `t` | `beta`.")
    
    tfbs_score_df = data_set_motif_score(
        kmer_obj=kmer_obj,
        motif_kmer=motif_kmer,
        norm=norm,
        norm_vec=norm_vec,
        harmony_vec=harmony_vec,
        collapse_fun=collapse_fun,
        verbosity=verbosity,
        verbosity_indent=verbosity_indent,
        **kwargs
    )

    total_tfbs_score_df = data_set_motif_score(
        kmer_obj=total_bkg_kmer,
        motif_kmer=motif_kmer,
        norm=norm,
        norm_vec=np.ones(1),
        harmony_vec=harmony_vec,
        collapse_fun=collapse_fun,
        verbosity=verbosity - 1,
        verbosity_indent=verbosity_indent,
        **kwargs
    )
    
    if ct_vec is None:
        return sig_fun(
            tfbs_score_df.to_numpy(),
            total_tfbs_score_df.to_numpy().flatten(),
            motif_vec=total_tfbs_score_df.columns,
            alternative=alternative,
            fdr_control=fdr_control,
            verbosity=verbosity,
            verbosity_indent=verbosity_indent
        )
    else:
        sig_test_results = {}
        for ct in ct_vec.unique():
            ct_mask = (ct == ct_vec).to_numpy()
            sig_test_results[ct] = sig_fun(
                tfbs_score_df[ct_mask].to_numpy(),
                total_tfbs_score_df.to_numpy().flatten(),
                motif_vec=total_tfbs_score_df.columns,
                alternative=alternative,
                fdr_control=fdr_control,
                verbosity=verbosity,
                verbosity_indent=verbosity_indent + ct + ": "
            )
        return sig_test_results


def sig_test(
        frg_sample: np.ndarray,
        bkg_sample: np.ndarray,
        motif_vec: pl.Series | pd.Series | np.ndarray | List,
        test_type: str = "mannwhitneyu",
        alternative: str = "greater",
        fdr_control: str | None = "bh",
        verbosity: int = 0,
        verbosity_indent: str = "",
        **kwargs
) -> pl.DataFrame:
    """
    Perform significance test for difference over given samples.

    :param np.ndarray frg_sample: foreground TFBS kmer sample (cells x feature)
    :param np.ndarray bkg_sample: background TFBS kmer sample (cells x feature)
    :param pd.Series | pl.Series | np.ndarray | List | None motif_vec: Vector with motif names.
    :param str test_type: Type of significance test. Choose between `mannwhitneyu` | `ks` for Kolmogorov-Smirnov
    :param str alternative: Hypotehsis test. Pass `greater` | `less` | `two-sided`
    :param str | None fdr_control: False-discovery control. Pass `bh` for Benjamini-Hochberg | `by` for
        Benjamini-Yekutieli | `none` for none.
    :param int verbosity: Verbosity level
    :param str verbosity_indent: Prefix for progress bar and print outs
    :param kwargs: Unused parameters.
    :return pl.Series: pvalues, fdr control (if set), statistics, and difference per motif.
    """
    if test_type.lower() == "ks":
        test_fun = st.ks_2samp
    elif test_type.lower() == "mannwhitneyu":
        test_fun = st.mannwhitneyu
    else:
        raise ValueError("Test statistic %s not understood. Please pass one of the following: ks | mannwhitneyu." % test_type)
    pval  = np.zeros(frg_sample.shape[1])
    stats = np.zeros(frg_sample.shape[1])
    data_iter = tqdm(
        np.arange(frg_sample.shape[1]),
        total=frg_sample.shape[1],
        desc="%sSignificant test" % verbosity_indent
    ) if verbosity > 0 else np.arange(frg_sample.shape[1])
    for data_idx in data_iter:
        res = test_fun(
            frg_sample[:, data_idx], 
            bkg_sample[:, data_idx], 
            alternative=alternative
        )
        pval[data_idx] = res.pvalue
        stats[data_idx] = res.statistic
        
    frg_mean = np.median(frg_sample, axis=0)
    bkg_mean = np.median(bkg_sample, axis=0)   
    div = np.std(frg_sample, axis=0)
    div[div == 0] = 1.
    diff = (frg_mean - bkg_mean) / div

    pval_fdr = np.full_like(pval, fill_value=np.nan)
    if fdr_control is not None:
        if fdr_control.lower() != "none":
            if verbosity > 1:
                print("Apply %s FDR control" % fdr_control)
            pval_fdr = st.false_discovery_control(
                pval,
                method=fdr_control
            )
            
    return pl.DataFrame({
        "name": motif_vec,
        "absolute diff": diff,
        "statistic": stats,
        "p-value": pval,
        "fdr": pval_fdr
    })


def equivalence_test(
        frg_sample: np.ndarray,
        bkg_sample: np.ndarray,
        motif_vec: pl.Series | pd.Series | np.ndarray | List,
        fdr_control: str | None = "bh",
        scale_dstat: bool = True,
        verbosity: int = 0,
        verbosity_indent: str = "",
        **kwargs
):
    r"""
    **Note that this method is experimental**. Equivalence test for Kolmogornov-Smirnov test taken from

    > Alexis (https://stats.stackexchange.com/users/44269/alexis), 
    > Is there a simple equivalence test version of the Kolmogorov–Smirnov test?, 
    > URL (version: 2021-04-14): https://stats.stackexchange.com/q/108487

    and adapted according to

    > Hodges Jr, J. L. "The significance probability of the Smirnov two-sample test." 
    > Arkiv för matematik 3.5 (1958): 469-486.

    Note that, despite the fact that there's a parameter for foreground and background values, the
    significance test is symmetric. Swapping foreground and background will provide the same results.
    Note that as pointed out in the Stackexchange comment, a p-value = 0.05 might not be the best
    approach, as the underlying Rayleigh distribution is non-symmetric which increases quickly for low 
    values with a sigma of 0.5 (which is the case for this equivalence test).
    The critical value is computed as in 

    .. math::
        Q(p) = \sqrt{\frac{-\ln{(1 - p)}}{2}}
    
    
    Given the variance the Rayleigh distribution is 0.5, the comment suggests a conservative threshold of
    
    .. math::
        Q(0.05) + \frac{\sigma}{4} = Q(0.05) + \frac{1}{8}
    
    
    (which is around 0.15); or a more liberal threshold when adding half of the variance, which results in a
    p-value of around 0.28.

    :param np.ndarray frg_sample: Foreground data values (KMer values or TFBS scores).
    :param np.ndarray bkg_sample: Background data values (KMer values or TFBS scores). 
    :param pl.Series | pd.Series | np.ndarray | List motif_vec: List or iterable with motif names
    :param str | None fdr_control: Algorithm for False-Discovery-Rate (FDR) control. Pass `bh` 
        for Benjamini-Hochberg | `by` for Benjamini-Yekutieli | `none` for none.
    :param bool scale_dstat: If `True`, scale KS statistic according to the number of data points used. 
    :param int verbosity: Verbosity level
    :param str verbosity_indent: Prefix for progress bar and print outs
    :param kwargs: Unused parameters.
    :return pl.Series: pvalues, fdr control (if set), statistics, and difference per motif.
    """

    pval  = np.zeros(frg_sample.shape[1])
    stats = np.zeros(frg_sample.shape[1])
    data_iter = tqdm(
        np.arange(frg_sample.shape[1]),
        total=frg_sample.shape[1],
        desc="%sEquivalence test" % verbosity_indent
    ) if verbosity > 0 else np.arange(frg_sample.shape[1])

    n_frg = frg_sample.shape[0]
    n_bkg = bkg_sample.shape[0]
    sample_scale = np.sqrt(n_frg * n_bkg / (n_frg + n_bkg))
    for data_idx in data_iter:
        # calculate D (maximum of D+ and D-)
        D_stat = st.ks_2samp(
            frg_sample[:, data_idx], 
            bkg_sample[:, data_idx], 
            alternative="two-sided"
        ).statistic  

        # scale D according to sample size
        D_sample = D_stat * sample_scale

        # use result in Hodges 1958 and stackexchange comment to compute p-value
        pval[data_idx] = st.rayleigh.cdf(D_sample if scale_dstat else D_stat, scale=0.5)
        stats[data_idx] = D_stat

    frg_mean = np.median(frg_sample, axis=0)
    bkg_mean = np.median(bkg_sample, axis=0)   
    diff = frg_mean - bkg_mean

    pval_fdr = np.full_like(pval, fill_value=np.nan)
    if fdr_control is not None:
        if fdr_control.lower() != "none":
            if verbosity > 1:
                print("Apply %s FDR control" % fdr_control)
            pval_fdr = st.false_discovery_control(
                pval,
                method=fdr_control
            )
            
    return pl.DataFrame({
        "name": motif_vec,
        "absolute diff": diff,
        "statistic": stats[data_idx],
        "p-value": pval,
        "fdr": pval_fdr
    })
   


def find_sig_tf(
        ct_vec: pd.Series | pl.Series | np.ndarray | List,
        kmer_obj: KMerClass | None = None,
        motif_kmer: KMerClass | None = None,
        tfbs_score: pd.DataFrame | None = None,
        norm: None | str | Callable = None,
        norm_vec: pd.Series | pl.Series | np.ndarray | List | None = None,
        harmony_vec: pd.Series | pl.Series | np.ndarray | List | None = None,
        use_kmer_dr: str | None = None,
        use_motif_dr: str | None = None,
        collapse_fun: str | Callable = "sum",
        sig_test_type: str = "divergence",
        tfbs_test_type: str = "ks",
        tfbs_alternative: str = "greater",
        tfbs_fdr_control: str | None = "bh",
        scale_by_size: bool = True,
        avg_policy: str = "median",
        verbosity: int = 0,
        verbosity_indent: str = "", 
        **kwargs
) -> Dict[str, pl.DataFrame]:
    """
    TFBS motif enrichment signficance or equivalence test. The function requires a cell type annotation and
    either the pre-computed TFBS scores or a KMer object for the data set and for the
    TFBS motifs (see function `motifs_to_kmer`). It then iterates over all cell types and comparse the TFBS
    distribution with all other cell types. Note that this circumvents the problem of a significance test
    over a multimodal distribution. Finally, all tests are aggregated together to yield a single
    enrichment, p, and q-value per cell type.

    :param pd.Series | pl.Series | np.ndarray | List ct_vec: Cell type annotation or cell grouping as a list, array
        or series.
    :param KMerClass | None kmer_obj: `KMerMatrix` or `KMerCollection` that contains the data KMer data. Only necessary when
        TFBS scores haven't been pre-computed.
    :param KMerClass | None motif_kmer: `KMerMatrix` for the TFBS motifs. The matrix can be created using the function
        `motifs_to_kmer`. Only necessary if TFBS scores haven't been pre-computed.
    :param pd.DataFrame | None tfbs_score: Pre-computed TFBS scores. 
    :param  None | str | Callable norm: Normalize with spyce normalization faction along `norm_vec`. To be more precise,
        The function iterates over unique values in `norm_vec`, creates a mask, and applies `norm` to the masked sub-matrices
        independently. 
    :param pd.Series | pl.Series | np.ndarray | List | None norm_vec: Normalization vector. The function iterates over the unique values,
        creates a mask for them, and applies the `norm` function to each sub-matrix independently. If `None` is passed, no normalization is
        performed.
    :param pd.Series | pl.Series | np.ndarray | List | None harmony_vec: If set, perform Harmony batch correction over these value.
        Disable by setting this value to `None`.
    :param str | None use_kmer_dr: Use a specific k-mer dimensionality reduction for creating the TFBS enrichment. If `None`,
        use the k-mer data directly.
    :param str | None use_motif_dr: Use a specific motif dimensionality reduction for creating the TFBS enrichment. If `None`,
        use the k-mer data directly.
    :param str | Callable collapse_fun: Aggregation function used for creating the TFBS motif enrichemnt score
        (for more information, see function `data_set_motif_score`).
    :param str sig_test_type: Pass `conservation` if you want to test for significant similarity, `divergence` if you want to 
        test for significant difference. Note that if you pass `conservation`, the `tfbs_test_type` will be automatically 
        set to `ks`. **Note that `conservation` is experimental.**
    :param str tfbs_test_type: Test type for significant TFBS motifs. Choose between `mannwhitneyu` and `ks`. Note that
        when choosing `sig_test_type=conservation`, this will be automatically set to `ks`. If you've set
        `mannwhitneyu` nonetheless, the function will raise a warning.
    :param str tfbs_alternative: Alternative for TFBS significant test. Choose between `greater` | `less` | `two-sided`.
        This parameter is ignored for `sig_test_type=conservation`
    :param str | None tfbs_fdr_control: FDR correction algorithm for TFBS signficant test. Pass `bh` for Benjamini-Hochberg 
        | `by` for Benjamini-Yekutieli | `none` for none.
    :param bool scale_by_size: If `True`, weigh results according to number of cells per type before aggregating using 
        `avg_policy` (does not apply when `avg_policy="fdr"`).
    :param str avg_policy: Significance tests are performed between every pair of cell types. `avg_policy` defines how 
        these results are combined to a single significance value for each cell type and TFBS. Choose between
        `mean` | `max_fdr` | `median` | `min_p` | `max_diff`.
    :param int verbosity: Verbosity levels
    :param str verbosity_indent: Prefix for output and progress bars.
    :param kwargs: Other key word parameters that are passed to subfunctions.
    :return Dict[str, pl.DataFrame]: A dictionary with the group name as key and the data frame with TFBS motif 
        enrichement results as value.
    """
    if isinstance(ct_vec, list) or isinstance(ct_vec, np.ndarray):
        ct_vec = pd.Series(ct_vec)

    if norm_vec is None:
        norm_vec = ct_vec

    if sig_test_type.lower() == "conservation" and tfbs_test_type.lower() == "mannwhitneyu":
        warnings.warn("You've passed `sig_test_type='conservation'` and `tfbs_test_type='mannwhitneyu'`. Significance test for "
                      "conservation are currently only provided for `ks` tests. `tfbs_test_type='mannwhitneyu'` will be ignored.")

    if sig_test_type.lower() == "divergence":
        compare_fun = sig_test 
    elif sig_test_type.lower() == "conservation":
        compare_fun = equivalence_test
    else:
        raise ValueError("`sig_test_type=%s` not understood. Please pass one of the following: `divergence` | `conservation`." % sig_test_type)
    
    if tfbs_score is None and kmer_obj is not None and motif_kmer is not None:
        if isinstance(harmony_vec, pl.Series):
            harmony_vec = harmony_vec.to_pandas()
        if (pd.Series(harmony_vec).value_counts() < 2).any():
            raise ValueError("There must be at least 2 entries per group in `harmony_vec`.")
        tfbs_score = data_set_motif_score(
            kmer_obj=kmer_obj,
            motif_kmer=motif_kmer,
            use_kmer_dr=use_kmer_dr,
            use_motif_dr=use_motif_dr,
            norm=norm,
            norm_vec=norm_vec,
            harmony_vec=harmony_vec,
            verbosity=verbosity,
            verbosity_indent=verbosity_indent,
            collapse_fun=collapse_fun,
            **kwargs
        )
    elif tfbs_score is not None:
        pass
    else:
        raise ValueError("You need to pass either a pre-computed TFBS score matrix or a data AND a motif KMerMatrix/KMerCollection.")
    
    n_cells = ct_vec.value_counts()
    ct_set = ct_vec.unique()
    ct_iterator = tqdm(
        ct_set,
        desc="%sTFBS for cell type" % verbosity_indent
    ) if verbosity > 0 else ct_set
    
    ct_sig_tfbs_dict = {}
    for ct in ct_iterator:
        other_ct = n_cells.drop(index=ct)
        ct_mask = (ct_vec == ct).to_numpy().astype("bool")
        if ct_mask.astype("int").sum() <= 5:
            warnings.warn("You must have more than 5 cells per annotated foreground cell type. Skip %s." % ct)
            continue

        # fetch tfbs scoring for foreground
        frg_samples = tfbs_score.iloc[ct_mask].to_numpy()
        ct_df_l = []
        for bkg_ct in ct_set:
            if bkg_ct == ct: continue
            bkg_mask = (ct_vec == bkg_ct).to_numpy().astype("bool")
            if bkg_mask.astype("int").sum() <= 5:
                warnings.warn("You must have more than 5 cells per annotated background cell type. Skip %s." % bkg_ct)
                continue
            
            # fetch tfbs scoring forbackground
            bkg_samples = tfbs_score.iloc[bkg_mask].to_numpy()

            if frg_samples.shape[0] == 0 or bkg_samples.shape[0] == 0: 
                continue
            
            bct_df = compare_fun(
                frg_sample=frg_samples,
                bkg_sample=bkg_samples,
                motif_vec=tfbs_score.columns,
                test_type=tfbs_test_type,
                alternative=tfbs_alternative,
                verbosity=verbosity - 1,
                verbosity_indent="%s\t" % verbosity_indent,
                fdr_control=tfbs_fdr_control,
                **kwargs
            )
    
            ct_df_l.append(
                bct_df.group_by("name").agg(pl.col(["absolute diff", "statistic", "p-value", "fdr"]).median()).with_columns(pl.lit(bkg_ct).alias("background"))
            )
            if scale_by_size and avg_policy.lower() != "fdr":
                scaling = other_ct.loc[bkg_ct] / float(other_ct.sum())
                ct_df_l[-1] = ct_df_l[-1].with_columns(
                    pl.col(["absolute diff", "statistic", "p-value", "fdr"]) * scaling
                )
        if len(ct_df_l) > 0:
            ct_sig_tfbs_dict[ct] = pl.concat(ct_df_l)
        else:
            ct_sig_tfbs_dict[ct] = pl.DataFrame(schema=["name", "absolute diff", "statistic", "p-value", "fdr"])
            continue
        if ct_sig_tfbs_dict[ct].shape[0] > 0:
            # significance is set to the largest fdr
            # determine average difference
            if avg_policy.lower() == "mean":
                ct_sig_tfbs_dict[ct] = ct_sig_tfbs_dict[ct].group_by("name").agg(pl.mean([ "absolute diff", "statistic", "p-value", "fdr"]))
            elif avg_policy.lower() == "max_fdr":
                ct_sig_tfbs_dict[ct] = ct_sig_tfbs_dict[ct].group_by("name").agg(
                    pl.all().sort_by(["fdr", "p-value"], descending=True).first()
                ).drop("background")
            elif avg_policy.lower() == "min_p":
                ct_sig_tfbs_dict[ct] = ct_sig_tfbs_dict[ct].group_by("name").agg(
                    pl.all().sort_by(["p-value"], descending=False).first()
                ).drop("background")
            elif avg_policy.lower() == "max_diff":
                ct_sig_tfbs_dict[ct] = ct_sig_tfbs_dict[ct].group_by("name").agg(
                    pl.all().sort_by(["absolute diff"], descending=True).first()
                ).drop("background")
            elif avg_policy.lower() == "median":
                ct_sig_tfbs_dict[ct] = ct_sig_tfbs_dict[ct].group_by("name").agg(pl.median(["absolute diff",  "statistic", "p-value", "fdr"]))
            else:
                raise ValueError("`avg_policy` not understood. Please pass one of the following: `mean` | `max_fdr` | `median` | `min_p` | `max_diff`.")
    return ct_sig_tfbs_dict    

