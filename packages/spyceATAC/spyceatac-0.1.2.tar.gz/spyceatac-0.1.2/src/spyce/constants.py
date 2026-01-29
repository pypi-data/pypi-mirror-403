#: Letters in the DNA code.
DNA_ALPHABET = ["A", "C", "G", "T"]
#: Letters in the RNA code.
RNA_ALPHABET = ["A", "C", "G", "U"]
#: DNA colors for plotting. There is no known convention for colour code, see discussion here https://www.biostars.org/p/171056/
DNA_ALPHABET_COLOR = {"A": "tab:blue", "C": "tab:orange", "G": "tab:green", "T": "tab:red"}
#: Maximum value for k until which sPYce will use a dense matrix representation. Note that most k-mers are normally present, and using a sparse matrix does not reduce memory when using k too low.
MAX_K_DENSE = 15
#: Strings that are used for GC content correction.
GC_CONTENT = ["C", "G"]
GC_TUPLE = ["CC", "CG", "GC", "GG"]
#: URL where to report a bug.
BUG_REPORT = "https://gitlab.pasteur.fr/cofugeno/spyce/-/issues"
