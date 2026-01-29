from __future__ import annotations

from typing import Dict, List, Tuple, Union
from tqdm import tqdm
from multiprocessing.pool import AsyncResult
import time
import warnings
from sklearn.neighbors import KDTree
from sklearn.metrics.pairwise import euclidean_distances
from scipy import sparse as sp
import numpy as np
from itertools import product, combinations
from Bio.Seq import Seq
from pandas import Series as pd_Series
import pandas as pd
from polars import Series as pl_Series

from spyce.constants import DNA_ALPHABET
from spyce.dataType import DataLoadingStructure, KMerHistogramObject


class TopicNode(DataLoadingStructure):
    """
    Node class for parsing framework-specific .embed files, which provide hierarchical information by indent
    Instances of this class are nodes in a topic tree that represents the hierarchical structure of the .embed files
    
    :param str indented_line: entire line of file as string including indents
    """
    def __init__(self, indented_line: str):
        self.children = []
        self.level = len(indented_line) - len(indented_line.lstrip())
        self.text = indented_line.strip()

    def add_children(self, topic_nodes: List):
        """
        Add topic children to node
        
        :param List topic_nodes: Topic nodes that are added as children
        :return: None
        """
        childlevel = topic_nodes[0].level
        while topic_nodes:
            tp = topic_nodes.pop(0)
            if tp.level == childlevel:  # add node as a child
                self.children.append(tp)
            elif tp.level > childlevel:  # add nodes as grandchildren of the last child
                topic_nodes.insert(0, tp)
                self.children[-1].add_children(topic_nodes)
            elif tp.level <= self.level:  # this node is a sibling, no more children
                topic_nodes.insert(0, tp)
                return

    def as_dict(self) -> Dict | str:
        """
        Convert hierarchical tree structure of which this node is root as dict
        
        :return Dict | str: tree structure as dict. If leaf node return string
        """
        if len(self.children) > 1:
            child_dict = {} 
            child_list = []
            for tp in self.children:
                tp_dict = tp.as_dict()
                try:
                    child_dict = dict(**child_dict, **tp_dict)
                except TypeError:
                    child_list.append(tp_dict)
            return {self.text: child_dict} if len(child_list) == 0 else {self.text: child_list}
        elif len(self.children) == 1:
            return {self.text: self.children[0].as_dict()}
        else:
            return self.text


def load_specifications(path: str) -> Dict:
    """
    Load an `.embed` file, parse to hierarchical tree, and convert to dict
    
    :param str path: path to .embed file
    :return Dict: python dict with hierarchical information
    """
    root_topic = TopicNode("root")
    with open(path, "r") as spec_file:
        root_topic.add_children([TopicNode(line) for line in spec_file.read().splitlines() if line.strip()])
    return root_topic.as_dict()["root"]


def seq_to_int(seq: str, alphabet: List[str], pattern_offsets: Dict[Tuple[int], int] | None = None) -> int:
    """
    Convert a sequence of letters to an integer value given a full alphabet
    
    :param str seq: sequence string, e.g. ACCAGTA
    :param List[str] alphabet: List with single characters representing alphabet
    :param int | None ell: Ell mer length when using gapped k-mers. If set to None, assume full k-mer length
    :param Dict[Tuple[int], int] | None pattern_offsets: Dictionary that maps gapped k-mer patterns (i.e. positions
        of wildcard symbol -). If none is passed, consider `seq` as full k-mer. If wildcard symbol is found, 
        raise error. To compute the `pattern_offsets`, use function `get_kmer_names` with `return_offset=True`.
    :return int: integer representing sequence
    """
    alphabet = list(sorted(alphabet))
    if pattern_offsets is not None:
        pattern = tuple(i_letter for i_letter, letter in enumerate(seq) if letter != '-')
        seq = [letter for letter in seq if letter != '-']
        offset = pattern_offsets[pattern]
    else:
        offset = 0
    value = 0
    for i_letter, letter in enumerate(reversed(seq)):
        if letter == "-":
            raise ValueError("Passed gapped k-mer without `pattern_offsets` dictionary. "
                             "Please create the offset diction by running `get_kmer_names` with `return_offset=True`.")
        value += alphabet.index(letter) * len(alphabet)**i_letter

    return value + offset


