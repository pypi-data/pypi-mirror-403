from __future__ import annotations
from typing import List, Tuple
import numpy as np
import pandas as pd
import polars as pl

from sklearn.metrics import silhouette_samples, adjusted_rand_score, matthews_corrcoef, precision_score, recall_score, f1_score
import networkx as nx
from scipy import sparse as sp

from spyce.utils import get_nn_mat

from tqdm import tqdm 


def convert_labels(labels: pd.Series | np.ndarray | List) -> np.ndarray:
    """
    Convert labels to to accepted numpy format for comparing integration performance

    :param pd.Series | np.ndarray | List labels: list or series of labels.
    :return np.ndarray: converted labels list
    """
    if isinstance(labels, list):
        label_codes = np.asarray(labels)
    elif isinstance(labels, pd.Series):
        label_codes = labels.astype("category").cat.codes
    elif isinstance(labels, np.ndarray):
        label_codes = labels.copy()
    else:
        raise ValueError("Expect label codes with data type np.ndarray | pd.Series | list.")
    return label_codes


def asw_score(
        data: np.ndarray,
        labels: pd.Series | np.ndarray | List
) -> Tuple[pl.DataFrame, float]:
    """
    Compute average silhouette score based on data and labels. Metric is computed as in
    https://doi.org/10.1038/s41592-021-01336-8

    :param np.ndarray data: data array
    :param pd.Series | np.ndarray | List labels: List or series of labels
    :return Tuple[pl.DataFrame, float]: Returns tuple, first value a polars dataframe with silhouette
        width per group, the second is the average over all groups.
    """
    # convert labels
    label_codes = convert_labels(labels=labels)
    sc_per_cell = silhouette_samples(
        data,
        labels=label_codes
    )
    # convert silhouette value to embedding score
    asw_df = pl.DataFrame(
        {"labels": labels, "silhouette": 1 - np.abs(sc_per_cell)}
    ).group_by("labels").agg(pl.mean("silhouette")).sort("labels")
    return asw_df, asw_df["silhouette"].mean()


def aws_score(
        data: np.ndarray,
        labels: pd.Series | np.ndarray | List
) -> Tuple[pl.DataFrame, float]:
    """
    Legacy function for average silhouette width that contained a typo.

    :param np.ndarray data: data array
    :param pd.Series | np.ndarray | List labels: List or series of labels
    :return Tuple[pl.DataFrame, float]: Returns tuple, first value a polars dataframe with silhouette
        width per group, the second is the average over all groups.
    """
    return asw_score(data=data, labels=labels)


def adjusted_rand_index(
        predicted_labels: pd.Series | np.ndarray | List,
        true_labels: pd.Series | np.ndarray | List
) -> float:
    """
    Compute adjusted rand index which measures overlap between annotation and predicted clusters. 
    Metric is computeed as in https://doi.org/10.1038/s41592-021-01336-8

    :param pd.Series | np.ndarray | List predicted_labels: list or series of predicted labels
    :param pd.Series | np.ndarray | List true_labels: list or series of true annotation labels
    :return float: adjusted rand index.
    """
    # convert labels
    p_label_codes = convert_labels(predicted_labels)
    t_label_codes = convert_labels(true_labels)
    return adjusted_rand_score(
        labels_pred=p_label_codes,
        labels_true=t_label_codes
    )


def binary(
        predict_mask:  pd.Series | np.ndarray | List,
        true_mask: pd.Series | np.ndarray | List,
        method: str["mcc" | "precision" | "recall" | "fscore"] = "mcc"
) -> float:
    """
    Calculate binary cluster metrics for two masks. This function can be used whether an algorithm finds
    similar cells belonging to a single annotated cell type.

    :param pd.Series | np.ndarray | List predict_mask: Mask marking which data points belong to a given cell
         type
    :param pd.Series | np.ndarray | List true_mask: Mask marking which data points really are annotated as the
        target cell type
    :param str["mcc" | "precision" | "recall" | "fscore"] method: Type of binary cluster metric to be applied. Choose
        between one of the following: `mcc` | `precision` | `recall` | `fscore`.
    :return float: Binary cluster score (depends on the passed `method`).
    """
    def convert_mask(mask_):
        if method == "mcc":
            label_vec_ = mask_.copy().astype("int")
            label_vec_[label_vec_ == 0] = -1
            return label_vec_
        else:
            return  mask_.copy().astype("int")
        
    cluster_metric = None
    if method.lower() == "mcc":
        cluster_metric = matthews_corrcoef
    elif method.lower() == "precision":
        cluster_metric = precision_score
    elif method.lower() == "recall":
        cluster_metric = recall_score
    elif method.lower() == "f1score":
        cluster_metric = f1_score
    else:
        raise ValueError("Cluster method not understood. Please choose between `mcc` | `f1score` | `precision` | `recall`")
    
    p_binary = convert_mask(predict_mask)
    t_binary = convert_mask(true_mask)
    return cluster_metric(y_true=t_binary, y_pred=p_binary)


def cluster_wise_binary(
        predicted_labels: pd.Series | np.ndarray | List,
        true_labels: pd.Series | np.ndarray | List,
        method: str["mcc" | "precision" | "recall" | "fscore"] = "mcc"
) -> Tuple[pl.DataFrame, float]:
    """
    Iterate over predicted labels and true labels and compute for each a binary cluster score, which
    can be Matthew's correlation coefficient, precision, recall, or F1 score. Note that the labels 
    should match between clusters and annotation.

    :param pd.Series | np.ndarray | List predicted_labels: Predicted labels
    :param pd.Series | np.ndarray | List true_labels: True annotation lables
    :param str["mcc" | "precision" | "recall" | "fscore"] method: Method used for computing the labels
    :return Tuple[pl.DataFrame, float]: Tuple containing a dataframe with the scores per label at first position
        and the average score over all labels at second.
    """        
    label_set = set(np.unique(predicted_labels).tolist())
    label_set = label_set.union(np.unique(true_labels).tolist())
    
    binary_cluster_df = {"cluster": [], "score": []}
    for label in label_set:
        binary_cluster_df["cluster"].append(label)
        binary_cluster_df["score"].append(binary(
            predicted_labels ==  label, 
            true_labels == label,
            method=method
        ))
       
    return pd.DataFrame(binary_cluster_df), np.mean(binary_cluster_df["score"])


