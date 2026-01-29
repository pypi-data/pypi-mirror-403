from __future__ import annotations

import os
import copy
import time
from typing import List, Callable, Tuple, Dict
from abc import ABC
from pathlib import Path
from collections import Counter
import warnings
import re

import pandas as pd
import pysam
import numpy as np
import polars as pl
import anndata as ad
import scipy.sparse as sp
from scipy.stats import spearmanr
from scipy.special import binom
from tqdm import tqdm
import umap
from itertools import product, chain, permutations
from Bio.Seq import Seq
import fcntl
from sklearn.metrics.pairwise import pairwise_distances
import dill
import multiprocessing


from spyce.dataType import KMerHistogramObject
from spyce.constants import DNA_ALPHABET, MAX_K_DENSE, BUG_REPORT, GC_CONTENT
from spyce.utils import seq_to_int, fetch_async_result, get_nn_mat, nozero_kmer_to_idx, get_kmer_names, get_gkm_mat
from spyce.normalize import convert_normalization, normalize_over_ord_vec, icp, harmony_correct


# Recursive pickling using Dill library.
dill.settings["recurse"] = True


def create_kmer_hist(
        seq_list: List[str],
        cell_id: str | int | None = None,
        k: int = 6,
        alphabet: List[str] = DNA_ALPHABET,
        mask_rep: bool = False,
        n_policy: str = "remove",
        return_dense: bool = False,
        rm_zeros: bool = True,
        equalize_counter: bool = True,
        dump_to: str | None = None,
        gkmer_mat: None | sp.csr_matrix = None,
        max_wait: float = 60.,
        **kwargs
) -> sp.coo_matrix | np.ndarray | None:
    """
    Create kmer histogram distribution

    :param List[str] seq_list: list with sequences of areas of interest (e.g. peaks)
    :param str | int | None cell_id: Only used if dumped to file. Cell identifier, can be barcode, index.
    :param int k: defines length of k-mers. For example `k=3` creates 3-mers, i.e. overlapping sequence strings of
        length 3.
    :param List[str] alphabet: List of alphabet characters
    :param bool mask_rep: If set to True, remove kmers that contain lower case letters indicating masked repetitive
        sequences. If set to False, treat masked sequences equal to non-masked sequences
    :param str n_policy: Defines how to deal with non-deterministic letters. Choose between remove | replace | keep.
        
        - `remove` filters out kmers with N occurrences.
        - `replace` replaces kmers that contain Ns with all possibilities
        - `keep` keeps the Ns untreated

    :param bool return_dense: if set to true and `dump_to` is None, return dense numpy array instead of sparse array.
    :param bool rm_zeros: If `equalize_counter` is set to `True`, the reverse complement kmer counts are added to 
        the forward kmer counts. This makes produces redundant entries, which can be set to zero and removed 
        to save memory (or storage when you save your object). However, some functions won't be available, such
        as performing a kmer transpositon.
    :param bool equalize_counter: If set to `True`, treat forward and reverse complement kmer as the same kmer. That
        means values for `GCGT` are added to the histogram values for `ACGC`. Otherwise, they are treated as independent
        entities. 
    :param str | None dump_to: path to file where to dump to results
    :param None | sp.csr_matrix gkmer_mat: Binary match matrix mapping ell-mers to gapped k-mers. If `None`, assume full
        k-mers, otherwise map ell-mer counts to gapped k-mer counts. 
    :param float max_wait: Maximum waiting time for trying accessing file.
    :param kwargs: unused parameters
    :return sp.coo_matrix | np.ndarray | None: Kmer histogram if not dumped to file. If `return_dense=True`, return as
        numpy array otherwise as sparse coo_matrix.
    """
    if not all([letter in DNA_ALPHABET for letter in alphabet]):
        equalize_counter = False
        warnings.warn("Alphabet doesn't correspond to DNA alphabet. Can't equalize counter for complement sequences.")
    # fetch kmers present in sequence list

    # quicker implementation for non-gapped kmers
    if not mask_rep:
        kmers = [seq[i:i + k].upper() for seq in seq_list for i in range(0, len(seq) - k + 1)]
    else:
        kmers = [seq[i:i + k] for seq in seq_list for i in range(0, len(seq) - k + 1)
                if seq[i:i + k].isupper()]

    n_policy = n_policy.lower()
    alphabet_ = copy.copy(alphabet)
    if n_policy == "remove":
        # filter out kmers that contain Ns
        kmers = [kmer for kmer in kmers if "N" not in kmer.upper()]
    elif n_policy == "replace":
        # replace kmers that contain Ns with all possible combinations
        for i_kmer in range(len(kmers)):
            kmer = kmers.pop(i_kmer)
            if "N" not in kmer.upper():
                kmers.append(kmer)
            else:
                new_kmers = []
                n_n = sum([letter.upper() == "N" for letter in kmer])
                possible_comb = product(alphabet, repeat=n_n)
                for combination in possible_comb:
                    new_kmer = ""
                    cntr = 0
                    for letter in kmer:
                        if letter.upper() != "N":
                            new_kmer += letter
                        else:
                            replace_letter = combination[cntr]
                            cntr += 1
                            new_kmer += replace_letter
                    new_kmers.append(new_kmer)
                kmers.extend(new_kmers)
    elif n_policy == "keep":
        if "N" not in alphabet_:
            alphabet_.append("N")
        # do nothing
        pass
    else:
        # rais error if policy not undersood
        raise ValueError("n_policy %s not understood. Choose between remove | replace | keep." % n_policy)
    # count occurrences

    kmer_counter = Counter(kmers)
    if equalize_counter:
        # account for the fact that the annotation could also occur for the reversed strand
        equalized_kmer_counter = {}
        # sort alphabetically
        for kmer, n_kmer in sorted(kmer_counter.items(), key=lambda _: _[0]):
            rev_kmer = str(Seq(kmer).reverse_complement())
            # account for palindromes that were already added
            if rm_zeros:
                save_kmer = kmer if kmer < rev_kmer else rev_kmer
                equalized_kmer_counter[save_kmer] = n_kmer + equalized_kmer_counter.get(rev_kmer, 0)
            else:
                if kmer in equalized_kmer_counter or rev_kmer in equalized_kmer_counter:
                    continue
                equalized_kmer_counter[kmer] = kmer_counter[kmer] + kmer_counter[rev_kmer]
                equalized_kmer_counter[rev_kmer] = kmer_counter[kmer] + kmer_counter[rev_kmer]
            
    else:
        equalized_kmer_counter = kmer_counter

    if len(kmers) > 0:
        kmer_list, n_kmer = zip(*sorted(equalized_kmer_counter.items(), key=lambda _: _[0]))
    else:
        kmer_list, n_kmer = [], []
    kmer_idx_dict = dict()
    # convert present kmers to unique numerical value
    if rm_zeros and equalize_counter and gkmer_mat is None:
        kmer_idx_dict = nozero_kmer_to_idx(alphabet=alphabet_, k=k)
        kmer_idx = [kmer_idx_dict[kmer] for kmer in kmer_list]
    else:
        kmer_idx = [seq_to_int(kmer, alphabet_, ) for kmer in kmer_list]
        
    # set kmer histogram values
    if rm_zeros and equalize_counter:
        n_kmer_cols = max(kmer_idx_dict.values()) + 1
    else:
        n_kmer_cols = len(alphabet_)**k

    if return_dense or dump_to is not None:
        # add one for kmer_idx_dict as it's zero-based
        kmer_hist = np.zeros(n_kmer_cols, dtype="int64")
        kmer_hist[kmer_idx] = n_kmer
        # gapped k-mer calculation if gkmer_mat is passed
        if gkmer_mat is not None:
            kmer_hist = kmer_hist @ gkmer_mat
    else:         
        # add one for kmer_idx_dict as it's zero-based   
        kmer_hist = sp.coo_matrix((n_kmer, ([0] * len(kmer_idx), kmer_idx)), shape=(1, n_kmer_cols), dtype="int64")
    # if provided, dump result into file
    if dump_to is not None:
        with open(dump_to, "a") as file:
            time_access = time.time()
            # as long as there is still time, try to access file
            while time.time() - time_access < max_wait:
                if file.writable():
                    # lock file to manage concurrent file access
                    fcntl.lockf(file, fcntl.LOCK_EX)
                    # write to file
                    file.write(",".join([str(cell_id), *kmer_hist.astype("str").tolist()]))
                    file.flush()
                    # unlock file
                    fcntl.lockf(file, fcntl.LOCK_UN)
                else:
                    # if file was still locked, wait half a second before re-trying
                    time.sleep(.5)
            else:
                # throw warning when exceeded waiting time
                warnings.warn("%s couldn't be written to file.")
        return
    return kmer_hist


def create_total_kmer(
        genome_path: str,
        feature_path: str,
        k: int = 6,
        ell: int | None = None,
        alphabet: List[str] = DNA_ALPHABET,
        mask_rep: bool = False,
        n_policy: str = "remove",
        rm_zeros: bool = True,
        equalize_counter: bool = True,
        verbosity: int = 0,
        verbosity_indent: str = "",
        **kwargs
) -> KMerWrapper:
    """
    Helper function to create a k-mer histogram over an entire annotated genome. It creates a KMer matrix wrapper, which
    you can largely treat like a conventional KMerObject. Note that there are no individual cells, and the KMer wrapper
    is strongly reduced in functionality.

    :param str genome_path: Path to genome fasta file
    :param str feature_path: Path to bed file containing features that are used for k-mer histogram creation
        (normally peaks).
    :param int k: k-mer size.
    :param int | None ell: Ell-mer length when using gapped k-mers. If None, no gapped k-mers are used.
    :param List[str] alphabet: Alphabet to use for KMer creation. 
    :param bool mask_rep: Ignore softmasked stretched in annotated genome.
    :param str n_policy: Defines how to deal with non-deterministic letters. Choose between remove | replace | keep.
        
        - `remove` filters out kmers with N occurrences.
        - `replace` replaces kmers that contain Ns with all possibilities
        - `keep` keeps the Ns untreated

    :param bool return_dense: if set to true and `dump_to` is None, return dense numpy array instead of sparse array.
    :param bool rm_zeros: If `equalize_counter` is set to `True`, the reverse complement kmer counts are added to 
        the forward kmer counts. This makes produces redundant entries, which can be set to zero and removed 
        to save memory (or storage when you save your object). However, some functions won't be available, such
        as performing a kmer transpositon.
    :param bool equalize_counter: If set to `True`, treat forward and reverse complement kmer as the same kmer. That
        means values for `GCGT` are added to the histogram values for `ACGC`. Otherwise, they are treated as independent
        entities.
    :param int verbosity: Verbosity levels.
    :param str verbosity_indent: Prefix before console output.
    :param kwargs: Further keyword arguments passed to the `create_kmer_hist` matrix
    :return KMerWrapper: Wrapper object for treating the k-mer histogram over the entire genome like a KMerObject 
    """
    # Create background kmer
    from pysam import FastaFile
    genome_fa = FastaFile(os.path.abspath(genome_path))
    feature_bed = pl.read_csv(
        feature_path,
        separator="\t",
        has_header=False,
        infer_schema_length=0
    )

    feature_iter = feature_bed.iter_rows(named=False)
    if verbosity > 0:
        feature_iter = tqdm(
            feature_iter,
            total=feature_bed.shape[0],
            desc="%sCreate KMer matrix over all features" % verbosity_indent
        )
    seq_list = [genome_fa.fetch(peak[0], int(peak[1]), int(peak[2]))
                            for peak in feature_iter]
    if ell is None:
        cols, idx_offset = get_kmer_names(k=k, ell=ell, alphabet=alphabet, return_offset=True)
        ell_list = get_kmer_names(k=ell, ell=None, alphabet=alphabet, return_offset=False)
        gkm_mat = get_gkm_mat(ell_names=ell_list, n_gapped_kmer=len(cols), offset_dict=idx_offset, alphabet=alphabet)
    else:
        gkm_mat = None

    bkg_kmer_hist = create_kmer_hist(
        seq_list,
        cell_id="total",
        k=k,
        alphabet=alphabet,
        return_dense=True,
        mask_rep=mask_rep,
        n_policy=n_policy,
        rm_zeros=rm_zeros,
        equalize_counter=equalize_counter,
        gkmer_mat=gkm_mat,
        **kwargs
    )
    total_kmerhist = KMerWrapper(bkg_kmer_hist.reshape(1, -1), k=k, ell=ell, alphabet=alphabet)
    return total_kmerhist