def nozero_kmer_to_idx(alphabet: List[str] = DNA_ALPHABET, k: int = 4) -> Dict[str, int]:
    """
    To avoid a bias based in the orientation of the reference genome, we treat a k-mer and its
    reverse implement (for example for `k=3`, `AAT` and `ATT` are treated as the same k-mer).
    This creates many values in the kmer histogram that will always be zero. This function
    returns a dictionary with all present k-mers and their indices.

    :param List[str] alphabet: Alphabet used for creating k-mer histogram.
    :param int k: Length of the k-mers
    :return Dict[str, int]: dictionary with (k-mer, index) key:value pairs.
    """
    kmer_idx_dict = {}
    ctr = 0
    for kmer in sorted(product(alphabet, repeat=k)):
        kmer = "".join(kmer)
        rev_kmer =  str(Seq(kmer).reverse_complement())
        save_kmer = kmer if kmer < rev_kmer else rev_kmer
        if save_kmer in kmer_idx_dict:
            continue
        else:
            kmer_idx_dict[save_kmer] = ctr
            ctr += 1
    return kmer_idx_dict


def fetch_async_result(
        job_list: List[Tuple[int | str, AsyncResult]],
        process_bar: tqdm | None = None,
        max_attempt: int | None = 200  # approx 100 secs
    ) -> List:
    """
    Fetch result from asynchronous job when ready.

    :param List[AsyncResult] job_list: list with asynchronous results.
    :param tqdm | None process_bar: Process bar. If none, no process bar is plotted
    :param int | None max_attempt: Maximum number of attempts to fetch result with half a second
        sleep time between each completed iteration through all remaining open jobs.
    :return List: List with results
    """
    processed_jobs = set()
    results = []
    attempts = 0
    while len(job_list) > 0:
        if attempts > max_attempt:
            warnings.warn("Reached limit of %d attempts without results. Continue." % max_attempt)
            break
        # get first in list
        i, async_res = job_list.pop(0)
        # wait when iterated through entire job list and still unfinished jobs
        if i in processed_jobs:
            # attempt to fetch the same
            attempts += 1
            time.sleep(.5)
            processed_jobs = set()
        processed_jobs.add(i)
        # check if ready and fetch
        if async_res.ready():
            attempts = 0
            results.append((i, async_res.get()))
            if process_bar is not None:
                process_bar.update(1)
        else:
            # otherwise add to end of list.
            job_list.append((i, async_res))
    return results


def get_dist_mat(data: np.ndarray) -> np.ndarray:
    """
    Get Euclidean distance matrix fromd ata points

    :param np.ndarray data: Data points
    :return np.ndarray: Distance matrix for every data point pair.
    """
    return euclidean_distances(data, data)


def get_nn_mat(
        data: np.ndarray | KMerHistogramObject,
        n_neighbors: int | None = 10,
        radius: float | None = None,
        neighbor_batch: int = 128,
        return_distance: bool = True,
        dr_name: str | None = None,
        verbosity: int = 0,
        verbosity_indent: str = ""
) -> sp.csc_matrix:
    """
    Calculate nearest neighbor adjacency matrix.

    :param np.ndarray | KMerHistogramObject data: Input data of size `(#cells x #features)`
    :param int n_neighbors: Number of nearest neighbors per cell.
    :param float | None radius: Use neighborhood radius around each cell rather than k-nearest neighbors.
    :param int neighbor_batch: Number of cells processed at the same time for finding the nearest neighbors.
    :param bool return_distance: Return distance between cell and neighbors instead of adjacency.
    :param str | None dr_name: Name of dimensionality reduction that should be used.
    :param int verbosity: Verbosity levels.
    :param str verbosity_indent: Prefix that is added to the output.
    :return sp.csc_matrix: Sparse adjacency matrix.
    """
    # number of neighbors must be larger than 1, otherwise only returns autoconnections
    if n_neighbors <= 1:
        raise ValueError("Number of neighbors must be at least 2.")
    
    # check whether data is KMerClass and extract data if necessary
    if isinstance(data, KMerHistogramObject):
        if dr_name is not None and dr_name in data.dr:
            data = data.dr[dr_name]
        else:
            data = data.kmer_hist

    # create KD tree
    kdtree = KDTree(data=data)
    adj_mat = sp.lil_matrix((data.shape[0], data.shape[0]), dtype="float")
    cell_kmer_iterator = tqdm(
        range(0, data.shape[0], neighbor_batch),
        desc="%s\tProgress" % verbosity_indent
    ) if verbosity > 0 else range(0, data.shape[0], neighbor_batch)
    # iterate over all cells to create adjacency matrix
    for i_cell_start in cell_kmer_iterator:
        # if based on neighbors, query with number of neighbors
        if radius is None and n_neighbors is not None:
            dist, neighbor_idc = kdtree.query(
                data[i_cell_start:np.minimum(i_cell_start + neighbor_batch, data.shape[0])],
                k=n_neighbors,
                return_distance=True
            )
            cell_idc = np.repeat(
                np.arange(i_cell_start, np.minimum(i_cell_start + neighbor_batch, data.shape[0]), 1),
                n_neighbors 
            )
        # if based on radius, query neighborhood of input data points
        elif radius is not None:
            dist, neighbor_idc = kdtree.query_radius(
                data[i_cell_start:np.minimum(i_cell_start + neighbor_batch, data.shape[0])],
                r=radius,
                return_distance=True
            )
            cell_idc = np.concatenate([
                i * np.ones(len(neighbor_idc[num]))
                for num, i in enumerate(
                    np.arange(i_cell_start, np.minimum(i_cell_start + neighbor_batch, data.shape[0]), 1)
                )
            ])
            dist = np.concatenate(dist)
            neighbor_idc = np.concatenate(neighbor_idc)
        else:
            raise ValueError("Pass either `n_neighbors` or `radius`.")

        # set adjacency matrix. If flag is set, return distance
        adj_mat[cell_idc, neighbor_idc.reshape(-1)] = dist.reshape(-1) if return_distance else 1.
    adj_mat = adj_mat.tocsc()
    return adj_mat