def graph_connectivity(
        data: np.ndarray,
        labels: pd.Series | np.ndarray | List,
        n_neighbors: int = 20,
        neighbor_batch: int = 128,
        adj_mat: None | sp.csc_matrix = None,
        verbosity: int = 0,
) -> Tuple[pl.DataFrame, float]:
    """
    Compute graph connectivity when subset based on annotation labels. Metric is computed as
    in https://doi.org/10.1038/s41592-021-01336-8

    :param np.ndarray data: data array
    :param pd.Series | np.ndarray | List labels: list or series of annotation labels
    :param int n_neighbors: Number of neighbors used for creating nearest neighbor graph
    :param int neighbor_batch: Number of data entries processed at once for calculating neighbor graph
    :param None | sp.csc_matrix adj_mat: precomputed adjacency matrix. If not passed, compute new one
    :param int verbosity: verbosity levels
    :return Tuple[pl.DataFrame, float]:  Returns tuple, first value is a polars data frame with 
        the size of the largest connected per label, second value is the average
    """
    if isinstance(labels, list) or isinstance(labels, np.ndarray):
        labels = pd.Series(labels, dthpe="string")
    if adj_mat is None:
        adj_mat = get_nn_mat(
            data=data,
            n_neighbors=n_neighbors,
            neighbor_batch=neighbor_batch,
            verbosity=verbosity,
            return_distance=False
        )

    adj_mat = adj_mat.astype("bool")
    # compute shared nearest neighbor graph
    snn_mat = adj_mat.multiply(adj_mat.T)
    graph = nx.Graph()
    # create graph with all nodes but no edges
    graph.add_nodes_from(np.arange(len(data)))

    neighbors_from, neighbors_to = snn_mat.nonzero()
    for node_name in tqdm(np.unique(neighbors_from), total=len(np.unique(neighbors_from)), desc="Create graph"):
        neighbor_idc = neighbors_to[neighbors_from == node_name]
        # add edges
        graph.add_edges_from(zip([node_name] * n_neighbors, neighbor_idc.reshape(-1).tolist()))

    lcc = {}
    for lb in tqdm(labels.unique(), total=len(labels.unique()), desc="Calculate connected components"):
        mask = (labels == lb).to_numpy()
        # get subgraph
        cluster_sgraph = graph.subgraph(np.arange(len(data))[mask])
        # get largest connected component
        largest_cc = max(
            nx.connected_components(cluster_sgraph), 
            key=len
        )
        # compute largest component connectivity
        lcc[lb] = [len(largest_cc) / float(np.sum(mask))]
    lcc_pd = pl.DataFrame(lcc)
    return lcc_pd, lcc_pd.to_numpy().mean()


def nn_graph_similarity(
        data_1: np.ndarray | None = None,
        data_2: np.ndarray | None = None,
        n_neighbors: int = 20,
        neighbor_batch: int = 128,
        adj_mat_1: None | sp.csc_matrix = None,
        adj_mat_2: None | sp.csc_matrix = None,
        verbosity: int = 0
) -> float:
    """
    Compute jaccard distance of nearest neighbor adjacency graph matrix.  

    :param np.ndarray | None data_1: First data matrix. Can be `None` if adjacency matrix 
        `adj_mat_1` is passed   
    :param np.ndarray | None data_2: Second data matrix. Can be `None` if adjacency matrix
        `adj_mat_2` is passed  
    :param int n_neighbors: Number of neighbors used for creating k-neighbor adjacency matrix  
    :param int neighbor_batch: Number of data values processed at once for adjacency matrix  
    :param None | sp.csc_matrix adj_mat_1: Pre-computed first adjacency matrix. Can be `None` if 
        `data_1` is passed.  
    :param None | sp.csc_matrix adj_mat_2: Pre-computed second adjacency matrix. Can be `None` if 
        `data_2` is passed.  
    :param int verbosity: Verbosity levels  
    :return float: average jaccard distance based on neighbor matching.  
    """
    is_data_none = data_1 is None or data_2 is None
    is_adj_none = adj_mat_1 is None or adj_mat_2 is None
    if is_data_none and is_adj_none:
        raise ValueError("Either set data or adjacency matrix")
    if adj_mat_1 is None:
        adj_mat_1 = get_nn_mat(
            data=data_1,
            n_neighbors=n_neighbors,
            neighbor_batch=neighbor_batch,
            return_distance=False,
            verbosity=verbosity
        )

    if adj_mat_2 is None:
        adj_mat_2 = get_nn_mat(
            data=data_2,
            n_neighbors=n_neighbors,
            neighbor_batch=neighbor_batch,
            return_distance=False,
            verbosity=verbosity
        )
    jacc_and = adj_mat_1.astype("bool").multiply(adj_mat_2.astype("bool")).sum(axis=1).A.reshape(-1).astype("float")
    jacc_or = (adj_mat_1.astype("bool") + adj_mat_2.astype("bool")).sum(axis=1).A.reshape(-1).astype("float")
    return (jacc_and / jacc_or).mean()
    
