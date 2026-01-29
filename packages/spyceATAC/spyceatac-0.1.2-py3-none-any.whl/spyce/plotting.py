from __future__ import annotations

import warnings
from typing import List, Tuple, Dict
from itertools import product

import numpy as np
import pandas as pd
import polars as pl
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
import seaborn as sns

from spyce.kmerMatrix import KMerClass, KMerMatrix
from spyce.utils import nozero_kmer_to_idx
from spyce.constants import DNA_ALPHABET

def get_color(
        kmer_obj: KMerClass, 
        ck: str | pd.Series | pl.Series | np.ndarray | List[str], 
        cmin: int | float = 0.,
        cmax: int | float | None = None,
        cmap: str | None = None,
) -> np.ndarray:
    # convert polars series to pandas
    if isinstance(ck, pl.Series):
        ck = ck.to_pandas()
    # convert list to pandas
    if isinstance(ck, list):
        ck = pd.Series(ck)
    if isinstance(ck, pd.Series):
        # if string type and cmap is not passed, assume it's the color names
        if str(ck.dtype) in ["category", "str", "string"] and cmap is None:
            ck = ck.astype("category")
            return ck.to_numpy()
        
        # if cmap is passed, assume that ck is a categorical variable wrt which a color is
        # set using the cmap
        if str(ck.dtype) in ["category", "str", "string"] and cmap is not None:
            ck = ck.astype("category").cat.codes
        if "int" in str(ck.dtype) or "float" in str(ck.dtype):
            ck = ck.to_numpy()

    if isinstance(ck, np.ndarray) and cmap is None:
        # color matrix is set
        if ck.shape[1] == 3 or ck.shape[1] == 4:
            return ck
        # if one-dim numpy array, then it's a numerical value and cmap must be passed
        raise ValueError("If ck is a numpy array, you need to pass a cmap.")
    elif isinstance(ck, np.ndarray) and cmap is not None:
        c_vec = ck
    elif isinstance(ck, str):
        # fetch coloring
        c_vec = np.zeros(len(kmer_obj))
        ck = ck.lower()
        if ck == "species":
            if isinstance(kmer_obj, KMerMatrix):
                pass
            else:
                species_dict = {}
                idx = 0
                for i_mat, mat_values in enumerate(kmer_obj.kmer_mat_idc_df.iter_rows(named=False)):
                    species = kmer_obj.kmer_mat_list[i_mat].species
                    if species in species_dict:
                        species_idx = species_dict[species]
                    else:
                        species_idx = idx
                        idx += 1
                        species_dict[species] = species_idx
                    c_vec[int(mat_values[1]):int(mat_values[2])] = species_idx
        elif ck == "matrix":
            if isinstance(kmer_obj, KMerMatrix):
                pass
            else:
                for i_mat, mat_values in enumerate(kmer_obj.kmer_mat_idc_df.iter_rows(named=False)):
                    c_vec[int(mat_values[1]):int(mat_values[2])] = i_mat
        elif ck in kmer_obj.clustering.keys():
            c_vec = kmer_obj.clustering[ck]
        else:
            raise NotImplementedError("Accepting cell annotation keys is not yet implemented.")
    else:
        raise ValueError("Input type of ck not understood. Pass str | pd.Series | pl.Series | np.ndarray")
    
    norm = Normalize(vmin=cmin, vmax=cmax)
    if isinstance(cmap, str):
        cmap = plt.get_cmap(cmap)
    return np.array([cmap(norm(val)) for val in c_vec])