class KMerClass(KMerHistogramObject, ABC):
    """
    Abstract KMer base class to define general attributes, clustering algorithms, umap, saving and loading.
    
    :param int k: defines length of k-mers. For example `k=3` creates 3-mers, i.e. overlapping sequence strings of length
        3.
    :param int | None ell: Ell-mer length when using gapped k-mers. When set to None, no gapped k-mers are used.
    :param List[str] alphabet: The alphabet to be considered. Note that some functions might be compromised when using another
        alphabet than DNA and RNA, such as defining the reverse compleme
    :param int verbosity: verbosity level. The lower, the less output.
    """
    def __init__(self, k: int = 6, ell: int | None = None, alphabet: List[str] = DNA_ALPHABET, verbosity: int = 0):
        self.verbosity = verbosity
        self.k = k
        self.ell = ell
        self.barcodes = None
        self.clustering = None
        self.kmer_hist = None
        self.x_umap = None
        self.dr = None
        self.alphabet = list(sorted(alphabet))
        self.shape = tuple()
        _, self.pattern_offset_dict = get_kmer_names(k=self.k, ell=self.ell, alphabet=self.alphabet, return_offset=True)

    def __len__(self):
        """
        Returns number of cells (i.e. rows) of the Kmer object
        """
        if len(self.shape) > 0:
            return self.kmer_hist.shape[0]
        else:
            return 0

    def __iter__(self):
        """
        Return iterator
        """
        if self.kmer_hist is not None:
            return self.kmer_hist.__iter__()
        else:
            return None  

    def __add__(self, other: KMerClass | np.ndarray | sp.csc_matrix | int | float):
        """
        Add `other` to kmer histogram

        :param KMerClass | np.ndarray | sp.csc_matrix | int | float other: Value added to histogram
        """
        if isinstance(other, KMerClass):
            other = other.kmer_hist
        self.kmer_hist = self.kmer_hist + other

    def __sub__(self, other: KMerClass | np.ndarray | sp.csc_matrix | int | float):
        """
        Subtract `other` from kmer histogram

        :param KMerClass | np.ndarray | sp.csc_matrix | int | float other: Value subtracted from histogram
        """
        if isinstance(other, KMerClass):
            other = other.kmer_hist
        self.kmer_hist = self.kmer_hist - other  

    def __mul__(self, other: KMerClass | np.ndarray | sp.csc_matrix | int | float):
        """
        Multiply `other` to kmer histogram. If passed as array or matrix, perform element-wise multiplication

        :param KMerClass | np.ndarray | sp.csc_matrix | int | float other: Value multiplied to histogram
        """
        if isinstance(other, KMerClass):
            other = other.kmer_hist
        self.kmer_hist = self.kmer_hist * other

    def _convert_item(
            self, 
            item: pd.Series | pl.Series | slice | int | np.ndarray | None, 
            is_kmer_item: bool = False
        ) -> np.ndarray:
        """
        Private function that converts indices representing a cell item to an integer numpy array

        :param pd.Series | pl.Series | slice | int | np.ndarray | None item: Indices representing cell item or kmer item. They can 
            either be a single integer value, a slice, a numpy array (boolean or integer), or a pandas or polars Series,
            representing a mask, integer indices, or cell-identifying barcodes. Note that they can only be barcodes if `is_kmer_item`
            is set to False
        :param bool is_kmer_item: If set, item is treated as kmer index instead of cell index
        :return np.ndarray: Numpy integer array representing cell positions in matrix.
        """
        max_val = len(self) if not is_kmer_item else self.shape[1]
        if item is None:
            return np.arange(max_val)
        if isinstance(item, pd.Series) or isinstance(item, pl.Series) or (isinstance(item, pd.Index) and is_kmer_item):
            item = item.to_numpy()   
        elif isinstance(item, pd.Index) and not is_kmer_item:
            item = pd.Series(np.arange(self.shape[0]), index=self.barcodes)[item].to_numpy()
        elif isinstance(item, slice):
            start_idx = item.start if item.start is not None else 0
            stop_idx = item.stop if item.stop is not None else max_val
            if start_idx < 0:
                start_idx = max_val + start_idx  # note that start idx is negative
            if stop_idx < 0:
                stop_idx = max_val + stop_idx  # note that stop idx is negative
            step = item.step if item.step is not None else 1
            item = np.arange(start_idx, stop_idx, step)
        elif isinstance(item, int):
            item = np.array([item])
        if isinstance(item, np.ndarray):
            if item.dtype == "bool":
                item, = np.where(item)
        return item.flatten()

    def _check_clustering(self):
        """
        Check whether clustering dictionary has been already set.
        """
        if self.clustering is None:
            self.clustering = dict()

    def _check_dr(self):
        """
        Check whether dimensionality reduction dictionary has been already set
        """
        if self.dr is None:
            self.dr = dict()

    def _check_umap(self):
        """
        Check whether dimensionality reduction dictionary has been already set
        """
        if self.x_umap is None:
            self.x_umap = dict()

    def _subset_dicts(
            self,
            items: int | np.ndarray | slice
        ) -> Tuple[
            Dict[str, np.ndarray] | None, 
            Dict[str, np.ndarray] | None, 
            Dict[str, np.ndarray] | None
        ]:
        """
        Return subset python dictionaries for cluster, dimensionality reduction, and UMAP embedding

        :param int | np.ndarray | slice items: Index or indices for the required items.
        :return Tuple[Dict[str, np.ndarray] | None, Dict[str, np.ndarray] | None, Dict[str, np.ndarray] | None]:
            Subset clustering, dimensionality reduction, UMAP embedding dictionaries.
        """
        subset_clustering = None
        if self.clustering is not None:
            subset_clustering = {key: array[items].copy() for key, array in self.clustering.items()}

        subset_dr = None
        if self.dr is not None:
            subset_dr = {key: array[items].copy() for key, array in self.dr.items()}

        subset_xumap = None
        if self.x_umap is not None:
            subset_xumap = {key: array[items].copy() for key, array in self.x_umap.items()}

        return subset_clustering, subset_dr, subset_xumap
    
    def mean(self, axis: int | None = 0) -> np.ndarray | sp.csc_matrix | float:
        """
        Calculate the mean over the kmer histogram

        :param int | None axis: Axis over which the mean is computed. If `None`, caclulate over entire kmer histogram.
        :return np.ndarray | sp.csc_matrix | float: Mean kmer value
        """
        return self.kmer_hist.mean(axis=axis)
    
    def sum(self, axis: int | None = 0) -> np.ndarray | sp.csc_matrix | float:
        """
        Calculate the sum over the kmer histogram

        :param int | None axis: Axis over which the sum is computed. If `None`, caclulate over entire kmer histogram.
        :return np.ndarray | sp.csc_matrix | float: Summed kmer value
        """
        return self.kmer_hist.sum(axis=axis)
    
    def std(self, axis: int | None = 0) -> np.ndarray | sp.csc_matrix | float:
        """
        Calculate the standard deviation over the kmer histogram

        :param int | None axis: Axis over which the standard deviation is computed. 
            If `None`, caclulate over entire kmer histogram.
        :return np.ndarray | sp.csc_matrix | float: Standard deviation in kmer histogram
        """
        return self.kmer_hist.std(axis=axis)

    def var(self, axis: int | None = 0) -> np.ndarray | sp.csc_matrix | float:
        """
        Calculate the variance over the kmer histogram

        :param int | None axis: Axis over which the variance is computed. 
            If `None`, caclulate over entire kmer histogram.
        :return np.ndarray | sp.csc_matrix | float: Variance ißn kmer histogram
        """
        return self.kmer_hist.var(axis=axis)
    
    def get_kmer_column_names(self) -> pd.Series:
        """
        Get kmer names ordered by column in the kmer histogram

        :return pd.Series: Kmer names.
        """
        if self.ell is not None or len(self.alphabet)**self.k == self.kmer_hist.shape[1]:
            cols = get_kmer_names(k=self.k, ell=self.ell, alphabet=self.alphabet, return_offset=False)
        else:
            cols = list(sorted(nozero_kmer_to_idx(alphabet=self.alphabet, k=self.k).keys()))
        return pd.Series(cols)
     
    def kmer_transpose(self):
        """
        Transpose Kmer histogram according to its reverse complement. The means that values that were
        before at `AGCG` are now at `CGCT`
        """
        if len(self.alphabet)**self.k > self.kmer_hist.shape[1]:
            raise ValueError("Equalized and reduced matrix during creation. "
                             "Cannot safely perform a KMer transposition. Please create a new KMerMatrix and set "
                             "`equalize_counter=False`.")
        if len(self.alphabet)**self.k < self.kmer_hist.shape[1] and self.ell is None:
            raise ValueError("Alphabet included Ns. Cannot safely perform a KMer transposition. Please create a new "
                             "KMerMatrix and set `n_policy='remove'`")
        transposed_kmer = np.zeros_like(self.kmer_hist)
        for kmer in product(self.alphabet, repeat=self.k):
            kmer = "".join(kmer)
            kmer_idc = seq_to_int(seq=kmer, alphabet=self.alphabet, pattern_offsets=self.pattern_offset_dict)
            rev_kmer = str(Seq(kmer).reverse_complement())
            rev_kmer_idc = seq_to_int(seq=rev_kmer, alphabet=self.alphabet, pattern_offsets=self.pattern_offset_dict)
            transposed_kmer[:, rev_kmer_idc] += self.kmer_hist[:, kmer_idc]
        self.kmer_hist = transposed_kmer

    def equalize_kmers(self):
        """
        Make add reverse complement to forward and vice versa.
        """
        kmer_l = self.get_kmer_column_names()
        equalized_kmer_l = []
        for kmer in kmer_l:
            rev_kmer = Seq(kmer).reverse_complement()  # can deal with gaps
            if rev_kmer in equalized_kmer_l or kmer in equalized_kmer_l:
                continue
            equalized_kmer_l.append(kmer)
            equalized_kmer_l.append(rev_kmer)
            kmer_idx = seq_to_int(seq=kmer, alphabet=self.alphabet, pattern_offsets=self.pattern_offset_dict)
            rev_kmer_idx = seq_to_int(seq=rev_kmer, alphabet=self.alphabet, pattern_offsets=self.pattern_offset_dict)
            kmer_count = self.kmer_hist[:, kmer_idx] + self.kmer_hist[:, rev_kmer_idx]
            self.kmer_hist[:, kmer_idx] = kmer_count
            self.kmer_hist[:, rev_kmer_idx] = kmer_count

    def pca(
            self,
            save_name: str = "dr",
            dr_name: str | None = None,
            seed: int | None = None,
            verbosity_indent: str = "",
            n_pca_components: int | str = 25,
            add_reduced_pca: bool = False,
            return_model: bool = False,
            **kwargs
    ):
        """
        Perform conventional PCA using sklearn. PCA results will be saved under `self.dr[save_name]`.

        :param str save_name: key for dimensionality reduction dictionary under which result will be saved
        :param str dr_name: Key for a dimensionality reduction that is used as input. This parameter is only useful
            if you you are working with large matrices for which you only want to use the most variable features.
        :param int | None seed: Seed for random number generator
        :param str verbosity_indent: Indentation symbold that can be used to see whether the function was called
            within a sub-routine
        :param int | str n_pca_components: Number of PCs
        :param bool add_reduced_pca: If set, automatically set a second entry in the dictionary with the first PC
            removed. The first PC contains GC content over the KMer histograms, which can make different clusters
            less distinct. The reduced PCs are saved under `self.dr[save_name + "_reduced"]`
        :param bool return_model: If set to `True`, return trained PCA model. This can be useful of you want to apply the
            same transformation to other data as well.
        :param kwargs: unused parameters
        :return: If `return_model=True`, return ratio of explained variance per principal component and PCA model. 
            Otherwise, return only ratio of explained variance.
        """
        from sklearn.decomposition import PCA
        self._check_dr()

        n_pca_components = int(n_pca_components)
        if self.verbosity > 0:
            print("%sStart PCA" % verbosity_indent,)
        pca = PCA(n_components=n_pca_components, random_state=seed)
        if dr_name is None:
            kmer_data = self.kmer_hist if self.k <= MAX_K_DENSE else self.kmer_hist.A
        else:
            if dr_name not in self.dr:
                raise ValueError("Data for dimensionality reduction %s not found. "
                                 "Please perform the dimensionality reduction before." % dr_name)
            kmer_data = self.dr[dr_name]
        self.dr[save_name] = pca.fit_transform(kmer_data)
        if add_reduced_pca:
            self.dr[save_name + "_reduced"] = self.dr[save_name][:, 1:]
        if return_model:
            return pca.explained_variance_ratio_, pca
        else:
            return pca.explained_variance_ratio_

    def sparse_pca(
            self,
            save_name: str = "dr",
            dr_name: str | None = None,
            seed: int | None = None,
            verbosity_indent: str = "",
            n_pca_components: int | str = 25,
            n_jobs: int | None = -1,
            max_no_improvement: int | str = 10,
            pca_batch_size: int | str = 5,
            pca_sparsity_alpha: int | str = 1,
            pca_ridge_alpha: float | str = .01,
            **kwargs
    ):
        """
        Perform conventional sparse PCA using sklearn. Sparse PCA results will be saved under `self.dr[save_name]`

        :param str save_name: key for dimensionality reduction dictionary under which result will be saved
        :param str dr_name: Key for a dimensionality reduction that is used as input. This parameter is only useful
            if you you are working with large matrices for which you only want to use the most variable features.
        :param int | None seed: Seed for random number generator
        :param str verbosity_indent: Indentation symbold that can be used to see whether the function was called
            within a sub-routine
        :param int | str n_pca_components: Number of PCs
        :param int | None n_jobs: Number of processes used
        :param int | str max_no_improvement: Maximum number of iterations without improvement before stopping
        :param int | str pca_batch_size: Number of PCs in batch
        :param int | str pca_sparsity_alpha: Sparsity controlling parameter. Higher values lead to sparser components.
        :param float | str pca_ridge_alpha: Amount of ridge shrinkage to apply in order to improve conditioning when 
            calling the transform method.
        :param kwargs: Unsused parameters
        :return: None
        """
        from sklearn.decomposition import MiniBatchSparsePCA
        self._check_dr()

        n_pca_components = int(n_pca_components)
        max_no_improvement = int(max_no_improvement)
        pca_batch_size = int(pca_batch_size)
        pca_sparsity_alpha = int(pca_sparsity_alpha)
        pca_ridge_alpha = float(pca_ridge_alpha)

        if self.verbosity > 0:
            print("%sStart Sparse PCA" % verbosity_indent)
        sparse_pca = MiniBatchSparsePCA(
            n_components=n_pca_components,
            random_state=seed,
            batch_size=pca_batch_size,
            alpha=pca_sparsity_alpha,
            ridge_alpha=pca_ridge_alpha,
            n_jobs=n_jobs,
            max_no_improvement=max_no_improvement,
        )
        if dr_name is None:
            kmer_data = self.kmer_hist if self.k <= MAX_K_DENSE else self.kmer_hist.A
        else:
            if dr_name not in self.dr:
                raise ValueError("Data for dimensionality reduction %s not found. "
                                 "Please perform the dimensionality reduction before." % dr_name)
        self.dr[save_name] = sparse_pca.fit_transform(kmer_data)

    def reduce_dimensionality(
            self,
            algorithm: str = "pca",
            save_name: str = "dr",
            dr_name: str | None = None,
            seed: int | None = None,
            n_jobs: int | None = -1,
            verbosity_indent: str = "\t",
            **kwargs

    ):
        """
        Wrapper for dimensionality reduction. Results are saved under `self.dr[save_name]`

        :param str algorithm: Type of dimensionality reduction performed. Choose between `pca` | `sparse_pca`.
        :param str save_name: key for dimensionality reduction dictionary under which result will be saved
        :param str dr_name: Key for a dimensionality reduction that is used as input. This parameter is only useful
            if you you are working with large matrices for which you only want to use the most variable features.
        :param int | None seed: Seed for random number generator
        :param int | None n_jobs: Number of processes used
        :param str verbosity_indent: Indentation symbold that can be used to see whether the function was called
            within a sub-routine
        :param kwargs: parameters that are passed to dimensionality reduction algorithm
        :return: If `algorithm="pca"`, then return explained variance ratio per PC. Otherwise, return `None`.
        """
        self._check_dr()
        algorithm = algorithm.lower()
        if algorithm == "pca":
            dr_fun = self.pca
        elif algorithm == "sparse_pca":
            dr_fun = self.sparse_pca
        else:
            raise ValueError("Dimensionality reduction %s not supported. "
                             "Please select between PCA | sparse_PCA" % algorithm)
        return dr_fun(
            save_name=save_name,
            dr_name=dr_name,
            seed=seed,
            verbosity_indent=verbosity_indent,
            n_jobs=n_jobs,
            **kwargs
        )
    
    def select_features(
            self,
            n_features: int = 15000,
            save_name: str = "selected_features"
    ):
        """
        Select most variable features in the KMer matrix by calculating the variance. 
        The result is saved in `self.dr[save_name]`.

        :param int n_features: Number of most variable k-mers selected.
        :param str save_name: Name used for saving the result in the object's `dr` dictionary.
        """
        self._check_dr()
        mat = self.kmer_hist
        dim_var = mat.var(axis=0)
        sort_idc = np.argsort(dim_var)
        self.dr[save_name] = mat[:, sort_idc[::-1][:n_features]]

    def cluster_leiden(
            self,
            save_name: str = "clustering",
            dr_name: str | None = None,
            seed: int | None = None,
            verbosity_indent: str = "",
            resolution: float | str = 1.,
            leiden_obj_fun: str | None = "modularity",
            min_cluster_size: int | str = 5,
            n_neighbors: int | str = 10,
            neighbor_batch: int | str = 128,
            n_iteration: int | str = -1,
            leiden_beta: float | str = .0,
            use_weights: bool | str = False,
            adj_mat: sp.csc_matrix | None = None,
            **kwargs
    ):
        r"""
        Perform leiden clustering based on adjacency graph. See https://leidenalg.readthedocs.io/en/stable/intro.html
        for more information. Publication can be found https://www.nature.com/articles/s41598-019-41695-z.
        Results will be saved under `self.clustering[save_name]`

        :param str save_name: Name under which clustering result is saved in object. Result will be accessible under
            `your_kmer_obj.clustering[save_name]`
        :param str | None dr_name:  Name of dimensionality reduction that should be used, which is saved under
            `your_kmer_obj.dr[dr_name]`. Please run the dimensionality reduction before. If none passed, use the full
            k-mer histogram.
        :param int | None seed: Seed for random number generator for reproducibility. Set to None for not using a seed.
        :param str verbosity_indent: Prefix for verbosity output to indicate that this routine was called within
            another function
        :param float | str resolution: Cluster resolution. A community (cluster in a graph) should have a density of at
            least the resolution parameter whereas the density between communities should be lower than the
            resolution parameter. Lower values lead to fewer communities.
        :param str | None leiden_obj_fun: Defines how communities are found.
            Select between `modularity` | `cpm`.
        :param int | str min_cluster_size: minimum size of clusters, otherwise associated to unknown.
        :param int | str n_neighbors: Number of nearest neighbors used for adjacency matrix.
            Only used when `adj_mat` not passed.
        :param int | str neighbor_batch: Number of samples for which neighbors are retrieved simultaneously.
            Only used when `adj_mat` not passed.
        :param int | str n_iteration: Maximum number of iterations. If negative continue until convergence.        :param float | str leiden_beta: Randomness in leiden algorithm. This affects only the refinement step
        :param bool | str use_weights: If set to true, create weight matrix based on similarity instead of 
            k-neighbor adjacency. Similarity is computed as :math:`\exp{ \left( -d(i, j) \right) }`, where
            :math:`d` is the Euclidean distance and :math:`i, j` are cells :math:`i` and :math:`j`, respectively. 
            If used and you have passed `adj_mat`, make sure that it includes distances.
        :param sp.csc_matrix | None adj_mat: Cell k-nearest neighbor adjacency or distance matrix.
        :param kwargs: arguments not used for leiden
        """
        import igraph as ig
        import random

        self._check_clustering()
        leiden_obj_fun = leiden_obj_fun.lower()

        # convert parameters from string to expected data type
        resolution = float(resolution)
        n_neighbors = int(n_neighbors)
        n_iteration = int(n_iteration)
        min_cluster_size = int(min_cluster_size)
        neighbor_batch = int(neighbor_batch)
        if  isinstance(use_weights, str):
            use_weights = use_weights == "True"
        if self.verbosity > 0:
            print("%sStart Leiden clustering" % verbosity_indent)
            
        if adj_mat is None:
            if self.verbosity > 0:
                print("%s\tCreate nearest neighbor ball" % verbosity_indent)
            if dr_name is None:
                kmer_data = self.kmer_hist if self.k <= MAX_K_DENSE else self.kmer_hist.A
            else:
                try:
                    kmer_data = self.dr[dr_name]
                except KeyError:
                    raise KeyError("Dimensionality reduction %s not found. Please run a dimensionality reduction "
                                "which is saved under this name." % dr_name)
            adj_mat = get_nn_mat(
                data=kmer_data,
                n_neighbors=n_neighbors,
                neighbor_batch=neighbor_batch,
                return_distance=True,
                verbosity=self.verbosity,
                verbosity_indent=verbosity_indent,
            )
            
        if self.verbosity > 0:
            print("%s\tCreate graph" % verbosity_indent)

        # create neighbor graph with undirected edges using the adjacency matrix
        n_vertex = self.shape[0]
        s_vertex, t_vertex = adj_mat.nonzero()
        edges = list(zip(list(s_vertex), list(t_vertex)))
        weights = np.exp(-np.ravel(adj_mat[(s_vertex, t_vertex)]))
        neighbor_graph = ig.Graph(n=n_vertex, edges=edges, directed=False, edge_attrs={"weight": weights})
        # run leiden clustering to find communities in graph
        ig.set_random_number_generator(seed)
        random.seed(seed)
        leiden_cluster = np.array(neighbor_graph.community_leiden(
            objective_function=leiden_obj_fun,
            n_iterations=n_iteration,
            weights=weights if use_weights else None,
            resolution_parameter=resolution,
            beta=leiden_beta
        ).membership)
        # set all clusters with size below a value to unknown cluster
        unknown_cluster = np.array([cl for cl, count in Counter(leiden_cluster).items()
                                    if int(count) < min_cluster_size])
        leiden_cluster[np.isin(leiden_cluster, unknown_cluster)] = -1
        self.clustering[save_name] = leiden_cluster

    def cluster_snn(
            self,
            save_name: str = "clustering",
            dr_name: str | None = None,
            verbosity_indent: str = "",
            min_cluster_size: int | str = 5,
            n_neighbors: int | str = 5,
            neighbor_batch: int | str = 128,
            adj_mat: sp.csc_matrix | None = None,
            **kwargs
    ):
        r"""
        Perform shared nearest neighbor clustering based on the following publication
        
            Ertöz, Levent, Michael Steinbach, and Vipin Kumar. 
            Finding clusters of different sizes, shapes, and densities in noisy, high dimensional data.
            Proceedings of the 2003 SIAM international conference on data mining.
            Society for Industrial and Applied Mathematics, 2003.

        It is only based on connected components that remain from the nearest neighbor graph after keeping
        exclusively the edges that are shared between any to neighbors. To be precise, for verices 
        :math:`u` and :math:`v`, only edges are kept when in the nearest neighbor graph when :math:`(u, v) \in E`
        and :math:`(v, u) \in E`, where :math:`E` is the edge list.)

        :param str save_name: Name under which clustering result is saved in object. Result will be accessible under
            `your_kmer_obj.clustering[save_name]`
        :param str | None dr_name:  Name of dimensionality reduction that should be used, which is saved under
            `your_kmer_obj.dr[dr_name]`. Please run the dimensionality reduction before. If none passed, use the full
            k-mer histogram.
        :param str verbosity_indent: Prefix for verbosity output to indicate that this routine was called within
            another function.
        :param int | str min_cluster_size: Minimum number of data points in cluster.
        :param int | str n_neighbors: Number of neighbors determined per data point in neighbor graph
        :param int | str neighbor_batch: Number of data points processed at the same time for determining
            nearest neighbors
        :param sp.csc_matrix | None adj_mat: Precomputed adjacency matrix. If not passed, the function computes the
            adjacency matrix with the parameters set above.
        :param kwargs: unused parameters
        """
        import networkx as nx

        self._check_clustering()
        # convert parameters from string to expected data type
        n_neighbors = int(n_neighbors)
        min_cluster_size = int(min_cluster_size)
        neighbor_batch = int(neighbor_batch)
        if self.verbosity > 0:
            print("%sStart SNN clustering" % verbosity_indent)
            
        if adj_mat is None:
            if self.verbosity > 0:
                print("%s\tCreate nearest neighbor ball" % verbosity_indent)
            if dr_name is None:
                kmer_data = self.kmer_hist if self.k <= MAX_K_DENSE else self.kmer_hist.A
            else:
                try:
                    kmer_data = self.dr[dr_name]
                except KeyError:
                    raise KeyError("Dimensionality reduction %s not found. Please run a dimensionality reduction "
                                "which is saved under this name." % dr_name)
            adj_mat = get_nn_mat(
                data=kmer_data,
                n_neighbors=n_neighbors,
                neighbor_batch=neighbor_batch,
                verbosity=self.verbosity,
                return_distance=False,
                verbosity_indent=verbosity_indent
            )
            
        if self.verbosity > 0:
            print("%s\tCreate graph" % verbosity_indent)

        adj_mat = adj_mat > 0  # make sure it's an adjacency matrix and no distance matrix
        adj_mat = adj_mat.multiply(adj_mat.T)
        # create neighbor graph with undirected edges using the adjacency matrix
        n_vertex = self.shape[0]
        s_vertex, t_vertex = adj_mat.nonzero()
        edges = list(zip(list(s_vertex), list(t_vertex)))
        snn_graph = nx.Graph()
        snn_graph.add_nodes_from(np.arange(n_vertex))
        snn_graph.add_edges_from(edges)

        leiden_cluster = -np.ones(n_vertex)  
        for i_cc, cc in enumerate(nx.connected_components(snn_graph)):
            leiden_cluster[np.array(list(cc))] = i_cc

        unknown_cluster = np.array([cl for cl, count in Counter(leiden_cluster).items()
                                    if int(count) < min_cluster_size])
        
        leiden_cluster[np.isin(leiden_cluster, unknown_cluster)] = -1
        # create correct order
        i_cc = 0
        for cc in np.unique(leiden_cluster):
            if cc == -1: continue
            leiden_cluster[leiden_cluster == cc] = i_cc
            i_cc += 1

        self.clustering[save_name] = leiden_cluster

    def cluster_minibatch_kmeans(
            self,
            save_name: str = "clustering",
            dr_name: str | None = None,
            seed: int | None = None,
            verbosity_indent: str = "",
            n_clusters: int | str = 10,
            cluster_init: str = "k-means++",
            batch_size: int | str = 4096,
            n_init: str | int = "auto",
            max_no_improvement: int | str | None = 10,
            **kwargs
    ):
        """
        Perform K-mean minibatch clustering. See
        https://scikit-learn.org/stable/modules/generated/sklearn.cluster.MiniBatchKMeans.html for more information.
        Results will be saved under `self.clustering[save_name]`

        :param str save_name: Name under which clustering result is saved in object. Result will be accessible under
            `your_kmer_obj.clustering[save_name]`
        :param str | None dr_name:  Name of dimensionality reduction that should be used, which is saved under
            `your_kmer_obj.dr[dr_name]`. Please run the dimensionality reduction before. If none passed, use the full
            k-mer histogram.
        :param int | None seed: Seed for random number generator for reproducibility. Set to None for not using a seed.
        :param str verbosity_indent: Prefix for verbosity output to indicate that this routine was called within
            another function
        :param int | str n_clusters: Number of clusters to be found
        :param str cluster_init: Defines how clustering centroids are established.
            Choose between `k-means++` | `random`.
        :param int | str batch_size: Batch size
        :param int | str n_init: Number of initialization iterations
        :param int | str | None max_no_improvement: Maximum number of iterations without improvement before early stopping
        :param kwargs: unused parameters
        """
        from sklearn.cluster import MiniBatchKMeans
        self._check_clustering()

        # convert parameters to expected data type
        n_clusters = int(n_clusters)
        batch_size = int(batch_size)
        try:
            n_init = int(n_init)
        except ValueError:
            pass
        max_no_improvement = int(max_no_improvement) if max_no_improvement is not None else None
        kmeans = MiniBatchKMeans(
            n_clusters=n_clusters,
            init=cluster_init,
            n_init=n_init,
            batch_size=batch_size,
            max_no_improvement=max_no_improvement,
            random_state=seed
        )
        if self.verbosity > 0:
            print("%sStart Mini-Batch K-Means." % verbosity_indent)
        if dr_name is None:
            kmer_data = self.kmer_hist if self.k <= MAX_K_DENSE else self.kmer_hist.A
        else:
            try:
                kmer_data = self.dr[dr_name]
            except KeyError:
                raise KeyError("Dimensionality reduction %s not found. Please run a dimensionality reduction "
                               "which is saved under this name." % dr_name)
        self.clustering[save_name] = kmeans.fit_predict(kmer_data)

    def cluster_dbscan(
            self,
            save_name: str = "clustering",
            dr_name: str | None = None,
            verbosity_indent: str = "",
            eps: float | str = 1e-3,
            min_samples: int | str = 10,
            metric: str = "euclidean",
            metric_params: dict | None = None,
            dbscan_algorithm: str = "auto",
            p: int | str = 2,
            n_jobs: int | None = -1,
            **kwargs
    ):
        """
        Perform DBSCAN clustering using densities. Points are classified as either core points, border points
        (which have a lower density but are within the neighborhood of a core point) and noise. See
        https://scikit-learn.org/stable/modules/generated/sklearn.cluster.DBSCAN.html#sklearn.cluster.DBSCAN for more
        information.
        Results will be saved under `self.clustering[save_name]`

        :param str save_name: Name under which clustering result is saved in object. Result will be accessible under
            `your_kmer_obj.clustering[save_name]`
        :param str | None dr_name:  Name of dimensionality reduction that should be used, which is saved under
            `your_kmer_obj.dr[dr_name]`. Please run the dimensionality reduction before. If none passed, use the full
            k-mer histogram.
        :param str verbosity_indent: Prefix for verbosity output to indicate that this routine was called within
            another function
        :param float | str eps: maximum distance between samples for one to be considered in the same neighborhood. The
            larger the value the lower the number of clusters.
        :param int | str min_samples: Minimum number of samples within `eps` neighborhood to be considered as a core point.
        :param str metric: Used distance metric. See https://scikit-learn.org/stable/modules/generated/sklearn.metrics.pairwise_distances.html#sklearn.metrics.pairwise_distances
        :param dict metric_params: Additional parameters that are used for the distance metric passed as a dict
        :param str dbscan_algorithm: algorithm that is used to determine the nearest neighbor graph.
            Choose between `auto` | `ball_tree` | `kd_tree` | `brute`
        :param int | str p: power of the Minkowski metric to calculate point distances
        :param int | None n_jobs: Number of jobs. -1 means use all available processors.
        :param kwargs: unused parameters
        """
        from sklearn.cluster import DBSCAN
        self._check_clustering()

        # convert parameters to expected data type
        eps = float(eps)
        min_samples = int(min_samples)
        p = int(p)
        dbscan = DBSCAN(
            eps=eps,
            min_samples=min_samples,
            metric=metric,
            metric_params=metric_params,
            algorithm=dbscan_algorithm,
            p=p,
            n_jobs=n_jobs
        )
        if self.verbosity > 0:
            print("%sStart DBSCAN." % verbosity_indent)
        if dr_name is None:
            kmer_data = self.kmer_hist if self.k <= MAX_K_DENSE else self.kmer_hist.A
        else:
            try:
                kmer_data = self.dr[dr_name]
            except KeyError:
                raise KeyError("Dimensionality reduction %s not found. Please run a dimensionality reduction "
                               "which is saved under this name." % dr_name)
        self.clustering[save_name] = dbscan.fit_predict(kmer_data)

    def cluster_optics(
            self,
            save_name: str = "clustering",
            dr_name: str | None = None,
            verbosity_indent: str = "",
            min_samples: int | float | str = 5,
            max_eps: float | np.ndarray | str = np.inf,
            metric: str = "minkowski",
            p: int | str = 2,
            metric_params: dict | None = None,
            cluster_method: str = "xi",
            eps: float | str | None = None,
            xi: float | str = 0.05,
            predecessor_correction: bool | str = True,
            min_cluster_size: int | float | str | None = None,
            optics_algorithm: str = "auto",
            n_jobs: int | None = -1,
            **kwargs
    ):
        """
        Perform OPTICS clustering on densities similar to DBSCAN, but it also detects meaningful clusters in data
        with varying densities. See
        https://scikit-learn.org/stable/modules/generated/sklearn.cluster.OPTICS.html for more information
        Results will be saved under `self.clustering[save_name]`

        :param str save_name: Name under which clustering result is saved in object. Result will be accessible under
            `your_kmer_obj.clustering[save_name]`
        :param str | None dr_name:  Name of dimensionality reduction that should be used, which is saved under
            `your_kmer_obj.dr[dr_name]`. Please run the dimensionality reduction before. If none passed, use the full
            k-mer histogram.
        :param str verbosity_indent: Prefix for verbosity output to indicate that this routine was called within
            another function
        :param int | str min_samples: Minimum number of samples within eps neighborhood to be considered as a core point.
        :param float | str max_eps: maximum distance between any two points to be considered in the neighborhood of each other
        :param str metric: Used distance metric. See https://scikit-learn.org/stable/modules/generated/sklearn.metrics.pairwise_distances.html#sklearn.metrics.pairwise_distances
        :param int | str p: power of the Minkowski metric to calculate point distances
        :param dict metric_params: Additional parameters that are used for the distance metric passed as a dict
        :param str cluster_method: Method used to extract clusters using the calculated reachability and ordering.
            Choose between `xi` | `dbscan`
        :param float | str eps: Neighborhood size used for extracting clusters when `cluster_method=dbscan`. If none, this
            value is set equal to `max_eps`
        :param float | str xi: Minimum steepness on reachability that defines a cluster boundary.
        :param bool | str predecessor_correction: Correct clusters according to the predecessors in OPTICS sorting.
        :param int | str min_cluster_size: Minimum number of samples per cluster. This can be an absolute value or a fraction
        :param str optics_algorithm: algorithm that is used to determine the nearest neighbor graph.
            Choose between `auto` | `ball_tree` | `kd_tree` | `brute`
        :param int n_jobs: Number of jobs
        :param kwargs: Unused parameters.
        """
        from sklearn.cluster import OPTICS
        self._check_clustering()

        # convert parameters to expected data type
        max_eps = float(max_eps)

        min_samples = float(min_samples)
        if not 0. <= min_samples <= 1.:
            min_samples = int(min_samples)

        p = int(p)
        if eps is not None:
            eps = float(eps)

        xi = float(xi)
        if isinstance(predecessor_correction, str):
            predecessor_correction = predecessor_correction == "True"
        
        if min_cluster_size is not None:
            min_cluster_size = float(min_cluster_size)
            if not 0. <= min_cluster_size <= 1.:
                min_cluster_size = int(min_cluster_size)
   
        optics = OPTICS(
            min_samples=min_samples,
            max_eps=max_eps,
            metric=metric,
            p=p,
            metric_params=metric_params,
            cluster_method=cluster_method,
            eps=eps,
            xi=xi,
            predecessor_correction=predecessor_correction,
            min_cluster_size=min_cluster_size,
            algorithm=optics_algorithm,
            n_jobs=n_jobs
        )

        if self.verbosity > 0:
            print("%sStart OPTICS." % verbosity_indent)

        if dr_name is None:
            kmer_data = self.kmer_hist if self.k <= MAX_K_DENSE else self.kmer_hist.A
        else:
            try:
                kmer_data = self.dr[dr_name]
            except KeyError:
                raise KeyError("Dimensionality reduction %s not found. Please run a dimensionality reduction "
                               "which is saved under this name." % dr_name)
        self.clustering[save_name] = optics.fit_predict(kmer_data)

    def cluster_hierarchical_kmeans(
            self,
            save_name: str = "clustering",
            dr_name: str | None = None,
            seed: int | None = None,
            verbosity_indent: str = "",
            n_clusters: int | str = 10,
            cluster_init: str = "k-means++",
            n_init: int | str = 1,
            max_iter: int | str = 300,
            hierarchical_kmeans_algorithm: str = "lloyd",
            bisecting_strategy: str = "biggest_inertia"
    ):
        """
        Perform hierarchical K-Means clustering. See
        https://scikit-learn.org/stable/modules/generated/sklearn.cluster.BisectingKMeans.html for more information
        Results will be saved under `self.clustering[save_name]`

        :param str save_name: Name under which clustering result is saved in object. Result will be accessible under
           ` your_kmer_obj.clustering[save_name]`
        :param str | None dr_name:  Name of dimensionality reduction that should be used, which is saved under
            `your_kmer_obj.dr[dr_name]`. Please run the dimensionality reduction before. If none passed, use the full
            k-mer histogram.
        :param int | None seed: Seed for random number generator for reproducibility. Set to None for not using a seed.
        :param str verbosity_indent: Prefix for verbosity output to indicate that this routine was called within another
            function
        :param int | str n_clusters: Number of clusters
        :param str cluster_init: Algorithm for initializing cluster centroids. Choose between `k-means++` | `random`.
        :param int | str n_init: Number of initializations
        :param int | str max_iter: Maximum number of iterations
        :param str hierarchical_kmeans_algorithm: K-means algorithm used in bisection. Choose between `lloyd` | `elkan`
        :param str bisecting_strategy: Defines which cluster is divided.
            Choose between `biggest_inertia` | `largest_cluster`
        :return: None
        """
        from sklearn.cluster import BisectingKMeans
        self._check_clustering()

        # convert parameters to expected data type
        n_clusters = int(n_clusters)
        n_init = int(n_init)
        max_iter = int(max_iter)
        h_kmean = BisectingKMeans(
            n_clusters=n_clusters,
            init=cluster_init,
            n_init=n_init,
            max_iter=max_iter,
            algorithm=hierarchical_kmeans_algorithm,
            bisecting_strategy=bisecting_strategy,
            random_state=seed
        )
        if self.verbosity > 0:
            print("%sStart hierarchical K-Means." % verbosity_indent)

        if dr_name is None:
            kmer_data = self.kmer_hist if self.k <= MAX_K_DENSE else self.kmer_hist.A
        else:
            try:
                kmer_data = self.dr[dr_name]
            except KeyError:
                raise KeyError("Dimensionality reduction %s not found. Please run a dimensionality reduction "
                               "which is saved under this name." % dr_name)
        self.clustering[save_name] = h_kmean.fit_predict(kmer_data)

    def run_clustering(
            self,
            algorithm: str = "leiden",
            dr_name: str | None = None,
            save_name: str = "clustering",
            seed: int | None = None,
            verbosity_indent: str = "",
            **kwargs
    ):
        """
        Cluster KMer histogram values. Result will be saved in `your_kmer_obj.clustering[save_name]`.
        Results will be saved under `self.clustering[save_name]`

        :param str algorithm: Clustering algorithm.
            Choose between leiden | snn | kmeans | DBSCAN | OPTICS | hierarchical_kmeans. All algorithms are scalable to
            large data sets
        :param str | None dr_name:  Name of dimensionality reduction that should be used, which is saved under
            `your_kmer_obj.dr[dr_name]`. Please run the dimensionality reduction before. If none passed, use the full
            k-mer histogram.
        :param str save_name: Name under which clustering result is saved in object. Result will be accessible under
            `your_kmer_obj.clustering[save_name]`
        :param int | None seed: Seed for random number generator for reproducibility. Set to None for not using a seed.
        :param str verbosity_indent: Prefix for verbosity output to indicate that this routine was called within
            another function
        :param kwargs: Additional clustering parameters that are passed to the respective algorithm defined with
            the algorithm parameter above. For more information, see clustering functions specified above.
        """
        if self.kmer_hist is None:
            raise ValueError("Kmer object has not been properly initialized. "
                             "No Kmer histogram could be found. Can't run clustering.")
        self._check_clustering()

        algorithm = algorithm.lower()
        # supported clustering algorithms scalable to very large data sets
        # from sklearn.cluster import MiniBatchKMeans, DBSCAN, OPTICS, BisectingKMeans
        if algorithm == "leiden":
            cluster_fun = self.cluster_leiden
        elif algorithm == "snn":
            cluster_fun = self.cluster_snn
        elif algorithm == "kmeans":
            cluster_fun = self.cluster_minibatch_kmeans
        elif algorithm == "dbscan":
            cluster_fun = self.cluster_dbscan
        elif algorithm == "optics":
            cluster_fun = self.cluster_optics
        elif algorithm == "hierarchical_kmeans":
            cluster_fun = self.cluster_hierarchical_kmeans
        else:
            raise ValueError("Clustering algorithm not supported. Please select between: "
                             "leiden | SNN | KMeans | DBSCAN | OPTICS | hierarchical_KMeans")

        # run clustering
        cluster_fun(
            save_name=save_name,
            dr_name=dr_name,
            seed=seed,
            verbosity_indent=verbosity_indent,
            **kwargs
        )

    def umap(
            self,
            n_neighbors: int = 30,
            dr_name: str | None = None,
            save_name: str = "umap",
            metric: str | Callable = "euclidean",
            min_dist: float = .1,
            n_components: int = 2,
            n_jobs: int = 1,
            verbosity_indent: str = ""
    ):
        """
        Calculate UMAP embedding for KMer histograms. See https://umap-learn.readthedocs.io/en/latest/ for
        more information. Result will be saved in `self.x_umap[save_name]`.

        :param int n_neighbors: Number of neighbors used for UMAP embedding.
        :param str | None dr_name:  Name of dimensionality reduction that should be used, which is saved under
            `your_kmer_obj.dr[dr_name]`. Please run the dimensionality reduction before. If none passed, use the full
            k-mer histogram.
        :param str save_name: Name under which results are saved in the `x_umap` dictionary.
        :param str | Callable metric: Distance metric. Can be either string or a user-defined callable. See
            https://umap-learn.readthedocs.io/en/latest/parameters.html#metric for more information
        :param float min_dist: Minimum distance between points
        :param int n_components: Dimension of manifold embedding. This should be lower than or equal to the dimension
            of the KMer histograms. If you want to plot the data using the plotting algorithm provided by the
            framework, the value must be 1 <= `n_components` <= 3
        :param int n_jobs: number of jobs used.
        :param str verbosity_indent: Prefix for verbosity output to indicate that this routine was called within
            another function
        """
        self._check_umap()

        umap_map = umap.UMAP(
            n_neighbors=n_neighbors,
            metric=metric,
            min_dist=min_dist,
            n_components=n_components,
            n_jobs=n_jobs
        )
        if self.verbosity > 0:
            print("%sCalculate UMAP embedding" % verbosity_indent)
        try:
            kmer_data = self.kmer_hist if dr_name is None else self.dr[dr_name]
        except KeyError:
            raise KeyError("Dimensionality reduction %s not found. Please run a dimensionality reduction "
                           "which is saved under this name." % dr_name)
        self.x_umap[save_name] = umap_map.fit_transform(kmer_data)

    def transfer_labels(
            self,
            other: KMerClass,
            cell_labels: pl.Series | pd.Series | np.ndarray | List,
            dr_name: str | None = None,
            other_dr_name: str | None = None,
            n_neighbors: str | int = 5,
            neighbor_batch: str | int = 128,
            max_dist: str | float | None = None,
            metric: str | Callable = "euclidean",
            leaf_size: str | int = 40,
            verbosity_indent: str = "",
        ) -> pl.Series:
        """
        Create a KD tree from query data, fetch the n clostest neighbors, and count most common cell label

        :param KMerClass other: Target KMer object
        :param pl.Series | pd.Series | np.ndarray | List cell_labels: Cell labels, annotations, or other 
            cell-specific data
        :param str | None dr_name: key for dimensionality reduction in query KMer object (self). If none, 
            compute KD tree based on complete KMer histogram
        :param str | None other_dr_name: key for dimensionality reduction in target KMer object. If none,
            compute KD tree based on complete KMer histogram
        :param str | int n_neighbors: Maximum number of nearest neighbors considered for label transfer
        :param str | int neighbor_batch: Batch size for iterating over target data.
        :param str | float | None max_dist: Maxmimum distance between query and target cell. If none, set to 
            infinity
        :param str | Callable metric: Distance metric accepted by sklearn's KD tree
        :param str | int leaf_size: Number of points at which to switch to brute-force. Does not affect results,
            but influences memory consumption and run time.
        :param str verbosity_indent:  Prefix for verbosity output to indicate that this routine was called within
            another function
        :return pl.Series: transfered labels.
        """
        from sklearn.neighbors import KDTree
        
        # convert input values
        n_neighbors = int(n_neighbors)
        cell_labels = pl.Series(cell_labels)
        neighbor_batch = int(neighbor_batch)
        leaf_size = int(leaf_size)
        if max_dist is None:
            max_dist = np.inf
        else:
            max_dist = float(max_dist)
        if dr_name is None:
            kmer_data = self.kmer_hist if self.k <= MAX_K_DENSE else self.kmer_hist.A
            other_data = other.kmer_hist if other.k <= MAX_K_DENSE else other.kmer_hist.A
        else:
            try:
                kmer_data = self.dr[dr_name]
                other_data = other.dr[other_dr_name]
            except KeyError:
                raise KeyError("Dimensionality reduction %s not found. Please run a dimensionality reduction "
                               "which is saved under this name." % dr_name)
            
        if kmer_data.shape[1] != other_data.shape[1]:
            raise ValueError("Query and target KMer object must have the same `k` or the same dimension saved "
                             "with the dimensionality reduction key.")

        if self.verbosity > 0:
            print("%s\tCreate nearest neighbor ball" % verbosity_indent)
        # fetch nearest neighbors
        kdtree = KDTree(kmer_data, metric=metric, leaf_size=leaf_size)
        target_labels = []
        if self.verbosity > 0:
            print("%s\t Transfer labels" % verbosity_indent)

        cell_kmer_iterator = tqdm(
            range(0, other_data.shape[0], neighbor_batch),
            desc="%s\tProgress" % verbosity_indent
        ) if self.verbosity > 0 else range(0, other_data.shape[0], neighbor_batch)
        # iterate over all cells to create adjacency matrix
        for i_cell_start in cell_kmer_iterator:
            query_dist, query_idc = kdtree.query(
                other_data[i_cell_start:np.minimum(i_cell_start + neighbor_batch, other_data.shape[0])],
                k=n_neighbors,
                return_distance=True
            )
            target_labels.extend(
                [Counter(cell_labels[idc[dist <= max_dist]]).most_common(1)[0][0]
                 for dist, idc in zip(query_dist, query_idc)]
            )

        return pl.Series(target_labels)  

    def to_anndata(
            self,
            barcodes: pl.Series | pd.Series | pd.Index | np.ndarray,
            obs: pl.DataFrame | pd.DataFrame | None = None,
            var: pl.DataFrame | pd.DataFrame | None = None
    ) -> ad.AnnData:
        """
        Convert KMer object to anndata

        :param pl.Series | pd.Series | pd.Index | np.ndarray barcodes: cell barcodes
        :param pl.DataFrame | pd.DataFrame | None obs: additional obs values
        :param pl.DataFrame | pd.DataFrame | None var: additional var values
        :return ad.AnnData: AnnData object.
        """
        # get data
        X_data = self.kmer_hist if self.kmer_hist is not None else None
        barcodes = pd.Index(barcodes)

        # convert obs and var data
        if isinstance(obs, pl.DataFrame):
            obs = obs.to_pandas()
        if isinstance(var, pl.DataFrame):
            var = var.to_pandas()
        if obs is None:
            obs = pd.DataFrame(index=barcodes)
        else:
            obs = obs.set_index(barcodes)

        clustering = {}
        if self.clustering is not None:
            clustering = {"cluster_%s" % key: value for key, value in self.clustering.items()}        

        # convert obsm data
        dr = {}
        if self.dr is not None:
            dr = {"dr_%s" % key: value for key, value in self.dr.items()}
        x_umap = {}
        if self.x_umap is not None:
            x_umap = {"x_umap_%s" % key: value for key, value in self.x_umap.items()}

        obsm = {**dr, **x_umap}
        clustering_df = pd.DataFrame(clustering, index=barcodes)
        obs = obs.join(clustering_df)

        var_names = product(self.alphabet, repeat=self.k)
        if var is None:
            var = pd.DataFrame(index=var_names)
        else:
            var = var.set_index(var_names)
        
        return ad.AnnData(X=X_data, obs=obs, var=var, obsm=obsm)
    
    def write_h5ad(
            self,
            path: str,
            adata: ad.AnnData | None = None
    ):
        """
        Save KMer object to H5ad file

        :param str path: Path to h5ad file
        :param ad.AnnData | None adata: KMer converted AnnData object. If `None`, convert entire object 
            to `AnnData` and write to file.
        """
        if not path.endswith(".h5ad"):
            raise ValueError("H5ad files must have a .h5ad file suffix.")
        if adata is None:
            adata = self.to_anndata(barcodes=self.barcodes)
        # create folders in path if not already present.
        Path("/".join(path.split("/")[:-1])).mkdir(exist_ok=True, parents=True)
        adata.write_h5ad(path)

    def copy(self) -> KMerClass:
        """
        Create copy of the KMerClass object. Note that the exact behavior is determined by 
        the inheriting class in the `__getitem__` function.
        
        :return KMerClass: Copy of the KMerClass
        """
        return self[:]
    
    def save(self, path: str):
        """
        Save KMer object to file using pickle.

        :param str path: Path to pickle file. This should have either the suffix .pkl or .pickle. If file doesn't exist,
            create new one. If file exists already, it is overwritten.
        """
        if not path.endswith(".pkl") and not path.endswith(".pickle"):
            raise ValueError("Please pass a path to pickle file with the suffix `.pkl` or `.pickle`.")
        with open(path, "wb") as pickle_file:
            dill.dump(self, pickle_file)

    @classmethod
    def load_pickle(cls, path: str) -> KMerClass:
        """
        Load KMer object from pickle file.

        :param str path: path to pickle file.
        :return KMerClass: The KMer object.
        """
        if not path.endswith(".pkl") and not path.endswith(".pickle"):
            raise ValueError("Please pass a path to pickle file with the suffix `.pkl` or `.pickle`.")
        with open(path, "rb") as pickle_file:
            return dill.load(pickle_file)
        