def match_annotations(
        annot_x: List | np.ndarray | pl_Series | pd_Series,
        annot_y: List | np.ndarray | pl_Series | pd_Series
) -> np.ndarray:
    """
    Return mask for matching annotation labels.

    :param List | np.ndarray | pl_Series | pd_Series annot_x: Cell type annotation
    :param List | np.ndarray | pl_Series | pd_Series annot_y: Cell type annotation `annot_x` is compared to
    :return np.ndarray: Mask for matching labels
    """
    def _convert(annot):
        if isinstance(annot, list):
            annot = np.array(annot)
        elif isinstance(annot_x, pl_Series) or isinstance(annot, pd_Series):
            annot = annot_x.to_numpy()
        return annot
    
    annot_x = _convert(annot_x)
    annot_y = _convert(annot_y)
    return annot_x == annot_y


def get_kmer_names(
        k: int, 
        ell: int | None = None, 
        alphabet: List[str] = DNA_ALPHABET, 
        return_offset: bool = False
    ) -> Union[List[str] | Tuple[List[str], Dict[Tuple[int], int]]]:
    """
    Get list of k-mer names corresponding to the positions in the k-mer histogram

    :param int k: length of k-mer
    :param int | None ell: Length of ell-mer when using gapped k-mers. If ell is passed, k is interpreted as the number of unmasked 
        positions. Otherwise, only consider full k-mers
    :param List[str] alphabet: Alphabet used
    :param bool return_offset: Return offset dictionary when computing positions of gapped k-mers. This is `None` when using full
        k-mers (i.e. when `ell=None`).
    :return Union[List[str] | Tuple[List[str], Dict[Tuple[int], int]]]: If `return_offset=False`, return only the list of k-mer strings sorted
        such that they correspond to the columns in the k-mer historgram. If `return_offset=True`, also return the offset dictionary
        containing positions where in the list a new masked pattern starts.
    """
    if ell is None:
        cols = product(alphabet, repeat=k)
        cols = ["".join(kmer) for kmer in cols]
        pattern_offsets = None
    else:
        patterns = list(combinations(range(ell), k))
        patterns.sort()  # lex order of positions
        block_size = len(alphabet)**k
        cols = []
        pattern_offsets = {}
        for p_idx, pattern in enumerate(patterns):
            pattern_offsets[pattern] = p_idx * block_size
            for km in product(alphabet, repeat=k):
                gapped = ['-'] * ell
                for pos, ch in zip(pattern, km):
                    gapped[pos] = ch
                cols.append(''.join(gapped))

    return cols if not return_offset else (cols, pattern_offsets)


def kmers_for_ellmer(seq: str, pattern_offset: Dict[Tuple[int], int], alphabet: List[str] = DNA_ALPHABET) -> np.ndarray:
    """
    Determine which gapped k-mer positions correspond to a given ell-mer. 

    :param str seq: ell-mer sequence
    :param Dict[Tuple[int], int] pattern_offset: Dictionary containing index postions where a new pattern starts in the 
        histogram containing gapped k-mers
    :param List[str] alphabet: Used alphabet
    :return np.ndarray: gapped k-mer indices matching ell-mer.
    """
    alphabet = list(sorted(alphabet))
    matches = []
    for pattern, offset in pattern_offset.items():
        val = 0
        for pos in pattern:
            val = val * len(alphabet) + alphabet.index(seq[pos])
        idx = offset + val
        matches.append(idx)
    return np.array(matches)


