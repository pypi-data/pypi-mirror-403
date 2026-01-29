import sys
from pathlib import Path
import matplotlib.pyplot as plt
from typing import List, Tuple
import argparse


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
        "--norm", type=str, default="centered_sum",
        help="Normalization for KMer matrices. Choose between none | max_norm | sum_norm | centered_sum | "
             "centered_max | centered_uniform_sum | centered_uniform_max."
    )
    parser.add_argument(
        "--max_region_size", type=int, default=701,
        help="Maximum peak size that is included for KMer creation."
    )
    parser.add_argument(
        "--n_policy", type=str, default="remove",
        help="How to deal with indeterministic sequence parts. Choose between remove | replace | keep."
    )
    parser.add_argument(
        "--mask_rep", action="store_true", dest="mask_rep",
        help="If set, mask repetitive sequences and don't consider them for KMer creation."
    )
    parser.add_argument(
        "--equalize_counter", action="store_true", dest="equalize_counter",
        help="If set, treat forward and reverse complement kmer as the same kmer, e.g. `ACGC` counts are "
            "added to `GCGT` counts."
    )
    parser.add_argument(
        "--verbosity", type=int, default=2,
        help="Verbosity level. Set to -1 for no output, 0 for only printing warnings and 1 for complete output."
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
        "--correct_gc", action="store_true", dest="correct_gc",
        help="If set, correct for GC distribution. The GC content per cell must then match the global GC "
            "content in all peaks."
    )
    parser.add_argument(
        "--n_jobs", type=int, default=8,
        help="Number of CPUs used."
    )
    args, addition_arg_list = parser.parse_known_args(args)
    addition_args = {opt_arg.split("=")[0].replace("--", ""): opt_arg.split("=")[1]
                     for opt_arg in addition_arg_list}
    return args, addition_args


def main():
    args_list = sys.argv[1:]
    args, optional_args = parse_args(args_list)

    from spyce.utils import load_specifications
    from spyce.kmerMatrix import KMerCollection
    setup_file_path = args.setup_file
    k = args.k
    ell = args.ell
    normalization = args.norm
    n_policy = args.n_policy
    mask_rep = args.mask_rep
    equalize_counter = args.equalize_counter
    verbosity = args.verbosity
    data_path = args.data_path
    fig_path = args.fig_path
    save_prefix = args.save_prefix
    correct_gc = args.correct_gc
    max_region_size = args.max_region_size
    n_jobs = args.n_jobs

    Path(data_path).mkdir(exist_ok=True, parents=True)
    Path(fig_path).mkdir(exist_ok=True, parents=True)
    setup_dict = load_specifications(setup_file_path)
    kmer_collect = KMerCollection(
        setup_dict=setup_dict,
        k=k,
        ell=ell,
        verbosity=verbosity,
        n_jobs=n_jobs,
        normalization=normalization,
        n_policy=n_policy,
        correct_gc=correct_gc,
        equalize_counter=equalize_counter,
        mask_rep=mask_rep,
        max_region_size=max_region_size
    )
    if verbosity > 0:
        print("Finished creating KMer collection, save to file.")
    save_path = "%s/%skmer_collection_obj.pkl" % (data_path, save_prefix)
    kmer_collect.save(path=save_path, save_prefix=save_prefix)


if __name__ == '__main__':
    main()