class KMerWrapper(KMerClass):
    """
    Minimal KMer wrapper object such that an array or matrix behaves like a KMer object. This is used particularly for 
    treating the k-mer histogram over the entire genome as a KMerObject.

    :param np.ndarray | sp.coo_matrix | sp.csr_matrix | sp.lil_matrix kmer_hist: array or sparse matrix that contains k-mer
        histogram information.
    :param int k: defines length of k-mers. For example `k=3` creates 3-mers, i.e. overlapping sequence strings of length
        3.
    :param int | None ell: Ell-mer length when using gapped k-mers. When None, no gapped k-mers are used.
    :param List[str] alphabet: The alphabet to be considered. Note that some functions might be compromised when using another
        alphabet than DNA and RNA, such as defining the reverse compleme
    :param int verbosity: verbosity level. The lower, the less output.
    """
    def __init__(
            self, 
            kmer_hist: np.ndarray | sp.coo_matrix | sp.csr_matrix | sp.lil_matrix, 
            k: int = 6, 
            ell: int | None = None,
            alphabet: List[str] = DNA_ALPHABET,
            verbosity: int = 0
        ):
        super(KMerWrapper, self).__init__(k=k, ell=ell, verbosity=verbosity, alphabet=alphabet)
        self.kmer_hist = kmer_hist
        self.barcodes = np.arange(kmer_hist.shape[0])
        self.shape = kmer_hist.shape
        
    def __getitem__(self, item):
        return KMerWrapper(self.kmer_hist[item], k=self.k)


