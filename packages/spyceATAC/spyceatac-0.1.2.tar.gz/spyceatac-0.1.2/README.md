(Credits avatar: Created with https://deepai.org/machine-learning-model/pop-art-generator)
# Single Cell Integration for Single Cell and Single Nucleus ATAC-seq Across Evolution (sPYce)

We present sPYce, a single-cell and single-nucleus ATAC-seq integration method across different species implemented in Python. sPYce takes single cell data (ie. a cell-by-feature matrix) and transforms it to single cell k-mer histograms. It was developed for single-cell and single-nucleus ATAC-seq data, but it can be similarly applied to any single cell data that follows an on-off relationship. In the case of single-cell ATAC-seq, the k-mer histogram represents the sequence composition of accessible regions. sPYce allows the straightforward combination of those k-mer histograms over several species, performs appropriate normalization, and defines an easy-to-use interface to run dimensionality reduction, clustering, embedding, visualisation, and automated label transfer.

For more information, please see our [documentation](http://cofugeno.pages.pasteur.fr/spyce/) with tutorials, instructions, and detailed API explanations.

> **News**: We added gapped k-mer support in version 0.1.1. Updated documentation and pip package will be available soon!

## Installation
The code was implemented and tested using `Python=3.9`, but any Python version greater than or equal to `3.6` should work. Make sure you have pip installed.

### pip
The easiest way to install our package is using `pip`. Simply run

```console
python3 -m pip install spyceATAC
```

Installation requires up to a minute on standard hardware. Using the packaging service also allows to use the entry points (see below).

### Git
If you want to contribute or customize the code, you can also clone the repository. Build and install the package from the code by navigating to the folder to which you cloned the repository. Then run
```console
python3 -m build
python3 -m pip install .
```
This will install sPYce from the files in the repository. Note that if you have changed the code yourself, they'll be reflected in the global installation.

If you only want to install the requirements, use `pip` via

```console
python3 -m pip install -r requirements.txt
```
or, if you're a developer, we recommend running
```console
python3 -m pip install -r requirements_dev.txt
```

Installation requires up to a minute on standard hardware. 

## Data
sPYce requires as data input the following files:
- a peak matrix per sample and species, rows representing cells, columns representing peaks
- a bed file with peaks in the same order as the peaks in the peak matrix. You need to have either one per peak matrix or one per species
- a reference genome as fasta `.fa` file per species

If you follow our [tutorial on our website](http://cofugeno.pages.pasteur.fr/spyce/), you can download the example data by running:

```console
sh shell/get_testdata.sh /path/to/spyce/dir /output/dir n_cpus
```

Please replace the paths and the number of used processes with the desired values.


## Example
sPYce's use is dependent on your data. Please follow the [tutorial](http://cofugeno.pages.pasteur.fr/spyce/) for more information. Generally, sPYce follows the workflow

1) KMer matrix creation
sPYce requires a setup file in which file paths per species are saved. This allows easy modification and archiving if you want to test different data versions. We developed the `.embed` file format to represent hierarchical data easily without knowing any `json` or `xml`. It roughly follows a pythonic syntax, and hierarchies are represented as tab indents. Follow the tutorial for more information.


Create your own KMer matrices based on your data using our command-line interface

```console
spyce-create --setup_file /path/to/setup/file --k k [optional parameters]
```
where you should replace `/path/to/setup/file` with the path to your own setup file, `k` with the desired k-mer length, and `[optional parameters]` with any additional parameter that you want to add. See full description by typing

```console
spyce-create --help
```

2) Analysis
Once the snATAC-seq peak matrices from all species were converted to a KMer matrix, you can analyse and treat the data (meaning the cell-by-k-mer histogram) as you want. Our interface tries to provide NumPy like interface.

```python
# spyce libraries
from spyce.kmerMatrix import KMerCollection
from spyce.plotting import plot_dr, plot_umap

species_c_vec = ... # define your species color vector

# Load kmer collection
kmer_collect = KMerCollection.load("../data/kmer/tutorial/tutorial_kmer_collection_obj.pkl")
# centered unit-sum normalization
kmer_collect.set_normalization("centered_sum") 

# Perform PCA and get explained variance ratio of the first 3 PCs
explained_var_ratio = kmer_collect.reduce_dimensionality(
    algorithm="pca",
    save_name="pca",
    n_pca_components=n_pca_components
)[:3]

# Remove non-linear species effects that can occur due to unequal cell type distribution
kmer_collect.remove_species_effect(
    batch_vec=species_vec,  # indicate along which values a batch/species effect can occur
    dr_key="pca",  # Use the dimensionality reduction saved under the pca key
    save_name="harmony_pca",  # save the Harmony corrected PCs under harmony_pca 
    algorithm="harmony"  # use Harmony batch correction algorithm
)

# plot PCA
fig, ax = plot_dr(
    kmer_collect,
    ck=species_c_vec,
    dr_key="harmony_pca",
    cmap=None,
    randomize=True,
    title="PCA Species (centered-sum)",
)
handles = [
    Line2D(
        [0], [0], marker="o", color="w", 
        markerfacecolor=c, markersize=5, label=s
    )
    for s, c in species_colors.items()
] 
fig.legend(handles=handles, loc=7)
fig.tight_layout()
fig.subplots_adjust(right=0.7)
plt.show()

# compute UMAP
kmer_collect.umap(
    dr_name="harmony_pca",  # use the Harmony-corrected PCs for UMAP
    n_neighbors=n_umap_neighbors, 
    min_dist=min_dist
)

fig, ax = plot_umap(
    kmer_collect,
    ck=species_c_vec,
    randomize=True,
    title="UMAP Species (centered-sum)",
    cmap=None
)
handles = [
    Line2D(
        [0], [0], marker="o", color="w", 
        markerfacecolor=c, markersize=5, label=s
    )
    for s, c in species_colors.items()
] 
fig.legend(handles=handles, loc=7)
fig.tight_layout()
fig.subplots_adjust(right=0.7)
plt.show()

# Calculate nearest neighbor adjacency matrix to avoid re-calculating it for different leiden parameters.
# However, this can also be done directly by running `run_clustering`.
nn_mat = get_nn_mat(
    kmer_collect.dr["harmony_pca"], 
    n_neighbors=15, 
    verbosity=1, 
    return_distance=True
)

# calculate leiden clustering and test several parameters
kmer_collect.run_clustering(
    algorithm="leiden",  # set algorithm
    save_name="leiden_0.6",  # save result under this name
    resolution=.6,  # additional leiden parameter - resolution
    leiden_beta=0.,  # additional leiden parameter - beta
    adj_mat=nn_mat  # additional leiden parameter - adjacency matrix
)
kmer_collect.run_clustering(
    algorithm="leiden",
    save_name="leiden_0.4",
    resolution=.4,
    leiden_beta=0.,
    adj_mat=nn_mat
)
kmer_collect.run_clustering(
    algorithm="leiden",
    save_name="leiden_0.2",
    resolution=.2,
    leiden_beta=0.,
    adj_mat=nn_mat
)
kmer_collect.run_clustering(
    algorithm="leiden",
    save_name="leiden_0.1",
    resolution=.1,
    leiden_beta=0.,
    adj_mat=nn_mat
)

# plot Leiden embedding
fig, ax = plt.subplots(2, 2, figsize=(8, 8))
x_umap = kmer_collect.x_umap["umap"]  # get UMAP coordinates
idc = np.arange(x_umap.shape[0])
np.random.shuffle(idc)  # randomly shuffle indices

scat = ax.reshape(-1)[0].scatter(
    x_umap[idc, 0],
    x_umap[idc, 1],
    marker=".",
    s=1.,
    cmap="jet",
    c=kmer_collect.clustering["leiden_0.1"][idc],  # set Leiden clustering as color vector
)
ax.reshape(-1)[0].set_title(r"$\sigma=0.1$")

scat = ax.reshape(-1)[1].scatter(
    x_umap[idc, 0],
    x_umap[idc, 1],
    marker=".",
    s=1.,
    cmap="jet",
    c=kmer_collect.clustering["leiden_0.2"][idc],
)
ax.reshape(-1)[1].set_title(r"$\sigma=0.2$")

scat = ax.reshape(-1)[2].scatter(
    x_umap[idc, 0],
    x_umap[idc, 1],
    marker=".",
    s=1.,
    cmap="jet",
    c=kmer_collect.clustering["leiden_0.4"][idc],
)
ax.reshape(-1)[2].set_title(r"$\sigma=0.4$")

scat = ax.reshape(-1)[3].scatter(
    x_umap[idc, 0],
    x_umap[idc, 1],
    marker=".",
    s=1.,
    cmap="jet",
    c=kmer_collect.clustering["leiden_0.6"][idc],
)
ax.reshape(-1)[3].set_title(r"$\sigma=0.6$")

fig.suptitle("Leiden clusters")
fig.tight_layout()
plt.show()
```

Note that this example is not exhaustive. You can equally perform label transfer and TFBS enrichment analysis. But these steps depend more on your research question in mind. Please see our [documentation and tutorials](http://cofugeno.pages.pasteur.fr/spyce/) for more information.

## Reference
If you found sPYce helpful for your own work, please consider citing.

> Zeitler, Leo, and Camille Berthelot. "Alignment-free integration of single-nucleus ATAC-seq across species with sPYce." bioRxiv (2025): 2025-05.

or

```
@article{zeitler2025sPYce,
  title={Alignment-free integration of single-nucleus ATAC-seq across species with sPYce},
  author={Zeitler, Leo and Berthelot, Camille},
  journal={bioRxiv},
  pages={2025--05},
  year={2025},
  publisher={Cold Spring Harbor Laboratory}
}
```
