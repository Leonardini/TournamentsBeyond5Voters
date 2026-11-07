#!/usr/bin/env Rscript
# make_chunks10.R INFILE OUTDIR [CHUNKSIZE] — split McKay's order-10 tournament catalogue into the
# chunked-RData input that solve_ilp10.R (chunk mode) expects. Each chunk_%03d.RData holds one object
# `G`, a list of 10x10 integer adjacency matrices (A[i,j]=1 means arc i->j). Streams the file, so memory
# stays constant (the whole catalogue as matrices would be ~10 GB in one go).
#
# INFILE  = McKay's order-10 catalogue, one tournament per line as C(10,2)=45 upper-triangular bits
#           (447 MB, too large to ship in this repo: fetch it once with `./get_data.sh n10` from
#            n12_unit_margin/, which downloads and verifies it into ../data/mckay/tournaments10.txt).
# OUTDIR  = directory to fill with chunk_000.RData, chunk_001.RData, ...
# CHUNKSIZE (default 10000) keeps the chunk count under 1000 for the full 9,733,056 catalogue (%03d).
#
# Run from this folder, e.g.:  Rscript make_chunks10.R ../data/mckay/tournaments10.txt out/chunks10

args <- commandArgs(trailingOnly = TRUE)
infile <- args[1]; outdir <- args[2]
chunksize <- if (length(args) >= 3) as.integer(args[3]) else 10000L
n <- 10
pu <- do.call(rbind, lapply(1:(n - 1), function(i) cbind(i, (i + 1):n))); pl <- pu[, c(2, 1)]
dir.create(outdir, showWarnings = FALSE, recursive = TRUE)

con <- file(infile, "r"); w <- 0L; tot <- 0L
repeat {
  lines <- readLines(con, n = chunksize); lines <- lines[nchar(lines) > 0]
  if (length(lines) == 0L) break
  G <- lapply(lines, function(s) { b <- utf8ToInt(s) - 48L; A <- matrix(0L, n, n); A[pu] <- b; A[pl] <- 1L - b; A })
  save(G, file = file.path(outdir, sprintf("chunk_%03d.RData", w)))
  tot <- tot + length(G); w <- w + 1L
}
close(con)
cat(sprintf("done: %d chunks, %d tournaments -> %s\n", w, tot, outdir))
cat(sprintf("now run the workers, e.g.:  for i in $(seq 0 %d); do Rscript solve_ilp10.R $i %d %s out; done\n",
            w - 1L, w, outdir))
