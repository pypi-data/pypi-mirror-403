import sys
from pathlib import Path
import matplotlib.pyplot as plt
from typing import List, Tuple
import argparse

from spyce.utils import load_specifications
from spyce.kmerMatrix import KMerCollection
from spyce.plotting import plot_umap


def parse_args(args: List[str]) -> Tuple[argparse.Namespace, dict]:
    parser = argparse.ArgumentParser("Embed binary single cell/nucleus sequencing data using k-mer fragmentation over "
                                     "single and across species.")
    parser.add_argument(
        "--setup_file", type=str, required=True,
        help="Path to setup file in framework-specific .embed format."
    )
    parser.add_argument(
        "--k", type=int, default=5,
        help="Length of sequences."
    )
    parser.add_argument(
        "--ell", type=int, 
        help="If passed, use gapped k-mers with ell being the full length. If not passed, no gapped k-mers are used and k represents"
            "the full k-mer length"
    )
    parser.add_argument(
        "--verbosity", type=int, default=2,
        help="Verbosity level. Set to -1 for no output, 0 for only printing warnings and 1 for complete output."
    )
    parser.add_argument(
        "--dr", type=str,
        help="Dimensionality reduction method that is used. It is recommended to use a dimensionality reduction "
             "when k > 5. If none passed, none is performed."
    )
    parser.add_argument(
        "--clustering_per_sample", type=str,
        help="If set, use this algorithm to cluster each sample individually according to its k-mer histogram. "
             "Choose between (not case-sensitive) leiden | KMeans | DBSCAN | OPTICS | hierarchical_KMeans. "
             "Their behavior can be specified by passing additional cml-parameters (see documentation)."
    )
    parser.add_argument(
        "--sample_cluster_name", type=str, default="clustering",
        help="Name used for saving the clustering result in object."
    )
    parser.add_argument(
        "--clustering_total", type=str,
        help="If set, use this algorithm to cluster the entire data set (e.g. across conditions or species) using the "
             "combined k-mer histogram. "
             "Choose between (not case-sensitive) leiden | KMeans | DBSCAN | OPTICS | hierarchical_KMeans. "
             "Their behavior can be specified by passing additional cml-parameters (see documentation)."
    )
    parser.add_argument(
        "--total_cluster_name", type=str, default="clustering",
        help="Name used for saving the clustering result in object."
    )
    parser.add_argument(
        "--seed", type=int,
        help="If set, use a seed to create reproducible results. Note that not all clustering algorithms accept seeds."
    )
    parser.add_argument(
        "--n_umap_neighbors", type=int, default=15,
        help="Number of nearest neighbors used for UMAP embedding."
    )
    parser.add_argument(
        "--umap_metric", type=str, default="euclidean",
        help="Metric used for calculating UMAP. See https://umap-learn.readthedocs.io/en/latest/parameters.html#metric."
    )
    parser.add_argument(
        "--umap_min_dist", type=float, default=.1,
        help="Minimum distance used for UMAP embedding."
    )
    parser.add_argument(
        "--n_umap_comp", type=int, default=2,
        help="Dimension of UMAP manifold. "
             "For plotting this value needs to be 1 <= n_umap_comp <= 3 or will otherwise fail."
    )
    parser.add_argument(
        "--color_key", action="append", type=str,
        help="Set according to which values in UMAP embedding should be colored during plotting. This value can be "
             "species | matrix | the clustering used (pass total_cluster_name or sample_cluster_name) | "
             "additional cell values that were either present in h5ad files defined in setup_file or in "
             "separate tables defined in setup_file (see documentation). Default is matrix."
    )
    parser.add_argument(
        "--cmap", type=str, default="nipy_spectral",
        help="Type of color map used for plotting. "
             "See https://matplotlib.org/stable/users/explain/colors/colormaps.html"
    )
    parser.add_argument(
        "--data_path", type=str, default="./",
        help="Data output directory."
    )
    parser.add_argument(
        "--fig_path", type=str, default="./",
        help="Figure output directory."
    )
    parser.add_argument(
        "--save_prefix", type=str, default="",
        help="Save prefix added to saved file names."
    )
    parser.add_argument(
        "--n_jobs", type=int, default=8,
        help="Number of CPUs used."
    )
    args, addition_arg_list = parser.parse_known_args(args)
    addition_args = {opt_arg.split("=")[0].replace("--", ""): opt_arg.split("=")[1]
                     for opt_arg in addition_arg_list}
    return args, addition_args