class KMerMatrix(KMerClass):
    """
    KMerMatrix class inherits from the abstract KMerClass. It creates the KMer histogram for a single h5ad file as well
    as saves additional cell and feature information

    :param np.ndarray | sp.csc_matrix | sp.lil_matrix | sp.csr_matrix | None kmer_hist: Pre-computed k-mer histogram. If None, 
        this will be computed based on the passed `genome_path`, `data_path`, and `feature_bed_path`.
    :param pd.Index | np.ndarray | pd.Series | pl.Series | List[str] | None barcodes: Cell IDs or barcodes. If set to 
        None and `kmer_hist` is None, use the `obs_names` of the h5ad file at `data_path`. If set to None and `kmer_hist`
        is passed, number cells in an ascending fashion.
    :param str genome_path: Path to genome fasta file
    :param str data_path: path to h5ad file, e.g. peak matrix or tile matrix saved as h5ad file
    :param str feature_bed_path: bed file that defines feature positions, e.g. peaks.
    :param str | List[str] | None white_list: White list for selected features / peaks. This can be either a list with entries
        of the form `chr:start-end` which match peak coordinates in `feature_bed_path`, or it is a path to a sub set of the
        peak entries in bed format.
    :param str | None cell_annotation_path: path to data table with additional cell information
    :param str | None feature_annotation_path: path to data table with additional feature information, e.g. peaks.
    :param int k: defines length of k-mers. For example `k=3` creates 3-mers, i.e. overlapping sequence strings of length
        3.
    :param int | None ell: Ell-mer length when using gapped k-mers. When None, no gapped k-mers are used.
    :param str | None species: Species name
    :param str | None matrix_name: Matrix name, which is used to identify independent samples. Ideally unique
        identifier, but this is no requirement.
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

        Default is None. We recommend using no normalization during KMer creation, and rather apply the normalization
        steps during the analysis.
    
    :param int max_region_size: Maximum peak or region length that is used for creating kmer histogram
    :param str annotation_sep: Separator character in `cell_annotation_path` table and `feature_annotation_path` table.
    :param bool annotation_has_header: If true, annotation files contain a header
    :param str | None cell_id_col: Column name in cell annotation that contains the unique cell identifier as used
        in the h5ad data files.
    :param bool mask_rep: If set to True, remove kmers that contain lower case letters indicating masked repetitive
        sequences. If set to False, treat masked sequences equal to non-masked sequences
    :param bool correct_gc: If set, correct for GC DNA content bias by sampling with replacement of accessible regions
        per cell that match the GC content distribution over all peaks.
    :param str n_policy: Defines how to deal with kmers that contain undeterministic nucleotides marked with the
        letter `N`. Choose between remove | replace | keep.

        - `remove` filters out kmers with N occurrences.
        - `replace` replaces kmers that contain Ns with all possibilities
        - `keep` keeps the Ns untreated

    :param List[str] alphabet: Used alphabet that is present in sequence. Default is a `A`, `C`, `G`, and `T`.
    :param bool rm_zeros: If `equalize_counter=True`, there are some redundancies, which can be set to zero and removed.
        by setting this flag. The flag is ignored when `equalize_counter=False`.
    :param bool equalize_counter: If set to `True`, treat forward and reverse complement kmer as the same kmer. That
        means values for `GCGT` are added to the histogram values for `ACGC`. Otherwise, they are treated as independent
        entities. 
    :param int n_jobs: Number of jobs used. If none or negative, then use all available cpus.
    :param int verbosity: Verbosity level
    :param str verbosity_indent: Prefix for verbosity output to indicate that this routine was called within
            another function
    :param str | None dump_to: Path to file where kmer histogram results are dumped to with barcode.
        If none, keep exclusively in memory.
    """
    def __init__(
            self,
            kmer_hist: np.ndarray | sp.csc_matrix | sp.lil_matrix | sp.csr_matrix | None = None,
            barcodes: pd.Index | np.ndarray | pd.Series | pl.Series | List[str] | None = None,
            genome_path: str | None = None,
            data_path: str | None = None,
            feature_bed_path: str | None = None,
            white_list: str | List[str] | None = None,
            cell_annotation_path: str | None = None,
            feature_annotation_path: str | None = None,
            k: int = 6,
            ell: int | None = None,
            species: str | None = None,
            matrix_name: str | None = None,
            normalization: Callable | str | None = "centered_sum",
            max_region_size: int | None  = 701,
            annotation_sep: str = "\t",
            annotation_has_header: bool = True,
            cell_id_col: str | None = None,
            mask_rep: bool = False,
            correct_gc: bool = False,
            n_policy: str = "remove",
            alphabet: List[str] = DNA_ALPHABET,
            rm_zeros: bool = True,
            equalize_counter: bool = False,
            n_jobs: int | None = None,
            verbosity: int = 1,
            verbosity_indent: str = "",
            dump_to: str | None = None
    ):
        super(KMerMatrix, self).__init__(k=k, ell=ell, verbosity=verbosity, alphabet=alphabet)
        self.genome_path = genome_path
        self.white_list = white_list
        self.data_path = data_path
        self.feature_bed_path = feature_bed_path
        self.cell_annotation_path = cell_annotation_path
        self.feature_annotation_path = feature_annotation_path
        self.annotation_sep = annotation_sep
        self.annotation_has_header = annotation_has_header
        self.cell_id_col = cell_id_col
        self.kmer_path = None

        # Set KMerMatrix object values
        self.species = species
        self.matrix_name = matrix_name
        normalization_fun = convert_normalization(normalization)
        if barcodes is not None:
            if isinstance(barcodes, np.ndarray) or isinstance(barcodes, list):
                barcodes = pd.Index(barcodes)
            elif isinstance(barcodes, pl.Series):
                barcodes = pd.Index(barcodes.to_pandas())
            elif isinstance(barcodes, pd.Series):
                barcodes = pd.Index(barcodes)

        if kmer_hist is not None:
            self.kmer_hist = kmer_hist
            if len(self.alphabet)**self.k < kmer_hist.shape[1]:
                raise ValueError("The passed `k` is too low for the passed `kmer_hist`.")
            elif len(self.alphabet)**self.k > kmer_hist.shape[1] and self.ell is None:
                if len(nozero_kmer_to_idx(self.alphabet, self.k)) != kmer_hist.shape[1]:
                    raise ValueError("Passed `kmer_hist` does neither seem to be full nor to be zero-reduced. There is a mismatch "
                                     "between the passed `k` and the `kmer_hist`.")
            if len(barcodes) != self.kmer_hist.shape[0]:
                warnings.warn("Number of barcodes is not equal to the number of data values. Use default numbering as barcode names instead.")
                barcodes = None
            if barcodes is None:
                barcodes = pd.Index(np.arange(self.kmer_hist.shape[0]))
            self.barcodes = barcodes
        else:
            self._compute_kmer_hist(
                max_region_size=max_region_size if max_region_size is not None else np.inf,
                mask_rep=mask_rep,
                n_policy=n_policy,
                rm_zeros=rm_zeros,
                correct_gc=correct_gc,
                equalize_counter=equalize_counter,
                n_jobs=n_jobs,
                verbosity_indent=verbosity_indent,
                dump_to=dump_to
            )

        self.barcodes = pd.Index(self.barcodes)
        self.shape = self.kmer_hist.shape
        self.kmer_hist = normalization_fun(self.kmer_hist)

    def __getstate__(self) -> dict:
        """
        Get state function removes the kmer_hist for efficient pickling.
        
        :return: Dictionary representing the object's state
        """
        state = self.__dict__.copy()
        # don't return kmer_hist, therefore it is not pickled
        del state["kmer_hist"]
        return state

    def __getitem__(
            self, 
            item: Tuple[
                int | np.ndarray | pd.Series | pl.Series | slice | None,
                int | np.ndarray | slice | None 
            ] | int | np.ndarray | pd.Series | pl.Series | slice | None = (None, None)
        ) -> KMerMatrix:
        """
        Get item subsets kmer matrix by creating a copy of self as well as setting kmer_hist 
        and barcodes as they're not included in __getstate__.

        **Important**: Note that when passing `kmer_idc`, the dimensionality reduction, UMAP, and
            clustering might be obsolute. They are copied nevertheless, but remember to re-run 
            for consistent results.

        :param int | np.ndarray | slice | pl.Series | pd.Series | None cell_item: Cell indices
        :param int | np.ndarray | slice | None kmer_item: Kmer indices
        :return: sub-setted kmer matrix. 
        """

        if isinstance(item, tuple):
            if len(item) == 2:
                cell_item, kmer_item = item
            elif len(item) == 1:
                cell_item = item
                kmer_item = None
            else:
                raise ValueError("__getitem__ only accepts maximally two values: cell index and kmer index.")
        else :
            cell_item = item
            kmer_item = None
        cell_item = self._convert_item(cell_item, is_kmer_item=False)
        kmer_item = self._convert_item(kmer_item, is_kmer_item=True)
        new_self = copy.copy(self)
        new_self.kmer_hist = self.kmer_hist.copy()
        if isinstance(new_self.kmer_hist, np.ndarray):
            new_self.kmer_hist = new_self.kmer_hist[cell_item]
        else:
            kmer_type = type(new_self.kmer_hist)
            new_self.kmer_hist = kmer_type(sp.lil_matrix(new_self.kmer_hist)[cell_item])

        if len(new_self.kmer_hist.shape) == 1:
            new_self.kmer_hist = self.kmer_hist.reshape(1, -1)
        new_self.kmer_hist = new_self.kmer_hist[:, kmer_item]
        new_self.shape = new_self.kmer_hist.shape
        new_self.barcodes = pd.Index(self.barcodes)[cell_item]
        new_self.clustering, new_self.dr, new_self.x_umap = self._subset_dicts(cell_item)
        new_self.verbosity = self.verbosity
        new_self.k = self.k
        new_self.ell = self.ell
        _, new_self.pattern_offset_dict = get_kmer_names(k=self.k, ell=self.ell, alphabet=self.alphabet, return_offset=True)
        return new_self
    
    def __str__(self) -> str:
        """To string function"""
        s = "Gapped " if self.ell is not None else ""
        s += "KMerMatrix %s of species %s with k=%d" % (self.matrix_name, self.species, self.k)
        if self.ell is not None:
            s += " and ell=%d" % self.ell
        s += "\n(%d, %d)" % self.shape
        return s
    
    def __repr__(self) -> str:
        """String representation"""
        return self.__str__()
    
    def _compute_kmer_hist(
            self,
            max_region_size: int  = 701,
            barcodes: pd.Series | None = None,
            min_peaks: int = 100,
            mask_rep: bool = False,
            n_policy: str = "remove",
            rm_zeros: bool = True,
            equalize_counter: bool = False,
            correct_gc: bool = False,  
            n_jobs: int | None = None,
            verbosity_indent: str = "",
            dump_to: str | None = None
        ):
        """
        Initialize kmer histogram matrix by using feature data and a reference genome.

        :param int max_region_size: Maximum peak or region length that is used for creating kmer histogram
        :param pd.Series | None barcodes: Barcode names. If None, use the `obs_names` from the h5ad data. 
        :param int min_peaks: Remove cells that have less peaks.
        :param bool mask_rep: If set to True, remove kmers that contain lower case letters indicating masked repetitive
            sequences. If set to False, treat masked sequences equal to non-masked sequences
        :param str n_policy: Defines how to deal with kmers that contain undeterministic nucleotides marked with the
            letter `N`. Choose between remove | replace | keep.

            - `remove` filters out kmers with N occurrences.
            - `replace` replaces kmers that contain Ns with all possibilities
            - `keep` keeps the Ns untreated

        :param bool equalize_counter: If set to `True`, treat forward and reverse complement kmer as the same kmer. That
            means values for `GCGT` are added to the histogram values for `ACGC`. Otherwise, they are treated as independent
            entities. 
        :param bool rm_zeros: If `equalize_counter=True`, there will be a some entries in the histogram that will always be zero.
            setting the flag `rm_zeros=True` will remove these entries. The flag is ignored when `equalize_counter=False`.
        :param bool correct_gc: Account for varying GC content between cells by sampling with replacement from each accessible
            regions in a single cell to match the GC distribution over all peaks.
        :param int n_jobs: Number of jobs used. If none or negative, then use all available cpus.
        :param str verbosity_indent: Prefix for verbosity output to indicate that this routine was called within
                another function
        :param str | None dump_to: Path to file where kmer histogram results are dumped to with barcode.
            If none, keep exclusively in memory.
        """
        if self.verbosity > 0:
            print("%sLoad data" % verbosity_indent)
        if n_jobs < 0:
            n_jobs = None
        # Create pool in the beginning to avoid copying unnecessary data files into child memory.
        # Also use spawn instead of fork as fork seems to be buggy, which additionally circumvents the memory problem
        with multiprocessing.get_context("spawn").Pool(processes=n_jobs) as pool:
            # create file to write results to. If not passed, make temporary file
            if dump_to is not None:
                Path(dump_to).touch(exist_ok=False)        
            # load data files
            if self.genome_path is None:
                raise ValueError("When not passing directly a kmer histogram, you need to pass a path to a genome fasta file `genome_path`.")
            genome = pysam.FastaFile(self.genome_path)
            if self.data_path is None:
                raise ValueError("When not passing directly a kmer histogram, you need to pass a path to a h5ad data file `data_path`.")
            data = ad.read_h5ad(self.data_path)
            data = data[np.argsort(data.obs_names)]  # sort alphabetically
            if barcodes is not None and len(barcodes) != data.n_obs:
                warnings.warn("Number of barcodes is not equal to the number of data values. Use `obs_names` as barcode names instead.")
                barcodes = None
            if barcodes is None:
                self.barcodes = pd.Index(data.obs_names)
            else:
                self.barcodes = pd.Index(barcodes)

            # load bed file
            if self.feature_bed_path is None:
                raise ValueError("When not passing directly a kmer histogram, you need to pass a path to peak bed file `feature_bed_path`.")
            feature_bed = pl.read_csv(
                self.feature_bed_path,
                separator="\t",
                has_header=False,
                infer_schema_length=0
            ).select(pl.col("column_1", "column_2", "column_3"))
            feature_bed.columns = ["chr", "start", "end"]

            # assume that peak bed order is identical to order in matrix
            feature_bed = feature_bed.with_columns(
                pl.Series(np.arange(feature_bed.shape[0], dtype="int")).alias("index")
            )

            # reshape peak sizes if too large
            feature_bed = feature_bed.with_columns(
                 (pl.col("end").cast(pl.Int64) - pl.col("start").cast(pl.Int64)).abs().alias("length")
            ).filter(
                pl.col("length") <= max_region_size
            )

            if self.white_list is not None:
                if isinstance(self.white_list, str):
                    # assume that it is in bed format
                    white_list = pl.read_csv(
                        self.white_list, 
                        separator="\t", 
                        has_header=False, 
                        infer_schema_length=0
                    ).select(pl.col("column_1", "column_2", "column_3"))
                    white_list.columns = ["chr", "start", "end"]
                    self.white_list = (white_list["chr"] + ":" + white_list["start"] + "-" + white_list["end"]).to_list()
                if isinstance(self.white_list, list):
                    feature_bed = feature_bed.filter(
                        (pl.col("chr") + ":" + pl.col("start") + "-" + pl.col("end")).is_in(self.white_list)
                    )
                else:
                    warnings.warn("White list format not understood. Do not subset feature bed file.")

            feature_bed = feature_bed.sort("index")
            kept_idc = feature_bed["index"].to_numpy()

            # assume that peak bed order is identical to order in matrix
            feature_bed = feature_bed.with_columns(
                pl.Series(np.arange(feature_bed.shape[0], dtype="int")).alias("index")
            )
            peak_gc, peak_gc_hist = None, None
            if correct_gc:
                peak_iter = tqdm(
                    feature_bed.sort("index").iter_rows(named=True),
                    desc="Determine GC content over peaks",
                    total=feature_bed.shape[0]
                ) if self.verbosity > 0 else feature_bed.sort("index").iter_rows(named=True)
                
                gc_bins = np.linspace(0., 1., 21)  # 5%-point steps
                peak_gc_l = []
                for peak in peak_iter:
                    seq = genome.fetch(peak["chr"], int(peak["start"]), int(peak["end"]))
                    # count GC content
                    peak_gc_l.append(
                        len(re.findall("|".join(GC_CONTENT), seq)) / float(len(seq))
                    )

                peak_gc = np.array(peak_gc_l)
                peak_gc_hist, _ = np.histogram(peak_gc, bins=gc_bins, density=False)  
                peak_gc_hist = peak_gc_hist / peak_gc_hist.sum()

            if self.verbosity > 0:
                print("%sCreate K-mer matrix" % verbosity_indent)
            self.kmer_hist = None
            # get bool data
            bool_data = data.X > 0
            # define iterator with progress bar depending on set verbosity levels
            cell_iterator = tqdm(
                np.arange(data.n_obs),
                desc="%sPrepare" % verbosity_indent
            ) if self.verbosity > 0 else np.arange(data.n_obs) > 0
            # iterate over all cells, fetch sequences for which peaks were detected and convert to kmer histogram
            kmer_jobs = []
            return_dense = self.k <= MAX_K_DENSE
            stack_lib = np if return_dense else sp
            # get kmer list for mapping index to sequence
            if self.ell is not None:
                col_names, idx_offset = get_kmer_names(k=self.k, ell=self.ell, alphabet=self.alphabet, return_offset=True)
                ell_list = get_kmer_names(k=self.ell, ell=None, alphabet=self.alphabet, return_offset=False)
                gkm_mat = get_gkm_mat(ell_names=ell_list, n_gapped_kmer=len(col_names), offset_dict=idx_offset, alphabet=self.alphabet)
            else:
                gkm_mat = None

            for i_cell in cell_iterator:
                _, peak_idx, _ = sp.find(bool_data[i_cell, kept_idc])
                if len(peak_idx) <= min_peaks: continue

                if correct_gc:
                    cell_gc = peak_gc[peak_idx]
                    # create GC histogram for cell
                    cell_gc_hist, _ = np.histogram(cell_gc, bins=gc_bins, density=False)
                    cell_gc_hist = cell_gc_hist / cell_gc_hist.sum()  
                    # evaluate difference between total GC distribution and cell GC
                    diff = peak_gc_hist - cell_gc_hist
                    div = np.maximum(cell_gc_hist, peak_gc_hist)
                    div[div == 0.] = 1.
                    # calcualte percentage
                    diff = diff / div
                    corrected_peak_idx = []
                    # correct per bin
                    for i_bin, (bin_s, bin_e) in enumerate(zip(gc_bins[:-1], gc_bins[1:])):
                        mask = np.logical_and(
                            cell_gc >= bin_s,
                            cell_gc < bin_e
                        )
                        n_peaks = np.sum(mask)
                        # sample with replacement
                        corrected_peak_idx.append(
                            np.random.choice(peak_idx[mask], replace=True, size=n_peaks + int(n_peaks * diff[i_bin]))
                        )
                    peak_idx = np.concatenate(corrected_peak_idx)

                # get cell peaks
                cell_peaks = feature_bed.filter(pl.col("index").is_in(peak_idx))
                cell_peaks = pl.DataFrame(cell_peaks.to_pandas().set_index("index").loc[peak_idx].sort_index())
                # fetch sequences
                seq_list = [genome.fetch(peak[0], int(peak[1]), int(peak[2]))
                            for peak in cell_peaks.iter_rows(named=False)]
   
                kmer_jobs.append((i_cell, pool.apply_async(
                    create_kmer_hist, args=(
                        seq_list,
                        self.barcodes[i_cell],
                        self.k if self.ell is None else self.ell,
                        self.alphabet,
                        mask_rep,
                        n_policy,
                        return_dense,
                        rm_zeros,
                        equalize_counter,
                        dump_to,
                        gkm_mat
                    ))))
            pbar = tqdm(total=data.n_obs, desc="%sFetch result" % verbosity_indent) if self.verbosity > 0 else None
            kmer_results = fetch_async_result(
                kmer_jobs, 
                process_bar=pbar, 
                # hardcoded number of attempts before cancelling
                max_attempt=200 if self.ell is None or self.ell < 10 else 500  
            )

        if self.verbosity > 0:
            print("%sFinished processing, combine cell k-mer histograms" % verbosity_indent)
        # update barcode as some cells might not have been able to be collected after parallelizing
        self.barcodes = self.barcodes[np.array([bc for bc, _ in sorted(kmer_results, key=lambda x: x[0])])]
        # stack kmer histograms over entire cell data set
        if dump_to is None:
            self.kmer_hist = stack_lib.vstack([y for _, y in sorted(kmer_results, key=lambda x: x[0])])
            if self.k > MAX_K_DENSE:
                self.kmer_hist = self.kmer_hist.tocsc()
        else:
            kmer_df = pl.read_csv(
                dump_to,
                has_header=False,
                separator=",",
                infer_schema_length=0
            ).sort(by="column_1")
            self.kmer_hist = kmer_df.drop("column_1").to_numpy().astype("int")

    def copy(self) -> KMerMatrix:
        """
        Create copy of KMerMatrix
        
        :return KMerMatrix: Copy of KMerMatrix
        """
        return self[:]

    def set_normalization(
            self, 
            normalization: Callable | str | None = "centered_sum",
            ord_vec: None | List | np.ndarray | pl.Series | pd.Series = None,
            prepare: Callable | None = None,
            **kwargs
        ):
        """
        Set and run normalization. Note that this will not create a copy, and the kmer histograms
        are overwritten. Running several normalizations in a row is therefore not possible.

        Note that we have tested different normalizations extensively, and we highly recommend to 
        use only `none` (default), `sum_norm`, and `centered_sum`. You should be very sure of what
        you're doing when using another normalization.

        :param Callable | str | None normalization: pass one of the following.

            - string identifying pre-implemented normalization, such as
                `none` | `max_norm` | `sum_norm` | `center_norm` | `centered_sum` | `centered_max` | 
                `centered_uniform_sum` | `centered_uniform_max`. Unless you know what you're doing, choose
                `centered_sum`
            - your own callable, which will be wrapped into a spyce normalization function
            - `None`, when no normalization should be performed

        :param  None | List | np.ndarray | pl.Series | pd.Series ord_vec: Ordinal vector with respect to which
            the data is normalized. With the provided methods, this is only used when the data is centered, or the
            standard deviation normalized. When passing an exclusively cell-based normalization (e.g. `sum_norm`),
            during which each cell row is normalized independently, this parameter has no effect. If not provided
            or `None`, normalize over entire matrix.
        :param Callable | None prepare: If passed, computes global values over entire histogram. Return value must be a dictionary
            that contains keyword parameters for the normalisation function. If the `prepare` dictionary also contains an
            `ord_vec` key or if the `ord_vec` value is explicitly set, the dictionar must be of the form
            
            .. code-block:: python

                {
                    "label1_in_vec": {"param1": param1_1, "param2": param2_1},
                    ...
                    "labeln_in_vec": {"param1": param1_n, "param2": param2_n},
                }
            
            
            where you need to replace the names and values according to your normalization function.
        :param kwargs: other parameters passed to normalization function
        """

        if prepare is not None:
            prep_kwargs = prepare(self.kmer_hist, **kwargs)
        else:
            prep_kwargs = {}

        if "ord_vec" in prep_kwargs:
            ord_vec = prep_kwargs["ord_vec"]
            del prep_kwargs["ord_vec"]
        normalization_fun = convert_normalization(normalization)
        if ord_vec is None:
            self.kmer_hist = normalization_fun(self.kmer_hist, **prep_kwargs, **kwargs)
        else:
            self.kmer_hist = normalize_over_ord_vec(
                self.kmer_hist,
                ord_vec,
                normalization_fun,
                **prep_kwargs,
                **kwargs
            )

    def fetch_cell_annotation(
            self,
            cell_id_col: str | None = None,
            idc: np.ndarray | None = None,
            barcodes: np.ndarray | pd.Series | pl.Series | None = None
    ) -> pl.DataFrame | None:
        """
        Fetches annotation file if passed. Note that this information is not hold by the object,
        and it is instead loaded from file every time this function is called. This permits to 
        link arbitrary tabular data to your file, as long as the barcodes are conistent and matching.

        :param str | None cell_id_col: Column name that contains the cell barcodes or IDs. If `None`, 
            use the `cell_id_col` name that is hold by the object.
        :param np.ndarray | None idc: If set, subset to these indices. Note that these are positional 
            indices and not barcodes or cell IDs. If you want to subset with respect to those, use 
            `barcodes` instead.
        :param np.ndarray | pd.Series | pl.Series | None barcodes: If set, subset fetched annotation to 
            the passed barcodes.
        :return pl.DataFrame: Polars data frame with the cell annotation information. If no cell_annotation is set, return None.
        """
        if self.cell_annotation_path is None:
            warnings.warn("No cell annotation path set.")
            return 
        
        cell_annotation = pl.read_csv(
            self.cell_annotation_path,
            separator=self.annotation_sep,
            has_header=self.annotation_has_header,
            infer_schema_length=0
        )
        if cell_id_col is not None:
            self.cell_id_col = cell_id_col

        cell_annotation = cell_annotation.filter(
            pl.col(self.cell_id_col).cast(pl.Utf8).is_in(self.barcodes.to_numpy().astype("str"))
        ).unique(self.cell_id_col).sort(by=self.cell_id_col)
        if idc is not None:
            cell_annotation = cell_annotation[idc]
        if barcodes is not None:
            if not isinstance(barcodes, np.ndarray):
                barcodes = barcodes.to_numpy().astype("str")
            cell_annotation = cell_annotation.filter(pl.col(self.cell_id_col).cast(pl.Utf8).is_in(barcodes))
        return cell_annotation

    def fetch_feature_annotation(self) -> pl.DataFrame | None:
        """
        Fetch feature annotation table. Note that any link between a particular peak or tile in the
        original data is lost after converting to the KMer histogram. However, this function allows
        to link arbitrary tabular information to the features that were used to create the KMer matrix.
        Note that the data is not hold by the object, and the table is load from file every time when
        the method is called.

        :return pl.DataFrame: Polars data frame with the feature anntotation. If no feature annotation path is set, return None.
        """
        if self.feature_annotation_path is None:
            warnings.warn("No feature annotation is set.")
            return
         
        return pl.read_csv(
            self.feature_annotation_path,
            separator=self.annotation_sep,
            has_header=self.annotation_has_header,
            infer_schema_length=0
        )

    def fetch_feature_bed(self) -> pl.DataFrame | None:
        """
        Fetch feature bed (peaks or tiles) file that was used to create the KMer histrograms. 
        It is expected that the file is saved in `.bed` format. Note that the bed file is not
        hold in memory by the object, and the table is loaded from file every time the method
        is called.

        :return pl.DataFrame: Polars data frame with the feature coordinates. If no feature bed path is set, return None
        """
        if self.feature_bed_path is None:
            warnings.warn("No feature bed path is set.")
            return
        
        feature_bed = pl.read_csv(
            self.feature_bed_path,
            separator="\t",
            has_header=False,
            infer_schema_length=0
        )
        if self.white_list is not None:
            if isinstance(self.white_list, list):
                feature_bed = feature_bed.filter(
                    (pl.col("chr") + ":" + pl.col("start") + "-" + pl.col("end")).is_in(self.white_list)
                )
            else:
                warnings.warn("White list format not understood. Do not subset feature bed file.")
        return feature_bed

    def fetch_h5ad(self) -> ad.AnnData | None:
        """
        Fetch h5ad file that was used for creating the Kmer matrix. Note that the file is not 
        hold in memory by the object, and it is reloaded from file every time the method is called.

        :return ad.AnnData: the h5ad file as an AnnData object. If not data path is set, return None.
        """
        if self.data_path is None:
            warnings.warn("No data path is set.")
            return
        
        h5ad_ad = ad.read_h5ad(self.data_path)
        # sort
        return h5ad_ad[np.argsort(h5ad_ad.obs_names)]

    def fetch_seq(
            self,
            return_seq_obj: bool = False,
            chromosome: str | None = None,
            start: int | None = None,
            end: int | None = None
    ) -> pysam.FastaFile | str | None:
        """
        Fetch genome sequence.

        :param bool return_seq_obj: If set to `True`, return the entire sequence as a `pysam.FastaFile`
            object. Otherwise, fetch sequence string defined by the other parameters `chromosome`,
            `start`, and `end`.
        :param str | None chromsome: Chromosome name.
        :param int | None start: Start position.
        :param int | None end: End position.
        :return pysam.FastaFile | str: If `return_seq_obj=True`, return pysam.FastaFile object, otherwise
            return sequence string as defined by `chromosome`, `start`, and `end`. If no genome path is set, 
            return None.
        """
        if self.genome_path is None:
            warnings.warn("No genome path is set.")
            return
        
        genome = pysam.FastaFile(self.genome_path)
        if return_seq_obj:
            return genome
        else:
            if any([param is None for param in [chromosome, start, end]]):
                raise ValueError("You need to pass chromosome, start, and end position when not fetching the "
                                 "Fasta object. If you want to retrieve the Fasta object as a whole, set "
                                 "return_seq_obj=True")
            return genome.fetch(chromosome, start, end)
        
    def transfer_labels(
            self,
            other: KMerClass,
            cell_anno: str | pd.Series | pl.Series | np.ndarray | List[str],
            dr_name: str | None = None,
            other_dr_name: str | None = None,
            verbosity_indent: str = "",
            **kwargs
        ) -> pl.Series:
        """
        Create a KD tree from query data, fetch the n clostest neighbors, and count most common cell label

        :param KMerClass other: Target KMer object
        :param str | pd.Series | pl.Series | np.ndarray | List[str] cell_anno: If passed as string, it's
            the column in cell annotation data that is used for label transfer. If passed as an accepted 
            iterable, then it is expected as the cell annotation sorted according to the barcodes.
        :param str | None dr_name: key for dimensionality reduction in query KMer object (self). If none, 
            compute KD tree based on complete KMer histogram
        :param str | None other_dr_name: key for dimensionality reduction in target KMer object. If none,
            compute KD tree based on complete KMer histogram
        :param str verbosity_indent:  Prefix for verbosity output to indicate that this routine was called within
            another function
        :param kwargs: Other keyword-value pairs that are passed as paramters to the super `transfer_labels` function
        :return pl.Series: transfered labels.
        """
        if isinstance(cell_anno, str):
            cell_anno_df = self.fetch_cell_annotation()[cell_anno]
        else:
            cell_anno_df = cell_anno
        return super(KMerMatrix, self).transfer_labels(
            other=other,
            cell_labels=cell_anno_df,
            dr_name=dr_name,
            other_dr_name=other_dr_name,
            verbosity_indent=verbosity_indent,
            **kwargs
        )
    
    def to_anndata(self) -> ad.AnnData:
        """
        Wrapper for transforming the data to an AnnData object. Fetches also the cell annotation if set.

        :return ad.AnnData: Return data as AnnData object.
        """
        cell_annotation = self.fetch_cell_annotation()
        return super(KMerMatrix, self).to_anndata(
            self.barcodes,
            obs=cell_annotation,
        )
    
    def write_h5ad(self, path: str):
        """
        Convert object to AnnData and write to h5ad file.

        :param str path: Path to where the h5ad file will be saved
        :return: None 
        """
        adata = self.to_anndata()
        return super().write_h5ad(path=path, adata=adata)

    def save(self, path: str, save_prefix: str = ""):
        """
        Save function. Note that the actual KMer histogram matrix is saved in an independent file. This
        independent file will be either `.csv` if the representation is a dense matrix, and it is
        `.npz` if the matrix is sparse. The meta data is saved as a serialized pickle file. Both files
        will be saved in the same folder. In order to avoid accidentally overwriting another matrix
        file in the same folder, you can pass a naming prefix.

        :param str path: Path to meta data pickle file that will be saved. Make sure it contains the file
            suffix `.pkl` or `.pickle`.
        :param str save_prefix: Prefix added to the matrix file, which is saved independently.
        :return: None 
        """
        path = os.path.abspath(path)
        save_dir = "/".join(path.split("/")[:-1])
        if self.kmer_path is None:
            self.kmer_path = os.path.abspath("%s/%s%s_%dmer_mat.%s" % (
                save_dir,
                save_prefix,
                self.matrix_name,
                self.k,
                "csv" if self.k <= MAX_K_DENSE else "npz"
            ))
        if self.k <= MAX_K_DENSE:
            np.savetxt(self.kmer_path, self.kmer_hist, delimiter=",")
        else:
            sp.save_npz(self.kmer_path, self.kmer_hist)
        super(KMerMatrix, self).save(path)

    @classmethod
    def load(cls, path: str, update_kmer_path: str | None = None) -> KMerMatrix:
        """
        Load `KMerMatrix` from file. Note that the KMer object is saved as two files, one representing
        the actual KMer histogram matrix, the other the saved object and meta data as a pickle file.
        The path to the matrix file is hold in the object, so you only need to pass the path to the 
        pickle file. However, if the matrix file path has changed, you can update it here too.

        :param str path: Path to pickle file holding the object and meta data information.
        :param str | None update_kmer_path: If passed, load matrix file that is saved here rather than
            the matrix file that is linked to the object in the pickle file. This must be a `.csv` or 
            `.npz` file.
        :return KMerMatrix: The KMerMatrix object loaded from file.
        """
        path = os.path.abspath(path)
        kmer_mat = cls.load_pickle(path)
        kmer_mat.kmer_path = os.path.abspath(kmer_mat.kmer_path)
        # legacy implementation for loading old version that didn't contain ell-mer length.
        if not hasattr(kmer_mat, "ell"):
            kmer_mat.ell = None
        if update_kmer_path is not None:
            kmer_mat.kmer_path = os.path.abspath(update_kmer_path)

        if kmer_mat.kmer_path.endswith(".csv"):
            kmer_mat.kmer_hist = np.loadtxt(kmer_mat.kmer_path, delimiter=",")
        elif kmer_mat.kmer_path.endswith(".npz"):
            kmer_mat.kmer_hist = sp.load_npz(kmer_mat.kmer_path)
        else:
            raise ValueError("KMer histogram is saved using an unknown file format.")
        
        if not isinstance(kmer_mat.kmer_hist, np.ndarray) and kmer_mat.k <= MAX_K_DENSE:
            kmer_mat.kmer_hist = kmer_mat.kmer_hist.A
        kmer_mat.shape = kmer_mat.kmer_hist.shape
        return kmer_mat


