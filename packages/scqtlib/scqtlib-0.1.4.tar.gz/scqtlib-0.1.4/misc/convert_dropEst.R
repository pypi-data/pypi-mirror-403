# Run with Rscript: Rscript convert_dropEst.R FULL_PATH_matrices.rds

library('Matrix')

read_matched_dropEst <- function(matrix_file) {
    dat = readRDS(matrix_file)
    cell_ids = colnames(dat$exon)
    
    # gene names
    g_exon = rownames(dat$exon)
    g_intron = rownames(dat$intron)
    g_spanning = rownames(dat$spanning)
    
    g_union = base::union(g_exon, c(g_intron, g_spanning))
    # length(g_union)
    
    ## Make expaned sparse matrix
    mxt_base <- Matrix::Matrix(c(0), length(g_union), length(cell_ids))
    rownames(mxt_base) <- g_union
    colnames(mxt_base) <- cell_ids
    
    mxt_exon <- mxt_intron <- mxt_spanning <- mxt_base
    
    mxt_exon[match(g_exon, g_union), ] <- dat$exon
    mxt_intron[match(g_intron, g_union), ] <- dat$intron
    mxt_spanning[match(g_spanning, g_union), ] <- dat$spanning
    
    list('exon'=mxt_exon, 'intron'=mxt_intron, 'spanning'=mxt_spanning)
}

write_matched_dropEst <- function(dat, out_dir) {
    Matrix::writeMM(dat$exon, paste0(out_dir, '/cell.counts.exon.mtx'))
    Matrix::writeMM(dat$intron, paste0(out_dir, '/cell.counts.intron.mtx'))
    Matrix::writeMM(dat$spanning, paste0(out_dir, '/cell.counts.spanning.mtx'))
    
    write.table(colnames(dat$exon), paste0(out_dir, '/barcodes.tsv'), 
                quote=FALSE, row.names=FALSE, col.names=FALSE)
    
    write.table(rownames(dat$exon), paste0(out_dir, '/genes.tsv'), 
            quote=FALSE, row.names=FALSE, col.names=FALSE)
}

## load args for RScript
args <- commandArgs(TRUE)
if (length(args) >= 1) {
    dropest_file <- as.character(args[1])
} else {
    stop("Please provide dropEst matrices rds file!")
}

# read data and match genes
dat <- read_matched_dropEst(dropest_file)

# write data into mtx files & tsv files for gene and cell names
write_matched_dropEst(dat, dirname(dropest_file))