def main(args_list: List[str]):
    args, optional_args = parse_args(args_list)
    setup_file_path = args.setup_file
    k = args.k
    ell = args.ell
    verbosity = args.verbosity
    clustering_per_sample = args.clustering_per_sample
    clustering_total = args.clustering_total
    seed = args.seed
    clustering_name_per_sample = args.sample_cluster_name
    clustering_name_total = args.total_cluster_name
    n_umap_neighbors = args.n_umap_neighbors
    dr = args.dr
    umap_metric = args.umap_metric
    umap_min_dist = args.umap_min_dist
    n_umap_comp = args.n_umap_comp
    color_key = args.color_key if args.color_key is not None else ["matrix"]
    cmap = args.cmap
    data_path = args.data_path
    fig_path = args.fig_path
    save_prefix = args.save_prefix
    n_jobs = args.n_jobs

    Path(data_path).mkdir(exist_ok=True, parents=True)
    Path(fig_path).mkdir(exist_ok=True, parents=True)
    setup_dict = load_specifications(setup_file_path)
    kmer_collect = KMerCollection(setup_dict=setup_dict, k=k, ell=ell, verbosity=verbosity, n_jobs=n_jobs)

    if dr is not None:
        if verbosity > 0:
            print("Perform dimensionality reduction.")
        kmer_collect.reduce_dimensionality(
            algorithm=dr,
            seed=seed,
            save_name=dr,
            verbosity_indent="\t",
            n_jobs=n_jobs
        )

    if clustering_per_sample is not None:
        if verbosity > 0:
            print("Perform clustering per data sample")
        for kmer_mat in kmer_collect.kmer_mat_list:
            kmer_mat.cluster(
                algorithm=clustering_per_sample,
                seed=seed,
                save_name=clustering_name_per_sample,
                verbosity_indent="\t",
                n_jobs=n_jobs,
                **optional_args
            )

    if clustering_total is not None:
        if verbosity > 0:
            print("Perform clustering over the entire dataset")
        kmer_collect.run_clustering(
            algorithm=clustering_total,
            dr_name=dr,
            seed=seed,
            save_name=clustering_name_total,
            verbosity_indent="\t",
            n_jobs=n_jobs,
            **optional_args
        )

    if verbosity > 0:
        print("Compute UMAP of entire dataset.")

    kmer_collect.umap(
        n_neighbors=n_umap_neighbors,
        dr_name=dr,
        metric=umap_metric,
        min_dist=umap_min_dist,
        n_components=n_umap_comp,
        verbosity_indent="\t"
    )

    if data_path is not None:
        save_path = "%s/%skmer_collection_obj.pkl" % (data_path, save_prefix)
        if verbosity > 0:
            print("Save KMerCollection object under %s" % save_path)
        kmer_collect.save(path=save_path)

    if verbosity > 0:
        print("Start plotting KMer embedding over entire data set")

    for ck in color_key:
        if verbosity > 0:
            print("\tColor plot w.r.t. %s" % ck)
        fig, ax = plot_umap(
            kmer_obj=kmer_collect,
            ck=ck,
            randomize=True,
            title=ck,
            cmap=cmap,
            verbosity=verbosity
        )
        fig.savefig("%s/%s%s.pdf" % (fig_path, save_prefix, ck), dpi=300)
        plt.close(fig)


if __name__ == "__main__":
    main(sys.argv[1:])