def plot_scatter(
        X: np.ndarray,
        c_vec: np.ndarray | List,
        fig: plt.Figure | None = None,
        ax: plt.Axes | None = None,
        randomize: bool = True,
        title: str = "",
        s_vec: float | np.ndarray = 1.,
        x_type: str = "UMAP",
        dim: np.ndarray | None = None,
        return_scat: bool = False
) -> Tuple[plt.Figure, plt.Axes] | Tuple[plt.Figure, plt.Axes, List]:
    """
    General function for creating a scatter plot using matplotlib. We recommend using only
    one of the wrappers provided.

    :param np.ndarray X: data (if size `#samples x #features`)
    :param np.ndarray | List c_vec: Color vector with one entry per data point
    :param plt.Figure | None fig: Matplotlib figure. Pass `None` to create a new figure.  
    :param plt.Axes | None ax: Matplotlib axes. Pass `None` to create new axes.
    :param bool randomize: If set to `True`, randomize order in which data points are plotted. 
    :param str title: Axes title
    :param float | np.ndarray s_vec: Size of plotted circles, can be a single float or a vector
        per data entry in `X`.
    :param str x_type: Type of representation that is used for labelling the x and y axes.
    :param np.ndarray | None dim: Dimension names for obtaining `features` in `X`.
    :param bool return_scat: Return the Matplotlib scatter object 
    :return Tuple[plt.Figure, plt.Axes] | Tuple[plt.Figure, plt.Axes, List]: If `return_scat=False`
        return only figure and axes, otherwise return figure, axes, and scatter object.
    """
    if ax is None or fig is None:
        fig = plt.figure()
        
    idc = np.arange(X.shape[0])
    if randomize:
        # shuffle data points
        np.random.shuffle(idc)

    if X.shape[1] < 3:
        # 1D and 2D plotting
        if ax is None:
            ax = fig.add_subplot(111)
        x_val = X[:, 0]
        y_val = np.arange(X.shape[0]) if X.shape[1] == 1 else X[:, 1]
        scat = ax.scatter(
            x_val[idc],
            y_val[idc],
            marker=".",
            s=s_vec,
            c=c_vec[idc],
        )
        if dim is None:
            dim = np.array([1, 2])
        else: 
            dim = dim + 1
        ax.set_xlabel("%s%d" % (x_type, dim[0]))
        ax.set_ylabel("%s%d" % (x_type, dim[1]))
        ax.set_xticks([])
        ax.set_yticks([])

    else:
        # 3D plotting
        if ax is None:
            ax = fig.add_subplot(111, projection="3d")
        else:
            warnings.warn("Cannot perform 3D projection when axis is passed.")
            return None, None, None
        scat = ax.scatter(
            X[idc, 0],
            X[idc, 1],
            X[idc, 2],
            marker=".",
            s=s_vec,
            c=c_vec[idc],
        )
        if dim is None:
            dim = np.array([1, 2, 3])
        else: 
            dim = dim + 1
        ax.set_xlabel("%s%d" % (x_type, dim[0]))
        ax.set_ylabel("%s%d" % (x_type, dim[1]))
        ax.set_zlabel("%s%d" % (x_type, dim[2]))
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_zticks([])

    ax.set_title(title)
    if return_scat:
        return fig, ax, scat
    else:
        return fig, ax


def plot_dr(
    kmer_obj: KMerClass,
    ck: str | pd.Series | pl.Series,
    dr_key: str = "pca",
    dim: np.ndarray = np.array([0, 1]),
    fig: plt.Figure | None = None,
    ax: plt.Axes | None = None,
    randomize: bool = True,
    title: str = "",
    cmin: int | float = 0.,
    cmax: int | float | None = None,
    cmap: str = "tab20",
    s_vec: float | np.ndarray = 1.,
    return_scat: bool = False
) -> Tuple[plt.Figure, plt.Axes] | Tuple[plt.Figure, plt.Axes, List]:
    """
    Plot data in KMer data object and color with respect to key

    :param KMerClass kmer_obj: KMer data object, either of type KMerMatrix or KMerCollection
    :param str ck: Color key which defines the coloring of the data points. Can be set to pne of the following:
        
        - `species`: Color w.r.t. species. Only useful if the KMer data object is of type KMerCollection
        - `matrix`: Color w.r.t. each matrix. Only useful if the KMer data object is of type KMerCollection
        - `your_cluster_key`: Cluster w.r.t. a clustering result saved under `your_cluster_key`. You must run a
            clustering algorithm before, which is saved under this name
        - `your_cell_annotation_col`: Cluster w.r.t. a column in the cell annotation table `your_cell_annotation_col`.
            This is only useful if a cell annotation table was set
        
    :param str dr_key: Key name for the dimensionality reduction to be used. This is a key in the `kmer_obj.dr` dict.
    :param np.ndarray dim: Dimensions to be used for plotting.
    :param plt.Figure | None fig: Figure which is used for plotting
    :param plt.Axes | None ax: Axis used for plotting
    :param bool randomize: If true, randomize data values for plotting
    :param str title: Title of axis
    :param int | float cmin: Minimum color value which is used for normalizing
    :param int | float | None cmax: Maximum color value. If not passed, use the maximum value found color key
    :param str cmap: Name of color map. See https://matplotlib.org/stable/users/explain/colors/colormaps.html
    :param float | np.ndarray s_vec: Size of plotted circles, can be a single float or a vector
        per data entry in `X`.
    :param bool return_scat: Return the Matplotlib scatter object 
    :return Tuple[plt.Figure, plt.Axes] | Tuple[plt.Figure, plt.Axes, List]: If `return_scat=False`
        return only figure and axes, otherwise return figure, axes, and scatter object.
    """
    if kmer_obj.dr is None:
        raise ValueError("Plotting requires a calculating a dimensionality reduction first.")

    if dr_key not in kmer_obj.dr:
        raise ValueError("Provided dimensionality reduction key doesn't exist.")
    
    if not 1 <= len(dim) <= 3:
        raise ValueError("Plotting requires a dimensionality reduction into a 1, 2, or 3-D space.")
    
    dim = np.array(dim)
    # get data
    x_dr = kmer_obj.dr[dr_key][:, dim]
    # get color
    c_vec = get_color(kmer_obj=kmer_obj, ck=ck, cmin=cmin, cmax=cmax, cmap=cmap)
    # plot
    return_vals = plot_scatter(
        X=x_dr,
        c_vec=c_vec,
        fig=fig,
        ax=ax,
        randomize=randomize,
        title=title,
        s_vec=s_vec,
        dim=dim,
        x_type=dr_key,
        return_scat=return_scat
    )
    return return_vals