def get_gkm_mat(
        ell_names: List[str], 
        n_gapped_kmer: int, 
        offset_dict: Dict[Tuple[int], int], 
        alphabet: List[str] = DNA_ALPHABET
    ) -> sp.csr_matrix:
    """
    Compute binary match matrix, linking ell-mers (rows) to gapped k-mers (columns).

    :param List[str] ell_names: Full list of *all* ell-mers.
    :param int n_gapped_kmer: Number of gapped k-mers, which is equal to

        .. math::
            \text{#gapped k-mers} = \binom{\ell}{k}4^k
        
        considering a conventional 4-letter nucleotide alphabet.

    :param Dict[Tuple[int], int] offset_dict: Dictionary containing offset indices for each gapped pattern
    :param List[str] alphabet: ell-mer alphabet (without wildcard).
    :return sp.ccsr_matrix: Sparse matrix mappint ell-mers to k-mers.
    """
    rows, cols = [], []
    for i, ellmer in enumerate(tqdm(ell_names)):
        matched_kmers = kmers_for_ellmer(ellmer, offset_dict, alphabet=alphabet)
        rows.extend([i] * len(matched_kmers))
        cols.extend(matched_kmers)

    return sp.csr_matrix(([1] * len(rows), (rows, cols)), shape=(len(ell_names), n_gapped_kmer))

def count_neighbors(
    nn_mat: sp.csc_matrix | np.ndarray,
    species1_mask: np.ndarray,
    species2_mask: np.ndarray,
    species1_labels: np.ndarray | pd.Series,
    species2_labels: np.ndarray | pd.Series,
    species1_name: str = "species 1",
    species2_name: str = "species 2",
    norm: str = "cell",
    verbosity: int = 0
) -> pd.DataFrame:
    """
    Calculate relative abundance of nearest neighbors in other species over a provided annotation

    :param sp.csc_matrix | np.ndarray nn_mat: Nearest neighbor matrix
    :param np.ndarray species1_mask: Mask indicating cells belonging to species 1
    :param np.ndarray species2_mask: Mask indicating cells belonging to species 2
    :param np.ndarray | pd.Series species1_labels: Annotation for species 1. The dimension should be equal to the number of 
        True values in species1_mask
    :param np.ndarray | pd.Series species2_labels: Annotation for species 2. The dimension should be equal to the number of 
        True values in species2_mask
    :param str species1_name: Name of species 1
    :param str species2_name: Name of species 2
    :param str norm: Normalization type. Choose between
    
        - cell (normalize over number of cells per label in species 1)
        - total (normalize over cells and total possible number of neighbors)
        - expected (normalize over cells and half of possible number of neighbors)
        
    :param int verbosity: Verbosity level
    :returns pd.DataFrame: Heatmap of relative abundance. Rows represent species 1, columns are species 2.
    """
    if not isinstance(nn_mat, np.ndarray):
        nn_mat = nn_mat.toarray()
    n_neighbor_mat = nn_mat.sum(axis=1).max()
    if norm.lower() == "expected":
        n_neighbor = n_neighbor_mat / 2.
    elif norm.lower() == "total":
        n_neighbor = n_neighbor_mat
    elif norm.lower() == "cell":
        n_neighbor = 1.
    submat_mat = nn_mat[np.where(species1_mask)[0].reshape(-1, 1), np.where(species2_mask)[0].reshape(1, -1)]
    label_cnts_tuples = []
    label_iter = np.unique(species1_labels)
    if verbosity > 0:
        label_iter = tqdm(label_iter) 
    for ls1 in label_iter:
        ls1_mask = ls1 == species1_labels
        avg_n_cells = []
        for ls2 in np.unique(species2_labels):
            ls2_mask = ls2 == species2_labels
            n_neighbors_other = submat_mat[
                np.where(ls1_mask)[0].reshape(-1, 1), 
                np.where(ls2_mask)[0].reshape(1, -1)
            ].sum()
            # heuristic was established on 50 nearest neighbors --> this is only a rule of thumb.
            avg_n_cells.append(50. * n_neighbors_other / float(ls1_mask.sum() * n_neighbor_mat))
            norm_n_neighbor = n_neighbors_other / float(ls1_mask.sum() * n_neighbor)
            label_cnts_tuples.append((ls1, ls2, norm_n_neighbor))
        if np.all(np.array(avg_n_cells) < 1.):
            warnings.warn(f"{ls1} in {species1_name} has less than 1 nearest neighbor for any cell type in {species2_name}."
                          f"This is only a rule of thumb, but it is possible that {ls1} has no equivalent in {species2_name}.")

    ct_cnts_df = pd.DataFrame(label_cnts_tuples, columns=[species1_name, species2_name, "overlap"])
    heatmap_df = ct_cnts_df.pivot_table(columns=[species2_name], index=[species1_name])
    heatmap_df.columns = [c[-1] for c in heatmap_df.columns]
    return heatmap_df
    
