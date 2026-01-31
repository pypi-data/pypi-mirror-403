# This file is to filter the 10x raw matrix with custermised 
# minimun counts for a cell

import sys
from optparse import OptionParser
from ..utils.io_utils import load_10X, save_10X


def main():
    # import warnings
    # warnings.filterwarnings('error')

    # parse command line options
    parser = OptionParser()

    parser.add_option("--inDir", "-i", dest="in_dir", default=None,
        help="Input path for loading raw matrix")
    parser.add_option("--outDir", "-o", dest="out_dir", default=None, 
        help="Output path for saving filtered matrix")
    parser.add_option("--minCount", dest="min_count", type="float", default=None, 
        help="Minimum read counts for effective cell [default: 0]")
    parser.add_option("--minCell", dest="min_cell", type="float", default=None, 
        help="Minimum cells for keeping a gene [default: 0]")
    parser.add_option("--barcodes", dest="barcodes", default=None, 
        help="Cell barcodes to keep [default: None]")
    parser.add_option("--cellranger3", "-3", dest="cellranger3", 
        action="store_true", default=False, 
        help="Use it for cellranger v3 instead of v2")
    
    
    (options, args) = parser.parse_args()
    if len(sys.argv[1:]) == 0:
        print("Welcome to filter-10x-raw!\n")
        print("use -h or --help for help on argument.")
        sys.exit(1)
    
    # Load input files
    CRv3 = options.cellranger3
    mat, genes, cells = load_10X(options.in_dir, min_counts=options.min_count, 
                                 min_cells=options.min_cell, version3=CRv3)
    print("%d cells %d genes are loaded." %(cells.shape[0], genes.shape[0]))
    
    # Filter cells
    if options.barcodes is not None:
        import hilearn
        import numpy as np
        cells_use = np.genfromtxt(options.barcodes, dtype='str')[:, 0]
        idx = hilearn.match(cells_use, cells)
        ## TODO: check if cells_use all included in cells
        
        mat = mat[:, idx]
        cells = cells[idx]
    
    # Save output files
    save_10X(path=options.out_dir, mat=mat, genes=genes, 
             barcodes=cells, version3=False)
    
    
if __name__ == "__main__":
    main()

    