class KMerCollection(KMerClass):
    """
    Collection of individual KMer matrices. Can be instantiated via a list of KMerMatrix or using a setup dictionary

    :param List[KMerMatrix] | None kmer_mat_list: List of KMerMatrix objects
    :param dict | None setup_dict: Dictionary with file paths and setup values. This is expected to represent
        hierarchical information. This is expected to be parsed from a embed file, see documentation for more
        information. The highest hierarchy commonly represent species, which must contain the following
        key:value pairs.

        - `genome_path`: a path to the fasta file
        - `data_path`: a list of paths for the h5ad data files
        - `peak_path`: a path to the peak matrix (or several if passed one per h5ad data path)
        
        There are the following optional key:value pairs possible

        - `cell_annotation`: path or list of paths to cell annotation tables
        - `feature_annotation`: path or list of paths to feature annotation tables
        - `name`: List of names, one per h5ad path. If not specified, set it to `species_{index_of_h5ad}`
        - `cell_id_col`: Column name in `cell_annotation` to sort barcodes accordingly

    :param int k: defines length of k-mers. For example `k=3` creates 3-mers, i.e. overlapping sequence strings of length
        3.
    :param int | None ell: Ell-mer length when using gapped k-mers. When None, no gapped k-mers are used.
    :param List[str] alphabet: Used alphabet that is present in sequence. Default is a `A`, `C`, `G`, and `T`.
    :param int | None n_jobs: Number of CPUs used.
    :param str | None dump_to_dir: directory where KMer histogram tables are dumped to. If none, keep it exclusively
        in memory.
    :param int verbosity: Verbosity level
    :param kwargs: Furhter keyword arguments passed to the `set_kmer_mat_setup_dict` function
    """
    def __init__(
            self,
            kmer_mat_list: List[KMerMatrix] | None = None,
            setup_dict: dict | None = None,
            k: int = 6,
            ell: int | None = None,
            alphabet: List[str] = DNA_ALPHABET,
            n_jobs: int | None = None,
            dump_to_dir: str | None = None,
            verbosity: int = 0,
            **kwargs
    ):
        super(KMerCollection, self).__init__(k=k, ell=ell, verbosity=verbosity, alphabet=alphabet)
        self.kmer_mat_list = None
        self.kmer_mat_idc_df = None
        self.mat_save_path = None
        if kmer_mat_list is not None:
            self.set_kmer_mat_list(kmer_mat_list)
        elif setup_dict is not None:
            self.set_kmer_mat_setup_dict(
                setup_dict, n_jobs=n_jobs, dump_to_dir=dump_to_dir, **kwargs)
    
    @property
    def kmer_hist(self):
        """
        Re-define kmer_hist property as function to dynamically fetch value and avoid double storing.
        """
        if self.kmer_mat_list is None:
            n_kmers = len(self.alphabet)**self.k
            if self.ell is not None:
                n_kmers = n_kmers * binom(self.ell, self.k)
            return np.array((0, n_kmers)) if self.k <= MAX_K_DENSE else sp.csc_array(shape=(0, n_kmers))
        
        stack_lib = np if self.k <= MAX_K_DENSE else sp
        return stack_lib.vstack([kmer_mat.kmer_hist for kmer_mat in self.kmer_mat_list])
    
    @kmer_hist.setter
    def kmer_hist(self, value):
        """
        Dummy setter. Use function `subset_kmer_hist` if you want to change the actual kmer 
        histogram values.
        """
        pass  


    def equalize_kmers(self):
        for kmer_mat in self.kmer_mat_list:
            kmer_mat.equalize_kmers()

    def subset_kmer_hist(
            self, 
            value: np.ndarray | sp.lil_array,
            item: Tuple[
                int | np.ndarray | pd.Series | pl.Series | slice | None,
                int | np.ndarray | slice | None 
            ] | int | np.ndarray | pd.Series | pl.Series | slice | None = (None, None), 
        ):
        """
        K-mer histogram setter that manipulates and sets the values in the corresponding KMerMatrix.
        Note that the interface is equivalent to the functional use of __setitem__. 

        :param np.ndarray | sp.lil_array value: New data values
        :param item: Either tuple, refrencing a particular cell and kmer, or a one dimensional value referencing the cell.
            Indices can be single integer values, slices, or numpy arrays. For cell, youy can also pass polars or pandas series
            representing the cell-identifying barcode.
        """
        if item is None:
            cell_item, kmer_item = np.arange(self.shape[0]), np.arange(self.shape[1])
        if isinstance(item, tuple):
            if len(item) == 2:
                cell_item, kmer_item = item
            elif len(item) == 1:
                cell_item = item
                kmer_item = np.arange(self.shape[1])
            else:
                raise ValueError("__getitem__ only accepts maximally two values: cell index and kmer index.")
        else:
            cell_item = item
            kmer_item = np.arange(self.shape[1])
        
        if len(value.shape) == 1 and value.shape[0] == self.shape[1]:
            value = value.reshape(1, -1)
        if self.k <= MAX_K_DENSE and not isinstance(value, np.ndarray):
            value = value.A
        if self.k > MAX_K_DENSE and not isinstance(value, sp.lil_array):
            value = sp.lil_array(value)

        cell_item = self._convert_item(cell_item, is_kmer_item=False)
        kmer_item = self._convert_item(kmer_item, is_kmer_item=True)
        if (cell_item.shape[0], kmer_item.shape[0]) != value.shape:
            raise ValueError("Selected k-mer histogram must have the same size as the value array. "
                             "Subset k-mer histogram has size (%d, %d), but value array has size %s" 
                             % (cell_item.shape[0], kmer_item.shape[0], value.shape))
        
        value_pos = 0
        for i_mat, (_, _, start, end) in enumerate(self.kmer_mat_idc_df.iter_rows()):
            cell_mat_items = cell_item[np.logical_and(
                cell_item >= start,
                cell_item < end
            )] - start
            if len(cell_mat_items) == 0:
                continue

            n_values = len(cell_mat_items)
            array_type = None
            if self.k > MAX_K_DENSE:
                array_type = type(self.kmer_mat_list[i_mat].kmer_hist)
                # allow subsetting
                self.kmer_mat_list[i_mat].kmer_hist = sp.lil_array(self.kmer_mat_list[i_mat].kmer_hist)
            self.kmer_mat_list[i_mat].kmer_hist[np.ix_(cell_mat_items.flatten(), kmer_item)] = value[value_pos:value_pos + n_values]
            if self.k > MAX_K_DENSE:
                # convert back
                self.kmer_mat_list[i_mat].kmer_hist = array_type(self.kmer_mat_list[i_mat].kmer_hist)

            value_pos += n_values
            if value_pos == value.shape[0]:
                return

    def __getitem__(
        self, 
        item: Tuple[
            int | np.ndarray | pd.Series | pl.Series | slice | None,
            int | np.ndarray | slice | None 
        ] | int | np.ndarray | pd.Series | pl.Series | slice | None = (None, None)
        ) -> KMerCollection:
        """
        Subsetting KMerCollection
        """
        if isinstance(item, tuple):
            if len(item) == 2:
                cell_item, kmer_item = item
            elif len(item) == 1:
                cell_item = item
                kmer_item = None
            else:
                raise ValueError("__getitem__ only accepts maximally two values: cell index and kmer index.")
        else :
            cell_item = item
            kmer_item = None

        new_self = KMerCollection()
        new_self.k = self.k
        new_self.ell = self.ell
        _, new_self.pattern_offset_dict = get_kmer_names(k=self.k, ell=self.ell, alphabet=self.alphabet, return_offset=True)
        new_self.verbosity = self.verbosity
        new_self.kmer_mat_list = []
        cell_item = self._convert_item(cell_item, is_kmer_item=False)
        kmer_item = self._convert_item(kmer_item, is_kmer_item=True)
        for i_mat, (species, mat_name, start, end) in enumerate(self.kmer_mat_idc_df.iter_rows()):
            if isinstance(cell_item, int) and start <= cell_item < end:
                new_self.kmer_mat_list = [self.kmer_mat_list[i_mat][cell_item - start, kmer_item]]
                new_self._set_idc()
                return new_self
            elif isinstance(cell_item, np.ndarray):
                if cell_item.dtype == "int":
                    cell_mat_items = cell_item[np.logical_and(
                        cell_item >= start,
                        cell_item < end
                    )]
                else:
                    cell_mat_items = pd.Index(cell_item).intersection(self.kmer_mat_list[i_mat].barcodes)
                if cell_mat_items.shape[0] == 0:
                    continue
                new_self.kmer_mat_list.append(self.kmer_mat_list[i_mat][cell_mat_items - start, kmer_item])
        if isinstance(cell_item, np.ndarray) and cell_item.dtype != "int":
            cell_item = np.where(np.isin(self.barcodes, pd.Index(cell_item).intersection(self.barcodes)))
        new_self.clustering, new_self.dr, new_self.x_umap = self._subset_dicts(cell_item)
        new_self._set_idc()
        return new_self

    def __getstate__(self):
        """
        Get state for pickling. Remove kmer histogram and kmer mat list as they are save independently when 
        writing to file

        :return dict state:
        """
        state = self.__dict__.copy()
        # don't return kmer_mat_list, therefore it's not pickled
        del state["kmer_mat_list"]
        # don't return kmer_mat_idc_df, therefore it's not 
        # idc df is set dynamically. this avoid complications with pickling polars
        del state["kmer_mat_idc_df"]
        # bugfix for older files where kmer_hist was saved in object directly
        if "kmer_hist" in state:
            # don't return kmer_hist, therefore it is not pickled
            del state["kmer_hist"]
        return state
    
    def __str__(self) -> str:
        """To string function"""
        s = "Gapped " if self.ell is not None else ""
        s += "KMerCollection containing %d samples and %d species with k=%d" % (
            len(self.kmer_mat_list), 
            len(self.kmer_mat_idc_df["species"].unique()), 
            self.k
        )
        if self.ell is not None:
            s += " and ell=%d" % self.ell
        s += "\n(%d, %d)" % self.shape
        return s
    
    def __repr__(self) -> str:
        """Call string representation"""
        return self.__str__()
    
    def __iter__(self):
        """Overwrite default iterator"""
        return chain(*[kmer.__iter__() for kmer in self.kmer_mat_list])
    
    def __add__(self, other: KMerClass | np.ndarray | sp.csc_matrix | int | float):
        """
        Add `other` to kmer histogram

        :param KMerClass | np.ndarray | sp.csc_matrix | int | float other: Value added to histogram
        """
        if isinstance(other, KMerClass):
            other = other.kmer_hist
        self.subset_kmer_hist(self.kmer_hist + other, item=None)

    def __sub__(self, other: KMerClass | np.ndarray | sp.csc_matrix | int | float):
        """
        Subtract `other` from kmer histogram

        :param KMerClass | np.ndarray | sp.csc_matrix | int | float other: Value subtracted from histogram
        """
        if isinstance(other, KMerClass):
            other = other.kmer_hist
        self.subset_kmer_hist(self.kmer_hist - other, item=None)

    def __mul__(self, other: KMerClass | np.ndarray | sp.csc_matrix | int | float):
        """
        Multiply `other` to kmer histogram. If passed as array or matrix, perform element-wise multiplication

        :param KMerClass | np.ndarray | sp.csc_matrix | int | float other: Value multiplied to histogram
        """
        if isinstance(other, KMerClass):
            other = other.kmer_hist
        self.subset_kmer_hist(self.kmer_hist * other, item=None)
    
    def _set_shape(self):
        """Setter function for shape as `kmer_hist` is not a variable anymore but a function call."""
        shape_array = np.stack([np.array(list(kmer_mat.kmer_hist.shape)) for kmer_mat in self.kmer_mat_list])
        if np.any(shape_array[:, 1] != shape_array[0, 1]):
            raise ValueError("Not all KMerMatrices have the same shape. Cannot combine KMerMatrices to KMerCollection")
        
        return (np.sum(shape_array[:, 0]), shape_array[0, 1])
    
    def _set_idc(self):
        """
        Save start and end indices per converted h5ad matrix to table for easy access
        
        :return: None
        """
        barcodes = []
        if self.kmer_mat_list is not None:
            kmer_names = np.array([kmer_mat.matrix_name for kmer_mat in self.kmer_mat_list])
            if len(np.unique(kmer_names)) != len(self.kmer_mat_list):
                if self.verbosity > 1:
                    print("Found matrix duplicates, add increment to make them unique") # TODO add merge possiblilty
                index = {}
                for kmer_mat in self.kmer_mat_list:
                    if np.sum(kmer_names == kmer_mat.matrix_name) > 1:
                        if kmer_mat.matrix_name in index:
                            index[kmer_mat.matrix_name] += 1
                        else:
                            index[kmer_mat.matrix_name] = 0
                        kmer_mat.matrix_name = kmer_mat.matrix_name + ("_%d" % index[kmer_mat.matrix_name])
            matrix_idc = []
            start_idx = 0
            for i_kmer_mat, kmer_mat in enumerate(self.kmer_mat_list):
                mat_name = kmer_mat.matrix_name
                species = kmer_mat.species
                # create new data entry
                matrix_idc.append((species, mat_name, start_idx, start_idx + kmer_mat.shape[0]))
                start_idx += kmer_mat.shape[0]
                barcodes.extend((str(kmer_mat.matrix_name) + pl.Series(pd.Series(kmer_mat.barcodes)).cast(pl.Utf8)).to_list())
            # save as polars data frame
            self.kmer_mat_idc_df = pl.DataFrame(pd.DataFrame(
                matrix_idc if len(matrix_idc) > 0 else None, 
                columns=["species", "matrix name", "start index", "end index"]
            ))
            self.barcodes = pd.Index(barcodes)
        self.shape = self._set_shape()

    def set_normalization(
            self, 
            normalization: Callable | str | None = "centered_sum",
            ord_vec: None | List | np.ndarray | pl.Series | pd.Series = None,
            prepare: Callable | None = None,
            **kwargs
        ):
        """
        Set and run normalization for each KMerMatrix independently.
        Note that this will not create a copy, and the kmer histograms
        are overwritten. Running several normalizations in a row is therefore not possible.

        Note that we have tested different normalizations extensively, and we highly recommend to 
        use only `none` (default), `sum_norm`, and `centered_sum`. You should be very sure of what
        you're doing when using another normalization.
        
        :param Callable | str | None normalization: pass one of the following.

            - string identifying pre-implemented normalization, such as
                `none` | `max_norm` | `sum_norm` | `center_norm` | `centered_sum` | `centered_max` | 
                `centered_uniform_sum` | `centered_uniform_max`. Unless you know what you're doing, choose
                `centered_sum`
            - your own callable, which will be wrapped into a spyce normalization function
            - `None`, when no normalization should be performed

        :param  None | List | np.ndarray | pl.Series | pd.Series ord_vec: Ordinal vector with respect to which
            the data is normalized. With the provided methods, this is only used when the data is centered, or the
            standard deviation normalized. When passing an exclusively cell-based normalization (e.g. `sum_norm`),
            during which each cell row is normalized independently, this parameter has no effect. If not provided
            or `None`, normalize over entire matrix.
        :param Callable | None prepare: If passed, computes global values over entire histogram. Return value must be a dictionary
            that contains keyword parameters for the normalisation function. If the `prepare` dictionary also contains an
            `ord_vec` key or if the `ord_vec` value is explicitly set, the dictionar must be of the form
            
            .. code-block:: python
            
                {
                    "label1_in_vec": {"param1": param1_1, "param2": param2_1},
                    ...
                    "labeln_in_vec": {"param1": param1_n, "param2": param2_n},
                }
            
            
            where you need to replace the names and values according to your normalization function.
        :param kwargs: Other paramters passed to normalization function
        :return: None
        """
        if prepare is not None:
            prep_kwargs = prepare(self.kmer_hist, **kwargs)
        else:
            prep_kwargs = {}
        if "ord_vec" in prep_kwargs:
            ord_vec = prep_kwargs["ord_vec"]
            del prep_kwargs["ord_vec"]

        if ord_vec is None:
            # self.kmer_mat_list
            kmer_iter = tqdm(
                self.kmer_mat_list,
                total=len(self.kmer_mat_list),
                desc="Normalize KMer matrices"
            ) if self.verbosity > 0 else self.kmer_mat_list
            for kmer_mat in kmer_iter:
                kmer_mat.set_normalization(normalization, **prep_kwargs, **kwargs)
        else:
            self._set_idc()  # make sure that indices are correctly set
            norm_kmer_mat = normalize_over_ord_vec(
                self.kmer_hist,
                vec=ord_vec,
                normalization=normalization,
                **prep_kwargs,
                **kwargs
            )
            self.kmer_mat_idc_df = self.kmer_mat_idc_df.sort("start index")
            for i_kmer_entry, kmer_entry in enumerate(self.kmer_mat_idc_df.iter_rows(named=True)):
                before_shape = self.kmer_mat_list[i_kmer_entry].shape
                self.kmer_mat_list[i_kmer_entry].kmer_hist = norm_kmer_mat[
                    int(kmer_entry["start index"]):
                    int(kmer_entry["end index"])
                ]
                if before_shape != self.kmer_mat_list[i_kmer_entry].shape:
                    raise RuntimeError("KMer histogram shape has changed after normalizing. "
                                       "It is likely that this is due to an internal bug. "
                                       "Please report on %s" % BUG_REPORT) 

        self._set_idc()

    def remove_species_effect(
            self, 
            batch_vec: np.ndarray |  pl.Series  | pd.Series | List ,
            dr_key: str | None = "pca", 
            save_name: str = "pca_correction",
            algorithm: str = "harmony",
            **kwargs
    ):
        """
        Remove species-specific bias via using batch correction methods. We implemented and tested two methods:
        Harmony and Iterative Closest Point (ICP). Harmony can correct several samples at the same time, 
        ICP can only match a source data set with a target data set. 

        :param np.ndarray |  pl.Series  | pd.Series | List batch_vec: Vector, array or list that contains 
            information about the cell groups that need to be corrected. This can be with respect to 
            species or sample. If `algorithm=harmony` this can be any ordinal vector. If `algorithm=ICP`,
            then it must be a binary vector, where `True` represents the target data set and all other
            cells must be corrected such that they are as close as possible to the target data set.
        :param str dr_key: Dimensionality reduction to be used. If `dr_key` does not exist, run new PCA and
            save under the passed key.
        :param str save_name: The name where the adjusted principal components will be saved. You can access it
            specifically via `self.dr[save_name]`.
        :param str algorithm: The correction algorithm to be used. You can choos between `harmony` for
            the Harmony batch correction | `ICP` for an adapted iterative closest point integration.
        :param kwargs: Other keyword parameters that are passed to the correction algorithm
        """
        n_default_comp = 30

        self._check_dr()
        # set default values
        if algorithm.lower() == "icp":
            correct_fun = icp
        elif algorithm.lower() == "harmony":
            correct_fun = harmony_correct
        else:
            raise ValueError("Correction function (passed as `algorithm`) not understood. "
                             "Please pass one of the following: harmony | ICP.")
        
        if dr_key is None:
            data = self.kmer_hist
        else:
            if dr_key not in self.dr:
                warnings.warn("Species correction can only be performed on a PCA matrix, "
                            "but your `dr_key` doesn't exist. Perfom PCA for you with %d components. "
                            "The result will be saved under %s" % (n_default_comp, dr_key))
                self.reduce_dimensionality(
                    algorithm="pca",
                    save_name=dr_key,
                    n_pca_components=n_default_comp
                )
            data = self.dr[dr_key]
        self.dr[save_name] = correct_fun(
            data,
            target_vec=batch_vec,
            verbosity=self.verbosity - 1,
            **kwargs
        )

    def merge_kmer_collections(self, kmer_collect_list: List[KMerCollection]):
        """
        Add a list of other `KMerCollection`s to this `KMerCollection` object, and update indices
        and matrices accordingly.

        :param List[KMerCollection] kmer_collect_list: List of `KMerCollection` objects.
        :return: None.
        """
        if self.verbosity > 1:
            warnings.warn("Merge KMer collections. Clustering, UMAP coordinates, and dimensionality reductions are not valid anymore. "
                  "Re-run if needed.") 
        self.clustering = None
        self.x_umap = None
        self.dr = None
        if self.kmer_mat_list is None:
            self.kmer_mat_list = []
        for i_kmer_collect, kmer_collect in enumerate(kmer_collect_list):
            # error breakdown
            if kmer_collect.k != self.k:
                raise ValueError("Cannot add %d. KMerCollection. k size differ." % i_kmer_collect)
            elif kmer_collect.ell is None and self.ell is not None:
                raise ValueError("self is gapped, but KMer collection %d is not." % i_kmer_collect)
            elif kmer_collect.ell is not None and self.ell is None:
                 raise ValueError("KMer collection %d is gapped, but self is not." % i_kmer_collect)
            elif kmer_collect.ell is not None and self.ell is not None and self.ell != kmer_collect.ell:
                raise ValueError("KMer collection %d is diffrently gapped to self (ell %d versus ell %d)"
                                  % (i_kmer_collect, kmer_collect.ell, self.ell))
            elif kmer_collect.shape[1] != self.shape[1]:
                raise ValueError("KMer collection have different shapes. Have you subset them?")
            else:
                if any(kmer.k != self.k for kmer in kmer_collect.kmer_mat_list):
                    raise ValueError("KMerMatrix in %d. KMerCollection has a differen k size than current "
                                     "KMerCollection." % i_kmer_collect)
                id_list = [id(kmer_mat) for kmer_mat in self.kmer_mat_list]
                for kmer_mat in kmer_collect.kmer_mat_list:
                    if id(kmer_mat) not in id_list:
                        self.kmer_mat_list.append(kmer_mat)
                    else:
                        warnings.warn("Found duplicated KMerMatrix objects. Only a single reference is added. If you "
                                      "want to add the same KMerMatrix several times, add a copy first.")
                

        self._set_idc()
                
    def set_kmer_mat_list(self, kmer_mat_list: List[KMerMatrix]):
        """
        Set KMer collection list by passing a list of already created KMer matrices
        
        :param List[KMerMatrix] kmer_mat_list: List of KMerMatrix objects
        :return: None
        """
        self.kmer_mat_list = kmer_mat_list
        for kmer_mat in self.kmer_mat_list:
            if kmer_mat.ell != self.ell:
                raise ValueError("Passed KMerMatrix objects differ in their ell values. All KMer matrices must be "
                                 "based on the same ell")
            if kmer_mat.k != self.k:
                raise ValueError("Passed KMerMatrix objects differ in their k values. All KMer matrices must be "
                                 "based on the same k")
            if len(self.alphabet) != len(kmer_mat.alphabet) or not all(
                letter1 == letter2 for letter1, letter2 in zip(sorted(self.alphabet), sorted(kmer_mat.alphabet))
            ):
                raise ValueError("KMer histograms were created based on different alphabets. They cannot be combined.")
        self._set_idc()

    def set_kmer_mat_setup_dict(
            self,
            setup_dict: dict,
            n_jobs: int | None = None,
            annotation_has_header: bool = True,
            correct_gc: bool = True,
            annotation_sep: str = "\t",
            n_policy: str = "remove",
            mask_rep: bool = False,
            normalization: Callable | str | None = "centered_sum",
            dump_to_dir: str | None = None,
            **kwargs

    ):
        """
        Create KMerMatrix objects and combine to collection based on setup dictionary.

        :param dict | None setup_dict: Dictionary with file paths and setup values. This is expected to represent
            hierarchical information. This is expected to be parsed from an `.embed` file, see documentation for more
            information. The highest hierarchy commonly represent species, which must contain the following
            key:value pairs.

            - `genome_path`: a path to the fasta file
            - `data_path`: a list of paths for the h5ad data files
            - `peak_path`: a path to the peak matrix (or several if passed one per h5ad data path)
            
            There are the following optional key:value pairs possible
            
            - `cell_annotation`: path or list of paths to cell annotation tables
            - `feature_annotation`: path or list of paths to feature annotation tables
            - `name`: List of names, one per h5ad path. If not specified, set it to `species_{index_of_h5ad}`
            - `cell_id_col`: Column name in `cell_annotation` to sort barcodes accordingly
        
        :param int n_jobs: Number of CPUs used
        :param bool annotation_has_header: Flag that indicates whether the cell annotation and feature annotation
            tables contain a header (if applicable).
        :param bool correct_gc: If set, correct for GC content bias via sampling with replacement per cell to match GC
            content distribution over all accessible peaks.
        :param str annotation_sep: Separator of the cell annotation and feature annotation tables (if applicable)
        :param str n_policy: Defines how to deal with kmers that contain undeterministic nucleotides marked with the
            letter `N`. Choose between remove | replace | keep.

            - `remove` filters out kmers with N occurrences.
            - `replace` replaces kmers that contain Ns with all possibilities
            - `keep` keeps the Ns untreated

        :param bool mask_rep: If set to true, mask repetitive sequences marked with lower case letters in fasta.
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
        
        :param str | None dump_to_dir:  directory where KMer histogram tables are dumped to. If none, keep it exclusively
            in memory.
        :param kwargs: Other keyword arguments that are passed the `KMerMatrix` constructor
        """
        if dump_to_dir is not None:
            Path(dump_to_dir).mkdir(exist_ok=True, parents=True)
        self.kmer_mat_list = []
        for species, species_dict in setup_dict.items():
            if self.verbosity > 0:
                print("Process species %s" % species)
            # collect mandatory values
            genome_path = species_dict["genome_path"]
            data_path_list = species_dict["data_path"]
            if isinstance(data_path_list, str):
                data_path_list = [data_path_list]
            peak_bed_list = species_dict["peak_path"]
            if isinstance(peak_bed_list, str):
                peak_bed_list = [peak_bed_list] * len(data_path_list)
            elif isinstance(peak_bed_list, list) and len(peak_bed_list) == 1:
                peak_bed_list = peak_bed_list * len(data_path_list)
            if len(data_path_list) != len(peak_bed_list):
                raise ValueError("There must be either one peak_bed for all data files "
                                 "or as many peak_bed values as there are data values.")

            # collect optional values
            cell_annotation_list = species_dict.get("cell_annotation", None)
            feature_annotation_list = species_dict.get("feature_annotation", None)
            data_name_list = species_dict.get("name", None)
            cell_id_col = species_dict.get("cell_id_col", None)
            white_list = species_dict.get("white_list", None)

            for i_data, (data_path, peak_bed_path) in enumerate(zip(data_path_list, peak_bed_list)):
                if self.verbosity > 0:
                    print("\tProcess data %d / %d" % (i_data + 1, len(data_path_list)))

                # fetch optional data if they were set
                if cell_annotation_list is None:
                    cell_annotation_path = None
                elif isinstance(cell_annotation_list, list):
                    cell_annotation_path = cell_annotation_list[i_data]
                else:
                    cell_annotation_path = cell_annotation_list

                if feature_annotation_list is None:
                    feature_annotation_path = None
                elif isinstance(feature_annotation_list, list):
                    feature_annotation_path = feature_annotation_list[i_data]
                else:
                    feature_annotation_path = feature_annotation_list

                if data_name_list is None:
                    matrix_name = "%s_%d" % (species, i_data)
                elif isinstance(data_name_list, list):
                    matrix_name = data_name_list[i_data]
                else:
                    matrix_name = data_name_list

                if dump_to_dir is not None:
                    dump_to = "%s/%s.csv" % (dump_to_dir, matrix_name)
                else:
                    dump_to = None
                # create new KMerMatrix obj
                self.kmer_mat_list.append(KMerMatrix(
                    genome_path=genome_path,
                    data_path=data_path,
                    feature_bed_path=peak_bed_path,
                    white_list=white_list,
                    cell_annotation_path=cell_annotation_path,
                    feature_annotation_path=feature_annotation_path,
                    k=self.k,
                    ell=self.ell,
                    normalization=normalization,
                    species=species,
                    correct_gc=correct_gc,
                    matrix_name=matrix_name,
                    annotation_has_header=annotation_has_header,
                    annotation_sep=annotation_sep,
                    verbosity=self.verbosity,
                    n_policy=n_policy,
                    mask_rep=mask_rep,
                    cell_id_col=cell_id_col,
                    alphabet=self.alphabet,
                    dump_to=dump_to,
                    n_jobs=n_jobs,
                    verbosity_indent="\t\t",
                    **kwargs
                ))

        if self.verbosity > 0:
            print("Combine KMer matrices and determine indices")
        self._set_idc()

    def select_features(
            self,
            n_features: int = 15000,
            save_name: str = "selected_features"
    ):
        """
        Updated algorithm for the KMer collection. Select most variable features in the KMer matrix by calculating the variance. 
        The result is saved in `self.dr[save_name]`.

        :param int n_features: Number of most variable k-mers selected.
        :param str save_name: Name used for saving the result in the object's `dr` dictionary.
        """
        self._check_dr()
        mean_array = np.zeros(self.shape[1])
        var_array = np.zeros(self.shape[1])
        n_vals = 0
        kmer_mat_iter = tqdm(
            enumerate(self.kmer_mat_list),
            total=len(self.kmer_mat_list),
            desc="Calculate batch variance"
        ) if self.verbosity > 0 else enumerate(self.kmer_mat_list)
        for i_kmer_mat, kmer_mat in kmer_mat_iter:
            mat = kmer_mat.kmer_hist
            if not isinstance(mat, np.ndarray):
                mat = mat.A
            kmer_mean = mat.mean(axis=0).flatten()
            kmer_var = mat.var(axis=0).flatten()
            n_mat = kmer_mat.kmer_hist.shape[0]
            if i_kmer_mat == 0:
                mean_array = kmer_mean.copy()
                var_array = kmer_var.copy()
            else:
                var_array = (((n_mat - 1) * kmer_var + (n_vals - 1) * var_array) / (n_mat + n_vals - 1)
                             + n_mat * n_vals * (kmer_mean - mean_array)**2 / ((n_mat + n_vals) * (n_mat + n_vals - 1)))
                mean_array = (n_mat * kmer_mean + n_vals * mean_array) / (n_mat + n_vals)
            n_vals += n_mat

        sort_idc = np.argsort(var_array)
        selected_kmer = np.zeros((self.shape[0], n_features))
        n_vals = 0

        kmer_mat_iter = tqdm(
            enumerate(self.kmer_mat_list),
            total=len(self.kmer_mat_list),
            desc="Fetch most variable k-mers"
        ) if self.verbosity > 0 else enumerate(self.kmer_mat_list)

        for i_kmer_mat, kmer_mat in kmer_mat_iter:
            mat = kmer_mat.kmer_hist
            if not isinstance(mat, np.ndarray):
                mat = mat.A
            selected_kmer[n_vals:n_vals + kmer_mat.shape[0]] = mat[:, sort_idc[::-1][:n_features]]
            n_vals += kmer_mat.shape[0]
        self.dr[save_name] = selected_kmer

    def fetch_cell_annotation(
            self,
            idc: np.ndarray | None = None,
    ) -> pl.DataFrame | None:
        """
        Fetch cell annotation from all KMerMatrix objects and combine to a single table.
        This requires that all cell annotation tables have the same layout.

        :param np.ndarray | None idc: If passed, return only annotation of these indices. Note that
            they are positional indices (i.e. integer values), not barcodes or cell IDs.
        :return pl.DataFrame | None: If cell tables follow the same layout, return concatenated
            polars data frame. Otherwise, return `None` and raise a warning (but no error).
        """
        cell_annotation_list = []
        if idc is None:
            for mat in self.kmer_mat_list:
                cell_annotation_list.append(mat.fetch_cell_annotation())
        else:
            for i_mat_range, mat_range in enumerate(
                self.kmer_mat_idc_df.sort("start index").iter_rows(named=True)
            ):
                mat_idc = idc[np.logical_and(
                    idc >= mat_range["start index"],
                    idc < mat_range["end index"],
                )] -  mat_range["start index"]
                cell_annotation_list.append(self.kmer_mat_list[i_mat_range].fetch_cell_annotation(
                    idc=mat_idc
                ))
        try:
            return pl.concat(cell_annotation_list)
        except pl.ShapeError:
            warnings.warn("Not all cell annotation tables follow the same layout. To fetch all cell "
                             "annotations over the KMerCollection, all tables need to have the same"
                             "columns and column order.")
            return None
        
    def transpose_to_same(self, metric: str = "euclidean", verbosity: int = 0):
        """
        Find kmer histogram representation that decreases the distance between the matrix average. 
        The first kmer histogram is arbitrarily used as reference. Default is the Euclidean distance. 
        Any metric accepted by `sklearn`'s `pairwise_distances` is accepted. For more information
        see  https://scikit-learn.org/1.5/modules/generated/sklearn.metrics.pairwise_distances.html.
        
        :param str metric: Metric name. All `sklearn` metrics are accepted. See 
            https://scikit-learn.org/1.5/modules/generated/sklearn.metrics.pairwise_distances.html for more 
            information
        :param int verbosity: Verbosity level. 
        """
        if len(self.kmer_mat_list) == 1:
            return
        avg_kmer = self.kmer_mat_list[0].kmer_hist.mean(axis=0).reshape(1, -1)
        if not isinstance(avg_kmer, np.ndarray):
            avg_kmer = np.asarray(avg_kmer.todense()).reshape(1, -1)

        kmer_iter = tqdm(
            range(1, len(self.kmer_mat_list)),
            total=len(self.kmer_mat_list) - 1,
            desc="Adaptation progress"
        ) if verbosity > 0 else range(1, len(self.kmer_mat_list))

        for i_kmer_mat in kmer_iter:
            avg_other_kmer = self.kmer_mat_list[i_kmer_mat].kmer_hist.mean(axis=0).reshape(1, -1)
            if not isinstance(avg_other_kmer, np.ndarray):
                avg_other_kmer = np.asarray(avg_other_kmer.todense()).reshape(1, -1)
            kmer_corr = pairwise_distances(
                np.asarray(avg_kmer), 
                np.asarray(avg_other_kmer),
                metric=metric
            ).flatten()
            self.kmer_mat_list[i_kmer_mat].kmer_transpose()
            avg_other_kmer_t = self.kmer_mat_list[i_kmer_mat].kmer_hist.mean(axis=0).reshape(1, -1)
            if not isinstance(avg_other_kmer_t, np.ndarray):
                avg_other_kmer_t = np.asarray(avg_other_kmer_t.todense()).reshape(1, -1)
            kmer_trans_corr = pairwise_distances(
                np.asarray(avg_kmer), 
                np.asarray(avg_other_kmer_t),
                metric=metric
            ).flatten()
            if float(kmer_trans_corr) <= float(kmer_corr):
                continue
            else:
                # transpose back
                self.kmer_mat_list[i_kmer_mat].kmer_transpose()
    
    def transfer_labels(
            self,
            other: KMerClass,
            cell_anno: str | pd.Series | pl.Series | np.ndarray | List[str],
            dr_name: str | None = None,
            other_dr_name: str | None = None,
            verbosity_indent: str = "",
            **kwargs
        ) -> pl.Series:
        """
        Create a KD tree from query data, fetch the n clostest neighbors, and count most common cell label

        :param KMerClass other: Target KMer object
        :param str | pd.Series | pl.Series | np.ndarray | List[str] cell_anno: If passed as string, it's
            the column in cell annotation data that is used for label transfer. If passed as an accepted 
            iterable, then it is expected as the cell annotation sorted according to the barcodes.
        :param str | None dr_name: key for dimensionality reduction in query KMer object (self). If none, 
            compute KD tree based on complete KMer histogram
        :param str | None other_dr_name: key for dimensionality reduction in target KMer object. If none,
            compute KD tree based on complete KMer histogram
        :param str verbosity_indent:  Prefix for verbosity output to indicate that this routine was called within
            another function
        :param kwargs: Other keyword-value pairs that are passed as paramters to the super `transfer_labels` function
        :return pl.Series: transfered labels.
        """
        if isinstance(cell_anno, str):
            cell_anno_df = self.fetch_cell_annotation()[cell_anno]
        else:
            cell_anno_df = cell_anno
        return super(KMerCollection, self).transfer_labels(
            other=other,
            cell_labels=cell_anno_df,
            dr_name=dr_name,
            other_dr_name=other_dr_name,
            verbosity_indent=verbosity_indent,
            **kwargs
        )
    
    def to_anndata(self) -> ad.AnnData:
        """
        Wrapper for transforming the data to an AnnData object. Fetches also the cell annotation if set.

        :return ad.AnnData: Return data as AnnData object.
        """
        cell_annotation = self.fetch_cell_annotation()
        return super(KMerCollection, self).to_anndata(
            self.barcodes,
            obs=cell_annotation,
        )
    
    def write_h5ad(self, path: str):
        """
        Convert object to AnnData and write to h5ad file.

        :param str path: Path to where the h5ad file will be saved
        :return: None 
        """

        adata = self.to_anndata()
        return super().write_h5ad(path=path, adata=adata)

    def save(
            self,
            path: str,
            save_prefix: str = "",
            reset_matpath: bool = False,
            mat_save_path: str | dict | None = None
    ):
        """
        Save function. Note that there will be several files created: one for the KMerCollection, holding 
        the object information; and two per KMerMatrix the actual KMer histogram matrix and the object meta
        data. To keep things clean, the `KMerCollection` file and the `KMerMatrix` files can be saved at different
        locations (ideally `KMerMatrix` files are in a subfolder.) You can also use a save prefix
        that is used for the `KMerMatrix` files.

        :param str path: Path to meta data pickle file that will be saved. Make sure it contains the file
            suffix `.pkl` or `.pickle`.
        :param str save_prefix: Prefix added to the `KMerMatrix` files, which are saved independently. This
            will affect both files if `mat_save_path` is not a `dict`, and only the matrix files otherwise.
        :param bool reset_matpath: If set, write new matrix files at passed path instead of overwriting old 
            matrices.
        :param str | dict | None mat_save_path: If not passed, create subfolder `matrices` that contains the
            `KMerMatrix` files. If passed as string, it must be a path a directory, where all
            `KMerMatrix` files will be stored. If passed as a `dict`, each KMerMatrix (identified by the 
            matrix name) must have an entry to the to-be-created `KMerMatrix` pickle file.
        :return: None 
        """
        path = os.path.abspath(path)
        if reset_matpath:
            self.mat_save_path = None
        if self.kmer_mat_list is not None:
            if self.mat_save_path is None:
                if mat_save_path is None:
                    mat_save_path = "/".join(path.split("/")[:-1]) + "/matrices/"
                if isinstance(mat_save_path, str):
                    Path(mat_save_path).mkdir(exist_ok=True, parents=True)
                    mat_save_path = {mat.matrix_name: "%s/%s%s.pkl" % (mat_save_path, save_prefix, mat.matrix_name)
                                     for mat in self.kmer_mat_list}
                if isinstance(mat_save_path, dict):
                    self.mat_save_path = mat_save_path
                else:
                    raise ValueError("When `mat_save_path` is passed, set it to either str or dict")

            for mat in self.kmer_mat_list:
                try:
                    mat.save(self.mat_save_path[mat.matrix_name], save_prefix=save_prefix)
                except KeyError:
                    raise KeyError("No path set for matrix %s" % mat.matrix_name)

        super(KMerCollection, self).save(path)

    @classmethod
    def load(cls, path: str, update_dict: dict[str, str] | None = None, n_jobs: int = 1) -> KMerCollection:
        """
        Load `KMerCollection` from file. Note that the actual object is separated into several files, one
        `KMerCollection` pickle file, one two files per `KMerMatrix`. Paths for loading and incorporating
        `KmerMatrix` files are saved in the `KMerCollection`, so you only need to pass the path to this
        pickle file. If you have changed the `KMerMatrix` objects independently or moved them, you can 
        update them by passing the `update_dict`.

        :param str path: Path to `KMerCollection` pickle file.
        :param dict[str, str] | None update_dict: Python `dict` holding for each `KMerMatrix` object
            (identified by their name as key) a corresponding updated path.
        :param int n_jobs: Number of jobs used for loading. Note that this is still experimental, and we generally
            recommend using only one CPU.
        :return KMerCollection: The loaded KMerCollection object.
        """
        with multiprocessing.get_context("spawn").Pool(processes=n_jobs) as pool:
            path = os.path.abspath(path)
            kmer_collect = cls.load_pickle(path)
            kmer_collect.kmer_mat_list = []
            kmer_collect.kmer_mat_idc_df = None
            if not hasattr(kmer_collect, "ell"):
                kmer_collect.ell = None
                kmer_collect.pattern_offset_dict = None

            if update_dict is not None:
                kmer_collect.mat_save_path = update_dict
            
            mat_entry_iter = tqdm(
                enumerate(kmer_collect.mat_save_path.items()),
                total=len(kmer_collect.mat_save_path),
                desc="Load KMerMatrices"
            ) if kmer_collect.verbosity > 0 else enumerate(kmer_collect.mat_save_path.items())

            load_list = []
            for i_mat_entry, (mat_name, mat_path) in mat_entry_iter:
                try:
                    load_path = os.path.abspath(mat_path)
                except KeyError:
                    raise KeyError("No entry found for KMer matrix %s. When passing an update_dict, "
                                "pass one path per matrix." % mat_name)
                
                suffix = ".pkl" if ".pkl" in load_path else ".pickle"
                if n_jobs <= 1 or n_jobs is None:
                    load_list.append(
                        KMerMatrix.load(load_path, update_kmer_path=mat_path.replace(suffix, "_%dmer_mat.csv" % kmer_collect.k))
                    )
                else:
                    load_list.append((i_mat_entry, pool.apply_async(
                        KMerMatrix.load, (load_path, mat_path.replace(suffix, "_%dmer_mat.csv" % kmer_collect.k), )
                    )))
            if n_jobs is not None and n_jobs > 1:
                pbar = tqdm(total=len(load_list), desc="Fetch results") if kmer_collect.verbosity > 0 else None
                load_list = fetch_async_result(load_list, process_bar=pbar)
                load_list = [x[1] for x in sorted(load_list, key=lambda _: _[0])]

            kmer_collect.kmer_mat_list = load_list
            kmer_collect._set_idc()
        return kmer_collect