def plot_umap(
        kmer_obj: KMerClass,
        ck: str,
        umap_key: str = "umap",
        fig: plt.Figure | None = None,
        ax: plt.Axes | None = None,
        randomize: bool = True,
        title: str = "",
        cmin: int | float = 0.,
        cmax: int | float | None = None,
        cmap: str = "tab20",
        s_vec: float | np.ndarray = 1.,
        return_scat: bool = False
) -> Tuple[plt.Figure, plt.Axes] | Tuple[plt.Figure, plt.Axes, List]:
    """
    Plot data in KMer data object and color with respect to key

    :param KMerClass kmer_obj: KMer data object, either of type KMerMatrix or KMerCollection
    :param str ck: Color key which defines the coloring of the data points. Can be set to pne of the following:
        
        - `species`: Color w.r.t. species. Only useful if the KMer data object is of type KMerCollection
        - `matrix`: Color w.r.t. each matrix. Only useful if the KMer data object is of type KMerCollection
        - `your_cluster_key`: Cluster w.r.t. a clustering result saved under `your_cluster_key`. You must run a
            clustering algorithm before, which is saved under this name
        - `your_cell_annotation_col`: Cluster w.r.t. a column in the cell annotation table `your_cell_annotation_col`.
            This is only useful if a cell annotation table was set
    
    :param str umap_key: Key name for the UMAP embedding to be used. This is a key in the `kmer_obj.x_umap` dict.
    :param plt.Figure | None fig: Figure which is used for plotting
    :param plt.Axes | None ax: Axis used for plotting
    :param bool randomize: If true, randomize data values for plotting
    :param str title: Title of axis
    :param int | float cmin: Minimum color value which is used for normalizing
    :param int | float | None cmax: Maximum color value. If not passed, use the maximum value found color key
    :param str cmap: Name of color map. See https://matplotlib.org/stable/users/explain/colors/colormaps.html
    :param float | np.ndarray s_vec: Size of plotted circles, can be a single float or a vector
        per data entry in `X`.
    :param bool return_scat: Return the Matplotlib scatter object 
    :return Tuple[plt.Figure, plt.Axes] | Tuple[plt.Figure, plt.Axes, List]: If `return_scat=False`
        return only figure and axes, otherwise return figure, axes, and scatter object.
    """
    if kmer_obj.x_umap is None:
        raise ValueError("Plotting requires a calculating the UMAP first.")

    if umap_key not in kmer_obj.x_umap:
        raise ValueError("Provided UMAP key doesn't exist.")
    
    if not 0 < kmer_obj.x_umap[umap_key].shape[1] <= 3:
        raise ValueError("Plotting requires an embedding into 1, 2, or 3-D manifold.")

    x_umap = kmer_obj.x_umap[umap_key]
    # get color
    c_vec = get_color(kmer_obj=kmer_obj, ck=ck, cmin=cmin, cmax=cmax, cmap=cmap)
    # plot
    return_vals = plot_scatter(
        X=x_umap,
        c_vec=c_vec,
        fig=fig,
        ax=ax,
        randomize=randomize,
        title=title,
        s_vec=s_vec,
        x_type=umap_key,
        return_scat=return_scat
    )
    return return_vals
    
    
def plot_clustermap(
        kmer_obj: KMerClass,
        row_colors: pd.Series | List[pd.Series] | None = None,
        col_colors: pd.Series | List[pd.Series] | None = None,
        cmin: float | int | None = None,
        cmax: float | int | None = None,
        col_cluster: bool = False,
        row_cluster: bool = True,
        clustermap_kw: Dict = {}
) -> sns.matrix.ClusterGrid:
    """
    Plot k-mer histogram as clustered heatmap using seaborn.

    :param KMerClass kmer_obj: KMer object whose cell/nucleus specific kmer histogram
        is used for plotting
    :param pd.Series | List[pd.Series] | None row_colors: Use these colors for idenifying rows.
    :param pd.Series | List[pd.Series] | None col_colors: Use these colors for idenifying columns.
    :param float | int | None cmin: Minimum color value
    :param float | int | None cmax: Maximum color value
    :param bool col_cluster: If set to true, cluster columns and visualize with dendrogram
    :param bool row_cluster: If set to true, cluster row and visualize with dendrogram
    :param dict clustermap_kw: Parameters that are passed to the cluster map function provided by Seaborn.
    :return sns.matrix.ClusterGrid: Seaborn cluster grid.
    """
    kmer_hist_hm = pd.DataFrame(kmer_obj.kmer_hist)
    kmer_hist_hm.columns = kmer_obj.get_kmer_column_names()

    cg = sns.clustermap(
        kmer_hist_hm,
        col_cluster=col_cluster,
        row_cluster=row_cluster,
        row_colors=row_colors,
        col_colors=col_colors,
        vmax=cmax,
        vmin=cmin,
        **clustermap_kw
    )
    return cg